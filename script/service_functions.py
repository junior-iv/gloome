from os import path, remove, makedirs
from typing import Callable, Any, Union, Dict, List
from datetime import timedelta
from shutil import make_archive, move
from numpy import ndarray
from .tree import Tree
from .design_functions import *
import inspect
import json

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


def create_file(file_path: str, data: Union[str, Any], file_name: Optional[str] = None) -> str:
    if file_name and isinstance(file_name, str):
        file_path = path.join(file_path, file_name)
    with open(file_path, 'w') as f:
        if isinstance(data, str):
            f.write(data)
        else:
            f.write(json.dumps(data))

    return file_path


def create_tmp_data_files(pattern: str, newick_tree: str, file_path: Optional[str] = None) -> Tuple[str, ...]:
    file_path = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'tmp') if file_path is None else file_path
    if not path.exists(file_path):
        makedirs(file_path)

    msa_file_path = create_file(file_path, pattern, 'msa_file.msa')
    tree_file_path = create_file(file_path, newick_tree, 'tree_file.tree')

    return msa_file_path, tree_file_path


def del_file(file_path: str) -> None:
    if path.isfile(file_path):
        remove(file_path)


def read_file(file_path: str) -> Optional[str]:
    if path.isfile(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    return ''


def loads_json(data: str) -> Any:
    return json.loads(data)


def dumps_json(data: Any) -> str:
    return json.dumps(data)


def del_files(files: Union[str, Tuple[str, ...]]) -> None:
    if isinstance(files, str):
        del_file(files)
    else:
        for file in files:
            del_file(file)


def get_log_file(data: Any, file_path: str, num: int = 1) -> int:
    log_name = path.basename(path.abspath(file_path))
    new_path = path.join(path.join(path.dirname(path.dirname(path.dirname(path.abspath(file_path)))), 'tmp'),
                         f'{log_name}_{num}.log')
    with open(new_path, 'a') as f:
        f.write(f"\n\n--- {log_name}_{num} str---\n")
        f.write(str(data))
        if not isinstance(data, str):
            f.write(f"\n\n--- {log_name}_{num} data---\n")
            f.write(json.dumps(data))
    num += 1
    return num


def execute_all_actions(newick_tree: Union[str, Tree], pattern: Union[Dict[str, str], str], file_path: str,
                        rate_vector: Optional[Tuple[Union[float, ndarray], ...]] = None,
                        alphabet: Optional[Tuple[str, ...]] = None) -> Union[Dict[str, str], str]:
    if isinstance(newick_tree, str):
        newick_tree = Tree.rename_nodes(newick_tree)
    if isinstance(pattern, str):
        pattern = newick_tree.get_pattern_dict(pattern)

    result = {'draw_tree': draw_tree(newick_tree, file_path, True)}
    result.update({'compute_likelihood_of_tree': compute_likelihood_of_tree(newick_tree, pattern, rate_vector,
                                                                            file_path, True)})
    result.update({'create_all_file_types': create_all_file_types(newick_tree, pattern, file_path, rate_vector,
                                                                  alphabet, True)})

    file_path = create_file(file_path, result, 'execute_all_actions.json')
    print(f'result: {result}')
    print(f'file_path: {file_path}')

    return file_path


def compute_likelihood_of_tree(newick_tree: Union[str, Tree], pattern: Union[Dict[str, str], str], rate_vector:
                               Optional[Tuple[Union[float, ndarray], ...]] = None, file_path: Optional[str] = None,
                               return_dict: bool = False) -> Union[dict[str, Union[float, ndarray,
                                                                   list[Union[float, ndarray]]]], str]:
    # start_time = time()
    if isinstance(newick_tree, str):
        newick_tree = Tree.rename_nodes(newick_tree)
    if isinstance(pattern, str):
        pattern = newick_tree.get_pattern_dict(pattern)

    newick_tree.calculate_likelihood(pattern, rate_vector=rate_vector)

    result = {'likelihood_of_the_tree': newick_tree.likelihood}
    result.update({'log-likelihood_of_the_tree': newick_tree.log_likelihood})
    result.update({'log-likelihood_list': newick_tree.log_likelihood_vector})
    if return_dict:
        return result

    file_path = create_file(file_path, result, 'compute_likelihood_of_tree.json')
    print(f'result: {result}')
    print(f'file_path: {file_path}')

    return file_path


def create_all_file_types(newick_tree: Union[str, Tree], pattern: Union[Dict[str, str], str], file_path: str,
                          rate_vector: Optional[Tuple[Union[float, ndarray], ...]] = None,
                          alphabet: Optional[Tuple[str, ...]] = None, return_dict: bool = False
                          ) -> Union[Dict[str, str], str]:
    # start_time = time()
    if isinstance(newick_tree, str):
        newick_tree = Tree.rename_nodes(newick_tree)
    if isinstance(pattern, str):
        pattern = newick_tree.get_pattern_dict(pattern)
    if alphabet is None:
        alphabet = Tree.get_alphabet_from_dict(pattern)
    path_dict = {'Interactive tree (html)': Tree.tree_to_interactive_html(newick_tree, pattern, alphabet,
                 file_name=f'{file_path}/interactive_tree.html', rate_vector=rate_vector)}
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

    archive_path = path.join(path.dirname(file_path), path.basename(file_path))
    archive_name = make_archive(archive_path, 'zip', file_path, '.')
    new_archive_name = path.join(file_path, path.basename(archive_name))
    move(archive_name, new_archive_name)

    path_dict.update({'Archive (zip)': new_archive_name})

    if return_dict:
        return path_dict

    file_path = create_file(file_path, path_dict, 'create_all_file_types.json')
    print(f'result: {path_dict}')
    print(f'file_path: {file_path}')

    return file_path


def draw_tree(newick_tree: Tree, file_path: str, return_dict: bool = False) -> Union[List[Any], str]:
    result = [newick_tree.get_json_structure(),
              newick_tree.get_json_structure(return_table=True),
              newick_tree.get_columns_list_for_sorting()]
    size_factor = min(1 + newick_tree.get_node_count({'node_type': ['leaf']}) // 7, 3)
    result.append({'Size factor': size_factor})
    if return_dict:
        return result

    file_path = create_file(file_path, result, 'draw_tree.json')
    print(f'result: {result}')
    print(f'file_path: {file_path}')

    return file_path
#
#
# def execute_function_with_delay(func: Callable, waiting_time: int = 10, steps_number: int = 6, **kwargs
#                                 ) -> Optional[Any]:
#     result_func = None
#     for _ in range(steps_number):
#         sleep(waiting_time)
#         result_func = func(**kwargs)
#         print(result_func)
#
#     return result_func


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
