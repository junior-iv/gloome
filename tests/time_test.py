from typing import Union, Any
from pathlib import Path
# from importlib.resources import files
from json import dumps
from line_profiler import LineProfiler
from gloome.tree.tree import Tree
from gloome.services.service_functions import draw_tree, compute_likelihood_of_tree, create_all_file_types

BIN_DIR = Path.cwd()


def read_file(file_path: Path) -> str:
    if file_path.is_file():
        with open(file_path, 'r') as f:
            return f.read()
    return ''


def write_file(file_path: Path, data: Union[str, Any]):
    file_path = file_path.parent.joinpath(f'{file_path.stem}_new{file_path.suffix}')
    with open(file_path, 'w') as f:
        if isinstance(data, str):
            f.write(data)
        else:
            f.write(dumps(data))


def main():
    dirname = BIN_DIR
    categories_quantity = 4
    alpha = 0.5
    pi_1 = 0.5
    coefficient_bl = 1
    is_optimize_pi = True
    is_optimize_pi_average = False
    is_optimize_alpha = True
    is_optimize_bl = True
    # msa_file = f'{dirname}/gloome/data/initial_data/msa/patternMSA11.fasta'
    # tree_file = f'{dirname}/gloome/data/initial_data/tree/newickTree11.nwk'
    # file_path = f'{dirname}/results/out/test_11_op/'
    # msa_file = f'{dirname}/gloome/data/initial_data/msa/patternMSA10.fasta'
    # tree_file = f'{dirname}/gloome/data/initial_data/tree/newickTree10.nwk'
    # file_path = f'{dirname}/results/out/test_10_op/'
    # msa_file = f'{dirname}/gloome/data/initial_data/msa/patternMSA1.msa'
    # tree_file = f'{dirname}/gloome/data/initial_data/tree/newickTree1.tree'
    # file_path = f'{dirname}/results/out/test_1_op/'
    msa_file = dirname.joinpath('gloome/data/initial_data/msa/patternMSA0.msa')
    tree_file = dirname.joinpath('gloome/data/initial_data/tree/newickTree0.tree')
    file_path = dirname.joinpath('results/out/test_0_op/')
    log_file = file_path.joinpath('log.log')
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
    print(msa_file, tree_file, form_data)

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
    selected_files = {'file_log_likelihood_tsv': True,
                      'file_table_of_attributes_tsv': True}
    create_all_file_types(newick_tree, file_path=file_path, log_file=log_file, with_internal_nodes=True,
                          selected_files=selected_files)
    # newick_tree.print_args('END')


use_line_profiler = False

if use_line_profiler:
    lp = LineProfiler()
    lp.add_function(main)
    lp.run('main()')
    lp.print_stats()
else:
    main()
