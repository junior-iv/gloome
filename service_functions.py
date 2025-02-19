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
    result.update({'log_likelihood_of_the_tree': newick_tree.log_likelihood})
    result.update({'log_likelihood_list': newick_tree.log_likelihood_vector})

    return result


def create_all_file_types(newick_text: str, pattern_msa: str, file_path: str) -> Dict[str, Union[str, float, int]]:
    start_time = time()
    path_dict = dict()
    newick_tree = Tree.rename_nodes(newick_text)
    pattern_dict = newick_tree.get_pattern_dict(pattern_msa)
    alphabet = Tree.get_alphabet_from_dict(pattern_dict)
    path_dict.update({'Interactive tree (html)': Tree.tree_to_interactive_html(newick_text, pattern_msa, alphabet,
                     file_name=f'{file_path}/interactive_tree.html', node_name='N')})
    # path_dict.update({'Interactive tree (svg)': Tree.tree_to_interactive_svg(newick_text, pattern_msa, alphabet,
    #                  file_name=f'{file_path}/interactive_tree.svg', node_name='N')})
    path_dict.update(Tree.tree_to_graph(newick_text, file_name=f'{file_path}/graph.txt',
                     file_extensions=('dot', 'png', 'svg'), node_name='N'))
    path_dict.update(Tree.tree_to_visual_format(newick_text, file_name=f'{file_path}/tree.svg',
                     file_extensions=('txt', 'png', 'svg'), with_internal_nodes=True, node_name='N'))
    path_dict.update({'Newick text (tree)': Tree.tree_to_newick_file(newick_text,
                     file_name=f'{file_path}/newick_tree.tree', with_internal_nodes=True, node_name='N')})
    path_dict.update({'Table of nodes (csv)': Tree.tree_to_csv(newick_text, file_name=f'{file_path}/tree.csv',
                     sep='\t', sort_values_by=('child', 'Name'), decimal_length=8, node_name='N')})
    path_dict.update({'Fasta (fasta)': Tree.tree_to_fasta(newick_text, pattern_msa, alphabet,
                     f'{file_path}/fasta_file.fasta')})

    result = {'execution_time': convert_seconds(time() - start_time)}
    for key, value in zip(path_dict.keys(), path_dict.values()):
        # # 'text/plain'
        # content_type = 'type="text/csv"' if sum([i in key for i in ('(dot)', '(csv)', '(fasta)')]) > 0 else ''
        result.update({f'{key}': f'<a href="{url_for("file", file_path=value)}" target="_blank">{value}</a>'})

    return result


def convert_seconds(seconds: float) -> str:
    return str(timedelta(seconds=seconds))
