from math import log
from typing import List, Union, Tuple, Optional, Dict
from tree import Tree
from node import Node
import numpy as np
import array_functions as af
import service_functions as sf


def compute_likelihood_of_tree(newick_text: str, pattern_msa: Optional[str] = None) -> Tuple[List[float], float, float]:
    pattern_msa_list = pattern_msa.split()
    pattern_msa_dict = dict()
    for j in range(len(pattern_msa_list) // 2):
        pattern_msa_dict.update({pattern_msa_list[j + j][1::]: pattern_msa_list[j + j + 1]})

    alphabet = sf.get_alphabet_from_dict(pattern_msa_dict)
    newick_tree = Tree(newick_text)
    alphabet_size = len(alphabet)

    leaves_info = newick_tree.get_list_nodes_info(True, 'pre-order', {'node_type': ['leaf']})

    len_seq = len(list(pattern_msa_dict.values())[0])
    likelihood = 1
    log_likelihood = 0
    log_likelihood_list = []
    for i_char in range(len_seq):
        leaves_dict = dict()
        for i in range(len(leaves_info)):
            node_name = leaves_info[i].get('node')
            sequence = pattern_msa_dict.get(node_name)[i_char]
            frequency = [0] * alphabet_size
            frequency[alphabet.index(sequence)] = 1
            leaves_dict.update({node_name: tuple(frequency)})
        char_likelihood = calculate_felsensteins_likelihood_of_tree(newick_tree.root, leaves_dict, alphabet)
        likelihood *= char_likelihood
        log_likelihood += log(char_likelihood)
        log_likelihood_list.append(log(char_likelihood))

    return log_likelihood_list, log_likelihood, likelihood


def calculate_felsensteins_likelihood_of_tree(newick_node: Node, leaves_dict: Dict[str, Tuple[int, ...]], alphabet:
                                              Tuple[str, ...]) -> Union[Tuple[Union[Tuple[np.ndarray, ...], Tuple[float,
                                                                        ...]], float], float]:
    alphabet_size = len(alphabet)
    if not newick_node.children:
        return leaves_dict.get(newick_node.name), newick_node.distance_to_father

    l_vect, l_dist = calculate_felsensteins_likelihood_of_tree(newick_node.children[0], leaves_dict, alphabet)
    r_vect, r_dist = calculate_felsensteins_likelihood_of_tree(newick_node.children[1], leaves_dict, alphabet)

    l_qmatrix = af.get_jukes_cantor_qmatrix(l_dist, alphabet_size)
    r_qmatrix = af.get_jukes_cantor_qmatrix(r_dist, alphabet_size)

    vector = []
    for j in range(alphabet_size):
        freq_l = freq_r = 0
        for i in range(alphabet_size):
            freq_l += l_qmatrix[i, j] * l_vect[i]
            freq_r += r_qmatrix[i, j] * r_vect[i]
        vector.append(freq_l * freq_r)
    vector = tuple(vector)

    if newick_node.father:
        return vector, newick_node.distance_to_father
    else:
        return np.sum([1 / alphabet_size * i for i in vector])
