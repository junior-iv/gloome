import inspect
import json
import re

from pathlib import Path
from typing import Callable, Any
from datetime import timedelta
from shutil import make_archive, move
from numpy import ndarray

from gloome.tree.tree import Tree
from gloome.services.design_functions import *

SELECTED_FILES = {'file_interactive_tree_html': True,
                  'file_newick_tree_png': True,
                  'file_table_of_posterior_rates_tsv': True,
                  'file_table_of_pearson_correlation_tsv': True,
                  'file_table_of_nodes_tsv': True,
                  'file_probability_per_pos_per_branches_tsv': True,
                  'file_table_of_branches_tsv': True,
                  'file_log_likelihood_tsv': True,
                  'file_table_of_attributes_tsv': True,
                  'file_phylogenetic_tree_nwk': True}
PREFERRED_URL_SCHEME = 'https'
WEBSERVER_NAME = 'gloome.tau.ac.il'
WEBSERVER_URL = f'{PREFERRED_URL_SCHEME}://{WEBSERVER_NAME}'


def get_digit(data: str) -> Union[int, float, str]:
    try:
        return int(data)
    except ValueError:
        try:
            return float(data)
        except ValueError:
            return str(data)


def get_variables(request_form: Dict[str, str]) -> Tuple[Union[str, int, float], ...]:
    result = [bool(int(v)) if k[:2] == 'is' or k[:4] == 'file' else get_digit(v) for k, v in request_form.items()]

    return tuple(result)


def get_dict(request_form: Dict[str, str]) -> Tuple[Union[str, int, float], ...]:
    result = {k: bool(int(v)) if k[:2] == 'is' or k[:4] == 'file' else get_digit(v) for k, v in request_form.items()}

    return tuple(result)


def get_path(path: Union[str, Path]) -> Path:
    if path and isinstance(path, str):
        return Path(path)

    return path


def create_file(file_path: Union[str, Path], data: Union[str, Any], file_name: Optional[str] = None) -> Path:
    file_path = get_path(file_path)
    if file_name and isinstance(file_name, str):
        file_path.joinpath(file_name)
    save_file(file_path, data)

    return file_path


def del_file(file_path: Union[str, Path]) -> None:
    file_path = get_path(file_path)
    if file_path.is_file():
        file_path.unlink(missing_ok=True)


def read_file(file_path: Union[str, Path], mode: str = 'r') -> str:
    file_path = get_path(file_path)
    if file_path.is_file():
        with open(file_path, mode) as f:
            return f.read()

    return ''


def save_file(file_path: Union[str, Path], data: Union[str, Any], mode: str = 'w') -> None:
    with open(file_path, mode) as f:
        if isinstance(data, str):
            f.write(data)
        else:
            f.write(dumps_json(data))


def loads_json(data: str) -> Any:

    return json.loads(data)


def dumps_json(data: Any) -> str:

    return json.dumps(data)


def del_files(file_list: Union[Union[str, Path], Tuple[Union[str, Path], ...]]) -> None:
    if isinstance(file_list, (str, Path)):
        del_file(file_list)
    else:
        for file in file_list:
            del_file(file)


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


def execute_all_actions(newick_tree: Union[str, Tree], file_path: Union[str, Path], create_new_file: bool = False,
                        form_data: Optional[Dict[str, Union[str, int, float, ndarray]]] = None,
                        log_file: Optional[str] = None, with_internal_nodes: bool = True,
                        actions: Optional[Dict[str, bool]] = None, selected_files: Optional[Dict[str, bool]] = None,
                        use_copap: Optional[bool] = None
                        ) -> Union[Dict[str, str], Path]:
    result_data = {}
    if actions is None or actions.get('draw_tree', False):
        result_data.update({'draw_tree': draw_tree(newick_tree)})
    if actions is None or actions.get('compute_likelihood_of_tree', False):
        result_data.update({'compute_likelihood_of_tree': compute_likelihood_of_tree(newick_tree)})
    if actions is None or actions.get('create_all_file_types', False):
        result_data.update({'create_all_file_types': create_all_file_types(newick_tree, file_path, log_file,
                                                                           with_internal_nodes, selected_files,
                                                                           use_copap)})
    if create_new_file:
        file_path = file_path.joinpath('result.json') if isinstance(file_path, Path) else f'{file_path}/result.json'
        return create_file(file_path, get_result_data(result_data, 'execute_all_actions', form_data), 'result.json')

    return result_data


def compute_likelihood_of_tree(newick_tree: Union[str, Tree]) -> Union[List[Union[float, ndarray]], str]:
    newick_tree.calculate_likelihood()
    result = [newick_tree.log_likelihood]

    return result


def create_all_file_types(newick_tree: Union[str, Tree], file_path: Union[str, Path],
                          log_file: Optional[Union[str, Path]] = None,
                          with_internal_nodes: Optional[bool] = True,
                          selected_files: Optional[Dict[str, bool]] = None,
                          use_copap: Optional[bool] = None
                          ) -> Union[Dict[str, str], str]:
    selected_files = (SELECTED_FILES if selected_files is None else selected_files)
    result = {}
    newick_tree = Tree.check_tree(newick_tree)
    taking_into_coefficient = newick_tree.coefficient_bl != 1
    # result.update(newick_tree.tree_to_graph(f'{file_path}/graph.txt', ('dot', 'png', 'svg')))
    # result.update(newick_tree.tree_to_visual_format(f'{file_path}/visual_tree.svg', True, ('txt', 'png', 'svg')))
    # result.update({'Newick text (tree)': newick_tree.tree_to_newick_file(f'{file_path}/newick_tree.tree', True)})
    # table = newick_tree.tree_to_table(columns=columns, list_type=list, lists=lists, distance_type=float)
    # result.update({'Fasta (fasta)': newick_tree.tree_to_fasta_file(f'{file_path}/fasta_file.fasta')})
    if selected_files.get('file_interactive_tree_html', False):
        result.update({'Interactive tree (html)':
                       newick_tree.tree_to_interactive_html(file_name=f'{file_path}/InteractiveTree.html',
                                                            taking_into_coefficient=taking_into_coefficient)})
    if selected_files.get('file_newick_tree_png', False):
        result.update(newick_tree.tree_to_visual_format(file_name=f'{file_path}/VisualTree.svg',
                                                        with_internal_nodes=with_internal_nodes,
                                                        taking_into_coefficient=taking_into_coefficient,
                                                        file_extensions=('png', )))
    if selected_files.get('file_table_of_posterior_rates_tsv', False) and use_copap:
        result.update({'Table of posterior rates (tsv)':
                       newick_tree.posterior_rates_to_tsv(file_name=f'{file_path}/PosteriorRates.tsv')})
    if selected_files.get('file_table_of_pearson_correlation_tsv', False) and use_copap:
        result.update({'Table of pearson correlation (tsv)':
                       newick_tree.pearson_correlation_to_tsv(file_name=f'{file_path}/PearsonCorrelation.tsv')})
    if selected_files.get('file_table_of_nodes_tsv', False):
        result.update({'Table of nodes (tsv)':
                       newick_tree.tree_to_tsv(file_name=f'{file_path}/Nodes.tsv',
                                               taking_into_coefficient=taking_into_coefficient,
                                               mode='node_tsv')})
    if selected_files.get('file_probability_per_pos_per_branches_tsv', False):
        result.update({'Probability per positions per branches (tsv)':
                       newick_tree.probability_to_tsv(file_name=f'{file_path}/ProbabilityPerPositionsPerBranches.tsv',
                                                      taking_into_coefficient=taking_into_coefficient)})
    if selected_files.get('file_table_of_branches_tsv', False):
        result.update({'Table of branches (tsv)':
                       newick_tree.tree_to_tsv(file_name=f'{file_path}/Branches.tsv',
                                               taking_into_coefficient=taking_into_coefficient,
                                               mode='branch_tsv')})
    if selected_files.get('file_log_likelihood_tsv', False):
        result.update({'Log-likelihood (tsv)':
                       newick_tree.likelihood_to_tsv(file_name=f'{file_path}/LogLikelihood.tsv')})
    if selected_files.get('file_table_of_attributes_tsv', False):
        result.update({'Tree attributes (tsv)':
                       newick_tree.attributes_to_tsv(file_name=f'{file_path}/TreeAttributes.tsv')})
    if selected_files.get('file_phylogenetic_tree_nwk', False):
        result.update({'Phylogenetic tree (nwk)':
                       newick_tree.tree_to_newick_file(file_name=f'{file_path}/PhylogeneticTree.nwk',
                                                       taking_into_coefficient=taking_into_coefficient,
                                                       with_internal_nodes=True,
                                                       decimal_length=0)})

    if result:
        file_path = get_path(file_path)
        archive_name = Path(make_archive(f'{file_path}', 'zip', f'{file_path}', '.'))
        new_archive_name = file_path.joinpath(archive_name.name)
        move(archive_name, new_archive_name)
        result.update({'Archive (zip)': f'{new_archive_name}'})

    if log_file is not None:
        result.update({'Log-File (log)': f'{log_file}'})

    return result


def draw_tree(newick_tree: Tree) -> Union[List[Any], str]:
    result = [newick_tree.get_json_structure(),
              newick_tree.get_json_structure(return_table=True),
              newick_tree.get_columns_list_for_sorting(),
              {'Size factor': min(1 + newick_tree.get_leaves_count() // 9, 6)},
              newick_tree.get_json_structure(return_table=True, mode='branch'),
              newick_tree.get_columns_list_for_sorting(mode='branch'),
              {'Sequence length': len(tuple(newick_tree.msa.values())[0])}]

    return result


def convert_seconds(seconds: float) -> str:

    return str(timedelta(seconds=seconds))


def del_bootstrap_values(newick_text: str) -> str:

    return Tree.del_bootstrap_values(newick_text)


def get_leaves(data) -> List[str]:

    return Tree(data).get_leaves(only_node_list=False)


def check_data(*args) -> List[Tuple[str, str]]:
    err_list = []
    newick_text = args[0].strip()
    msa = args[1].strip()
    categories_quantity = int(args[2])
    alpha = float(args[3])
    pi_1 = float(args[4])
    coefficient_bl = float(args[5])
    probability_lg = float(args[6])
    number_lg = int(args[7])
    e_mail = args[8]
    is_optimize_pi = bool(args[9])
    is_optimize_pi_average = bool(args[10])
    is_optimize_alpha = bool(args[11])
    is_optimize_bl = bool(args[12])
    is_do_not_use_copap = bool(args[13])
    is_do_not_use_e_mail = bool(args[14])
    file_interactive_tree_html = bool(args[15])
    file_newick_tree_png = bool(args[16])
    file_table_of_posterior_rates_tsv = bool(args[17])
    file_table_of_pearson_correlation_tsv = bool(args[18])
    file_table_of_nodes_tsv = bool(args[19])
    file_probability_per_pos_per_branches_tsv = bool(args[20])
    file_table_of_branches_tsv = bool(args[21])
    file_log_likelihood_tsv = bool(args[22])
    file_table_of_attributes_tsv = bool(args[23])
    file_phylogenetic_tree_nwk = bool(args[24])
    rooting_method = args[25].strip()
    leaf = args[26].strip()

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

    if not isinstance(probability_lg, float) or not 0.01 <= probability_lg <= 0.99:
        err_list.append((f'Probability of loss/gain event value error [ {probability_lg} ]',
                         f'The value must be between 0.01 and 0.99.'))

    if not isinstance(number_lg, int) or not 1 <= number_lg <= 20:
        err_list.append((f'Number of loss/gain events value error [ {number_lg} ]',
                         f'The value must be between 1 and 20.'))

    if ((not isinstance(e_mail, str) or not e_mail) or not validate_email(e_mail)) and not is_do_not_use_e_mail:
        err_list.append((f'Invalid email address [ {e_mail} ]', f'Must be valid email address.'))

    if not isinstance(is_optimize_pi, bool):
        err_list.append((f'Optimize π1 value (algorithmic) error [ {is_optimize_pi} ]',
                         f'The value must be boolean type.'))

    if not isinstance(is_optimize_pi_average, bool):
        err_list.append((f'Optimize π1 value (empirical) error [ {is_optimize_pi_average} ]',
                         f'The value must be boolean type.'))

    if not isinstance(is_optimize_alpha, bool):
        err_list.append((f'Optimize α value error [ {is_optimize_alpha} ]', f'The value must be boolean type.'))

    if not isinstance(is_optimize_bl, bool):
        err_list.append((f'Optimize branch lengths coefficient value error [ {is_optimize_bl} ]',
                         f'The value must be boolean type.'))

    if not isinstance(is_do_not_use_copap, bool):
        err_list.append((f'Do not use CoPAP value error [ {is_do_not_use_copap} ]',
                         f'The value must be boolean type.'))

    if not isinstance(is_do_not_use_e_mail, bool):
        err_list.append((f'Do not use e-mail value error [ {is_do_not_use_e_mail} ]',
                         f'The value must be boolean type.'))

    if not isinstance(file_interactive_tree_html, bool):
        err_list.append((f'Interactive tree (html) value error [ {file_interactive_tree_html} ]',
                         f'The value must be boolean type.'))

    if not isinstance(file_newick_tree_png, bool):
        err_list.append((f'Newick tree (png) value error [ {file_newick_tree_png} ]',
                         f'The value must be boolean type.'))

    if not isinstance(file_table_of_posterior_rates_tsv, bool):
        err_list.append((f'Table of posterior rates (tsv) value error [ {file_table_of_posterior_rates_tsv} ]',
                         f'The value must be boolean type.'))

    if not isinstance(file_table_of_pearson_correlation_tsv, bool):
        err_list.append((f'Table of pearson correlation (tsv) value error [ {file_table_of_pearson_correlation_tsv} ]',
                         f'The value must be boolean type.'))

    if not isinstance(file_table_of_nodes_tsv, bool):
        err_list.append((f'Table of nodes (tsv) value error [ {file_table_of_nodes_tsv} ]',
                         f'The value must be boolean type.'))

    if not isinstance(file_probability_per_pos_per_branches_tsv, bool):
        err_list.append((f'Probability per positions per branches (tsv) value error [ '
                         f'{file_probability_per_pos_per_branches_tsv} ]', f'The value must be boolean type.'))

    if not isinstance(file_table_of_branches_tsv, bool):
        err_list.append((f'Table of branches (tsv) value error [ {file_table_of_branches_tsv} ]',
                         f'The value must be boolean type.'))

    if not isinstance(file_log_likelihood_tsv, bool):
        err_list.append((f'Log-likelihood (tsv) value error [ {file_log_likelihood_tsv} ]',
                         f'The value must be boolean type.'))

    if not isinstance(file_table_of_attributes_tsv, bool):
        err_list.append((f'Table of attributes (tsv) value error [ {file_table_of_attributes_tsv} ]',
                         f'The value must be boolean type.'))

    if not isinstance(file_phylogenetic_tree_nwk, bool):
        err_list.append((f'Phylogenetic tree (nwk) value error [ {file_phylogenetic_tree_nwk} ]',
                         f'The value must be boolean type.'))

    if not isinstance(rooting_method, str):
        err_list.append((f'Rooting method value error [ {rooting_method} ]', f'The value must be string type.'))

    if (not isinstance(leaf, str) or not leaf) and rooting_method == 'outgroup':
        err_list.append((f'Leaf value error [ {leaf} ]', f'The value must be a non-empty string.'))

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
        elif (not (newick_text.startswith('(') and newick_text.endswith(';')) or
              (newick_text.count('(') != newick_text.count(')'))):
            err_list.append((f'TREE error', f'Wrong Phylogenetic tree format. Please provide a tree in Newick format.'))
        else:
            try:
                current_tree = Tree(newick_text)
                Tree.rename_nodes(current_tree)
            except ValueError:
                current_tree = None

            if current_tree:
                for current_node in current_tree.get_list_nodes_info(with_additional_details=True, filters={'distance':
                                                                     [0.0, ]}, only_node_list=True):
                    current_node.distance_to_father = float(f'{current_node.distance_to_father:.4f}1')
                edges_distances_list = current_tree.tree_to_table(filters={'node_type': ['leaf', 'node']},
                                                                  columns={'distance': 'distance'},
                                                                  distance_type=float,
                                                                  taking_into_coefficient=False).T.values[0].tolist()
                if not all(edges_distances_list):
                    err_list.append((f'TREE error',
                                     f'One or more branches in the tree have zero length.\n'
                                     f'{edges_distances_list}'))
                if not (current_tree.get_leaves_count() == len(msa.split('\n')) / 2 == msa.count('>')):
                    err_list.append((f'MSA error',
                                     f'A discrepancy exists between the number of leaves in the phylogenetic tree and '
                                     f'the number of sequences present in the MSA data.'))

                tree_taxa_info = current_tree.tree_to_table(filters={'node_type': ['leaf']}, columns={'node': 'node'},
                                                            taking_into_coefficient=False).T.values[0].tolist()

                if len(tree_taxa_info) != len(set(tree_taxa_info)):
                    err_list.append((f'TREE error', f'Duplicate taxa names found.'))

                if set(tree_taxa_info).difference(set(msa_taxa_info)):
                    err_list.append((f'DATA MISMATCH error',
                                     f'Taxa names in the MSA and phylogenetic tree do not match.'))
                if not current_tree.all_nodes.get(leaf) and rooting_method == 'outgroup':
                    err_list.append((f'TREE error', f'Leaf {leaf} not found.'))
            else:
                err_list.append((f'TREE error',
                                 f'Wrong Phylogenetic tree format. Please provide a tree in Newick format.'))

    return err_list


def validate_email(e_mail: str) -> bool:
    regex = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}'

    return bool(re.fullmatch(regex, e_mail))


def get_function_parameters(func: Callable) -> Tuple[str, ...]:

    return tuple(inspect.signature(func).parameters.keys())


def recompile_json(output_file: Union[str, Path], process_id: int, create_link: bool) -> str:
    file_contents = read_file(file_path=output_file)
    json_object = loads_json(file_contents)
    action_name = json_object.pop('action_name')
    data = json_object.pop('data') if 'data' in json_object.keys() else json_object.copy()

    if 'execute_all_actions' in action_name:
        for key, value in data.items():
            data.update({key: get_response_design(value, key, create_link, output_file)})
    else:
        data = get_response_design(data, action_name, create_link, output_file)

    data.update({'title': process_id})
    data.update({'form_data': json_object.pop('form_data')})
    data.update({'action_name': action_name})
    create_file(file_path=output_file, data=data)

    return '; '.join(data.keys())


def get_response_design(json_object: Optional[Any], action_name: str, create_link: bool,
                        output_file:  Union[str, Path] = '') -> Optional[Any]:
    if 'create_all_file_types' in action_name and create_link:
        if output_file:
            json_object.update({'json response file (json)': output_file})

        json_object = result_design(link_design(json_object), change_value='compute_likelihood_of_tree' in action_name,
                                    change_value_style=False, change_key=True, change_key_style=False)

    return json_object


def create_url(file_path: Path, mode: str = 'view'):

    return f'{WEBSERVER_URL}/get_file?file_path={str(file_path).replace("/", "%2F")}&mode={mode}'


def link_design(json_object: Any) -> Any:
    for key, value in json_object.items():
        if key == 'execution_time':
            continue
        json_object.update(
            {f'{key}': [f'<a class="w-auto mw-auto form-control btn btn-outline-link rounded-pill" href="'
                        f'{create_url(file_path=value, mode="download")}" target="_blank">'
                        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" height="21" width="21" version="1.1" id="Layer_1" viewBox="0 0 512 512" xml:space="preserve"><path style="fill:#A5A5A5;" d="M503.916,433.853L503.916,433.853c0,23.812-19.304,43.116-43.116,43.116H51.2  c-23.812,0-43.116-19.304-43.116-43.116l0,0c0-23.812,19.304-43.116,43.116-43.116h409.6  C484.612,390.737,503.916,410.041,503.916,433.853z"/><path style="fill:#CCCAC4;" d="M471.579,132.042v237.137c0,23.812-19.304,43.116-43.116,43.116H83.537  c-23.812,0-43.116-19.304-43.116-43.116V132.042c0-23.812,19.304-43.116,43.116-43.116h344.926  C452.275,88.926,471.579,108.23,471.579,132.042z"/><path style="fill:#F2EFE2;" d="M428.463,390.737H83.537c-11.906,0-21.558-9.651-21.558-21.558V132.042  c0-11.906,9.651-21.558,21.558-21.558h344.926c11.906,0,21.558,9.651,21.558,21.558v237.137  C450.021,381.085,440.37,390.737,428.463,390.737z"/><path style="fill:#CFDFE2;" d="M374.568,315.284H137.432c-35.718,0-64.674-28.956-64.674-64.674l0,0  c0-35.718,28.955-64.674,64.674-64.674h237.137c35.718,0,64.674,28.955,64.674,64.674l0,0  C439.242,286.329,410.287,315.284,374.568,315.284z"/><path style="fill:#FC8059;" d="M427.217,313.706l-33.082,41.92c-3.322,4.209-8.707,4.209-12.029,0l-33.082-41.92  c-1.661-2.105-1.661-5.518,0-7.622c0.798-1.011,1.88-1.578,3.007-1.578h22.537V91.621c0-22.289-18.132-40.421-40.421-40.421  c-21.382,0-38.928,16.69-40.321,37.726h-16.2c1.412-29.957,26.221-53.895,56.522-53.895c31.204,0,56.589,25.385,56.589,56.589  v212.884h33.473c1.127,0,2.21,0.568,3.007,1.578C428.878,308.188,428.878,311.601,427.217,313.706z"/><path style="fill:#4C4C4C;" d="M477.048,385.298c1.687-5.073,2.615-10.488,2.615-16.119V132.042c0-28.231-22.969-51.2-51.2-51.2  h-32.326c-1.412-29.957-26.222-53.895-56.522-53.895c-30.3,0-55.11,23.938-56.522,53.895H83.537c-28.231,0-51.2,22.969-51.2,51.2  v237.137c0,5.631,0.927,11.047,2.614,16.119C14.441,392.122,0,411.417,0,433.853c0,28.231,22.969,51.2,51.2,51.2h409.6  c28.231,0,51.2-22.969,51.2-51.2C512,411.417,497.558,392.122,477.048,385.298z M417.798,312.589l-29.678,37.609l-29.678-37.609  H417.798z M48.505,132.042c0-19.317,15.716-35.032,35.032-35.032H353.01c4.466,0,8.084-3.618,8.084-8.084  c0-4.466-3.618-8.084-8.084-8.084h-53.716c1.393-21.036,18.94-37.726,40.321-37.726c22.289,0,40.421,18.132,40.421,40.421v212.884  h-28.004c-3.611,0-7.02,1.697-9.353,4.653c-3.97,5.028-3.97,12.611-0.001,17.639l33.081,41.921  c3.126,3.961,7.631,6.232,12.361,6.232c4.73,0,9.234-2.271,12.361-6.232l33.079-41.92c3.97-5.028,3.97-12.611,0.005-17.632  c-2.333-2.962-5.744-4.661-9.358-4.661h-28.004V97.011h32.258c19.317,0,35.032,15.715,35.032,35.032v237.137  c0,19.317-15.715,35.032-35.032,35.032H83.537c-19.316,0-35.032-15.715-35.032-35.032V132.042z M460.8,468.884H51.2  c-19.316,0-35.032-15.715-35.032-35.032c0-16.258,11.075-30.111,26.431-33.961c9.35,12.431,24.219,20.488,40.937,20.488h344.926  c16.718,0,31.588-8.056,40.937-20.488c15.356,3.85,26.431,17.703,26.431,33.961C495.832,453.17,480.117,468.884,460.8,468.884z   M172.463,444.632c0,4.466-3.62,8.084-8.084,8.084H78.147c-4.465,0-8.084-3.618-8.084-8.084s3.62-8.084,8.084-8.084h86.232  C168.844,436.547,172.463,440.166,172.463,444.632z M441.937,444.632c0,4.466-3.618,8.084-8.084,8.084H272.168  c-4.466,0-8.084-3.618-8.084-8.084s3.618-8.084,8.084-8.084h161.684C438.318,436.547,441.937,440.166,441.937,444.632z   M243.604,444.632c0,4.466-3.62,8.084-8.084,8.084h-1.078c-4.465,0-8.084-3.618-8.084-8.084s3.62-8.084,8.084-8.084h1.078  C239.985,436.547,243.604,440.166,243.604,444.632z M210.189,444.632c0,4.466-3.62,8.084-8.084,8.084h-1.078  c-4.465,0-8.084-3.618-8.084-8.084s3.62-8.084,8.084-8.084h1.078C206.57,436.547,210.189,440.166,210.189,444.632z M127.194,241.987  c4.465,0,8.084,3.618,8.084,8.084v1.078c0,4.466-3.62,8.084-8.084,8.084c-4.465,0-8.084-3.618-8.084-8.084v-1.078  C119.11,245.606,122.729,241.987,127.194,241.987z M151.446,251.149v-1.078c0-4.466,3.62-8.084,8.084-8.084  c4.465,0,8.084,3.618,8.084,8.084v1.078c0,4.466-3.62,8.084-8.084,8.084C155.066,259.234,151.446,255.615,151.446,251.149z   M236.596,251.149v-1.078c0-4.466,3.62-8.084,8.084-8.084c4.465,0,8.084,3.618,8.084,8.084v1.078c0,4.466-3.62,8.084-8.084,8.084  C240.215,259.234,236.596,255.615,236.596,251.149z M277.016,259.234c-4.466,0-8.084-3.618-8.084-8.084v-1.078  c0-4.466,3.618-8.084,8.084-8.084s8.084,3.618,8.084,8.084v1.078C285.1,255.615,281.481,259.234,277.016,259.234z M84.135,271.571  c-11.558-11.558-11.558-30.364,0-41.923l51.887-51.887c3.157-3.156,8.276-3.156,11.432,0c3.157,3.158,3.157,8.276,0,11.433  l-51.887,51.887c-5.254,5.254-5.254,13.801,0,19.055l51.887,51.887c3.157,3.158,3.157,8.276,0,11.433  c-1.578,1.578-3.648,2.367-5.716,2.367c-2.068,0-4.138-0.789-5.716-2.367L84.135,271.571z M256.757,312.025l51.886-51.887  c5.254-5.254,5.254-13.801,0-19.055l-51.886-51.887c-3.157-3.158-3.157-8.276,0-11.433c3.157-3.156,8.275-3.156,11.433,0  l51.887,51.887c11.557,11.558,11.557,30.364,0,41.923l-51.887,51.887c-1.579,1.578-3.649,2.367-5.717,2.367  c-2.069,0-4.138-0.789-5.716-2.367C253.598,320.3,253.598,315.182,256.757,312.025z M172.705,334.881l43.116-172.463  c1.082-4.332,5.477-6.959,9.803-5.882c4.332,1.083,6.965,5.472,5.882,9.805L188.39,338.804c-0.918,3.672-4.215,6.126-7.836,6.126  c-0.65,0-1.309-0.079-1.967-0.244C174.256,343.602,171.621,339.212,172.705,334.881z"/></svg>'
                        f'</a>',
                        f'<a class="w-auto mw-auto form-control btn btn-outline-link rounded-pill" href="'
                        f'{create_url(file_path=value, mode="view")}" target="_blank">'
                        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" height="21" width="21" version="1.1" id="Layer_1" viewBox="0 0 512 512" xml:space="preserve"><path style="fill:#FED766;" d="M503.916,256L503.916,256c0,23.812-19.304,43.116-43.116,43.116h-15.595  C425.598,385.518,348.335,450.021,256,450.021S86.402,385.518,66.795,299.116H51.2c-23.812,0-43.116-19.304-43.116-43.116l0,0  c0-23.812,19.304-43.116,43.116-43.116h15.595C86.402,126.482,163.665,61.979,256,61.979s169.598,64.503,189.205,150.905H460.8  C484.612,212.884,503.916,232.188,503.916,256z"/><path style="fill:#E8BA52;" d="M8.084,256h495.832c0,23.812-19.304,43.116-43.116,43.116h-15.595  C425.598,385.518,348.335,450.021,256,450.021S86.402,385.518,66.795,299.116H51.2C27.388,299.116,8.084,279.812,8.084,256z"/><path style="fill:#DCF3F9;" d="M364.529,208.198c6.451,14.624,10.04,30.793,10.04,47.802c0,65.483-53.085,118.568-118.568,118.568  S137.432,321.483,137.432,256S190.517,137.432,256,137.432c17.01,0,33.179,3.589,47.802,10.04c7.486-6.265,17.126-10.04,27.65-10.04  c23.812,0,43.116,19.304,43.116,43.116C374.568,191.072,370.793,200.712,364.529,208.198z"/><path style="fill:#84A7B7;" d="M364.529,208.198c6.45,14.624,10.04,30.793,10.04,47.802c0,65.483-53.085,118.568-118.568,118.568  S137.432,321.483,137.432,256S190.517,137.432,256,137.432c17.01,0,33.179,3.589,47.802,10.04  c-9.451,7.91-15.466,19.788-15.466,33.076c0,23.812,19.304,43.116,43.116,43.116C344.74,223.663,356.619,217.648,364.529,208.198z"/><path style="fill:#FFFFFF;" d="M328.758,256c0,40.119-32.639,72.758-72.758,72.758S183.242,296.119,183.242,256  c0-23.174,10.658-44.428,29.242-58.315c3.578-2.672,8.644-1.939,11.316,1.636c2.672,3.576,1.94,8.643-1.636,11.316  c-14.46,10.805-22.753,27.339-22.753,45.363c0,31.204,25.385,56.589,56.589,56.589s56.589-25.385,56.589-56.589l-0.005-0.142  c-0.006-0.18-0.012-0.36-0.014-0.542c-0.054-4.465,3.521-8.127,7.986-8.181c0.032,0,0.067,0,0.099,0  c4.419,0,8.028,3.555,8.082,7.987l0.005,0.158C328.751,255.519,328.758,255.759,328.758,256z M254.285,199.433  c0.071,0,0.142-0.001,0.213-0.002c0.498-0.013,0.998-0.019,1.483-0.019l0.16,0.005c0.18,0.006,0.36,0.012,0.542,0.014  c0.033,0,0.066,0,0.099,0c4.413,0,8.007-3.547,8.068-7.972c0.061-4.459-3.513-8.126-7.971-8.195l-0.161-0.005  c-0.875-0.03-1.762-0.013-2.64,0.01c-4.464,0.115-7.988,3.828-7.872,8.291C246.322,195.95,249.917,199.433,254.285,199.433z"/><path style="fill:#4C4C4C;" d="M460.8,204.8h-9.248c-10.85-41.46-35.035-78.928-68.594-106.056  C347.181,69.823,302.093,53.895,256,53.895c-46.094,0-91.181,15.928-126.959,44.849C95.482,125.872,71.298,163.34,60.448,204.8H51.2  C22.969,204.8,0,227.769,0,256s22.969,51.2,51.2,51.2h9.248c10.849,41.46,35.034,78.928,68.593,106.056  c35.777,28.921,80.865,44.849,126.959,44.849c46.093,0,91.181-15.928,126.958-44.849c33.559-27.128,57.743-64.596,68.594-106.056  h9.248c28.231,0,51.2-22.969,51.2-51.2S489.031,204.8,460.8,204.8z M460.8,291.032h-15.595c-3.776,0-7.048,2.613-7.884,6.295  C418,382.472,343.438,441.937,256,441.937c-87.439,0-162.001-59.465-181.321-144.61c-0.835-3.682-4.109-6.295-7.884-6.295H51.2  c-19.317,0-35.032-15.716-35.032-35.032s15.715-35.032,35.032-35.032h15.595c3.776,0,7.048-2.613,7.884-6.295  C93.999,129.528,168.561,70.063,256,70.063c87.438,0,162,59.465,181.321,144.61c0.835,3.682,4.109,6.295,7.884,6.295H460.8  c19.317,0,35.032,15.716,35.032,35.032S480.117,291.032,460.8,291.032z M331.453,129.347c-10.67,0-20.586,3.285-28.797,8.892  c-14.845-5.896-30.514-8.892-46.656-8.892c-69.837,0-126.653,56.816-126.653,126.653S186.163,382.653,256,382.653  S382.653,325.837,382.653,256c0-16.14-2.995-31.811-8.892-46.656c5.606-8.21,8.892-18.126,8.892-28.797  C382.653,152.316,359.684,129.347,331.453,129.347z M366.484,180.547c0,19.316-15.715,35.032-35.032,35.032  c-19.317,0-35.032-15.716-35.032-35.032s15.715-35.032,35.032-35.032C350.77,145.516,366.484,161.231,366.484,180.547z M256,366.484  c-60.922,0-110.484-49.563-110.484-110.484S195.078,145.516,256,145.516c11.616,0,22.951,1.77,33.828,5.274  c-6.018,8.394-9.575,18.665-9.575,29.757c0,28.231,22.969,51.2,51.2,51.2c11.093,0,21.364-3.557,29.757-9.575  c3.504,10.877,5.274,22.211,5.274,33.828C366.484,316.922,316.922,366.484,256,366.484z M247.916,18.863V8.084  C247.916,3.62,251.534,0,256,0c4.466,0,8.084,3.62,8.084,8.084v10.779c0,4.465-3.618,8.084-8.084,8.084  C251.534,26.947,247.916,23.328,247.916,18.863z M264.084,493.137v10.779c0,4.465-3.618,8.084-8.084,8.084  c-4.466,0-8.084-3.62-8.084-8.084v-10.779c0-4.465,3.618-8.084,8.084-8.084C260.466,485.053,264.084,488.672,264.084,493.137z   M74.981,86.413c-3.157-3.157-3.157-8.276,0-11.432c3.158-3.157,8.276-3.157,11.433,0l7.622,7.622c3.157,3.157,3.157,8.276,0,11.432  c-1.579,1.578-3.649,2.368-5.717,2.368c-2.068,0-4.138-0.789-5.717-2.368L74.981,86.413z M437.019,425.587  c3.157,3.157,3.157,8.276,0,11.432c-1.579,1.578-3.649,2.368-5.717,2.368s-4.138-0.789-5.717-2.368l-7.622-7.622  c-3.157-3.157-3.157-8.276,0-11.432c3.158-3.157,8.276-3.157,11.433,0L437.019,425.587z M417.964,94.036  c-3.157-3.157-3.157-8.276,0-11.432l7.622-7.622c3.158-3.157,8.276-3.157,11.433,0c3.157,3.157,3.157,8.276,0,11.432l-7.622,7.622  c-1.579,1.578-3.649,2.368-5.717,2.368C421.612,96.404,419.544,95.614,417.964,94.036z M94.036,417.964  c3.157,3.157,3.157,8.276,0,11.432l-7.622,7.622c-1.579,1.578-3.649,2.368-5.717,2.368c-2.068,0-4.138-0.789-5.717-2.368  c-3.157-3.157-3.157-8.276,0-11.432l7.622-7.622C85.761,414.808,90.878,414.808,94.036,417.964z"/></svg>'
                        
                        f'</a>']})

    return json_object


def get_error(err_list: List[Tuple[str, str]]) -> str:

    return ''.join([f'{key_design(error_type, True, 14)}{value_design(error, True, 14)}\n'
                    for error_type, error in err_list])
