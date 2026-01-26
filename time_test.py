from typing import Optional, Union, Any
from os import path
from json import dumps
from line_profiler import LineProfiler

from script.tree import Tree
from script.service_functions import draw_tree, compute_likelihood_of_tree, create_all_file_types


def read_file(file_path: str) -> Optional[str]:
    if path.isfile(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    return ''


def write_file(file_path: str, data: Union[str, Any]):
    # data = read_file(file_path)
    file_name = path.splitext(path.basename(file_path))
    file_path = path.join(path.dirname(file_path), f'{file_name[0]}_new{file_name[1]}')
    with open(file_path, 'w') as f:
        if isinstance(data, str):
            f.write(data)
        else:
            f.write(dumps(data))


def main():
    dirname = path.dirname(path.abspath(__file__))
    categories_quantity = 4
    alpha = 0.5
    pi_1 = 0.5
    coefficient_bl = 1
    is_optimize_pi = True
    is_optimize_pi_average = False
    is_optimize_alpha = True
    is_optimize_bl = True
    # msa_file = f'{dirname}/src/initial_data/msa/patternMSA11.fasta'
    # tree_file = f'{dirname}/src/initial_data/tree/newickTree11.nwk'
    # file_path = f'{dirname}/results/out/test_11_op/'
    # msa_file = f'{dirname}/src/initial_data/msa/patternMSA10.fasta'
    # tree_file = f'{dirname}/src/initial_data/tree/newickTree10.nwk'
    # file_path = f'{dirname}/results/out/test_10_op/'
    # msa_file = f'{dirname}/src/initial_data/msa/patternMSA1.msa'
    # tree_file = f'{dirname}/src/initial_data/tree/newickTree1.tree'
    # file_path = f'{dirname}/results/out/test_1_op/'
    msa_file = f'{dirname}/src/initial_data/msa/patternMSA0.msa'
    tree_file = f'{dirname}/src/initial_data/tree/newickTree0.tree'
    file_path = f'{dirname}/results/out/test_0_op/'
    log_file = path.join(file_path, 'log.log')
    form_data = {'msaText': read_file(msa_file),
                 'newickText': read_file(tree_file),
                 'isOptimizePi': is_optimize_pi,
                 'isOptimizePiAverage': is_optimize_pi_average,
                 'isOptimizeAlpha': is_optimize_alpha,
                 'isOptimizeBL': is_optimize_bl,
                 'isDoNotUseEMail': True,
                 'coefficientBL': coefficient_bl,
                 'pi1': pi_1,
                 'alpha': alpha,
                 'categoriesQuantity': categories_quantity,
                 'eMail': ''}

    newick_tree = Tree(form_data.get('newickText'))
    newick_tree.set_tree_data(msa=form_data.get('msaText'),
                              categories_quantity=categories_quantity,
                              alpha=alpha, pi_1=pi_1,
                              coefficient_bl=coefficient_bl,
                              is_optimize_pi=is_optimize_pi,
                              is_optimize_pi_average=is_optimize_pi_average,
                              is_optimize_alpha=is_optimize_alpha,
                              is_optimize_bl=is_optimize_bl)
    newick_tree.calculate_tree_for_fasta()
    newick_tree.calculate_ancestral_sequence()
    draw_tree(newick_tree)
    compute_likelihood_of_tree(newick_tree)
    create_all_file_types(newick_tree, file_path=file_path, log_file=log_file, with_internal_nodes=True)
    newick_tree.print_args('END')


use_line_profiler = True

if use_line_profiler:
    lp = LineProfiler()
    lp.add_function(main)
    lp.run('main()')
    lp.print_stats()
else:
    main()
