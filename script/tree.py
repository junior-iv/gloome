import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from shutil import rmtree
from json import loads
from os import path, makedirs
from d3blocks import D3Blocks
from .node import Node
from typing import Optional, List, Union, Dict, Tuple, Set, Any, Callable
from Bio import Phylo
from scipy.stats import gamma
from scipy.special import gammainc
from scipy.optimize import minimize_scalar


class Tree:
    root: Optional[Node] = None
    alphabet: Optional[Tuple[str, ...]] = None
    msa: Optional[Dict[str, str]] = None
    rate_vector: Tuple[Union[float, np.ndarray, int], ...] = (1.0, )
    alpha: Optional[Union[float, np.ndarray, int]] = None
    categories_quantity: Optional[int] = None
    pi_0: Optional[Union[float, np.ndarray, int]] = None
    pi_1: Optional[Union[float, np.ndarray, int]] = None
    coefficient_bl: Optional[Union[float, np.ndarray, int]] = 1,
    log_likelihood_vector: Optional[List[Union[float, np.ndarray]]] = None
    log_likelihood: Optional[Union[float, np.ndarray]] = None
    likelihood: Optional[Union[float, np.ndarray]] = None
    calculated_ancestor_sequence: bool = False
    calculated_tree_for_fasta: bool = False
    calculated_likelihood: bool = False

    def __init__(self, data: Optional[Union[str, Node]] = None, node_name: Optional[str] = None, **kwargs) -> None:
        """
        Parameters
        ----------
            data: Optional[Union[str, Node]] = None
            node_name: Optional[str] = None
            msa: Optional[Union[Dict[str, str], str]] = None
            categories_quantity: Optional[float] = None
            alpha: Optional[float] = None
            beta: Optional[float] = None
            pi_0: Optional[Union[float, np.ndarray, int]] = None
            pi_1: Optional[Union[float, np.ndarray, int]] = None
            coefficient_bl: Optional[Union[float, np.ndarray, int]] = None
            is_optimize_pi: Optional[bool] = None,
            is_optimize_pi_average: Optional[bool] = None
            is_optimize_alpha: Optional[bool] = None
            is_optimize_bl: Optional[bool] = None
    """
        available_parameters = {'data', 'node_name', 'msa', 'categories_quantity', 'alpha', 'beta', 'pi_0', 'pi_1',
                                'coefficient_bl', 'is_optimize_pi', 'is_optimize_pi_average', 'is_optimize_alpha',
                                'is_optimize_bl'}
        invalid_parameters = set(kwargs.keys()) - available_parameters
        for key in invalid_parameters:
            del kwargs[key]

        if isinstance(data, str):
            self.newick_to_tree(data)
            if node_name and isinstance(node_name, str):
                Tree.rename_nodes(self, node_name)
        elif isinstance(data, Node):
            self.root = data
        else:
            self.root = Node('root')

        self.is_optimize_pi, self.is_optimize_pi_average, self.is_optimize_alpha, self.is_optimize_bl = (None, None,
                                                                                                         None, None)
        self.msa, self.alphabet, self.categories_quantity, self.alpha = None, None, None, None
        self.rate_vector = (1.0,)
        self.pi_0, self.pi_1, self.coefficient_bl = None, None, 1
        # self.likelihood, self.log_likelihood, self.log_likelihood_vector = 1, 0, []
        self.log_likelihood_vector, self.log_likelihood, self.likelihood = None, None, None
        self.calculated_ancestor_sequence = self.calculated_tree_for_fasta = self.calculated_likelihood = False

        if any(kwargs.values()):
            self.set_tree_data(**kwargs)
        elif invalid_parameters:
            print(f'There are invalid parameters: {", ".join(invalid_parameters)}')

    def __str__(self) -> str:
        return self.get_newick()

    def __len__(self) -> int:
        return self.get_node_count()

    def __eq__(self, other) -> bool:
        return str(self).lower() == str(other).lower()

    def __ne__(self, other) -> bool:
        return not self == other

    def __lt__(self, other) -> bool:
        return len(self) < len(other)

    def __le__(self, other) -> bool:
        return self < other or self == other or len(str(self)) < len(str(other))

    def __gt__(self, other) -> bool:
        return len(self) > len(other)

    def __ge__(self, other) -> bool:
        return self > other or self == other or len(str(self)) > len(str(other))

    def print_node_list(self, with_additional_details: bool = False, mode: Optional[str] = None,
                        filters: Optional[Dict[str, List[Union[float, int, str, List[float]]]]] = None) -> None:
        """
        Print a list of nodes.

        This function prints a list of nodes.

        Args:
            with_additional_details (bool, optional): `False` (default)
            mode (str, optional): `None` (default), 'pre-order', 'in-order', 'post-order', 'level-order'.
            filters (Dict, optional): `None` (default)
        Returns:
            None: This function does not return any value; it only prints the nodes to the standard output.
        """
        data_structure = self.root.get_list_nodes_info(with_additional_details, mode, filters)

        str_result = ''
        for i in data_structure:
            str_result = f'{str_result}\n{i}'
        print(str_result, '\n')

    def get_tree_info(self, filters: Optional[Dict[str, List[Union[float, int, str, List[float]]]]] = None
                      ) -> pd.Series:
        nodes_info = self.get_list_nodes_info(True, 'pre-order', filters)

        return pd.Series([pd.Series(i) for i in nodes_info], index=[i.get('node') for i in nodes_info])

    def get_list_nodes_info(self, with_additional_details: bool = False, mode: Optional[str] = None, filters:
                            Optional[Dict[str, List[Union[float, int, str, List[float]]]]] = None, only_node_list:
                            bool = False) -> List[Union[Dict[str, Union[float, np.ndarray, bool, str, List[float],
                                                  List[np.ndarray]]], 'Node']]:
        """
        Args:
            with_additional_details (bool, optional): `False` (default).
            mode (Optional[str]): `None` (default), 'pre-order', 'in-order', 'post-order', 'level-order'.
            filters (Dict, optional): `None` (default).
            only_node_list (Dict, optional): `False` (default).
        """
        return self.root.get_list_nodes_info(with_additional_details, mode, filters, only_node_list)

    def get_node_count(self, filters: Optional[Dict[str, List[Union[float, int, str, List[float]]]]] = None) -> int:
        """
        Args:
            filters (Dict, optional):
        """
        return len(self.get_list_nodes_info(True, None, filters))

    def get_node_by_name(self, name: str) -> Optional[Node]:

        return self.root.get_node_by_name(name)

    def get_newick(self, with_internal_nodes: bool = False, decimal_length: int = 0) -> str:

        """
        Convert the current tree structure to a Newick formatted string.

        This function serializes the tree into a Newick format, which is a standard format for representing
        tree structures.

        Args:
            with_internal_nodes (bool, optional):
            decimal_length (int, optional):

        Returns:
            str: A Newick formatted string representing the tree structure.
        """
        return f'{self.root.subtree_to_newick(with_internal_nodes, decimal_length)};'

    def find_node_by_name(self, name: str) -> bool:
        """
        Search for a node by its name in a tree structure.

        This function searches for a node with a specific name within a tree. If a root node is provided,
        the search starts from that node; otherwise, it searches from the default root of the tree.
        The function returns `True` if a node with the specified name is found, and `False` otherwise.

        Args:
            name (str): The name of the node to search for. This should be the exact name of the node
                        as a string.

        Returns:
            bool: `True` if a node with the specified name is found; `False` otherwise.
        """

        return name in self.root.get_list_nodes_info()

    def newick_to_tree(self, newick: str) -> Optional['Tree']:
        """
        Convert a Newick formatted string into a tree object.

        This function parses a Newick string, which represents a tree structure in a compact format,
        and constructs a tree object from it. The Newick format is often used in phylogenetics to
        describe evolutionary relationships among species.

        Args:
            newick (str): A string in Newick format representing the tree structure. The string
                              should be properly formatted according to Newick syntax.

        Returns:
            Tree: An object representing the tree structure parsed from the Newick string. The tree
                  object provides methods and properties to access and manipulate the tree structure.
        """
        newick = newick.replace(' ', '').strip()
        if newick.startswith('(') and newick.endswith(';'):

            len_newick = len(newick)
            list_end = [i for i in range(len_newick) if newick[i:i + 1] == ')']
            list_start = [i for i in range(len_newick) if newick[i:i + 1] == '(']
            list_children = []

            num = self.__counter()

            while list_start:
                int_start = list_start.pop(-1)
                int_end = min([i for i in list_end if i > int_start]) + 1
                list_end.pop(list_end.index(int_end - 1))
                node_name = newick[int_end: min([x for x in [newick.find(':', int_end), newick.find(',', int_end),
                                                 newick.find(';', int_end), newick.find(')', int_end)] if x >= 0])]
                distance_to_father = newick[int_end + len(node_name): min([x for x in [newick.find(',', int_end),
                                                                          newick.find(';', int_end), newick.find(')',
                                                                          int_end)] if x >= 0])]

                (visibility, node_name) = (True, node_name) if node_name else (False, 'nd' + str(num()).rjust(4, '0'))

                sub_str = newick[int_start:int_end]
                list_children.append({'children': sub_str, 'node': node_name, 'distance_to_father': distance_to_father,
                                      'visibility': visibility})

            list_children.sort(key=lambda x: len(x.get('children')), reverse=True)

            for i in range(len(list_children)):
                for j in range(i + 1, len(list_children)):
                    node_name = list_children[j].get('node') if list_children[j].get('visibility') else ''
                    list_children[i].update({'children': list_children[i].get('children').replace(
                        list_children[j].get('children') + node_name, list_children[j].get('node'))})
            for dict_children in list_children:
                if list_children.index(dict_children):
                    newick_node = self.get_node_by_name(dict_children.get('node'))
                    newick_node = newick_node if newick_node else self.__set_node(
                        f'{dict_children.get("node")}{dict_children.get("distance_to_father")}', num)
                else:
                    newick_node = self.__set_node(
                        f'{dict_children.get("node")}{dict_children.get("distance_to_father")}', num)
                    self.root = newick_node

                self.__set_children_list_from_string(dict_children.get('children'), newick_node, num)

            return self

    def get_html_tree(self, style: str = '', status: str = '') -> str:
        """This method is for internal use only."""
        return self.structure_to_html_tree(self.tree_to_structure(), style, status)

    def tree_to_structure(self) -> dict:
        """This method is for internal use only."""
        return self.subtree_to_structure(self.root)

    def add_distance_to_father(self, distance_to_father: float = 0) -> None:
        def add_distance(newick_node: Node) -> None:
            nonlocal distance_to_father
            newick_node.distance_to_father += distance_to_father
            newick_node.distance_to_father = round(newick_node.distance_to_father, 12)
            for child in newick_node.children:
                add_distance(child)

        add_distance(self.root)

    def get_edges_list(self) -> List[str]:
        list_result = []

        def get_list(newick_node: Node) -> None:
            nonlocal list_result
            if newick_node.father:
                list_result.append((newick_node.father.name, newick_node.name))
            for child in newick_node.children:
                get_list(child)

        get_list(self.root)

        return list_result

    def __set_children_list_from_string(self, str_children: str, father: Optional[Node], num) -> None:
        """This method is for internal use only."""
        str_children = str_children[1:-1] if str_children.startswith('(') and str_children.endswith(
            ')') else str_children
        lst_nodes = str_children.split(',')
        for str_node in lst_nodes:
            newick_node = self.__set_node(str_node.strip(), num)
            father.add_child(newick_node)

    def check_tree_for_binary(self) -> bool:
        nodes_list = self.get_list_nodes_info(True)
        for newick_node in nodes_list:
            for key in newick_node.keys():
                if key == 'children' and len(newick_node.get(key)) > 2:
                    return False
        return True

    def tree_to_table(self, sort_values_by: Optional[Tuple[str, ...]] = None, decimal_length: int = 8, columns: Optional
                      [Dict[str, str]] = None, filters: Optional[Dict[str, List[Union[float, int, str, List[float]]]]] =
                      None, distance_type: type = str, list_type: type = str, lists: Optional[Tuple[str, ...]] = None
                      ) -> pd.DataFrame:
        nodes_info = self.get_list_nodes_info(True, None, filters)
        columns = columns if columns else {'node': 'Name', 'father_name': 'Parent', 'distance': 'Distance to parent',
                                           'children': 'Children', 'lavel': 'Lavel', 'node_type': 'Node type',
                                           'full_distance': 'Full distance', 'up_vector': 'Up', 'down_vector': 'Down',
                                           'likelihood': 'Likelihood', 'sequence_likelihood': 'Likelihood of sequence',
                                           'log_likelihood': 'Log-likelihood', 'log_likelihood_vector':
                                           'Vector of log-likelihood', 'marginal_vector': 'Marginal vector',
                                           'probability_vector': 'Probability vector', 'probable_character':
                                           'Probable character', 'sequence': 'Sequence', 'ancestral_sequence':
                                           'Ancestral Comparison', 'probabilities_sequence_characters':
                                           'Probabilities sequence characters', 'probability_vector_gain':
                                           'Gain probability', 'probability_vector_loss': 'Loss probability'}
        lists = lists if lists else ('children', 'full_distance', 'up_vector', 'down_vector', 'marginal_vector',
                                     'probability_vector', 'probabilities_sequence_characters', 'log_likelihood_vector',
                                     'ancestral_sequence', 'probability_vector_gain', 'probability_vector_loss',
                                     'sequence')

        for node_info in nodes_info:
            for i in set(node_info.keys()) - set(columns.keys()):
                node_info.pop(i)
            if not node_info.get('father_name'):
                node_info.update({'father_name': 'root'})
            if columns.get('distance'):
                if distance_type is str:
                    node_info.update({'distance': ' ' * decimal_length if not node_info.get('distance') else
                                     f'{node_info.pop("distance"):.10f}'.ljust(decimal_length, "0")})
                else:
                    node_info.update({'distance': distance_type(node_info.get('distance'))})
            for i in lists:
                if columns.get(i):
                    if list_type in (list, tuple, set):
                        # info = list_type(map(lambda x: f'{x:.3f}' if (isinstance(x, (int, float)) and
                        #                                               change_content_type) else x, node_info.get(i)))
                        info = list_type(map(lambda x: np.round(x, 4) if (isinstance(x, (int, float))
                                                                          ) else x, node_info.get(i)))
                    else:
                        info = ' '.join(map(str, node_info.get(i)))
                    node_info.update({i: info})

        tree_table = pd.DataFrame([i for i in nodes_info], index=None)
        tree_table = tree_table.rename(columns=columns)
        tree_table = tree_table.reindex(columns=columns.values())
        if isinstance(list_type, (list, tuple, set)):
            lists_names = [v for k, v in columns.items() if k in lists]
            sort_values_by = tuple([i for i in sort_values_by if i not in lists_names])

        return tree_table.sort_values(by=list(sort_values_by)) if sort_values_by else tree_table

    def calculate_ancestral_sequence(self, newick_node: Optional[Union[Node, str]] = None) -> None:
        if self.alphabet and not self.calculated_ancestor_sequence:
            node_list = []
            if not newick_node:
                node_list = self.root.get_list_nodes_info(filters={'node_type': ['node', 'leaf']}, only_node_list=True)
            else:
                node_list.append(newick_node)

            ancestral_alphabet = Tree.get_ancestral_alphabet()
            for current_node in node_list:
                current_node.ancestral_sequence = ''
                if current_node.father:
                    for i in range(len(current_node.sequence)):
                        if current_node.sequence[i] == current_node.father.sequence[i] == self.alphabet[0]:
                            current_node.ancestral_sequence += ancestral_alphabet[0]
                        elif ((current_node.sequence[i] != current_node.father.sequence[i])
                              and (current_node.sequence[i] == self.alphabet[0])):
                            current_node.ancestral_sequence += ancestral_alphabet[1]
                        elif ((current_node.sequence[i] != current_node.father.sequence[i])
                              and (current_node.sequence[i] == self.alphabet[1])):
                            current_node.ancestral_sequence += ancestral_alphabet[2]
                        elif current_node.sequence[i] == current_node.father.sequence[i] == self.alphabet[1]:
                            current_node.ancestral_sequence += ancestral_alphabet[3]
            self.calculated_ancestor_sequence = True

    # def calculate_marginal(self, newick_node: Optional[Union[Node, str]] = None, msa: Optional[str] = None) -> None:
    #     node_list = []
    #     if not newick_node:
    #         node_list = self.root.get_list_nodes_info(filters={'node_type': ['node', 'root']}, only_node_list=True)
    #         if node_list:
    #             newick_node = np.random.choice(np.array(node_list))
    #     else:
    #         if isinstance(newick_node, str):
    #             newick_node = self.get_node_by_name(newick_node)
    #         node_list.append(newick_node)
    #     if not newick_node.up_vector and msa:
    #         self.calculate_up(msa)
    #     if not newick_node.down_vector and newick_node.up_vector:
    #         self.calculate_down()

    def calculate_gl_probability(self) -> None:
        node_list = self.root.get_list_nodes_info(filters={'node_type': ['node', 'leaf']}, only_node_list=True)

        for current_node in node_list:
            current_node.calculate_gl_probability(alphabet=self.alphabet, rate_vector=self.rate_vector, pi_0=self.pi_0,
                                                  pi_1=self.pi_1)

    def calculate_marginal(self, newick_node: Optional[Union[Node, str]] = None) -> None:
        if not newick_node:
            node_list = self.root.get_list_nodes_info(filters={'node_type': ['node', 'root']}, only_node_list=True)
        else:
            node_list = []
            if isinstance(newick_node, str):
                node_list.append(self.get_node_by_name(newick_node))
            elif isinstance(newick_node, Node):
                node_list.append(newick_node)

        for current_node in node_list:
            current_node.calculate_marginal(alphabet=self.alphabet, rate_vector=self.rate_vector, pi_0=self.pi_0,
                                            pi_1=self.pi_1)

    def calculate_up(self, msa: str) -> Union[Tuple[Union[List[np.ndarray], List[float]], float], float]:

        return self.root.calculate_up(self.get_msa_dict(msa, self.alphabet), self.alphabet, self.rate_vector, self.pi_0,
                                      self.pi_1)

    def calculate_down(self) -> None:

        self.root.calculate_down(self.get_tree_info(), len(self.alphabet), self.rate_vector, self.pi_0, self.pi_1)

    def get_msa_dict(self, msa: str, alphabet: Optional[Union[Tuple[str, ...], str]] = None, only_leaves: bool = True
                     ) -> Dict[str, Union[Tuple[int, ...], str]]:
        node_types = ['leaf'] if only_leaves else ['leaf', 'node', 'root']
        nodes_info = self.get_list_nodes_info(True, 'pre-order', {'node_type': node_types})
        msa_list = msa.strip().split()
        msa_list_size, msa_dict = len(msa_list), dict()
        if msa_list_size == 1:
            for i, node_info in enumerate(nodes_info):
                if alphabet:
                    value = [0] * len(alphabet)
                    value[alphabet.index(msa[i])] = 1
                    value = tuple(value)
                else:
                    value = msa[i]
                msa_dict.update({node_info.get('node'): value})
        else:
            for j in range(msa_list_size // 2):
                node_name = msa_list[j + j][1::]
                if self.find_dict_in_iterable(nodes_info, 'node', node_name):
                    value = msa_list[j + j + 1]
                    value = ''.join(value)
                    msa_dict.update({node_name: value})

        return msa_dict

    def clean_all(self):
        self.root.clean_all()
        self.likelihood, self.log_likelihood, self.log_likelihood_vector = 1, 0, []

    def calculate_tree_for_fasta(self) -> str:
        if self.msa and not self.calculated_tree_for_fasta:
            self.clean_all()

            leaves = self.get_list_nodes_info(filters={'node_type': ['leaf']}, only_node_list=True)
            len_seq = len(min(list(self.msa.values())))
            for i in range(len_seq):
                self.likelihood *= self.calculate_up(msa=''.join([self.msa.get(leaf.name)[i] for leaf in leaves]))
                self.calculate_down()
                self.calculate_marginal()
                self.calculate_gl_probability()
            self.log_likelihood, self.log_likelihood_vector = self.root.log_likelihood, self.root.log_likelihood_vector
            self.calculated_tree_for_fasta = True
            self.calculated_likelihood = True

        return self.get_fasta_text()

    def calculate_likelihood(self) -> None:
        if self.msa and self.alphabet and not self.calculated_likelihood:
            self.clean_all()
            self.log_likelihood_vector, self.log_likelihood, self.likelihood = (
                self.root.calculate_likelihood(self.msa, self.alphabet, self.rate_vector, self.pi_0, self.pi_1))
            self.calculated_likelihood = True

    def get_fasta_text(self) -> str:
        fasta_text = ''
        for k, v in self.msa.items():
            fasta_text += f'>{k}\n{v}\n'

        return fasta_text[:-1]

    def get_json_structure(self, return_table: bool = False, columns: Optional[Dict[str, str]] = None,
                           mode: str = 'node') -> Dict[str, Union[List[str], str]]:
        """
        Args:
            return_table (bool, optional): `False` (default).
            columns (dict, optional): `None` (default).
            mode (str, optional): 'node' (default), 'branch'.

        Returns:
            Dict: An dictionary representing the tree structure.
        """
        if return_table:
            columns, lists = self.get_columns(mode, columns)
            column_name = 'Name' if mode == 'node' else 'Child node'

            table = self.tree_to_table(columns=columns, list_type=list, lists=lists, distance_type=float)
            dict_json = dict()
            for row in table.T:
                dict_row = dict()
                for key in columns.values():
                    dict_row.update({key: table[key][row]})
                dict_json.update({table[column_name][row]: dict_row})
        else:
            dict_json = self.root.node_to_json()

        return loads(str(dict_json).replace(f'\'', r'"'))

    @staticmethod
    def get_columns(mode: str = 'node', columns: Optional[Dict[str, str]] = None
                    ) -> Tuple[Dict[str, str], Tuple[str, ...]]:
        lists = ('children', 'full_distance', 'up_vector', 'down_vector', 'marginal_vector', 'probability_vector',
                 'probabilities_sequence_characters', 'log_likelihood_vector', 'sequence', 'ancestral_sequence',
                 'probability_vector_gain', 'probability_vector_loss')
        if mode == 'node':
            columns = columns if columns else {'node': 'Name', 'node_type': 'Node type', 'distance':
                                               'Distance to parent', 'sequence': 'Sequence',
                                               'probabilities_sequence_characters': 'Probability coefficient',
                                               'ancestral_sequence': 'Ancestral Comparison'}
            lists = ('probabilities_sequence_characters', 'sequence', 'ancestral_sequence')
        elif mode == 'branch' or mode == 'branch_tsv':
            columns = columns if columns else {'father_name': 'Parent node', 'node': 'Child node', 'distance':
                                               'Branch length', 'probability_vector_gain': 'Gain probability',
                                               'probability_vector_loss': 'Loss probability'}
            lists = ('probability_vector_gain', 'probability_vector_loss')
        elif mode == 'node_tsv':
            columns = columns if columns else {'node': 'Name', 'father_name': 'Parent', 'distance':
                                               'Distance to parent', 'children': 'Children', 'sequence': 'Sequence',
                                               'probabilities_sequence_characters': 'Probability coefficient',
                                               'ancestral_sequence': 'Ancestral comparison', 'sequence_likelihood':
                                               'Likelihood of sequence', 'log_likelihood': 'Log-likelihood',
                                               'log_likelihood_vector': 'Vector of log-likelihood'}
            lists = ('children', 'probabilities_sequence_characters', 'sequence', 'ancestral_sequence',
                     'log_likelihood_vector')

        return columns, lists

    @staticmethod
    def get_alpha_beta(alpha: Optional[float] = None, beta: Optional[float] = None) -> Tuple[float, ...]:
        alpha = alpha if alpha else (beta if beta else 0.5)
        beta = beta if beta else alpha

        return alpha, beta

    def get_gamma_distribution_categories_vector(self, categories_quantity: Optional[int] = None,
                                                 alpha: Optional[float] = None, beta: Optional[float] = None
                                                 ) -> Tuple[float, ...]:
        categories_quantity = 1 if categories_quantity is None else categories_quantity
        alpha, beta = self.get_alpha_beta(alpha, beta)
        categories_vector = []
        gamma_percent_point = Tree.get_gamma_distribution_percent_point(categories_quantity, alpha, beta)
        for i in range(categories_quantity):
            lower_gamma_inc_1 = gammainc(alpha + 1, gamma_percent_point[i] * beta)
            lower_gamma_inc_2 = gammainc(alpha + 1, gamma_percent_point[i + 1] * beta)
            mean = (alpha / beta) * (lower_gamma_inc_2 - lower_gamma_inc_1) / (1 / categories_quantity)
            categories_vector.append(mean)

        self.rate_vector = tuple(categories_vector)
        self.categories_quantity = categories_quantity

        return self.rate_vector

    def parameters_optimization(self, pi_0: Optional[Union[float, np.ndarray, int]] = None,
                                pi_1: Optional[Union[float, np.ndarray, int]] = None,
                                is_optimize_pi: Optional[bool] = None, is_optimize_pi_average: Optional[bool] = None
                                ) -> None:
        if isinstance(pi_0, (float, np.ndarray, int)) and pi_0:
            self.pi_0 = self.optimize_pi(pi=pi_0, mode=0, is_optimize_pi=is_optimize_pi,
                                         is_optimize_pi_average=is_optimize_pi_average)
        elif isinstance(pi_1, (float, np.ndarray, int)) and pi_1:
            self.pi_1 = self.optimize_pi(pi=pi_1, mode=1, is_optimize_pi=is_optimize_pi,
                                         is_optimize_pi_average=is_optimize_pi_average)
        self.is_optimize_pi = False if is_optimize_pi is None else is_optimize_pi
        self.is_optimize_pi_average = False if is_optimize_pi_average is None else is_optimize_pi_average

    def set_tree_data(self, msa: Optional[Union[Dict[str, str], str]] = None,
                      categories_quantity: Optional[int] = None,
                      alpha: Optional[float] = None,
                      beta: Optional[float] = None,
                      pi_0: Optional[Union[float, np.ndarray, int]] = None,
                      pi_1: Optional[Union[float, np.ndarray, int]] = None,
                      coefficient_bl: Optional[Union[float, np.ndarray, int]] = None,
                      is_optimize_pi: Optional[bool] = None,
                      is_optimize_pi_average: Optional[bool] = None,
                      is_optimize_alpha: Optional[bool] = None,
                      is_optimize_bl: Optional[bool] = None
                      ) -> None:
        if isinstance(msa, str):
            self.msa = self.get_msa_dict(msa)
        elif isinstance(msa, dict):
            self.msa = msa
        if isinstance(self.msa, dict) and self.msa:
            self.alphabet = Tree.get_alphabet_from_dict(self.msa)

        alpha, beta = self.get_alpha_beta(alpha, beta)

        self.optimize_coefficient_bl(coefficient_bl, is_optimize_bl)
        self.parameters_optimization(pi_0, pi_1, is_optimize_pi, is_optimize_pi_average)
        self.optimize_alpha(alpha, categories_quantity, is_optimize_alpha)

        if (self.is_optimize_alpha or self.is_optimize_pi) and self.is_optimize_bl:
            self.optimize_coefficient_bl(self.coefficient_bl, self.is_optimize_bl)

    def tree_to_fasta_file(self, file_name: str = 'file.fasta') -> str:

        fasta_text = self.get_fasta_text()

        return self.write_file(file_name, fasta_text)

    def likelihood_to_tsv(self, file_name: str = 'log_likelihood.tsv', sep: str = '\t') -> str:

        Tree.make_dir(file_name)
        self.calculate_likelihood()
        tree_table = pd.DataFrame({'POS': range(len(self.log_likelihood_vector)),
                                   'log-likelihood': self.log_likelihood_vector})
        tree_table.to_csv(file_name, sep=sep, index=False)

        return file_name

    def tree_to_tsv(self, file_name: str = 'node_results.tsv', sep: str = '\t', mode: str = 'node', **kwargs) -> str:

        Tree.make_dir(file_name)
        columns, lists = kwargs.get('columns', None), kwargs.get('lists', None)
        if columns is None or lists is None:
            columns, lists = self.get_columns(mode, columns)

        if kwargs.get('columns', None) is None:
            kwargs.update(columns=columns)
        if kwargs.get('lists', None) is None:
            kwargs.update(lists=lists)
        if kwargs.get('list_type', None) is None:
            kwargs.update(list_type=list)
        if kwargs.get('distance_type', None) is None:
            kwargs.update(distance_type=float)
        table = self.tree_to_table(**kwargs)
        table.to_csv(file_name, index=False, sep=sep)

        return file_name

    def tree_to_newick_file(self, file_name: str = 'tree_file.tree', with_internal_nodes: bool = False,
                            decimal_length: int = 0) -> str:

        newick_text = self.get_newick(with_internal_nodes, decimal_length)

        return self.write_file(file_name, newick_text)

    def tree_to_visual_format(self, file_name: str = 'tree_file.svg', with_internal_nodes: bool = False,
                              file_extensions: Optional[Union[str, Tuple[str, ...]]] = None, show_axes: bool = False
                              ) -> Dict[str, str]:
        file_extensions = Tree.check_file_extensions_tuple(file_extensions, 'svg')

        Tree.make_dir(file_name)
        tmp_dir = path.join(path.dirname(file_name), 'tmp')
        tmp_file = path.join(tmp_dir, f'{Tree.get_random_name()}.tree')
        Tree.make_dir(tmp_file)
        self.tree_to_newick_file(tmp_file, with_internal_nodes)
        phylogenetic_tree = Phylo.read(tmp_file, 'newick')

        j = file_name[::-1].find('.')
        file_names = dict()
        for file_extension in file_extensions:
            file_name = f'{file_name[:-(j + 1)]}.{file_extension}' if len(file_name) > j > -1 else (f'{file_name}.'
                                                                                                    f'{file_extension}')
            file_names.update({f'Newick tree ({file_extension})': file_name})
            if file_extension == 'txt':
                with open(file_name, 'w') as f:
                    Phylo.draw_ascii(phylogenetic_tree, f)
            else:
                Phylo.draw(phylogenetic_tree, do_show=False)
                plt.axis('on' if show_axes else 'off')
                kwargs = {'format': file_extension, 'bbox_inches': 'tight', 'dpi': 300} if (
                        file_extension == 'svg') else {'format': file_extension}
                plt.savefig(file_name, **kwargs)
                plt.close()
        rmtree(tmp_dir, ignore_errors=True)

        return file_names

    def tree_to_interactive_html(self, file_name: str = 'interactive_tree.svg') -> str:

        self.calculate_tree_for_fasta()
        self.calculate_ancestral_sequence()
        size_factor = min(1 + self.get_node_count({'node_type': ['leaf']}) // 7, 3)

        df = self.tree_to_table(columns={'node': 'target', 'father_name': 'source', 'distance': 'weight', 'sequence':
                                         'sequence', 'probabilities_sequence_characters': 'prob_characters',
                                         'node_type': 'node_type', 'ancestral_sequence': 'ancestral_sequence'},
                                distance_type=float, filters={'node_type': ['leaf', 'node', 'root']}, list_type=list)
        df_copy = df.copy()
        del df['sequence'], df['node_type'], df['prob_characters']
        df = df.iloc[1:]

        d3 = D3Blocks(verbose=100, chart='tree', frame=False)
        d3.set_node_properties(df)

        d3.font = {'size': 12}
        d3.hierarchy = [i for i in range(1, len(df_copy.T.count()) + 1)]
        d3.title = 'Phylogenetic tree'
        d3.filepath = file_name
        d3.figsize = (500, 500)
        d3.showfig, d3.overwrite, d3.reset_properties, d3.save_button = True, True, True, True
        d3.notebook = False
        d3.config = d3.chart.set_config(config=d3.config, filepath=d3.filepath, font=d3.font, title=d3.title,
                                        margin={"top": 20, "right": 40, "bottom": 20, "left": 40},
                                        showfig=d3.showfig, overwrite=d3.overwrite, figsize=d3.figsize,
                                        reset_properties=d3.reset_properties, notebook=d3.notebook,
                                        hierarchy=d3.hierarchy, save_button=d3.save_button)

        colors = ['crimson', 'orangered', 'darkorange', 'gold', 'yellowgreen', 'forestgreen', 'mediumturquoise',
                  'dodgerblue', 'slateblue', 'darkviolet']
        colors_as = {'A': 'crimson', 'L': 'darkorange', 'G': 'forestgreen', 'P': 'slateblue'}
        for i in df_copy.T:
            # probability_mark = probability_coefficient = ancestral_sequence = ''
            probability_coefficient = ancestral_sequence = ''
            sequence = ''.join([Node.draw_cell_html_table(colors[Node.get_integer(j)], j)
                                for j in df_copy['sequence'][i]])
            sequence = Node.draw_row_html_table('Sequence', sequence)
            if df_copy["node_type"][i] != 'root':
                ancestral_sequence = ''.join([Node.draw_cell_html_table(colors_as[j], j)
                                              for j in df_copy['ancestral_sequence'][i]])
                ancestral_sequence = Node.draw_row_html_table('Ancestral Comparison', ancestral_sequence)
            if df_copy["node_type"][i] != 'leaf':
                # probability_mark = ''.join([Node.draw_cell_html_table(colors[Node.get_integer(j)], "9" if j == 1 else
                #                             int(j * 10)) for j in df_copy['prob_characters'][i]])
                # probability_mark = Node.draw_row_html_table('Probability mark (0-9)', probability_mark)
                probability_coefficient = ''.join([Node.draw_cell_html_table(colors[Node.get_integer(j)], f'{j:.3f}')
                                                  for j in df_copy['prob_characters'][i]])
                probability_coefficient = Node.draw_row_html_table('Probability coefficient', probability_coefficient)
                if df_copy["node_type"][i] == 'node':
                    d3.node_properties.get(df_copy['target'][i])['color'] = 'darkorange'
                    d3.node_properties.get(df_copy['target'][i])['size'] = 15 / size_factor
                if df_copy["node_type"][i] == 'root':
                    d3.node_properties.get(df_copy['target'][i])['color'] = 'firebrick'
                    d3.node_properties.get(df_copy['target'][i])['size'] = 20 / size_factor
            else:
                d3.node_properties.get(df_copy['target'][i])['color'] = 'forestgreen'
                d3.node_properties.get(df_copy['target'][i])['size'] = 10 / size_factor
            distance = f'<td class="h7 w-auto text-center">{df_copy["weight"][i]}</td>'
            # info = (f'{Node.draw_row_html_table("Distance", distance)}{sequence}{ancestral_sequence}'
            #         f'{probability_mark}{probability_coefficient}')
            info = (f'{Node.draw_row_html_table("Distance", distance)}{sequence}{probability_coefficient}'
                    f'{ancestral_sequence}')
            d3.node_properties.get(df_copy['target'][i])['tooltip'] = Node.draw_html_table(info)
            d3.font.update({'type': 'Anonymous Pro'})

        d3.set_edge_properties(df)
        d3.show()
        # html = d3.chart.show(d3.edge_properties, config=d3.config, node_properties=d3.node_properties)
        return file_name

    def tree_to_graph(self, file_name: str = 'graph.svg', file_extensions: Optional[Union[str, Tuple[str, ...]]] = None
                      ) -> Union[str, Dict[str, str]]:
        file_extensions = Tree.check_file_extensions_tuple(file_extensions, 'png')

        size_factor = min(1 + self.get_node_count({'node_type': ['leaf']}) // 7, 3)
        Tree.make_dir(file_name)
        columns = {'node': 'Name', 'father_name': 'Parent', 'distance': 'Distance to parent'}
        table = self.tree_to_table(None, 0, columns)
        table = table.drop(0)
        j = file_name[::-1].find('.')
        file_name_sm = f'{file_name[:-j]}' if len(file_name) > j > -1 else f'{file_name}.'
        file_names = dict()
        for file_extension in file_extensions:
            file_name = f'{file_name_sm}{file_extension}'
            file_names.update({f'Graph ({file_extension})': file_name})
            graph = nx.Graph()
            for row in table.values:
                graph.add_edge(row[1], row[0], length=row[2] if row[2] else 0.0)
            if file_extension in ('svg', 'png'):
                nx.draw(graph, with_labels=True, font_color='Maroon', node_color='Gold', node_size=1000//size_factor,
                        font_size=12//size_factor, font_weight='bold')
                plt.savefig(file_name, **{'format': file_extension, 'bbox_inches': 'tight', 'dpi': 300})
                plt.close()
            if file_extension in ('dot', ):
                nx.drawing.nx_pydot.write_dot(graph, file_name)

        return file_names

    def optimize(self, func: Union[Callable, str], bracket: Tuple[Union[float, np.ndarray], ...] = (0.5,),
                 bounds: Tuple[Union[float, np.ndarray], ...] = (0.001, 0.999),
                 args: Optional[Tuple[Any, ...]] = None, result_fild: Optional[str] = None):
        """
            result_fild: `str` (default), message, success, status, fun, x, nit, nfev
        """
        self.clean_all()
        func = self.__getattribute__(func) if isinstance(func, str) else func
        min_scalar = minimize_scalar(func, bracket=bracket, bounds=bounds) if args is None else (
            minimize_scalar(func, args=args, bracket=bracket, bounds=bounds))

        return min_scalar[result_fild] if result_fild else min_scalar

    def pi_optimization(self, pi: Union[float, np.ndarray], mode: int = 0) -> Union[float, np.ndarray]:
        current_pi = (pi, None)
        return -self.root.calculate_likelihood(self.msa, self.alphabet, self.rate_vector, pi_0=current_pi[mode],
                                               pi_1=current_pi[::-1][mode])[1]

    def alpha_optimization(self, alpha: Union[int, float, np.ndarray], categories_quantity: int = 1
                           ) -> Union[float, np.ndarray]:
        self.get_gamma_distribution_categories_vector(categories_quantity, alpha)
        return -self.root.calculate_likelihood(self.msa, self.alphabet, self.rate_vector, self.pi_0, self.pi_1)[1]

    def set_coefficient_bl(self, coefficient_bl: Union[int, float, np.ndarray]) -> None:
        node_list = self.root.get_list_nodes_info(only_node_list=True)
        for current_node in node_list:
            current_node.coefficient_bl = coefficient_bl

    def coefficient_bl_optimization(self, coefficient_bl: Union[int, float, np.ndarray]) -> Union[float, np.ndarray]:
        self.set_coefficient_bl(coefficient_bl)

        return -self.root.calculate_likelihood(self.msa, self.alphabet, self.rate_vector, self.pi_0, self.pi_1)[1]

    def optimize_pi_average(self, mode: int = 0, msa: Optional[str] = None) -> float:
        all_lines = ''
        if isinstance(msa, str) and msa:
            for i, current_line in enumerate(msa.split()):
                if i % 2:
                    all_lines += current_line.strip()
        else:
            all_lines = ''.join(self.msa.values())

        return all_lines.count(self.alphabet[mode]) / len(all_lines)

    def optimize_coefficient_bl(self, coefficient_bl: Optional[Union[int, float, np.ndarray]] = None,
                                is_optimize_bl: Optional[bool] = None) -> Union[float, np.ndarray, int]:
        if is_optimize_bl:
            coefficient_bl = self.optimize(func=self.coefficient_bl_optimization, bracket=(1, ),
                                           bounds=(0.1, 10), result_fild='x')

        self.set_coefficient_bl(coefficient_bl)
        self.is_optimize_bl = False if is_optimize_bl is None else is_optimize_bl
        self.coefficient_bl = 1.0 if coefficient_bl is None else coefficient_bl

        return coefficient_bl

    def optimize_alpha(self, alpha: Union[int, float, np.ndarray], categories_quantity: int = 1,
                       is_optimize_alpha: Optional[bool] = None) -> Union[float, np.ndarray, int]:
        if is_optimize_alpha:
            alpha = self.optimize(func=self.alpha_optimization, bracket=(0.5, ), bounds=(0.1, 20),
                                  args=(categories_quantity, ), result_fild='x')
        self.alpha = alpha
        self.is_optimize_alpha = False if is_optimize_alpha is None else is_optimize_alpha
        self.get_gamma_distribution_categories_vector(categories_quantity, self.alpha, self.alpha)

        return alpha

    def optimize_pi(self, pi: Union[int, float, np.ndarray], mode: int = 0, is_optimize_pi: Optional[bool] = None,
                    is_optimize_pi_average: Optional[bool] = None, msa: Optional[str] = None
                    ) -> Union[float, np.ndarray, int]:
        if is_optimize_pi:
            pi = self.optimize(func=self.pi_optimization, bracket=(0.5, ), bounds=(0.001, 0.999), args=(mode, ),
                               result_fild='x')
        elif is_optimize_pi_average:
            pi = self.optimize_pi_average(mode=mode, msa=msa)

        return pi

    @staticmethod
    def write_file(file_name: str, file_text: str) -> str:

        try:
            Tree.make_dir(file_name)
            with open(file_name, 'w') as f:
                f.write(file_text)
        except Exception as e:
            print(f'An error occurred while saving the file: {e}')
            file_name = ''

        return file_name

    @staticmethod
    def get_alphabet_from_dict(msa_dict: Dict[str, str]) -> Tuple[str, ...]:
        character_list = []
        for sequence in msa_dict.values():
            character_list += [i for i in sequence]

        return Tree.get_alphabet(set(character_list))

    @staticmethod
    def get_columns_list_for_sorting(mode: str = 'node') -> Dict[str, List[str]]:
        if mode == 'node':
            result = {'List for sorting': ['Name', 'Node type', 'Distance to parent', 'Sequence',
                                           'Probability coefficient', 'Ancestral Comparison']}
        else:
            result = {'List for sorting': ['Parent node', 'Child node', 'Branch length', 'Gain probability',
                                           'Loss probability']}

        return loads(str(result).replace(f'\'', r'"'))

    @staticmethod
    def get_random_name(lenght: int = 24) -> str:
        abc_list = [_ for _ in 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890']

        return ''.join(np.random.choice(abc_list, lenght))

    @staticmethod
    def get_ancestral_alphabet() -> Tuple[str, ...]:

        return 'A', 'L', 'G', 'P'

    @staticmethod
    def get_alphabet(search_argument: Union[Set[str], int, str]) -> Tuple[str, ...]:
        alphabets = (('0', '1'), ('A', 'C', 'G', 'T'),
                     ('A', 'R', 'N', 'D', 'C', 'Q', 'E', 'G', 'H', 'I', 'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W', 'Y',
                      'V'))
        if isinstance(search_argument, int):
            return tuple(alphabets[search_argument])
        if isinstance(search_argument, str):
            search_argument = set([i for i in search_argument])
        if isinstance(search_argument, set):
            for alphabet in alphabets:
                if not search_argument - set(alphabet):
                    return alphabet

    @staticmethod
    def find_dict_in_iterable(iterable: Union[List[Union[Dict[str, Union[float, np.ndarray, bool, str, List[float],
                              List[np.ndarray]]], 'Node']], Tuple[Dict[str, Union[float, bool, str, List[float], Tuple[
                                   int, ...]]]]], key: str, value: Optional[Union[float, bool, str, List[float]]] = None
                              ) -> Dict[str, Union[float, bool, str, List[float], List[int], Tuple[int, ...]]]:
        for index, dictionary in enumerate(iterable):
            if key in dictionary and (True if value is None else dictionary[key] == value):
                return dictionary

    @staticmethod
    def make_dir(file_path: str, **kwargs) -> None:
        dir_path = path.dirname(file_path)
        if not path.exists(dir_path) and dir_path:
            makedirs(dir_path, **kwargs)

    @staticmethod
    def check_tree(newick_tree: Union[str, 'Tree']) -> 'Tree':
        if isinstance(newick_tree, str):
            newick_tree = Tree(newick_tree)

        return newick_tree

    @staticmethod
    def check_file_extensions_tuple(file_extensions: Optional[Union[str, Tuple[str, ...]]] = None, default_value: str =
                                    'txt') -> Tuple[str, ...]:
        file_extensions = file_extensions if file_extensions else (default_value,)
        if isinstance(file_extensions, str):
            file_extensions = (file_extensions,)

        return file_extensions

    @staticmethod
    def check_newick(newick_text: str) -> bool:
        newick_text = newick_text.strip()
        return newick_text and newick_text.startswith('(') and newick_text.endswith(';')

    @staticmethod
    def __set_node(node_str: str, num) -> Node:
        """This method is for internal use only."""
        if node_str.find(':') > -1:
            node_data: List[Union[str, int, float]] = node_str.split(':')
            node_data[0] = node_data[0] if node_data[0] else 'nd' + str(num()).rjust(4, '0')
            try:
                node_data[1] = float(node_data[1])
            except ValueError:
                node_data[1] = 0.0
        else:
            node_data = [node_str if node_str else 'nd' + str(num()).rjust(4, '0'), 0.0]

        newick_node = Node(node_data[0])
        newick_node.distance_to_father = float(node_data[1])
        return newick_node

    @staticmethod
    def get_gamma_distribution_percent_point(categories_quantity: int, alpha: float, beta: float) -> List[float]:
        probability_vector = np.linspace(0, 1, categories_quantity + 1)

        return gamma.ppf(probability_vector, a=alpha, scale=1/beta)

    @staticmethod
    def rename_nodes(newick_tree: Union[str, 'Tree'], node_name: str = 'N', fill_character: str = '0', number_length:
                     int = 0) -> 'Tree':
        newick_tree = Tree.check_tree(newick_tree)
        num = newick_tree.__counter()

        nodes_list = [newick_tree.root]
        while nodes_list:
            newick_node = nodes_list.pop(0)

            if newick_node.children:
                newick_node.name = f'{node_name}{str(num()).rjust(number_length, fill_character)}'
                for nodes_child in newick_node.children:
                    nodes_list.append(nodes_child)

        return newick_tree

    @staticmethod
    def __counter():
        """This method is for internal use only."""
        count = 0

        def sub_function():
            nonlocal count
            count += 1
            return count

        return sub_function

    @classmethod
    def __get_html_tree(cls, structure: dict, status: str) -> str:
        """This method is for internal use only."""
        tags = (f'<details {status}>', '</details>', '<summary>', '</summary>') if structure['children'] else ('', '',
                                                                                                               '', '')
        str_html = (f'<li> {tags[0]}{tags[2]}{structure["name"].strip()} \t ({structure["distance_to_father"]}) '
                    f'{tags[3]}')
        for child in structure['children']:
            str_html += f'<ul>{cls.__get_html_tree(child, status)}</ul>\n' if child[
                'children'] else f'{cls.__get_html_tree(child, status)}'
        str_html += f'{tags[1]}</li>'
        return str_html

    @classmethod
    def get_robinson_foulds_distance(cls, tree1: Union['Tree', str], tree2: Union['Tree', str]) -> float:
        """This method is for internal use only."""
        tree1 = Tree(tree1) if type(tree1) is str else tree1
        tree2 = Tree(tree2) if type(tree2) is str else tree2

        edges_list1 = sorted(tree1.get_edges_list(), key=lambda item: item[1])
        edges_list2 = sorted(tree2.get_edges_list(), key=lambda item: item[1])

        distance = 0
        for newick_node in edges_list1:
            distance += 0 if edges_list2.count(newick_node) else 1
        for newick_node in edges_list2:
            distance += 0 if edges_list1.count(newick_node) else 1

        return distance / 2

    @classmethod
    def structure_to_html_tree(cls, structure: dict, styleclass: str = '', status: str = '') -> str:
        """This method is for internal use only."""
        return (f'<ul {f" class = {chr(34)}{styleclass}{chr(34)}" if styleclass else ""}>'
                f'{cls.__get_html_tree(structure, status)}</ul>')

    @classmethod
    def subtree_to_structure(cls, newick_node: Node) -> Dict[str, str]:
        """This method is for internal use only."""
        dict_node = {'name': newick_node.name.strip(), 'distance_to_father': newick_node.distance_to_father}
        list_children = []
        if newick_node.children:
            for child in newick_node.children:
                list_children.append(cls.subtree_to_structure(child))
        dict_node.update({'children': list_children})

        return dict_node
