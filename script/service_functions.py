from time import time
from typing import Union, Dict, Optional, Tuple, List, Callable, Set
from datetime import timedelta
from flask import url_for
from numpy import ndarray
from .tree import Tree
from .design_functions import *
import inspect

# ERR = [f'{key_design("Incorrect phylogenetic tree of newick format", True, 14)}',
#        f'{key_design("Incorrect pattern MSA", True, 14)}',
#        f'{key_design("Number of leaves doesn`t match", True, 14)}',
#        f'{key_design("Different length of the sequences in the pattern MSA", True, 14)}',
#        f'{key_design("correct examples", True, 14)}']

ERR = (f'Incorrect phylogenetic tree of newick format',
       f'Incorrect pattern MSA',
       f'Number of leaves doesn`t match',
       f'Different length of the sequences in the pattern MSA',
       f'correct examples')

EXAMPLES = (('((S1:0.3,S2:0.15):0.1,S3:0.4);', '((S1:0.3,S2:0.15)N2:0.1,S3:0.4)N1;'),
            ('>S1', '0', '>S2', '1', '>S3', '0'),
            ('>S1', '0', '>S2', '1', '>S3', '0', '((S1:0.3,S2:0.15):0.1,S3:0.4);'),
            ('>S1', '010', '>S2', '111', '>S3', '001'))


def get_digit(data: str) -> Union[int, float, str]:
    try:
        return int(data)
    except ValueError:
        try:
            return float(data)
        except ValueError:
            return str(data)


def get_tree_variables(request_form: Dict[str, str]) -> Tuple[Union[str, int, float], ...]:
    result = []
    for key in request_form.keys():
        result.append(get_digit(request_form[key]))

    return tuple(result)


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


def create_all_file_types(newick_tree: Union[str, Tree], pattern: Union[Dict[str, str], str], file_path: str,
                          rate_vector: Optional[Tuple[Union[float, ndarray], ...]] = None,
                          alphabet: Tuple[str, ...] = None, local: bool = True) -> Dict[str, Union[str, float, int]]:
    start_time = time()
    path_dict = dict()
    if isinstance(newick_tree, str):
        newick_tree = Tree.rename_nodes(newick_tree)
    if isinstance(pattern, str):
        pattern = newick_tree.get_pattern_dict(pattern)
    if isinstance(alphabet, str):
        alphabet = Tree.get_alphabet_from_dict(pattern)
    path_dict.update({'Interactive tree (html)': Tree.tree_to_interactive_html(newick_tree, pattern, alphabet,
                     file_name=f'{file_path}/interactive_tree.html', rate_vector=rate_vector)})
    path_dict.update(Tree.tree_to_graph(newick_tree, file_name=f'{file_path}/graph.txt',
                     file_extensions=('dot', 'png', 'svg')))
    path_dict.update(Tree.tree_to_visual_format(newick_tree, file_name=f'{file_path}/visual_tree.svg',
                     file_extensions=('txt', 'png', 'svg'), with_internal_nodes=True))
    path_dict.update({'Newick text (tree)': Tree.tree_to_newick_file(newick_tree,
                     file_name=f'{file_path}/newick_tree.tree', with_internal_nodes=True)})
    path_dict.update({'Table of nodes (csv)': Tree.tree_to_csv(newick_tree, file_name=f'{file_path}/tree.csv',
                     sep='\t', sort_values_by=('child', 'Name'), decimal_length=8)})
    path_dict.update({'Fasta (fasta)': Tree.tree_to_fasta(newick_tree, pattern, alphabet,
                     file_name=f'{file_path}/fasta_file.fasta', rate_vector=rate_vector)})
    path_dict.update({'log-Likelihood (csv)': Tree.likelihood_to_csv(newick_tree, pattern,
                     file_name=f'{file_path}/log-likelihood.csv', sep='\t', rate_vector=rate_vector)})

    result = {'execution_time': convert_seconds(time() - start_time)}
    # result.update({'process id': process_id})
    for key, value in zip(path_dict.keys(), path_dict.values()):
        if local:
            result.update({key: value})
        else:
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
    return ''.join([f'{ERR[i]}{value_design(err, True, 5)}'
                    f'{ERR[-1]}{value_design(EXAMPLES[i], True, 5)}' for i, err in err_list])


def check_data(newick_text: str, pattern_msa: str) -> List[Tuple[str, str]]:
    err_list = []

    # print(newick_text)
    if not Tree.check_newick(newick_text):
        err_list.append((ERR[0], newick_text if newick_text else 'text missing'))
    if not pattern_msa:
        err_list.append((ERR[1], 'text missing'))
    elif (Tree.check_newick(newick_text) and
          not (Tree(newick_text).get_node_count({'node_type': ['leaf']}) == len(pattern_msa.split('\n')) / 2 ==
          pattern_msa.count('>'))):
        err_list.append((ERR[2], pattern_msa.split('\n') if pattern_msa else 'text missing'))
    else:
        row_len = len(pattern_msa.split('\n')[1].strip())
        if not min([len(j.strip()) == row_len for i, j in enumerate(pattern_msa.split('\n')) if i % 2]):
            err_list.append((ERR[3], pattern_msa.split('\n')))
    return err_list


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


def get_function_parameters(func: Callable) -> Tuple[str, ...]:
    return tuple(inspect.signature(func).parameters.keys())


#
# def progress_bar(progress: Union[str, int, float]):
#     def actual_decorator(func):
#         import time
#
#         def wrapper(*args, **kwargs):
#             total = 0
#             for i in range(iters):
#                 start = time.time()
#                 return_value = func(*args, **kwargs)
#                 end = time.time()
#                 total = total + (end - start)
#             print('[*] Среднее время выполнения: {} секунд.'.format(total / iters))
#             return return_value
#
#         return wrapper
#
#     return actual_decorator
