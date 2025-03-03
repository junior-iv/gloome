import os
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import json
from d3blocks import D3Blocks
from node import Node
from typing import Optional, List, Union, Dict, Tuple, Set
from Bio import Phylo


class Tree:
    root: Optional[Node]
    log_likelihood_vector: List[Union[float, np.ndarray]]
    log_likelihood: Union[float, np.ndarray]
    likelihood: Union[float, np.ndarray]

    def __init__(self, data: Union[str, Node, None] = None, node_name: Optional[str] = None) -> None:
        if isinstance(data, str):
            self.newick_to_tree(data)
            if node_name and isinstance(node_name, str):
                Tree.rename_nodes(self, node_name)
        elif isinstance(data, Node):
            self.root = data
        else:
            self.root = Node('root')

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
            mode (Optional[str]): `None` (default), 'pre-order', 'in-order', 'post-order', 'level-order'.
            filters (Dict, optional):
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

    def get_list_nodes_info(self, with_additional_details: bool = False, mode: Optional[str] =
                            None, filters: Optional[Dict[str, List[Union[float, int, str, List[float]]]]] = None
                            ) -> List[Union[Dict[str, Union[float, np.ndarray, bool, str, List[float],
                                      List[np.ndarray]]], 'Node']]:
        """
        Args:
            with_additional_details (bool, optional): `False` (default).
            mode (Optional[str]): `None` (default), 'pre-order', 'in-order', 'post-order', 'level-order'.
            filters (Dict, optional):
        """
        return self.root.get_list_nodes_info(with_additional_details, mode, filters)

    def get_node_count(self, filters: Optional[Dict[str, List[Union[float, int, str, List[float]]]]] = None) -> int:
        """
        Args:
            filters (Dict, optional):
        """
        return len(self.get_list_nodes_info(True, None, filters))

    def get_node_by_name(self, name: str) -> Optional[Node]:

        return self.root.get_node_by_name(name)

    def get_newick(self, with_internal_nodes: bool = False) -> str:

        """
        Convert the current tree structure to a Newick formatted string.

        This function serializes the tree into a Newick format, which is a standard format for representing
        tree structures.

        Args:
            with_internal_nodes (bool, optional):

        Returns:
            str: A Newick formatted string representing the tree structure.
        """
        return f'{self.root.subtree_to_newick(with_internal_nodes)};'

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
                      None, distance_type: type = str, list_type: type = str, lists: Optional[Tuple[str, ...]] = None,
                      change_content_type: bool = False) -> pd.DataFrame:
        nodes_info = self.get_list_nodes_info(True, None, filters)
        columns = columns if columns else {'node': 'Name', 'father_name': 'Parent', 'distance': 'Distance to father',
                                           'children': 'child', 'lavel': 'Lavel', 'node_type': 'Node type',
                                           'full_distance': 'Full distance', 'up_vector': 'Up', 'down_vector': 'Down',
                                           'likelihood': 'Likelihood', 'marginal_vector': 'Marginal vector',
                                           'probability_vector': 'Probability vector', 'probable_character':
                                           'Probable character', 'sequence': 'Sequence', 'ancestral_sequence':
                                           'Ancestral sequence', 'probabilities_sequence_characters':
                                           'Probabilities sequence characters'}
        lists = lists if lists else ('children', 'full_distance', 'up_vector', 'down_vector', 'marginal_vector',
                                     'probability_vector', 'probabilities_sequence_characters')

        for node_info in nodes_info:
            for i in set(node_info.keys()) - set(columns.keys()):
                node_info.pop(i)
            if not node_info.get('father_name'):
                node_info.update({'father_name': 'root'})
            if columns.get('distance'):
                # if isinstance(distance_type, str):
                if distance_type is str:

                    node_info.update({'distance': ' ' * (decimal_length // 2) if not node_info.get('distance') else
                                     f'{str(node_info.pop("distance")).ljust(decimal_length, "0")}'})
                else:
                    node_info.update({'distance': distance_type(node_info.get('distance'))})
            for i in lists:
                if columns.get(i):
                    if list_type in (list, tuple, set):
                        info = list_type(map(lambda x: f'{x:.3f}' if (isinstance(x, (int, float)) and
                                                                      change_content_type) else x, node_info.get(i)))
                    else:
                        info = ' '.join(map(str, node_info.get(i)))
                    node_info.update({i: info})

        tree_table = pd.DataFrame([i for i in nodes_info], index=None)
        tree_table = tree_table.rename(columns=columns)
        tree_table = tree_table.reindex(columns=columns.values())

        return tree_table.sort_values(by=list(sort_values_by)) if sort_values_by else tree_table

    def calculate_ancestral_sequence(self, newick_node: Optional[Union[Node, str]] = None) -> None:
        node_list = []
        if not newick_node:
            node_list = self.root.get_list_nodes_info(filters={'node_type': ['node', 'leaf']}, only_node_list=True)
        else:
            node_list.append(newick_node)

        ancestral_alphabet = Tree.get_ancestral_alphabet()
        alphabet = Tree.get_alphabet(0)
        for current_node in node_list:
            current_node.ancestral_sequence = ''
            if current_node.father:
                for i in range(len(current_node.sequence)):
                    if current_node.sequence[i] == current_node.father.sequence[i] == alphabet[0]:
                        current_node.ancestral_sequence += ancestral_alphabet[0]
                    elif ((current_node.sequence[i] != current_node.father.sequence[i])
                          and (current_node.sequence[i] == alphabet[0])):
                        current_node.ancestral_sequence += ancestral_alphabet[1]
                    elif ((current_node.sequence[i] != current_node.father.sequence[i])
                          and (current_node.sequence[i] == alphabet[1])):
                        current_node.ancestral_sequence += ancestral_alphabet[2]
                    elif current_node.sequence[i] == current_node.father.sequence[i] == alphabet[1]:
                        current_node.ancestral_sequence += ancestral_alphabet[3]

    def calculate_marginal(self, newick_node: Optional[Union[Node, str]], alphabet: Union[Tuple[str, ...], str],
                           pattern: Optional[str] = None, node_name: Optional[str] = None
                           ) -> Tuple[Union[List[np.ndarray], List[float]], Union[np.ndarray, float]]:
        node_list, result = [], None
        if node_name and isinstance(node_name, str):
            Tree.rename_nodes(self, node_name)
        if not newick_node:
            node_list = self.root.get_list_nodes_info(filters={'node_type': ['node', 'root']}, only_node_list=True)
            if node_list:
                newick_node = np.random.choice(np.array(node_list))
        else:
            if isinstance(newick_node, str):
                newick_node = self.get_node_by_name(newick_node)
            node_list.append(newick_node)
        if not newick_node.up_vector and pattern:
            self.calculate_up(pattern, alphabet)
        if not newick_node.down_vector and newick_node.up_vector:
            self.calculate_down(alphabet)

        for current_node in node_list:
            qmatrix = current_node.get_jukes_cantor_qmatrix(len(alphabet))
            result = current_node.calculate_marginal(qmatrix, alphabet)

        return result

    def calculate_up(self, pattern: str, alphabet: Union[Tuple[str, ...], str]) -> Union[Tuple[Union[List[np.ndarray],
                                                                                         List[float]], float], float]:

        return self.root.calculate_up(self.get_pattern_dict(pattern, alphabet), alphabet)

    def calculate_down(self, alphabet: Union[Tuple[str, ...], str]) -> None:

        self.root.calculate_down(self.get_tree_info(), len(alphabet))

    def get_pattern_dict(self, pattern: str, alphabet: Optional[Union[Tuple[str, ...], str]] = None, only_leaves:
                         bool = True, value_is_string: bool = True) -> Dict[str, Union[Tuple[int, ...], str]]:
        node_types = ['leaf'] if only_leaves else ['leaf', 'node', 'root']
        nodes_info = self.get_list_nodes_info(True, 'pre-order', {'node_type': node_types})
        pattern_list = pattern.strip().split()
        pattern_list_size, pattern_dict = len(pattern_list), dict()
        if pattern_list_size == 1:
            for i, node_info in enumerate(nodes_info):
                if alphabet:
                    value = [0] * len(alphabet)
                    value[alphabet.index(pattern[i])] = 1
                else:
                    value = pattern[i]
                pattern_dict.update({node_info.get('node'): tuple(value)})
        else:
            for j in range(pattern_list_size // 2):
                node_name = pattern_list[j + j][1::]
                if self.find_dict_in_iterable(nodes_info, 'node', node_name):
                    if alphabet:
                        value = [int(k == pattern_list[j + j + 1]) for k in alphabet]
                    else:
                        value = pattern_list[j + j + 1]
                    value = ''.join(value) if value_is_string else tuple(value)
                    pattern_dict.update({node_name: value})

        return pattern_dict

    def calculate_tree_for_fasta(self, pattern: Union[Dict[str, str], str], alphabet: Union[Tuple[str, ...], str]
                                 ) -> str:
        node_list = self.root.get_list_nodes_info(only_node_list=True)
        for current_node in node_list:
            current_node.sequence = ''

        if isinstance(pattern, str):
            self.calculate_up(pattern, alphabet)
            self.calculate_down(alphabet)
            self.calculate_marginal(self.root, alphabet, pattern)
        else:
            leaves_info = self.get_list_nodes_info(True, None, {'node_type': ['leaf']})
            len_seq = len(min(list(pattern.values())))
            for i_char in range(len_seq):
                current_pattern = ''
                for i in range(len(leaves_info)):
                    node_name = leaves_info[i].get('node')
                    current_pattern += pattern.get(node_name)[i_char]
                self.calculate_up(current_pattern, alphabet)
                self.calculate_down(alphabet)
                self.calculate_marginal(None, alphabet, current_pattern)

        # self.calculate_ancestral_sequence()
        #
        return self.get_fasta_text()

    def calculate_likelihood(self, pattern: str, alphabet: Optional[Union[Tuple[str, ...], str]] = None) -> None:
        pattern_dict = self.get_pattern_dict(pattern)
        alphabet = alphabet if alphabet else Tree.get_alphabet_from_dict(pattern_dict)

        self.log_likelihood_vector, self.log_likelihood, self.likelihood = self.root.calculate_likelihood(pattern_dict,
                                                                                                          alphabet)

    def get_fasta_text(self, columns: Optional[Dict[str, str]] = None) -> str:
        columns = columns if columns else {'node': 'Name', 'sequence': 'Sequence', 'ancestral_sequence':
                                           'Ancestral sequence', 'children': 'child', 'lavel': 'Lavel', 'node_type':
                                           'Node Type'}
        table = self.tree_to_table(('Node Type', 'Name'), columns=columns)
        fasta_text = ''
        dict_table = table.to_dict()
        for i in table.T:
            fasta_text += f'>{dict_table.get("Name").get(i)}\n{dict_table.get("Sequence").get(i)}\n'

        return fasta_text[:-1]

    def get_json_structure(self, return_table: bool = False, columns: Optional[Dict[str, str]] = None
                           ) -> Dict[str, Union[List[str], str]]:
        if return_table:
            columns = columns if columns else {'node': 'Name', 'node_type': 'Node type', 'distance':
                                               'Distance to father', 'sequence': 'Sequence',
                                               'probabilities_sequence_characters': 'Probability coefficient',
                                               'ancestral_sequence': 'Ancestral sequence'}
            lists = ('probabilities_sequence_characters', 'sequence', 'ancestral_sequence')

            table = self.tree_to_table(columns=columns, list_type=list, lists=lists, distance_type=float,
                                       change_content_type=True)
            dict_json = dict()
            for row in table.T:
                dict_row = dict()
                for key in columns.values():
                    dict_row.update({key: table[key][row]})
                dict_json.update({table['Name'][row]: dict_row})
        else:
            dict_json = self.root.node_to_json(dict())

        return json.loads(str(dict_json).replace(f'\'', r'"'))

    def tree_to_newick_text(self, with_internal_nodes: bool = False, decimal_length: int = 0) -> str:

        return f'{self.root.subtree_to_newick(with_internal_nodes, decimal_length)};'

    @staticmethod
    def copy_to_txt_file(file_name: str) -> None:
        j = file_name[::-1].find('.')
        file_name_sm = f'{file_name[:-j]}' if len(file_name) > j > -1 else f'{file_name}.'
        with open(file_name, 'rb') as f:
            content = f.read()
            with open(f'{file_name_sm}txt', 'wb') as f_copy:
                f_copy.write(content)
                f_copy.flush()

    @staticmethod
    def get_columns_list_for_sorting() -> Dict[str, List[str]]:
        result = {'List for sorting': ['Name', 'Node type', 'Distance to father', 'Sequence', 'Probability coefficient',
                                       'Ancestral sequence']}

        return json.loads(str(result).replace(f'\'', r'"'))

    @staticmethod
    def tree_to_fasta(newick_tree: Union[str, 'Tree'], pattern: str, alphabet: Union[Tuple[str, ...], str],
                      file_name: str = 'file.fasta', node_name: Optional[str] = None, with_copy: bool = True) -> str:
        if node_name and isinstance(node_name, str):
            newick_tree = Tree.rename_nodes(newick_tree, node_name)
        else:
            newick_tree = Tree.check_tree(newick_tree)

        newick_tree.calculate_tree_for_fasta(newick_tree.get_pattern_dict(pattern), alphabet)
        Tree.make_dir(file_name)
        fasta_text = newick_tree.get_fasta_text()
        with open(file_name, 'w') as f:
            f.write(fasta_text)
        if with_copy:
            Tree.copy_to_txt_file(file_name)

        return file_name

    @staticmethod
    def likelihood_to_csv(newick_tree: Union[str, 'Tree'], pattern: str, file_name: str = 'file.csv', sep: str = '\t',
                          node_name: Optional[str] = None, with_copy: bool = True) -> str:
        if node_name and isinstance(node_name, str):
            newick_tree = Tree.rename_nodes(newick_tree, node_name)
        else:
            newick_tree = Tree.check_tree(newick_tree)

        Tree.make_dir(file_name)
        newick_tree.calculate_likelihood(pattern)
        tree_table = pd.DataFrame({'POS': range(len(newick_tree.log_likelihood_vector)),
                                   'log-likelihood': newick_tree.log_likelihood_vector})
        tree_table.to_csv(file_name, sep=sep, index=False)
        if with_copy:
            Tree.copy_to_txt_file(file_name)

        return file_name

    @staticmethod
    def tree_to_csv(newick_tree: Union[str, 'Tree'], file_name: str = 'file.csv', sep: str = '\t', sort_values_by:
                    Optional[Tuple[str, ...]] = None, decimal_length: int = 0, columns: Optional[Dict[str, str]] = None,
                    filters: Optional[Dict[str, List[Union[float, int, str, List[float]]]]] = None, node_name:
                    Optional[str] = None, with_copy: bool = True) -> str:
        if node_name and isinstance(node_name, str):
            newick_tree = Tree.rename_nodes(newick_tree, node_name)
        else:
            newick_tree = Tree.check_tree(newick_tree)

        Tree.make_dir(file_name)
        columns = columns if columns else {'node': 'Name', 'father_name': 'Parent', 'distance': 'Distance to father',
                                           'children': 'child'}
        table = newick_tree.tree_to_table(sort_values_by, decimal_length, columns, filters)
        table.to_csv(file_name, index=False, sep=sep)
        if with_copy:
            Tree.copy_to_txt_file(file_name)

        return file_name

    @staticmethod
    def tree_to_newick_file(newick_tree: Union[str, 'Tree'], file_name: str = 'tree_file.tree', with_internal_nodes:
                            bool = False, decimal_length: int = 0, node_name: Optional[str] = None, with_copy: bool =
                            True) -> str:
        if node_name and isinstance(node_name, str):
            newick_tree = Tree.rename_nodes(newick_tree, node_name)
        else:
            newick_tree = Tree.check_tree(newick_tree)

        newick_text = newick_tree.tree_to_newick_text(with_internal_nodes, decimal_length)

        Tree.make_dir(file_name)
        with open(file_name, 'w') as f:
            f.write(newick_text)
        if with_copy:
            Tree.copy_to_txt_file(file_name)

        return file_name

    @staticmethod
    def tree_to_visual_format(newick_tree: Union[str, 'Tree'], file_name: str = 'tree_file.svg', file_extensions:
                              Optional[Union[str, Tuple[str, ...]]] = None, with_internal_nodes: bool = False,
                              show_axes: bool = False, node_name: Optional[str] = None) -> Dict[str, str]:
        file_extensions = Tree.check_file_extensions_tuple(file_extensions, 'svg')
        if node_name and isinstance(node_name, str):
            newick_tree = Tree.rename_nodes(newick_tree, node_name)
        else:
            newick_tree = Tree.check_tree(newick_tree)

        Tree.make_dir(file_name)
        j = file_name[::-1].find('/')
        tmp_file = (f'{file_name[:-(j + 1)]}/tmp/{Tree.get_random_name()}'
                    f'.tree') if len(file_name) > j > -1 else f'tmp/{Tree.get_random_name()}.tree'
        Tree.make_dir(tmp_file)
        Tree.tree_to_newick_file(newick_tree, tmp_file, with_internal_nodes, with_copy=False)
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
        os.remove(tmp_file)

        return file_names

    @staticmethod
    def tree_to_interactive_html(newick_tree: Union[str, 'Tree'], pattern: str, alphabet: Union[Tuple[str, ...], str],
                                 file_name: str = 'interactive_tree.svg', node_name: Optional[str] = None) -> str:
        if node_name and isinstance(node_name, str):
            newick_tree = Tree.rename_nodes(newick_tree, node_name)
        else:
            newick_tree = Tree.check_tree(newick_tree)

        newick_tree.calculate_tree_for_fasta(newick_tree.get_pattern_dict(pattern), alphabet)
        newick_tree.calculate_ancestral_sequence()

        df = newick_tree.tree_to_table(columns={'node': 'target', 'father_name': 'source', 'distance': 'weight',
                                       'sequence': 'sequence', 'probabilities_sequence_characters': 'prob_characters',
                                                'node_type': 'node_type', 'ancestral_sequence': 'ancestral_sequence'},
                                       distance_type=float, filters={'node_type': ['leaf', 'node', 'root']},
                                       list_type=list)
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
        colors_as = {"A": "crimson", "G": "darkorange", "L": "forestgreen", "P": "slateblue"}
        for i in df_copy.T:
            probability_mark = probability_coefficient = ancestral_sequence = ''
            sequence = ''.join([Node.draw_cell_html_table(colors[Node.get_integer(j)], j)
                                for j in df_copy['sequence'][i]])
            sequence = Node.draw_row_html_table('Sequence', sequence)
            if df_copy["node_type"][i] != 'root':
                ancestral_sequence = ''.join([Node.draw_cell_html_table(colors_as[j], j)
                                              for j in df_copy['ancestral_sequence'][i]])
                ancestral_sequence = Node.draw_row_html_table('Ancestral sequence', ancestral_sequence)
            if df_copy["node_type"][i] != 'leaf':
                probability_mark = ''.join([Node.draw_cell_html_table(colors[Node.get_integer(j)], "9" if j == 1 else
                                            int(j * 10)) for j in df_copy['prob_characters'][i]])
                probability_mark = Node.draw_row_html_table('Probability mark (0-9)', probability_mark)
                probability_coefficient = ''.join([Node.draw_cell_html_table(colors[Node.get_integer(j)], f'{j:.3f}')
                                                  for j in df_copy['prob_characters'][i]])
                probability_coefficient = Node.draw_row_html_table('Probability coefficient', probability_coefficient)
                if df_copy["node_type"][i] == 'node':
                    d3.node_properties.get(df_copy['target'][i])['color'] = 'darkorange'
                    d3.node_properties.get(df_copy['target'][i])['size'] = 15
                if df_copy["node_type"][i] == 'root':
                    d3.node_properties.get(df_copy['target'][i])['color'] = 'firebrick'
                    d3.node_properties.get(df_copy['target'][i])['size'] = 20
            else:
                d3.node_properties.get(df_copy['target'][i])['color'] = 'forestgreen'
                d3.node_properties.get(df_copy['target'][i])['size'] = 10
            distance = f'<td class="h7 w-auto text-center">{df_copy["weight"][i]}</td>'
            info = (f'{Node.draw_row_html_table("Distance", distance)}{sequence}{ancestral_sequence}{probability_mark}'
                    f'{probability_coefficient}')
            d3.node_properties.get(df_copy['target'][i])['tooltip'] = Node.draw_html_table(info)
            d3.font.update({'type': 'Anonymous Pro'})

        d3.set_edge_properties(df)
        d3.show()
        # html = d3.chart.show(d3.edge_properties, config=d3.config, node_properties=d3.node_properties)
        return file_name
    #
    # @staticmethod
    # def tree_to_interactive_svg(newick_tree: Union[str, 'Tree'], pattern: str, alphabet: Union[Tuple[str, ...], str],
    #                             file_name: str = 'interactive_tree.svg', node_name: Optional[str] = None) -> str:
    #     from ete3 import (Tree as eteTree, NodeStyle as eteNodeStyle, TreeStyle as eteTreeStyle,
    #                       TextFace as eteTextFace)
    #
    #     # def my_layout(newick_node):
    #     #     if newick_node.is_leaf():
    #     #         newick_node.img_style["size"] = 10
    #     #         newick_node.img_style["fgcolor"] = "red"
    #     #     else:
    #     #         newick_node.img_style["size"] = 20
    #     #         newick_node.img_style["fgcolor"] = "blue"
    #
    #     if node_name and isinstance(node_name, str):
    #         newick_tree = Tree.rename_nodes(newick_tree, node_name)
    #     else:
    #         newick_tree = Tree.check_tree(newick_tree)
    #
    #     pattern_msa_dict = newick_tree.get_pattern_dict(pattern)
    #     newick_tree.calculate_tree_for_fasta(pattern_msa_dict, alphabet)
    #     newick_text = newick_tree.tree_to_newick_text(True)
    #
    #     Tree.make_dir(file_name)
    #
    #     ete_tree = eteTree(newick_text, format=1)
    #     tr_style = eteTreeStyle()
    #     # tr_style.layout_fn = my_layout
    #     tr_style.show_branch_support = True
    #     tr_style.mode = 'r'
    #     tr_style.branch_vertical_margin = 40
    #     tr_style.title.add_face(eteTextFace(newick_text, fsize=5, fgcolor='darkred'), column=0)
    #     tr_style.show_leaf_name, tr_style.show_scale, tr_style.show_branch_length = False, False, True
    #     tr_style.margin_left, tr_style.margin_right, tr_style.margin_top, tr_style.margin_bottom = 20, 20, 20, 20
    #
    #     nd_style = eteNodeStyle(shape='sphere', size=6, fgcolor='darkred', vt_line_type=0, vt_line_color='darkgray',
    #                             hz_line_type=0, hz_line_color='darkgray', bgcolor='white')
    #     for n in ete_tree.traverse():
    #         n.add_face(eteTextFace(n.name, fsize=10, fgcolor='maroon'), column=0)
    #         probability = ''.join(['9' if i == 1 else f'{int(i * 10)}'
    #                                for i in newick_tree.get_node_by_name(n.name).probabilities_sequence_characters])
    #         n.add_face(eteTextFace(newick_tree.get_node_by_name(n.name).sequence, fsize=10, fgcolor='navy'), column=0)
    #         n.add_face(eteTextFace(probability, fsize=10, fgcolor='darkgray'), column=0)
    #         n.set_style(nd_style)
    #     ete_tree.render(file_name, tree_style=tr_style)
    #     # ete_tree.show(tree_style=tr_style)
    #
    #     return file_name

    @staticmethod
    def tree_to_graph(newick_tree: Union[str, 'Tree'], file_name: str = 'graph.svg', file_extensions:
                      Optional[Union[str, Tuple[str, ...]]] = None, node_name: Optional[str] = None, with_copy: bool =
                      True) -> Union[str, Dict[str, str]]:
        file_extensions = Tree.check_file_extensions_tuple(file_extensions, 'png')
        if node_name and isinstance(node_name, str):
            newick_tree = Tree.rename_nodes(newick_tree, node_name)
        else:
            newick_tree = Tree.check_tree(newick_tree)

        Tree.make_dir(file_name)
        columns = {'node': 'Name', 'father_name': 'Parent', 'distance': 'Distance to father'}
        table = newick_tree.tree_to_table(None, 0, columns)
        table = table.drop(0)
        j = file_name[::-1].find('.')
        file_name_sm = f'{file_name[:-j]}' if len(file_name) > j > -1 else f'{file_name}.'
        file_names = dict()
        for file_extension in file_extensions:
            # file_name = f'{file_name[:-(j + 1)]}.{file_extension}' if len(file_name) > j > -1 else (f'{file_name}.'
            #                                                                                         f'{file_extension}')
            file_name = f'{file_name_sm}{file_extension}'
            file_names.update({f'Graph ({file_extension})': file_name})
            graph = nx.Graph()
            for row in table.values:
                graph.add_edge(row[1], row[0], length=(float(row[2]) if row[2] else 0.0))
            if file_extension in ('svg', 'png'):
                nx.draw(graph, with_labels=True, font_color='Maroon', node_color='Gold', node_size=1000,
                        font_weight='bold')
                plt.savefig(file_name, **{'format': file_extension, 'bbox_inches': 'tight', 'dpi': 300})
                plt.close()
            if file_extension in ('dot', ):
                nx.drawing.nx_pydot.write_dot(graph, file_name)
                if with_copy:
                    Tree.copy_to_txt_file(file_name)

        return file_names

    @staticmethod
    def get_random_name(lenght: int = 24) -> str:
        abc_list = [_ for _ in 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890']

        return ''.join(np.random.choice(abc_list, lenght))

    @staticmethod
    def get_ancestral_alphabet() -> Tuple[str, ...]:

        return 'A', 'G', 'L', 'P'

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
    def get_alphabet_from_dict(pattern_msa_dict: Dict[str, str]) -> Tuple[str, ...]:
        character_list = []
        for sequence in pattern_msa_dict.values():
            character_list += [i for i in sequence]

        return Tree.get_alphabet(set(character_list))

    @staticmethod
    def find_dict_in_iterable(iterable: Union[List[Union[Dict[str, Union[float, np.ndarray, bool, str, List[float],
                              List[np.ndarray]]], 'Node']], Tuple[Dict[str, Union[float, bool, str, List[float], Tuple[
                                   int, ...]]]]], key: str, value: Optional[Union[float, bool, str, List[float]]] = None
                              ) -> Dict[str, Union[float, bool, str, List[float], List[int], Tuple[int, ...]]]:
        for index, dictionary in enumerate(iterable):
            if key in dictionary and (True if value is None else dictionary[key] == value):
                return dictionary

    @staticmethod
    def make_dir(path: str) -> None:
        if path.find('/') > -1:
            path = '/'.join(path.split('/')[:-1])
            if not os.path.exists(path):
                os.makedirs(path)

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
    def __counter():
        """This method is for internal use only."""
        count = 0

        def sub_function():
            nonlocal count
            count += 1
            return count

        return sub_function

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
