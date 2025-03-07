from time import time
from typing import Union, Dict, Optional, Tuple
from datetime import timedelta
from tree import Tree
from flask import url_for
from numpy import ndarray


def compute_likelihood_of_tree(newick_text: str, pattern_msa: str, rate_vector:
                               Optional[Tuple[Union[float, ndarray], ...]] = None) -> Dict[str, Union[str, float, int]]:
    start_time = time()
    newick_tree = Tree.rename_nodes(newick_text)
    newick_tree.calculate_likelihood(pattern_msa, rate_vector=rate_vector)

    result = {'execution_time': convert_seconds(time() - start_time)}
    result.update({'likelihood_of_the_tree': newick_tree.likelihood})
    result.update({'log-likelihood_of_the_tree': newick_tree.log_likelihood})
    result.update({'log-likelihood_list': newick_tree.log_likelihood_vector})

    return result


def create_all_file_types(newick_text: str, pattern_msa: str, file_path: str, rate_vector:
                          Optional[Tuple[Union[float, ndarray], ...]] = None) -> Dict[str, Union[str, float, int]]:
    start_time = time()
    path_dict = dict()
    newick_tree = Tree.rename_nodes(newick_text)
    pattern_dict = newick_tree.get_pattern_dict(pattern_msa)
    alphabet = Tree.get_alphabet_from_dict(pattern_dict)
    path_dict.update({'Interactive tree (html)': Tree.tree_to_interactive_html(newick_tree, pattern_msa, alphabet,
                     file_name=f'{file_path}/interactive_tree.html')})
    path_dict.update(Tree.tree_to_graph(newick_tree, file_name=f'{file_path}/graph.txt',
                     file_extensions=('dot', 'png', 'svg')))
    path_dict.update(Tree.tree_to_visual_format(newick_tree, file_name=f'{file_path}/visual_tree.svg',
                     file_extensions=('txt', 'png', 'svg'), with_internal_nodes=True))
    path_dict.update({'Newick text (tree)': Tree.tree_to_newick_file(newick_tree,
                     file_name=f'{file_path}/newick_tree.tree', with_internal_nodes=True)})
    path_dict.update({'Table of nodes (csv)': Tree.tree_to_csv(newick_tree, file_name=f'{file_path}/tree.csv',
                     sep='\t', sort_values_by=('child', 'Name'), decimal_length=8)})
    path_dict.update({'Fasta (fasta)': Tree.tree_to_fasta(newick_tree, pattern_msa, alphabet,
                     file_name=f'{file_path}/fasta_file.fasta')})
    path_dict.update({'log-Likelihood (csv)': Tree.likelihood_to_csv(newick_tree, pattern_msa,
                     file_name=f'{file_path}/log-likelihood.csv', sep='\t', rate_vector=rate_vector)})

    result = {'execution_time': convert_seconds(time() - start_time)}
    for key, value in zip(path_dict.keys(), path_dict.values()):
        value = value[value.index(file_path) + len(file_path):]
        result.update({f'{key}': f'<a mx-2 class="w-auto mw-auto form-control btn btn-outline-link rounded-pill" '
                                 f'href="{url_for("get_file", file_path=value, mode="download")}" '
                                 f'target="_blank"><h7>download</h7></a>\t'
                                 f'<a mx-2 class="w-auto mw-auto form-control btn btn-outline-link rounded-pill" '
                                 f'href="{url_for("get_file", file_path=value, mode="view")}" '
                                 f'target="_blank"><h7>view</h7></a>'})

    return result


def convert_seconds(seconds: float) -> str:
    return str(timedelta(seconds=seconds))
