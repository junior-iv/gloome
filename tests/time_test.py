import linecache
import csv

from typing import Union, Any, List
from pathlib import Path
from json import dump
from line_profiler import LineProfiler
from gloome.tree.tree import Tree
from gloome.services.service_functions import recompile_json, execute_all_actions

SELECTED_FILES = {'file_interactive_tree_html': True,
                  'file_newick_tree_png': True,
                  'file_table_of_coevolution_tsv': True,
                  'file_simulated_datasets_fastas': True,
                  'file_table_of_posterior_rates_tsv': True,
                  'file_barplot_of_correlation_svg': True,
                  'file_plot_distribution_of_correlation_svg': True,
                  'file_plot_correlation_by_rate_bin_svg': True,
                  'file_table_of_pearson_correlation_tsv': True,
                  'file_table_of_nodes_tsv': True,
                  'file_branch_position_probabilities_tsv': True,
                  'file_table_of_branches_tsv': True,
                  'file_log_likelihood_tsv': True,
                  'file_table_of_attributes_tsv': True,
                  'file_table_of_parsimony_and_homoplasy_scores_tsv': True,
                  'file_phylogenetic_tree_nwk': True}
MAIN_ACTIONS = {'compute_likelihood_of_tree': False,
                'draw_tree': True,
                'create_all_file_types': False}
MODE = ['draw_tree', 'compute_likelihood_of_tree', 'create_all_file_types', 'execute_all_actions']
ROOTING_METHODS = [('mad', 'Minimal Ancestor Deviation'), ('mvr', 'Minimum Variance Rooting'),
                   ('midpoint', 'Midpoint Rooting'), ('outgroup', 'Outgroup Rooting')]
BIN_DIR = Path.cwd()

use_line_profiler = True

check_file_creation_time = True
check_correlation_calculation_time = True
check_ancestral_sequence_calculation_time = True
check_dataset_simulation_time = True
check_tree_drawing_time = True
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


def draw_tree(newick_tree: Tree) -> Union[List[Any], str]:
    result = [newick_tree.get_json_structure(),
              newick_tree.get_json_structure(return_table=True),
              newick_tree.get_columns_list_for_sorting(),
              {'Size factor': min(1 + newick_tree.get_leaves_count() // 9, 6)},
              newick_tree.get_json_structure(return_table=True, mode='branch'),
              newick_tree.get_columns_list_for_sorting(mode='branch'),
              {'Sequence length': len(tuple(newick_tree.msa.values())[0])}]

    return result


def read_file(current_file_path: Path) -> str:
    if current_file_path.is_file():
        with open(current_file_path, 'r', encoding='utf-8') as current_file:
            return current_file.read()
    return ''


def write_file(current_file_path: Path, data: Union[str, Any]):
    current_file_path = current_file_path.parent.joinpath(f'{current_file_path.stem}_new{current_file_path.suffix}')

    with open(current_file_path, 'w', encoding='utf-8') as current_file:
        if isinstance(data, str):
            current_file.write(data)
        else:
            dump(data, current_file, indent=4, ensure_ascii=False)


msa_file = dirname.joinpath('gloome/data/initial_data/msa/patternMSA0.msa')
tree_file = dirname.joinpath('gloome/data/initial_data/tree/newickTree0.tree')
file_path = dirname.joinpath('results/correlation_test')
log_file = file_path.joinpath('log_file.log')
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

form_data = {'msaText': fasta_text,
             'newickText': newick_text,
             'isOptimizePi': is_optimize_pi,
             'isOptimizePiAverage': is_optimize_pi_average,
             'isOptimizeAlpha': is_optimize_alpha,
             'isOptimizeBL': is_optimize_bl,
             'isDoNotUseCoPAP': 1,
             'fileInteractiveTreeHtml': 0,
             'fileNewickTreePng': 0,
             'fileTableOfCoevolutionTsv': 0,
             'fileSimulatedDatasetsFastas': 0,
             'fileBarplotOfCorrelationSvg': 0,
             'filePlotDistributionOfCorrelationSvg': 0,
             'filePlotCorrelationByRateBinSvg': 0,
             'fileTableOfPosteriorRatesTsv': 0,
             'fileTableOfPearsonCorrelationTsv': 0,
             'fileTableOfNodesTsv': 0,
             'fileBranchPositionProbabilitiesTsv': 0,
             'fileTableOfBranchesTsv': 0,
             'fileLogLikelihoodTsv': 0,
             'fileTableOfAttributesTsv': 0,
             'fileTableOfParsimonyAndHomoplasyScores': 0,
             'filePhylogeneticTreeNwk': 0,
             'numberDatasets': number_datasets,
             'numberLG': number_lg,
             'probabilityLG': probability_lg,
             'coefficientBL': coefficient_bl,
             'pi1': pi_1,
             'alpha': alpha,
             'categoriesQuantity': categories_quantity,
             'eMail': '',
             'rootingMethod': ROOTING_METHODS[2][0],
             'leaf': '',
             'rootingMethods': ROOTING_METHODS}


def main():
    gloome_tree = Tree(newick_text, msa=fasta_text, **tree_data)
    Tree.rename_nodes(gloome_tree)
    form_data.update({'leaves': list(gloome_tree.msa.keys())})

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
                                        with_internal_nodes=with_internal_nodes,
                                        decimal_length=0)
    if check_dataset_simulation_time:
        gloome_tree.simulate_datasets(file_path=f'{file_path}',
                                      number_datasets=number_datasets,
                                      use_simulated_datasets_file=check_file_creation_time,
                                      use_coevolution_file=check_file_creation_time,
                                      use_barplot_of_correlation_file=check_file_creation_time,
                                      use_plot_distribution_of_correlation_file=check_file_creation_time,
                                      use_plot_correlation_by_rate_bin_file=check_file_creation_time)
    if check_tree_drawing_time:
        execute_all_actions(file_path=file_path,
                            create_new_file=True,
                            form_data=form_data,
                            newick_tree=gloome_tree,
                            with_internal_nodes=True,
                            log_file=f'{log_file}',
                            actions=MAIN_ACTIONS,
                            selected_files=SELECTED_FILES,
                            use_copap=False,
                            probability_lg=probability_lg,
                            number_lg=number_lg,
                            number_datasets=number_datasets)
        recompile_json(output_file=file_path.joinpath('result.json'),
                       process_id=1,
                       create_link=False)


if use_line_profiler:
    lp = LineProfiler()
    lp.add_function(main)
    lp.run('main()')
    lp.print_stats()
    stats = lp.get_stats()
    timer_unit = stats.unit

    flat_data = []

    for (filename, line_start, func_name), timings in stats.timings.items():
        linecache.checkcache(filename)
        total = sum([c for a, b, c in timings])

        for line_no, hits, total_time in timings:
            total_seconds = total_time * timer_unit
            per_hit_seconds = total_seconds / hits if hits > 0 else 0
            percent = round(100 * total_time / total, 1) if total_seconds > 0 else 0

            line_content = linecache.getline(filename, line_no).strip()

            flat_data.append({
                "Line #": line_no,
                "Hits": hits,
                "Time": total_seconds,
                "Per Hit": per_hit_seconds,
                '% Time': percent,
                "Line Contents": line_content
            })

    with open(file_path.joinpath('profiler_results.json'), 'w', encoding='utf-8') as f:
        dump(flat_data, f, indent=4, ensure_ascii=False)
    with open(file_path.joinpath('profiler_with_code.csv'), 'w', newline='', encoding='utf-8') as f:
        if flat_data:
            writer = csv.DictWriter(f, fieldnames=flat_data[0].keys(), delimiter='\t')
            writer.writeheader()
            writer.writerows(flat_data)
else:
    main()
