from time import time
from typing import Union, Dict
from datetime import timedelta
from tree import Tree
from flask import url_for


def compute_likelihood_of_tree(newick_text: str, pattern_msa: str) -> Dict[str, Union[str, float, int]]:
    start_time = time()
    newick_tree = Tree.rename_nodes(newick_text)
    newick_tree.calculate_likelihood(pattern_msa)

    result = {'execution_time': convert_seconds(time() - start_time)}
    result.update({'likelihood_of_the_tree': newick_tree.likelihood})
    result.update({'log-likelihood_of_the_tree': newick_tree.log_likelihood})
    result.update({'log-likelihood_list': newick_tree.log_likelihood_vector})

    return result


def create_all_file_types(newick_text: str, pattern_msa: str, file_path: str) -> Dict[str, Union[str, float, int]]:
    start_time = time()
    path_dict = dict()
    newick_tree = Tree.rename_nodes(newick_text)
    pattern_dict = newick_tree.get_pattern_dict(pattern_msa)
    alphabet = Tree.get_alphabet_from_dict(pattern_dict)
    path_dict.update({'Interactive tree (html)': Tree.tree_to_interactive_html(newick_tree, pattern_msa, alphabet,
                     file_name=f'{file_path}/interactive_tree.html')})
    # path_dict.update({'Interactive tree (svg)': Tree.tree_to_interactive_svg(newick_text, pattern_msa, alphabet,
    #                  file_name=f'{file_path}/interactive_tree.svg')})
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
                     file_name=f'{file_path}/log-likelihood.csv', sep='\t')})
    # path_dict.update({'up_vector (csv)': Tree.tree_to_csv(newick_tree, columns={'node': 'Name'},
    #                   file_name=f'{file_path}/up_vector.csv', sep='\t')})
    # path_dict.update({'down_vector (csv)': Tree.tree_to_csv(newick_tree, columns={'node': 'Name'},
    #                   file_name=f'{file_path}/down_vector.csv', sep='\t')})
    # path_dict.update({'marginal_vector (csv)': Tree.tree_to_csv(newick_tree, columns={'node': 'Name'},
    #                   file_name=f'{file_path}/marginal_vector.csv', sep='\t')})
    # path_dict.update({'probability_vector (csv)': Tree.tree_to_csv(newick_tree, columns={'node': 'Name'},
    #                   file_name=f'{file_path}/probability_vector.csv', sep='\t')})
    # path_dict.update({'probabilities_sequence_characters (csv)': Tree.tree_to_csv(newick_tree,
    #                   columns={'node': 'Name'},
    #                   file_name=f'{file_path}/probabilities_sequence_characters.csv', sep='\t')})

    result = {'execution_time': convert_seconds(time() - start_time)}
    for key, value in zip(path_dict.keys(), path_dict.values()):
        result.update({f'{key}': f'<a mx-2 class="w-auto mw-auto form-control btn btn-outline-link rounded-pill" '
                                 f'href="{url_for("download_file", file_path=value)}" target="_blank" download><h7>'
                                 f'download</h7></a>\t<a mx-2 class="w-auto mw-auto form-control btn btn-outline-link '
                                 f'rounded-pill" href="{url_for("view_file", file_path=value)}" target="_blank"><h7>'
                                 f'view</h7></a>'})

    return result


def convert_seconds(seconds: float) -> str:
    return str(timedelta(seconds=seconds))
