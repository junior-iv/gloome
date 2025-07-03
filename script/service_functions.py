from os import path, remove, makedirs
from typing import Callable, Any
from datetime import timedelta
from shutil import make_archive, move
from numpy import ndarray
from .tree import Tree
from .design_functions import *
import inspect
import json


def get_digit(data: str) -> Union[int, float, str]:
    try:
        return int(data)
    except ValueError:
        try:
            return float(data)
        except ValueError:
            return str(data)


def get_variables(request_form: Dict[str, str]) -> Tuple[Union[str, int, float], ...]:
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


def convert_seconds(seconds: float) -> str:
    return str(timedelta(seconds=seconds))


def get_error(err_list: List[Tuple[str, str]]) -> str:
    return ''.join([f'{key_design(error_type, True, 14)}'
                    f'{value_design(error, True, 14)}\n' for error_type, error in err_list])


def check_data(*args) -> List[Tuple[str, str]]:
    err_list = []
    newick_text = args[0].strip()
    pattern_msa = args[1].strip()
    categories_quantity = args[2]
    alpha = args[3]

    if not isinstance(categories_quantity, int) or not 1 <= categories_quantity <= 1000:
        err_list.append((f'Number of rate categories value error <{categories_quantity}>',
                         f'The value must be between 1 and 1000.'))
    if not isinstance(alpha, float) or not 0.01 <= alpha <= 100000:
        err_list.append((f'Alpha value error <{alpha}>', f'The value must be between 1 and 1000.'))

    if not pattern_msa:
        err_list.append(('MSA error', 'No MSA was provided.'))
    elif not pattern_msa.startswith('>'):
        err_list.append(('MSA error', 'Wrong MSA format. Please provide MSA in FASTA format.'))
    elif len(pattern_msa.split('\n')) / 2 < 2:
        err_list.append(('MSA error', 'There should be at least two sequences in the MSA.'))
    else:
        len_list = []
        incorrect_characters = ''
        for i, current_line in enumerate(pattern_msa.split('\n')):
            if i % 2:
                current_line = current_line.strip()
                len_list.append(len(current_line))
                for j in current_line:
                    if j not in '01':
                        incorrect_characters += f'{j} '
        if min(len_list) != max(len_list):
            err_list.append((f'MSA error', f'The MSA contains sequences of different lengths.'))
        elif incorrect_characters:
            err_list.append(('MSA error',
                             f'MSA file contains an illegal character(s) <{incorrect_characters}>.\n'
                             f'Please note that “0” and “1” are the only allowed characters in the phyletic '
                             f'pattern MSAs.'))

        if not newick_text:
            err_list.append((f'TREE error', f'No Phylogenetic tree was provided.'))
        elif (not (newick_text.startswith('(') and newick_text.endswith(';') and newick_text[:-1].endswith(')')) or
              (newick_text.count('(') != newick_text.count(')'))):
            err_list.append((f'TREE error', f'Wrong Phylogenetic tree format. Please provide a tree in Newick format'))
        else:
            try:
                current_tree = Tree(newick_text)
            except ValueError:
                current_tree = None

            if current_tree:
                if not (current_tree.get_node_count({'node_type': ['leaf']}) == len(pattern_msa.split('\n')) / 2 ==
                        pattern_msa.count('>')):
                    err_list.append((f'MSA error',
                                     f'A discrepancy exists between the number of leaves in the phylogenetic tree and '
                                     f'the number of sequences present in the MSA data'))
            else:
                err_list.append((f'TREE error',
                                 f'Wrong Phylogenetic tree format. Please provide a tree in Newick format'))

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
