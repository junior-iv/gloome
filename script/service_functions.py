import inspect
import json

from os import path, remove, makedirs
from typing import Callable, Any
from datetime import timedelta
from shutil import make_archive, move
from numpy import ndarray
from .tree import Tree
from .design_functions import *


def get_digit(data: str) -> Union[int, float, str]:
    try:
        return int(data)
    except ValueError:
        try:
            return float(data)
        except ValueError:
            return str(data)


def get_variables(request_form: Dict[str, str]) -> Tuple[Union[str, int, float], ...]:
    result = [bool(int(v)) if k[:2] == 'is' else get_digit(v) for k, v in request_form.items()]

    return tuple(result)


def get_dict(request_form: Dict[str, str]) -> Tuple[Union[str, int, float], ...]:
    result = {k: bool(int(v)) if k[:2] == 'is' else get_digit(v) for k, v in request_form.items()}

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


def create_tmp_data_files(msa: str, newick_tree: str, file_path: Optional[str] = None) -> Tuple[str, ...]:
    file_path = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'tmp') if file_path is None else file_path
    if not path.exists(file_path):
        makedirs(file_path)

    msa_file_path = create_file(file_path, msa, 'msa_file.msa')
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


def get_result_data(data: Union[Dict[str, Union[str, int, float, ndarray, List[Union[float, ndarray]]]],
                                List[Union[float, ndarray, Any]]],
                    action_name: str, form_data: Optional[Dict[str, Union[str, int, float, ndarray]]] = None
                    ) -> Dict[str, Union[str, int, float, ndarray, Dict[str, Union[str, int, float, ndarray]],
                                         List[Union[float, ndarray, Any]]]]:
    result = {'action_name': action_name, 'data': data}
    if form_data is not None:
        result.update({'form_data': form_data})

    return result


def check_tree_data(newick_tree: Union[str, Tree], msa: Union[Dict[str, str], str],
                    alphabet: Optional[Tuple[str, ...]]):
    if isinstance(newick_tree, str):
        newick_tree = Tree.rename_nodes(newick_tree)
    if isinstance(msa, str):
        msa = newick_tree.get_msa_dict(msa)
    if alphabet is None:
        alphabet = Tree.get_alphabet_from_dict(msa)
    return newick_tree, msa, alphabet


def execute_all_actions(newick_tree: Union[str, Tree], file_path: str, create_new_file: bool = False,
                        form_data: Optional[Dict[str, Union[str, int, float, ndarray]]] = None
                        ) -> Union[Dict[str, str], str]:

    result_data = {'draw_tree': draw_tree(newick_tree, file_path)}
    result_data.update({'compute_likelihood_of_tree': compute_likelihood_of_tree(newick_tree, file_path)})
    result_data.update({'create_all_file_types': create_all_file_types(newick_tree, file_path)})
    if create_new_file:
        return create_file(file_path, get_result_data(result_data, 'execute_all_actions', form_data), 'result.json')

    return result_data


def compute_likelihood_of_tree(newick_tree: Union[str, Tree], file_path: Optional[str] = None,
                               form_data: Optional[Dict[str, Union[str, int, float, ndarray]]] = None,
                               create_new_file: bool = False
                               ) -> Union[List[Union[float, ndarray]], str]:

    newick_tree.calculate_likelihood()
    result = [newick_tree.log_likelihood]

    if create_new_file:
        return create_file(file_path, get_result_data(result, 'compute_likelihood_of_tree', form_data), 'result.json')

    return result


def create_all_file_types(newick_tree: Union[str, Tree], file_path: str, create_new_file: bool = False,
                          form_data: Optional[Dict[str, Union[str, int, float, ndarray]]] = None
                          ) -> Union[Dict[str, str], str]:

    result = {'Interactive tree (html)': newick_tree.tree_to_interactive_html(f'{file_path}/interactive_tree.html')}
    # result.update(newick_tree.tree_to_graph(f'{file_path}/graph.txt', ('dot', 'png', 'svg')))
    # result.update(newick_tree.tree_to_visual_format(f'{file_path}/visual_tree.svg', True, ('txt', 'png', 'svg')))
    result.update(newick_tree.tree_to_visual_format(f'{file_path}/visual_tree.svg', True, ('png', )))
    # result.update({'Newick text (tree)': newick_tree.tree_to_newick_file(f'{file_path}/newick_tree.tree', True)})
    result.update({'Table of nodes (tsv)': newick_tree.tree_to_csv(f'{file_path}/node_results.tsv')})
    # result.update({'Fasta (fasta)': newick_tree.tree_to_fasta_file(f'{file_path}/fasta_file.fasta')})
    result.update({'log-Likelihood (tsv)': newick_tree.likelihood_to_csv(f'{file_path}/log_likelihood.tsv')})

    archive_path = path.join(path.dirname(file_path), path.basename(file_path))
    archive_name = make_archive(archive_path, 'zip', file_path, '.')
    new_archive_name = path.join(file_path, path.basename(archive_name))
    move(archive_name, new_archive_name)

    result.update({'Archive (zip)': new_archive_name})

    if create_new_file:
        return create_file(file_path, get_result_data(result, 'create_all_file_types', form_data), 'result.json')

    return result


def draw_tree(newick_tree: Tree, file_path: str, create_new_file: bool = False,
              form_data: Optional[Dict[str, Union[str, int, float, ndarray]]] = None) -> Union[List[Any], str]:
    size_factor = min(1 + newick_tree.get_node_count({'node_type': ['leaf']}) // 7, 3)
    result = [newick_tree.get_json_structure(),
              newick_tree.get_json_structure(return_table=True),
              newick_tree.get_columns_list_for_sorting(),
              {'Size factor': size_factor},
              newick_tree.get_json_structure(return_table=True, mode='branch'),
              newick_tree.get_columns_list_for_sorting(mode='branch')]

    if create_new_file:
        return create_file(file_path, get_result_data(result, 'draw_tree', form_data), 'result.json')

    return result


def convert_seconds(seconds: float) -> str:
    return str(timedelta(seconds=seconds))


def get_error(err_list: List[Tuple[str, str]]) -> str:
    return ''.join([f'{key_design(error_type, True, 14)}'
                    f'{value_design(error, True, 14)}\n' for error_type, error in err_list])


def check_data(*args) -> List[Tuple[str, str]]:
    err_list = []
    newick_text = args[0].strip()
    msa = args[1].strip()
    categories_quantity = int(args[2])
    alpha = float(args[3])
    pi_1 = float(args[4])
    coefficient_bl = float(args[5])
    is_optimize_pi = bool(args[6])
    is_optimize_pi_average = bool(args[7])
    is_optimize_alpha = bool(args[8])
    is_optimize_bl = bool(args[9])

    if not isinstance(categories_quantity, int) or not 1 <= categories_quantity <= 16:
        err_list.append((f'Number of rate categories value error [ {categories_quantity} ]',
                         f'The value must be between 1 and 16.'))

    if not isinstance(alpha, float) or not 0.1 <= alpha <= 20:
        err_list.append((f'Alpha value error [ {alpha} ]', f'The value must be between 0.1 and 20.'))

    if not isinstance(pi_1, float) or not 0.001 <= pi_1 <= 0.999:
        err_list.append((f'π1 value error [ {pi_1} ]', f'The value must be between 0.001 and 0.999.'))

    if not isinstance(coefficient_bl, float) or not 0.1 <= coefficient_bl <= 10:
        err_list.append((f'Branch lengths (BL) coefficient value error [ {coefficient_bl} ]',
                         f'The value must be between 0.1 and 10.'))

    if not isinstance(is_optimize_pi, bool):
        err_list.append((f'optimize π1 value (algorithmic) error [ {is_optimize_pi} ]',
                         f'The value must be boolean type.'))

    if not isinstance(is_optimize_pi_average, bool):
        err_list.append((f'optimize π1 value (empirical) error [ {is_optimize_pi_average} ]',
                         f'The value must be boolean type.'))

    if not isinstance(is_optimize_alpha, bool):
        err_list.append((f'optimize α value error [ {is_optimize_alpha} ]', f'The value must be boolean type.'))

    if not isinstance(is_optimize_bl, bool):
        err_list.append((f'optimize branch lengths coefficient value error [ {is_optimize_bl} ]',
                         f'The value must be boolean type.'))

    if not msa:
        err_list.append(('MSA error', 'No MSA was provided.'))
    elif not msa.startswith('>'):
        err_list.append(('MSA error', 'Wrong MSA format. Please provide MSA in FASTA format.'))
    elif len(msa.split('\n')) / 2 < 2:
        err_list.append(('MSA error', 'There should be at least two sequences in the MSA.'))
    else:
        len_list = []
        incorrect_characters = ''
        for i, current_line in enumerate(msa.split()):
            if i % 2:
                current_line = current_line.strip()
                len_list.append(len(current_line))
                for j in current_line:
                    if j not in '01':
                        incorrect_characters += f'{j} '

        if min(len_list) != max(len_list):
            err_list.append((f'MSA error', f'The MSA contains sequences of different lengths.'))
        if incorrect_characters:
            err_list.append(('MSA error',
                             f'MSA file contains an illegal character(s) [ {incorrect_characters.strip()} ]. '
                             f'Please note that “0” and “1” are the only allowed characters in the phyletic MSAs.'))

        msa_list = msa.strip().split()
        msa_taxa_info = [msa_list[j + j][1::] for j in range(len(msa_list) // 2)]

        if len(msa_taxa_info) != len(msa_taxa_info):
            err_list.append((f'MSA error', f'Duplicate taxa names found.'))

        if not newick_text:
            err_list.append((f'TREE error', f'No Phylogenetic tree was provided.'))
        elif (not (newick_text.startswith('(') and newick_text.endswith(';') and newick_text[:-1].endswith(')')) or
              (newick_text.count('(') != newick_text.count(')'))):
            err_list.append((f'TREE error', f'Wrong Phylogenetic tree format. Please provide a tree in Newick format.'))
        else:
            try:
                current_tree = Tree(newick_text)
            except ValueError:
                current_tree = None

            if current_tree:
                edges_distances_list = current_tree.tree_to_table(filters={'node_type': ['leaf', 'node']},
                                                                  columns={'distance': 'distance'},
                                                                  distance_type=float).T.values[0].tolist()
                if not all(edges_distances_list):
                    err_list.append((f'TREE error', f'One or more branches in the tree have zero length.'))
                if not (current_tree.get_node_count({'node_type': ['leaf']}) == len(msa.split('\n')) / 2 ==
                        msa.count('>')):
                    err_list.append((f'MSA error',
                                     f'A discrepancy exists between the number of leaves in the phylogenetic tree and '
                                     f'the number of sequences present in the MSA data.'))

                tree_taxa_info = current_tree.tree_to_table(filters={'node_type': ['leaf']},
                                                            columns={'node': 'node'}).T.values[0].tolist()

                if len(tree_taxa_info) != len(set(tree_taxa_info)):
                    err_list.append((f'TREE error', f'Duplicate taxa names found.'))

                if set(tree_taxa_info).difference(set(msa_taxa_info)):
                    err_list.append((f'DATA MISMATCH error',
                                     f'Taxa names in the MSA and phylogenetic tree do not match.'))
            else:
                err_list.append((f'TREE error',
                                 f'Wrong Phylogenetic tree format. Please provide a tree in Newick format.'))

    return err_list


def get_function_parameters(func: Callable) -> Tuple[str, ...]:
    return tuple(inspect.signature(func).parameters.keys())
