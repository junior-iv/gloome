import pandas as pd
import numpy as np
from typing import Optional, Dict, Union, List, Tuple, Any
from scipy.linalg import expm
from math import log
from math import prod


class Node:
    father: Optional['Node']
    children: List['Node']
    name: str
    distance_to_father: Union[float, np.ndarray]
    likelihood: Union[float, np.ndarray]
    up_vector: List[Union[float, np.ndarray]]
    down_vector: List[Union[float, np.ndarray]]
    marginal_vector: List[Union[float, np.ndarray]]
    probability_vector: List[Union[float, np.ndarray]]
    probable_character: str
    sequence: str
    probabilities_sequence_characters: List[Union[float, np.ndarray]]

    def __init__(self, name: Optional[str]) -> None:
        self.father = None
        self.children = []
        self.name = name
        self.distance_to_father = 0.0
        self.likelihood = 0.0
        self.up_vector = []
        self.down_vector = []
        self.marginal_vector = []
        self.probability_vector = []
        self.probable_character = ''
        self.sequence = ''
        self.probabilities_sequence_characters = []

    def __str__(self) -> str:
        return self.get_name(True)

    def __dir__(self) -> list:
        return ['children', 'distance_to_father', 'father', 'name', 'up_vector', 'down_vector', 'likelihood',
                'marginal_vector', 'probability_vector', 'probable_character', 'sequence',
                'probabilities_sequence_characters']

    def get_list_nodes_info(self, with_additional_details: bool = False, mode: Optional[str] = None, filters:
                            Optional[Dict[str, List[Union[float, int, str, List[float]]]]] = None, only_node_list:
                            bool = False) -> List[Union[Dict[str, Union[float, np.ndarray, bool, str, List[float],
                                                  List[np.ndarray]]], 'Node']]:
        """
        Retrieve a list of descendant nodes from a given node, including the node itself or retrieve a list of
        descendant nodes from the current instance of the `Tree` class.

        This function collects all child nodes of the specified `node`, including the `node` itself, or collects all
        child nodes of the current instance of the `Tree` class if `node` is not provided. The function
        returns these nodes names as a list.

        Args:
            with_additional_details (bool, optional): `False` (default).
            mode (Optional[str]): `None` (default), 'pre-order', 'in-order', 'post-order', 'level-order'.
            filters (Dict, optional):
            only_node_list (Dict, optional): `False` (default).
        Returns:
            list: A list of nodes names including the specified `node` (or the current instance's nodes  names) and its
                                    children.
        """
        list_result = []
        mode = 'pre-order' if mode is None or mode.lower() not in ('pre-order', 'in-order', 'post-order', 'level-order'
                                                                   ) else mode.lower()
        condition = with_additional_details or only_node_list

        def get_list(trees_node: Node) -> None:
            nonlocal list_result, filters, mode, condition

            nodes_info = trees_node.get_nodes_info()
            list_item = trees_node if only_node_list else nodes_info
            if trees_node.check_filter_compliance(filters, nodes_info):
                if mode == 'pre-order':
                    list_result.append(list_item if condition else trees_node.name)

                for i, child in enumerate(trees_node.children):
                    get_list(child)
                    if mode == 'in-order' and not i:
                        list_result.append(list_item if condition else trees_node.name)

                if not trees_node.children:
                    if mode == 'in-order':
                        list_result.append(list_item if condition else trees_node.name)

                if mode == 'post-order':
                    list_result.append(list_item if condition else trees_node.name)
            else:
                for child in trees_node.children:
                    get_list(child)

        if mode == 'level-order':
            nodes_list = [self]
            while nodes_list:
                newick_node = nodes_list.pop(0)
                if newick_node.check_filter_compliance(filters, newick_node.get_nodes_info()):
                    level_order_item = newick_node if only_node_list else newick_node.get_nodes_info()
                    list_result.append(level_order_item if condition else newick_node.name)

                for nodes_child in newick_node.children:
                    nodes_list.append(nodes_child)
        else:
            get_list(self)

        return list_result

    def get_nodes_info(self) -> Dict[str, Union[float, np.ndarray, bool, str, List[float], List[np.ndarray]]]:
        lavel = 1
        full_distance = [self.distance_to_father]
        father = self.father
        if father:
            father_name = father.name
            node_type = 'node'
            while father:
                full_distance.append(father.distance_to_father)
                lavel += 1
                father = father.father
        else:
            father_name = ''
            node_type = 'root'

        if not self.children:
            node_type = 'leaf'

        return {'node': self.name, 'distance': full_distance[0], 'lavel': lavel, 'node_type': node_type, 'father_name':
                father_name, 'full_distance': full_distance, 'children': [i.name for i in self.children], 'up_vector':
                self.up_vector, 'down_vector': self.down_vector, 'likelihood': self.likelihood, 'marginal_vector':
                self.marginal_vector, 'probability_vector': self.probability_vector, 'probable_character':
                self.probable_character, 'sequence': self.sequence, 'probabilities_sequence_characters':
                self.probabilities_sequence_characters}

    def get_node_by_name(self, node_name: str) -> Optional['Node']:
        if node_name == self.name:
            return self
        else:
            for child in self.children:
                newick_node = child.get_node_by_name(node_name)
                if newick_node:
                    return newick_node
        return None

    def calculate_marginal(self, qmatrix: np.ndarray, alphabet: Union[Tuple[str, ...], str]
                           ) -> Tuple[Union[List[np.ndarray], List[float]], Union[np.ndarray, float]]:
        alphabet_size = len(alphabet)
        self.marginal_vector = []
        for i in range(alphabet_size):
            marg = 0
            for j in range(alphabet_size):
                marg += qmatrix[i, j] * self.down_vector[j]
            self.marginal_vector.append(1 / alphabet_size * self.up_vector[i] * marg)

        likelihood = np.sum(self.marginal_vector)

        self.probability_vector = []
        for i in range(alphabet_size):
            self.probability_vector.append(self.marginal_vector[i] / likelihood)
        self.probable_character = alphabet[self.probability_vector.index(max(self.probability_vector))]
        self.sequence = f'{self.sequence}{self.probable_character}'
        self.probabilities_sequence_characters += [max(self.probability_vector)]

        return self.marginal_vector, likelihood

    def calculate_up(self, nodes_dict: Dict[str, Tuple[int, ...]], alphabet: Union[Tuple[str, ...], str]
                     ) -> Union[Union[List[np.ndarray], List[float]], float]:
        alphabet_size = len(alphabet)
        if not self.children:
            self.up_vector = list(nodes_dict.get(self.name))
            self.likelihood = np.sum([1 / alphabet_size * i for i in self.up_vector])
            self.probable_character = alphabet[self.up_vector.index(max(self.up_vector))]
            self.sequence = f'{self.sequence}{self.probable_character}'
            self.probabilities_sequence_characters += [max(self.up_vector)]
            return self.up_vector

        dict_children = {}
        for child in self.children:
            dict_children.update({child.name: (child.get_jukes_cantor_qmatrix(alphabet_size),
                                               child.calculate_up(nodes_dict, alphabet))})

        self.up_vector = []
        for j in range(alphabet_size):
            probabilities = {}
            for i in range(alphabet_size):
                for child in self.children:
                    qmatrix, up_vector = dict_children.get(child.name)
                    probabilities.update({child.name: probabilities.get(child.name, 0) + (qmatrix[j, i] * up_vector[i])}
                                         )
            self.up_vector.append(prod(probabilities.values()))
        self.likelihood = np.sum([1 / alphabet_size * i for i in self.up_vector])

        if self.father:
            return self.up_vector
        else:
            return self.likelihood

    def calculate_down(self, tree_info: pd.Series, alphabet_size: int) -> None:
        father = self.father
        if father:
            dict_brothers = {}
            brothers = tuple(set(tree_info.get(father.name).get('children')) - {self.name})
            brothers = [father.get_node_by_name(i) for i in brothers]
            for brother in brothers:
                dict_brothers.update({brother.name: (brother.get_jukes_cantor_qmatrix(alphabet_size),
                                                     brother.up_vector)})

            f_vector = father.down_vector
            f_qmatrix = father.get_jukes_cantor_qmatrix(alphabet_size)
            self.down_vector = []
            for j in range(alphabet_size):
                probabilities = {}
                for i in range(alphabet_size):
                    for brother in brothers:
                        b_qmatrix, b_vector = dict_brothers.get(brother.name)
                        probabilities.update(
                            {brother.name: probabilities.get(brother.name, 0) + (b_qmatrix[j, i] * b_vector[i])})
                    probabilities.update(
                        {father.name: probabilities.get(father.name, 0) + (f_qmatrix[j, i] * f_vector[i])})

                self.down_vector.append(prod(probabilities.values()))

            for child in self.children:
                child.calculate_down(tree_info, alphabet_size)
        else:
            self.down_vector = [1] * alphabet_size
            for child in self.children:
                child.calculate_down(tree_info, alphabet_size)

    def calculate_likelihood_for_msa(self, pattern_msa_dict: Dict[str, str], alphabet: Union[Tuple[str, ...], str]
                                     ) -> Tuple[List[float], float, float]:

        leaves_info = self.get_list_nodes_info(True, 'pre-order', {'node_type': ['leaf']})

        len_seq = len(min(list(pattern_msa_dict.values())))
        likelihood, log_likelihood, log_likelihood_list = 1, 0, []
        for i_char in range(len_seq):
            nodes_dict = dict()
            for i in range(len(leaves_info)):
                node_name = leaves_info[i].get('node')
                character = pattern_msa_dict.get(node_name)[i_char]
                nodes_dict.update({node_name: tuple([int(j == character) for j in alphabet])})

            char_likelihood = self.calculate_up(nodes_dict, alphabet)
            likelihood *= char_likelihood
            log_likelihood += log(char_likelihood)
            log_likelihood_list.append(log(char_likelihood))

        return log_likelihood_list, log_likelihood, likelihood

    def get_jukes_cantor_qmatrix(self, alphabet_size: int) -> np.ndarray:
        qmatrix = np.ones((alphabet_size, alphabet_size))
        np.fill_diagonal(qmatrix, 1 - alphabet_size)
        qmatrix = qmatrix * 1 / (alphabet_size - 1)

        return expm(qmatrix * self.distance_to_father)

    def node_to_json(self, dict_json: Dict[str, Union[str, List[Any], float, np.ndarray]]
                     ) -> Dict[str, Union[str, List[Any], float, np.ndarray]]:
        sequence = '\t'.join([j for j in self.sequence])
        info = f'Name: {self.name}<br>Distance: {str(self.distance_to_father)}<br>Sequence: <br>{sequence}'
        dict_json.update({'name': self.name})
        dict_json.update({'info': info})
        dict_json.update({'distance': str(self.distance_to_father)})
        if self.children:
            probability_mark = '\t'.join(['9' if j == 1 else f'{int(j * 10)}'
                                          for j in self.probabilities_sequence_characters])
            probability_coefficient = ' '.join([f'{self.sequence[i]} [{j:.2f}]' for i, j in
                                                enumerate(self.probabilities_sequence_characters)])
            info += (f'<br>Probability mark (0-9): <br>{probability_mark}<br>Probability coefficient: <br>'
                     f'{probability_coefficient}')
            dict_json.update({'children': []})
            for child in self.children:
                dict_json['children'].append(child.node_to_json(dict()))
                dict_json.update({'info': info})

        return dict_json

    def subtree_to_newick(self, with_internal_nodes: bool = False, decimal_length: int = 0
                          ) -> str:
        """This method is for internal use only."""
        node_list = self.children
        if node_list:
            result = '('
            for child in node_list:
                if child.children:
                    child_name = child.subtree_to_newick(with_internal_nodes, decimal_length)
                else:
                    child_name = child.name
                result += f'{child_name}:{str(child.distance_to_father).ljust(decimal_length, "0")},'
            result = f'{result[:-1]}){self.name if with_internal_nodes else ""}'
        else:
            result = f'{self.name}:{str(self.distance_to_father).ljust(decimal_length, "0")}'
        return result

    def get_name(self, is_full_name: bool = False) -> str:
        return (f'{self.subtree_to_newick() if self.children and is_full_name else self.name}:'
                f'{self.distance_to_father:.6f}')

    def add_child(self, child: 'Node', distance_to_father: Optional[float] = None) -> None:
        self.children.append(child)
        child.father = self
        if distance_to_father is not None:
            child.distance_to_father = distance_to_father

    def get_full_distance_to_father(self, return_list: bool = False) -> Union[List[float], float]:
        list_result = []
        father = self
        while father:
            list_result.append({'node': father, 'distance': father.distance_to_father})
            father = father.father
        result = [i['distance'] for i in list_result]
        return result if return_list else sum(result)

    def get_full_distance_to_leaves(self, return_list: bool = False) -> Union[List[float], float]:
        list_result = []
        children = [self]
        while children:
            child = children.pop(0)
            list_result.append({'node': child, 'distance': child.distance_to_father})
            for ch in child.children:
                children.append(ch)
        result = [i['distance'] for i in list_result]
        return result if return_list else sum(result)

    @staticmethod
    def check_filter_compliance(filters: Optional[Dict[str, List[Union[float, int, str, List[float]]]]], info: Dict[str,
                                Union[float, bool, str, list[float]]]) -> bool:
        permission = 0
        if filters:
            for key in filters.keys():
                for value in filters.get(key):
                    permission += sum(k == key and info[k] == value for k in info)
        else:
            permission = 1

        return bool(permission)
