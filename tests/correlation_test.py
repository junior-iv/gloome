from gloome.tree.tree import Tree
from typing import Union, Any
from pathlib import Path
from json import dumps

BIN_DIR = Path.cwd().parent


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
    dirname = BIN_DIR
    msa_file = dirname.joinpath('gloome/data/initial_data/msa/patternMSA0.msa')
    tree_file = dirname.joinpath('gloome/data/initial_data/tree/newickTree0.tree')
    # msa_file = dirname.joinpath('gloome/data/initial_data/msa/patternMSA11.fasta')
    # tree_file = dirname.joinpath('gloome/data/initial_data/tree/newickTree11.nwk')
    fasta_text = read_file(msa_file)
    newick_text = read_file(tree_file)
    file_path = dirname.joinpath('results/correlation_test')
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

    print(f'\trate_vector (4 Gamma categories): {[round(float(r), 4) for r in gloome_tree.rate_vector]}')
    number_datasets = 100
    use_simulated_datasets_file = True
    use_coevolution_file = True
    use_barplot_of_correlation_file = True
    use_plot_distribution_of_correlation_file = True
    use_plot_correlation_by_rate_bin_file = True

    gloome_tree.calculate_tree()
    gloome_tree.calculate_ancestral_sequence()
    gloome_tree.calculate_correlation(probability_lg=probability_lg, number_lg=number_lg)
    gloome_tree.posterior_rates_to_tsv(f'{file_path}/PosteriorRates.tsv')
    # gloome_tree.tree_to_tsv(f'{file_path}/Branches.tsv', mode='branch_tsv', taking_into_coefficient=True)
    gloome_tree.pearson_correlation_to_tsv(f'{file_path}/PearsonCorrelation.tsv')
    # gloome_tree.parsimony_score_to_tsv(file_name=f'{file_path}/ParsimonyAndHomoplasyScores.tsv')
    gloome_tree.simulate_datasets(file_path=f'{file_path}',
                                  number_datasets=number_datasets,
                                  use_simulated_datasets_file=use_simulated_datasets_file,
                                  use_coevolution_file=use_coevolution_file,
                                  use_barplot_of_correlation_file=use_barplot_of_correlation_file,
                                  use_plot_distribution_of_correlation_file=use_plot_distribution_of_correlation_file,
                                  use_plot_correlation_by_rate_bin_file=use_plot_correlation_by_rate_bin_file)


main()
