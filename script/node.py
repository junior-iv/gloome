import pandas as pd
import numpy as np

from typing import Optional, Dict, Union, List, Tuple, Any
from scipy.linalg import expm
from math import log, prod

eps = 5e-324


class Node:
    father: Optional['Node']
    children: List['Node']
    name: str
    distance_to_father: Union[float, np.ndarray]
    log_likelihood_vector: List[Union[float, np.ndarray]]
    log_likelihood: Union[float, np.ndarray]
    sequence_likelihood: Union[float, np.ndarray]
    likelihood: Union[float, np.ndarray]
    up_vector: List[List[Union[float, np.ndarray]]]
    down_vector: List[List[Union[float, np.ndarray]]]
    marginal_vector: List[List[Union[float, np.ndarray]]]
    probability_vector: List[Union[float, np.ndarray]]
    branch_probability_vector: List[List[Union[float, np.ndarray]]]
    probability_vector_gain: List[Union[float, np.ndarray]]
    probability_vector_loss: List[Union[float, np.ndarray]]
    probable_character: str
    sequence: str
    probabilities_sequence_characters: List[Union[float, np.ndarray]]
    ancestral_sequence: str
    coefficient_bl: Union[float, np.ndarray, int]
    pmatrix: List[np.ndarray]

    def __init__(self, name: Optional[str]) -> None:
        self.father = None
        self.children = []
        self.name = name
        self.distance_to_father = 0.0
        self.log_likelihood_vector = []
        self.log_likelihood = 0.0
        self.sequence_likelihood = 1.0
        self.likelihood = 0.0
        self.up_vector = []
        self.down_vector = []
        self.marginal_vector = []
        self.probability_vector = []
        self.branch_probability_vector = []
        self.probability_vector_gain = []
        self.probability_vector_loss = []
        self.probable_character = ''
        self.sequence = ''
        self.probabilities_sequence_characters = []
        self.ancestral_sequence = ''
        self.coefficient_bl = 1
        self.pmatrix = []

    def __str__(self) -> str:
        return self.get_name(True)

    def __dir__(self) -> list:
        return ['children', 'distance_to_father', 'father', 'name', 'up_vector', 'down_vector', 'likelihood',
                'marginal_vector', 'probability_vector', 'probable_character', 'sequence',
                'probabilities_sequence_characters', 'ancestral_sequence', 'branch_probability_vector',
                'probability_vector_gain', 'probability_vector_loss']

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
                self.up_vector, 'down_vector': self.down_vector, 'likelihood': self.likelihood, 'sequence_likelihood':
                self.sequence_likelihood, 'log_likelihood': self.log_likelihood, 'log_likelihood_vector':
                self.log_likelihood_vector, 'marginal_vector': self.marginal_vector, 'probability_vector':
                self.probability_vector, 'probable_character': self.probable_character, 'sequence': self.sequence,
                'probabilities_sequence_characters': self.probabilities_sequence_characters, 'ancestral_sequence':
                self.ancestral_sequence, 'branch_probability_vector': self.branch_probability_vector,
                'probability_vector_gain': self.probability_vector_gain, 'probability_vector_loss':
                self.probability_vector_loss}

    def get_node_by_name(self, node_name: str) -> Optional['Node']:
        if node_name == self.name:
            return self
        else:
            for child in self.children:
                newick_node = child.get_node_by_name(node_name)
                if newick_node:
                    return newick_node
        return None

    def get_pmatrix(self, alphabet_size: int, rate: Union[float, np.ndarray] = 1.0, pi_0: Optional[float] = None,
                    pi_1: Optional[float] = None) -> np.ndarray:
        return self.get_one_parameter_pmatrix(rate, pi_0, pi_1, alphabet_size)

    def calculate_sequence_likelihood(self) -> None:
        self.sequence_likelihood *= self.likelihood
        self.log_likelihood += log(max(self.likelihood, eps))
        self.log_likelihood_vector.append(log(max(self.likelihood, eps)))

    def calculate_gl_probability(self, alphabet: Union[Tuple[str, ...], str],
                                 rate_vector: Optional[Tuple[Union[float, np.ndarray], ...]] = None,
                                 pi_0: Optional[float] = None, pi_1: Optional[float] = None) -> None:
        alphabet_size, rate_vector, rate_vector_size, frequency = self.get_vars(alphabet, rate_vector, pi_0, pi_1)
        marginal_bl_vector = []
        if not self.pmatrix:
            self.pmatrix = [self.get_pmatrix(alphabet_size, r, pi_0, pi_1) for r in rate_vector]

        for r in range(rate_vector_size):
            current_marginal_bl_vector = []
            for j in range(alphabet_size):
                for i in range(alphabet_size):
                    current_marginal_bl_vector.append(frequency[i] * self.up_vector[r][i] *
                                                      self.pmatrix[r][i, j] * self.down_vector[r][j])
            marginal_bl_vector.append(current_marginal_bl_vector)

        likelihood = np.sum([1 / rate_vector_size * np.sum(self.father.marginal_vector[r]) for r in
                             range(rate_vector_size)])
        likelihood = max(likelihood, eps)

        branch_probability_vector = []
        for i in range(alphabet_size * alphabet_size):
            branch_probability_vector.append(np.sum([marginal_bl_vector[r][i] for r in range(rate_vector_size)]) /
                                             rate_vector_size / likelihood)
        self.branch_probability_vector.append(branch_probability_vector)
        self.probability_vector_gain.append(branch_probability_vector[1])
        self.probability_vector_loss.append(branch_probability_vector[2])

    def calculate_marginal(self, alphabet: Union[Tuple[str, ...], str],
                           rate_vector: Optional[Tuple[Union[float, np.ndarray], ...]] = None,
                           pi_0: Optional[float] = None, pi_1: Optional[float] = None
                           ) -> Tuple[Union[Union[List[List[np.ndarray]], List[List[float]]], float],
                                      Union[np.ndarray, float]]:
        alphabet_size, rate_vector, rate_vector_size, frequency = self.get_vars(alphabet, rate_vector, pi_0, pi_1)
        self.marginal_vector = []
        if not self.pmatrix:
            self.pmatrix = [self.get_pmatrix(alphabet_size, r, pi_0, pi_1) for r in rate_vector]

        for r in range(rate_vector_size):
            current_marginal_vector = []
            for i in range(alphabet_size):
                marg = 0
                for j in range(alphabet_size):
                    marg += self.pmatrix[r][i, j] * self.down_vector[r][j]
                current_marginal_vector.append(frequency[i] * self.up_vector[r][i] * marg)
            self.marginal_vector.append(current_marginal_vector)

        likelihood = np.sum([1 / rate_vector_size * np.sum(self.marginal_vector[r]) for r in range(rate_vector_size)])
        likelihood = max(likelihood, eps)

        self.probability_vector = []
        for i in range(alphabet_size):
            self.probability_vector.append(np.sum([self.marginal_vector[r][i] for r in range(rate_vector_size)]) /
                                           rate_vector_size / likelihood)
        self.probable_character = alphabet[self.probability_vector.index(max(self.probability_vector))]
        self.sequence = f'{self.sequence}{self.probable_character}'
        self.probabilities_sequence_characters += [max(self.probability_vector)]

        return self.marginal_vector, likelihood

    def calculate_up(self, nodes_dict: Dict[str, Tuple[int, ...]], alphabet: Union[Tuple[str, ...], str],
                     rate_vector: Optional[Tuple[Union[float, np.ndarray], ...]] = None, pi_0: Optional[float] = None,
                     pi_1: Optional[float] = None, alphabet_size: Optional[int] = None,
                     rate_vector_size: Optional[int] = None,
                     frequency: Optional[Tuple[Union[float, np.ndarray], ...]] = None) -> Union[Union[List[List[np.ndarray]], List[List[float]]], float]:
        if None in (alphabet_size, rate_vector, rate_vector_size, frequency):
            alphabet_size, rate_vector, rate_vector_size, frequency = self.get_vars(alphabet, rate_vector, pi_0, pi_1)
        if not self.pmatrix:
            self.pmatrix = [self.get_pmatrix(alphabet_size, r, pi_0, pi_1) for r in rate_vector]

        self.up_vector = []
        self.likelihood = 0

        if not self.children:
            up_vector = list(nodes_dict.get(self.name))
            self.likelihood = np.sum([frequency[up_vector.index(max(up_vector))] * 1 / rate_vector_size * i for i in
                                      up_vector])
            self.probable_character = alphabet[up_vector.index(max(up_vector))]
            self.sequence = f'{self.sequence}{self.probable_character}'
            self.probabilities_sequence_characters += [max(up_vector)]
            self.up_vector = [up_vector for _ in range(rate_vector_size)]

            self.calculate_sequence_likelihood()

            return self.up_vector

        for child in self.children:
            child.calculate_up(nodes_dict, alphabet, rate_vector, pi_0, pi_1, alphabet_size, rate_vector_size,
                               frequency)

        for r in range(rate_vector_size):
            current_up_vector = []
            for j in range(alphabet_size):
                probabilities = {}
                for i in range(alphabet_size):
                    for child in self.children:
                        p1 = child.pmatrix[r][j, i] * child.up_vector[r][i]
                        probabilities.update({child.name: probabilities.get(child.name, 0.0) + p1})

                current_up_vector.append(prod(probabilities.values()))
            self.up_vector.append(current_up_vector)
            self.likelihood += np.sum([frequency[i] * 1 / rate_vector_size * v for i, v in
                                       enumerate(current_up_vector)])

        self.calculate_sequence_likelihood()

        if self.father:
            return self.up_vector
        else:
            return self.likelihood

    def calculate_down(self, tree_info: pd.Series, alphabet_size: int,
                       rate_vector: Optional[Tuple[Union[float, np.ndarray], ...]] = None,
                       pi_0: Optional[float] = None, pi_1: Optional[float] = None) -> None:
        rate_vector = rate_vector if rate_vector else (1.0,)
        rate_vector_size = len(rate_vector)
        self.down_vector = []
        if not self.pmatrix:
            self.pmatrix = [self.get_pmatrix(alphabet_size, r, pi_0, pi_1) for r in rate_vector]

        father = self.father
        if father:
            brothers = [father.get_node_by_name(i) for i in tree_info.get(father.name).get('children') if i !=
                        self.name]
            for brother in brothers:
                if not brother.pmatrix:
                    brother.pmatrix = [self.get_pmatrix(alphabet_size, r, pi_0, pi_1) for r in rate_vector]

            if not father.pmatrix:
                father.pmatrix = [self.get_pmatrix(alphabet_size, r, pi_0, pi_1) for r in rate_vector]
            for r in range(rate_vector_size):
                current_down_vector = []
                for j in range(alphabet_size):
                    probabilities = {}
                    for i in range(alphabet_size):
                        for brother in brothers:
                            probabilities.update(
                                {brother.name:
                                 probabilities.get(brother.name, 0) + (brother.pmatrix[r][j, i] *
                                                                       brother.up_vector[r][i])})
                        probabilities.update(
                            {father.name: probabilities.get(father.name, 0) + (father.pmatrix[r][j, i] *
                                                                               father.down_vector[r][i])})

                    current_down_vector.append(prod(probabilities.values()))
                self.down_vector.append(current_down_vector)

            for child in self.children:
                child.calculate_down(tree_info, alphabet_size, rate_vector, pi_0, pi_1)
        else:
            self.down_vector = [[1] * alphabet_size for _ in range(rate_vector_size)]
            for child in self.children:
                child.calculate_down(tree_info, alphabet_size, rate_vector, pi_0, pi_1)

    def clean_all(self):
        for current_node in self.get_list_nodes_info(only_node_list=True):
            current_node.log_likelihood_vector = []
            current_node.log_likelihood = 0.0
            current_node.sequence_likelihood = 1.0
            current_node.likelihood = 0.0
            current_node.up_vector = []
            current_node.down_vector = []
            current_node.marginal_vector = []
            current_node.probability_vector = []
            current_node.branch_probability_vector = []
            current_node.probability_vector_gain = []
            current_node.probability_vector_loss = []
            current_node.probable_character = ''
            current_node.sequence = ''
            current_node.probabilities_sequence_characters = []
            current_node.ancestral_sequence = ''
            current_node.coefficient_bl = 1
            current_node.pmatrix = []

    def calculate_likelihood(self, msa_dict: Dict[str, str], alphabet: Union[Tuple[str, ...], str],
                             rate_vector: Optional[Tuple[Union[float, np.ndarray], ...]] = None,
                             pi_0: Optional[float] = None, pi_1: Optional[float] = None, alphabet_size: int = None,
                             rate_vector_size: int = None, frequency: Tuple[Union[float, np.ndarray], ...] = None) -> Tuple[List[float], float, float]:

        leaves_info = self.get_list_nodes_info(True, 'pre-order', {'node_type': ['leaf']})

        len_seq = len(min(list(msa_dict.values())))
        likelihood, log_likelihood, log_likelihood_list = 1, 0, []
        if None in (alphabet_size, rate_vector, rate_vector_size, frequency):
            alphabet_size, rate_vector, rate_vector_size, frequency = self.get_vars(alphabet, rate_vector, pi_0, pi_1)
        if not self.pmatrix:
            self.pmatrix = [self.get_pmatrix(alphabet_size, r, pi_0, pi_1) for r in rate_vector]
        for i_char in range(len_seq):
            nodes_dict = dict()
            for i in range(len(leaves_info)):
                node_name = leaves_info[i].get('node')
                character = msa_dict.get(node_name)[i_char]
                nodes_dict.update({node_name: tuple([int(j == character) for j in alphabet])})

            char_likelihood = self.calculate_up(nodes_dict, alphabet, rate_vector, pi_0, pi_1, alphabet_size,
                                                rate_vector_size, frequency)
            likelihood *= char_likelihood
            log_likelihood += log(max(char_likelihood, eps))
            log_likelihood_list.append(log(max(char_likelihood, eps)))

        return log_likelihood_list, log_likelihood, likelihood

    def get_one_parameter_pmatrix(self, rate: Union[float, np.ndarray] = 1, pi_0: Optional[float] = None,
                                  pi_1: Optional[float] = None, alphabet_size: int = 2) -> np.ndarray:
        qmatrix = np.zeros((2, 2), dtype='float32')
        pi_1 = pi_1 if pi_1 else 1 - (pi_0 if pi_0 else 1 / alphabet_size)

        qmatrix[0, 0] = - 1 / (2 * (1 - pi_1))
        qmatrix[0, 1] = 1 / (2 * (1 - pi_1))
        qmatrix[1, 0] = 1 / (2 * pi_1)
        qmatrix[1, 1] = - 1 / (2 * pi_1)

        return expm(qmatrix * (self.distance_to_father * self.coefficient_bl * rate))

    def get_jukes_cantor_pmatrix(self, alphabet_size: int, rate: Union[float, np.ndarray] = 1) -> np.ndarray:
        qmatrix = np.ones((alphabet_size, alphabet_size))
        np.fill_diagonal(qmatrix, 1 - alphabet_size)
        qmatrix = qmatrix * 1 / (alphabet_size - 1)

        return expm(qmatrix * (self.distance_to_father * self.coefficient_bl * rate))

    def node_to_json(self) -> Dict[str, Union[str, List[Any], float, np.ndarray]]:
        dict_json = dict()
        dict_json.update({'name': self.name})
        dict_json.update({'distance': str(self.distance_to_father)})

        if self.children:
            dict_json.update({'children': []})
            for child in self.children:
                dict_json['children'].append(child.node_to_json())

        return dict_json

    def subtree_to_newick(self, with_internal_nodes: bool = False, decimal_length: int = 0) -> str:
        """This method is for internal use only."""
        node_list = self.children
        if node_list:
            result = '('
            for child in node_list:
                if child.children:
                    child_name = child.subtree_to_newick(with_internal_nodes, decimal_length)
                else:
                    child_name = child.name
                result += f'{child_name}:' + f'{child.distance_to_father:.10f}'.ljust(decimal_length, '0') + ','
            result = f'{result[:-1]}){self.name if with_internal_nodes else ""}'
        else:
            result = f'{self.name}:' + f'{self.distance_to_father}'.ljust(decimal_length, '0')
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
    def get_vars(alphabet: Union[Tuple[str, ...], str],
                 rate_vector: Optional[Tuple[Union[float, np.ndarray], ...]] = None,
                 pi_0: Optional[float] = None, pi_1: Optional[float] = None
                 ) -> Tuple[int, Tuple[Union[float, np.ndarray], ...], int, Tuple[Union[float, np.ndarray], ...]]:
        alphabet_size = len(alphabet)
        rate_vector = rate_vector if rate_vector else (1.0,)
        rate_vector_size = len(rate_vector)
        if pi_0:
            frequency = (pi_0, 1 - pi_0)
        elif pi_1:
            frequency = (1 - pi_1, pi_1)
        else:
            frequency = (1 / alphabet_size, 1 / alphabet_size)
        # frequency = (pi_0, 1 - pi_0) if pi_0 else ((1 - pi_1, pi_1) if pi_1 else
        #                                            (1 / alphabet_size, 1 / alphabet_size))
        # frequency = pi_1 if pi_1 else 1 - (pi_0 if pi_0 else 1 / alphabet_size)

        return alphabet_size, rate_vector, rate_vector_size, frequency

    @staticmethod
    def get_integer(data: Union[str, int, float]) -> int:
        result = float(data) * 10

        return int(result - 1 if result == 10 else result)

    @staticmethod
    def draw_html_table(data: str) -> str:

        return f'<table class="w-97 p-4 tooltip">{data}</table>'

    @staticmethod
    def draw_row_html_table(name: str, data: str) -> str:

        return f'<tr><th class="p-2 h7 ">{name}:</th><th>{data}</td></th></tr>'

    @staticmethod
    def draw_cell_html_table(color: str, data: str) -> str:

        return f'<td style="color: {color}" class="h7 w-auto text-center">{data}</td>'

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
