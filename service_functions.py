from time import time
from typing import Union, Dict, Optional, Tuple, List
from datetime import timedelta
from tree import Tree
from flask import url_for
from numpy import ndarray
import design_functions as df

ERR = [f'{df.key_design("Incorrect phylogenetic tree of newick format", True, 14)}',
       f'{df.key_design("Incorrect pattern MSA", True, 14)}',
       f'{df.key_design("Number of leaves doesn`t match", True, 14)}',
       f'{df.key_design("Different length of the sequences in the pattern MSA", True, 14)}',
       f'{df.key_design("correct examples", True, 14)}']

EXAMPLES = (('((S1:0.3,S2:0.15):0.1,S3:0.4);', '((S1:0.3,S2:0.15)N2:0.1,S3:0.4)N1;'),
            ('>S1', '0', '>S2', '1', '>S3', '0'),
            ('>S1', '0', '>S2', '1', '>S3', '0', '((S1:0.3,S2:0.15):0.1,S3:0.4);'),
            ('>S1', '010', '>S2', '111', '>S3', '001'))



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


def get_error(err_list: List[Tuple[int, str]]) -> str:
    return ''.join([f'{ERR[i]}{df.value_design(err, True, 5)}'
                    f'{ERR[-1]}{df.value_design(EXAMPLES[i], True, 5)}' for i, err in err_list])


def check_form(newick_text: str, pattern_msa: str) -> List[Tuple[int, str]]:
    err_list = []

    if not Tree.check_newick(newick_text):
        err_list.append((0, newick_text if newick_text else 'text missing'))
    if not pattern_msa:
        err_list.append((1, 'text missing'))
    elif (Tree.check_newick(newick_text) and
          not (Tree(newick_text).get_node_count({'node_type': ['leaf']}) == len(pattern_msa.split('\n')) / 2 ==
          pattern_msa.count('>'))):
        err_list.append((2, pattern_msa.split('\n') if pattern_msa else 'text missing'))
    else:
        row_len = len(pattern_msa.split('\n')[1].strip())
        if not min([len(j.strip()) == row_len for i, j in enumerate(pattern_msa.split('\n')) if i % 2]):
            err_list.append((3, pattern_msa.split('\n')))
    return err_list
