from app.http_utils import *
from gloome.consts import *


def read_file(file_path: str) -> str:
    full_file_name = f'{INITIAL_DATA_DIR}/{file_path}'
    with open(full_file_name, 'r') as f:
        return f.read().strip()


e_mail = REPORT_RECEIVERS.split()
mode = MODE[3]
file_numbe = 1
kwargs = {'msaText': read_file(f'msa/patternMSA{file_numbe}.msa'),
          'newickText': read_file(f'tree/newickTree{file_numbe}.tree'),
          'isOptimizePi': int(DEFAULT_ARGUMENTS.is_optimize_pi),
          'isOptimizePiAverage': int(DEFAULT_ARGUMENTS.is_optimize_pi_average),
          'isOptimizeAlpha': int(DEFAULT_ARGUMENTS.is_optimize_alpha),
          'isOptimizeBL': int(DEFAULT_ARGUMENTS.is_optimize_bl),
          'isDoNotUseEMail': int(DEFAULT_ARGUMENTS.is_do_not_use_e_mail),
          'fileInteractiveTreeHtml': int(DEFAULT_ARGUMENTS.file_interactive_tree_html),
          'fileNewickTreePng': int(DEFAULT_ARGUMENTS.file_newick_tree_png),
          'fileTableOfNodesTsv': int(DEFAULT_ARGUMENTS.file_table_of_nodes_tsv),
          'fileProbabilityPerPosPerBranchesTsv':
              int(DEFAULT_ARGUMENTS.file_probability_per_pos_per_branches_tsv),
          'fileTableOfBranchesTsv': int(DEFAULT_ARGUMENTS.file_table_of_branches_tsv),
          'fileLogLikelihoodTsv': int(DEFAULT_ARGUMENTS.file_log_likelihood_tsv),
          'fileTableOfAttributesTsv': int(DEFAULT_ARGUMENTS.file_table_of_attributes_tsv),
          'filePhylogeneticTreeNwk': int(DEFAULT_ARGUMENTS.file_phylogenetic_tree_nwk),
          'coefficientBL': DEFAULT_ARGUMENTS.coefficient_bl,
          'pi1': DEFAULT_ARGUMENTS.pi_1,
          'alpha': DEFAULT_ARGUMENTS.alpha,
          'categoriesQuantity': DEFAULT_ARGUMENTS.categories_quantity,
          'eMail': e_mail[-1] if e_mail else '',
          'rootingMethod': DEFAULT_ARGUMENTS.rooting_method,
          'leaf': DEFAULT_ARGUMENTS.leaf,
          'rootingMethods': DEFAULT_ARGUMENTS.rooting_methods,
          'leaves': DEFAULT_ARGUMENTS.leaves}
start_background_job(mode=mode, **kwargs)