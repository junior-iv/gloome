from typing import Union, Any
from pathlib import Path
from json import dumps
from line_profiler import LineProfiler
from gloome.tree.tree import Tree

BIN_DIR = Path.cwd().parent

use_line_profiler = True

check_file_creation_time = True
check_correlation_calculation_time = True
check_ancestral_sequence_calculation_time = True
check_dataset_simulation_time = True
dirname = BIN_DIR

categories_quantity = 4
alpha = 0.5
pi_1 = 0.5
coefficient_bl = 1
is_optimize_pi = True
is_optimize_pi_average = False
is_optimize_alpha = True
is_optimize_bl = True

probability_lg = 0.5
number_lg = 1

number_datasets = 100


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
    msa_file = dirname.joinpath('gloome/data/initial_data/msa/patternMSA11.msa')
    tree_file = dirname.joinpath('gloome/data/initial_data/tree/newickTree11.tree')
    file_path = dirname.joinpath('results/correlation_test')
    fasta_text = read_file(msa_file)
    newick_text = read_file(tree_file)
    tree_data = {'pi_1': pi_1,
                 'alpha': alpha,
                 'categories_quantity': categories_quantity,
                 'coefficient_bl': coefficient_bl,
                 'is_optimize_pi': is_optimize_pi,
                 'is_optimize_pi_average': is_optimize_pi_average,
                 'is_optimize_alpha': is_optimize_alpha,
                 'is_optimize_bl': is_optimize_bl,
                 }

    gloome_tree = Tree(newick_text, msa=fasta_text, **tree_data)
    Tree.rename_nodes(gloome_tree)

    gloome_tree.calculate_likelihood()
    gloome_tree.calculate_down()
    gloome_tree.calculate_marginal()

    if check_ancestral_sequence_calculation_time:
        gloome_tree.calculate_ancestral_sequence()

    if check_correlation_calculation_time:
        gloome_tree.calculate_correlation(probability_lg=probability_lg, number_lg=number_lg)

    if check_file_creation_time:
        taking_into_coefficient = gloome_tree.coefficient_bl != 1
        with_internal_nodes = True

        gloome_tree.tree_to_interactive_html(file_name=f'{file_path}/InteractiveTree.html',
                                             taking_into_coefficient=taking_into_coefficient)
        gloome_tree.tree_to_visual_format(file_name=f'{file_path}/VisualTree.svg',
                                          with_internal_nodes=with_internal_nodes,
                                          taking_into_coefficient=taking_into_coefficient,
                                          file_extensions=('png', ))
        gloome_tree.posterior_rates_to_tsv(file_name=f'{file_path}/PosteriorRates.tsv')
        gloome_tree.pearson_correlation_to_tsv(file_name=f'{file_path}/PearsonCorrelation.tsv',
                                               probability_lg=probability_lg,
                                               number_lg=number_lg)
        gloome_tree.tree_to_tsv(file_name=f'{file_path}/Nodes.tsv',
                                taking_into_coefficient=taking_into_coefficient,
                                mode='node_tsv')
        gloome_tree.probability_to_tsv(file_name=f'{file_path}/BranchPositionProbabilities.tsv',
                                       taking_into_coefficient=taking_into_coefficient)
        gloome_tree.tree_to_tsv(file_name=f'{file_path}/Branches.tsv',
                                taking_into_coefficient=taking_into_coefficient,
                                mode='branch_tsv')
        gloome_tree.likelihood_to_tsv(file_name=f'{file_path}/LogLikelihood.tsv')
        gloome_tree.attributes_to_tsv(file_name=f'{file_path}/TreeAttributes.tsv')
        gloome_tree.parsimony_score_to_tsv(file_name=f'{file_path}/ParsimonyAndHomoplasyScores.tsv')
        gloome_tree.tree_to_newick_file(file_name=f'{file_path}/PhylogeneticTree.nwk',
                                        taking_into_coefficient=taking_into_coefficient,
                                        with_internal_nodes=True,
                                        decimal_length=0)

    if check_dataset_simulation_time:
        gloome_tree.simulate_datasets(file_path=f'{file_path}',
                                      number_datasets=number_datasets,
                                      use_simulated_datasets_file=check_file_creation_time,
                                      use_coevolution_file=check_file_creation_time,
                                      use_barplot_of_correlation_file=check_file_creation_time,
                                      use_plot_distribution_of_correlation_file=check_file_creation_time,
                                      use_plot_correlation_by_rate_bin_file=check_file_creation_time)


if use_line_profiler:
    lp = LineProfiler()
    lp.add_function(main)
    lp.run('main()')
    lp.print_stats()
else:
    main()
