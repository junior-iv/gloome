import argparse
import traceback
from zipfile import ZipFile, ZIP_DEFLATED
from shutil import copy
from json import dumps
from SharedConsts import *
from utils import *


class Config:
    def __init__(self, **attributes):
        # self.DEFAULT_ARGUMENTS = DEFAULT_ARGUMENTS
        self.DEFAULT_FORM_ARGUMENTS = DEFAULT_FORM_ARGUMENTS
        # self.PREFIX = PREFIX
        # self.APPLICATION_ROOT = APPLICATION_ROOT
        self.COMMAND_LINE = COMMAND_LINE
        self.BIN_DIR = BIN_DIR
        self.SCRIPT_DIR = SCRIPT_DIR
        self.INITIAL_DATA_DIR = INITIAL_DATA_DIR
        self.SRC_DIR = SRC_DIR
        self.APP_DIR = APP_DIR
        self.TEMPLATES_DIR = TEMPLATES_DIR
        self.ERROR_TEMPLATE = ERROR_TEMPLATE

        self.IS_PRODUCTION = False
        self.IS_LOCAL = True
        self.MSA_FILE_NAME = MSA_FILE_NAME
        self.TREE_FILE_NAME = TREE_FILE_NAME

        self.PROCESS_ID = get_new_process_id()

        self.SERVERS_RESULTS_DIR = path.join(SERVERS_RESULTS_DIR, self.PROCESS_ID)
        self.SERVERS_INPUT_DIR = path.join(str(self.SERVERS_RESULTS_DIR), INPUT_DIR_NAME)
        self.INPUT_MSA_FILE = path.join(self.SERVERS_INPUT_DIR, self.MSA_FILE_NAME)
        self.INPUT_TREE_FILE = path.join(self.SERVERS_INPUT_DIR, self.TREE_FILE_NAME)
        self.SERVERS_OUTPUT_DIR = path.join(str(self.SERVERS_RESULTS_DIR), OUTPUT_DIR_NAME)
        self.SERVERS_LOGS_DIR = path.join(SERVERS_LOGS_DIR, self.PROCESS_ID)

        self.ACTIONS = ACTIONS
        self.VALIDATION_ACTIONS = VALIDATION_ACTIONS
        self.DEFAULT_ACTIONS = DEFAULT_ACTIONS

        self.CURRENT_ARGS = DEFAULT_ARGUMENTS
        self.CURRENT_ARGS.update(DEFAULT_FORM_ARGUMENTS)

        self.MSA_FILE = None
        self.TREE_FILE = None

        self.CALCULATED_ARGS = CALCULATED_ARGS
        self.CALCULATED_ARGS.file_path = self.SERVERS_RESULTS_DIR

        self.MENU = MENU
        self.PROGRESS_BAR = PROGRESS_BAR

        self.WEBSERVER_NAME_CAPITAL = WEBSERVER_NAME_CAPITAL
        self.WEBSERVER_NAME = WEBSERVER_NAME
        self.WEBSERVER_URL = WEBSERVER_URL
        self.WEBSERVER_TITLE = WEBSERVER_TITLE
        self.WEBSERVER_RESULTS_URL = path.join(WEBSERVER_RESULTS_URL, self.PROCESS_ID)
        self.WEBSERVER_LOG_URL = path.join(WEBSERVER_LOG_URL, self.PROCESS_ID)
        self.USAGE = USAGE
        if attributes:
            for key, value in attributes.items():
                setattr(self, key, value)

    def check_and_set_input_and_output_variables(self):
        """get variables from input arguments and fill out the Variable Class properties"""
        if len(self.COMMAND_LINE) < 5:
            print(len(self.COMMAND_LINE))
            print('At least two required parameters --msa_file --tree_file.' + self.USAGE)
            sys.exit()

        if len(self.COMMAND_LINE) > 4 and self.COMMAND_LINE[1].startswith('-') and self.COMMAND_LINE[3].startswith('-'):
            self.parse_arguments()
            self.check_arguments_for_errors()
            self.execute_calculation()

    def execute_calculation(self):
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('calculate_tree_for_fasta', False):
            try:
                self.ACTIONS.calculate_tree_for_fasta(self.CALCULATED_ARGS.newick_tree,
                                                      self.CALCULATED_ARGS.pattern_dict,
                                                      self.CALCULATED_ARGS.alphabet,
                                                      self.CALCULATED_ARGS.rate_vector)
            except ValueError:
                self.CALCULATED_ARGS.err_list.append((f'Error executing command \'calculate_tree_for_fasta\'',
                                                      traceback.format_exc()))
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('calculate_ancestral_sequence', False):
            try:
                self.ACTIONS.calculate_ancestral_sequence(self.CALCULATED_ARGS.newick_tree)
            except ValueError:
                self.CALCULATED_ARGS.err_list.append((f'Error executing command \'calculate_ancestral_sequence\'',
                                                      traceback.format_exc()))
        result = [self.CALCULATED_ARGS.newick_tree.get_json_structure(),
                  self.CALCULATED_ARGS.newick_tree.get_json_structure(return_table=True),
                  Tree.get_columns_list_for_sorting()]
        size_factor = min(1 + self.CALCULATED_ARGS.newick_tree.get_node_count({'node_type': ['leaf']}) // 7, 3)
        result.append([size_factor, int(self.CURRENT_ARGS.get('is_radial_tree')),
                       int(self.CURRENT_ARGS.get('show_distance_to_parent'))])
        file_name = path.join(self.SERVERS_OUTPUT_DIR, 'tree.json')
        with open(file_name, 'w') as f:
            f.write(dumps(result))

        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('create_all_file_types', False):
            try:
                file_list = self.ACTIONS.create_all_file_types(self.CALCULATED_ARGS.newick_tree,
                                                               self.CALCULATED_ARGS.pattern_dict,
                                                               self.SERVERS_OUTPUT_DIR,
                                                               self.CALCULATED_ARGS.rate_vector,
                                                               self.CALCULATED_ARGS.alphabet,
                                                               )
                zipf = ZipFile(path.join(self.SERVERS_OUTPUT_DIR, f'{self.PROCESS_ID}.zip'), 'w', ZIP_DEFLATED, )
                for value in list(file_list.values())[1:]:
                    zipf.write(path.join(self.SERVERS_OUTPUT_DIR, value[len(value) - value[::-1].find('/'):]))
            except ValueError:
                self.CALCULATED_ARGS.err_list.append((f'Error executing command \'create_all_file_types\'',
                                                      traceback.format_exc()))

    def check_arguments_for_errors(self):
        # for i in vars(self).items():
        #     print(i)
        if not path.exists(self.SERVERS_RESULTS_DIR):
            makedirs(self.SERVERS_RESULTS_DIR)
        if not path.exists(self.SERVERS_INPUT_DIR):
            makedirs(self.SERVERS_INPUT_DIR)
        if not path.exists(self.SERVERS_OUTPUT_DIR):
            makedirs(self.SERVERS_OUTPUT_DIR)

        copy(self.MSA_FILE, self.INPUT_MSA_FILE)
        copy(self.TREE_FILE, self.INPUT_TREE_FILE)

        with open(self.TREE_FILE, 'r') as f:
            self.CALCULATED_ARGS.newick_text = f.read()
        with open(self.MSA_FILE, 'r') as f:
            self.CALCULATED_ARGS.pattern_msa = f.read()

        # for i in self.CURRENT_ARGS.items():
        #     print(i)
        if not self.CALCULATED_ARGS.err_list and self.VALIDATION_ACTIONS.get('check_data', False):
            self.CALCULATED_ARGS.err_list += self.ACTIONS.check_data(self.CALCULATED_ARGS.newick_text,
                                                                     self.CALCULATED_ARGS.pattern_msa)
        if not self.CALCULATED_ARGS.err_list and self.VALIDATION_ACTIONS.get('check_tree', False):
            try:
                self.CALCULATED_ARGS.newick_tree = self.ACTIONS.check_tree(self.CALCULATED_ARGS.newick_text)
            except ValueError:
                self.CALCULATED_ARGS.err_list.append((ERR[0], self.CALCULATED_ARGS.newick_text.split('\n')))
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('rename_nodes', False):
            try:
                self.ACTIONS.rename_nodes(self.CALCULATED_ARGS.newick_tree)
            except ValueError:
                self.CALCULATED_ARGS.err_list.append((f'Error executing command \'rename_nodes\'',
                                                      traceback.format_exc()))
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('rate_vector', False):
            try:
                self.CALCULATED_ARGS.rate_vector = self.ACTIONS.rate_vector(
                    self.CURRENT_ARGS.get('categories_quantity'), self.CURRENT_ARGS.get('alpha'))
            except ValueError:
                self.CALCULATED_ARGS.err_list.append(('Error executing command \'rate_vector\'',
                                                      traceback.format_exc()))
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('pattern_dict', False):
            try:
                self.CALCULATED_ARGS.pattern_dict = self.ACTIONS.pattern_dict(self.CALCULATED_ARGS.newick_tree,
                                                                              self.CALCULATED_ARGS.pattern_msa)
            except ValueError:
                self.CALCULATED_ARGS.err_list.append(('Error executing command \'pattern_dict\'',
                                                      traceback.format_exc()))
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('alphabet', False):
            try:
                self.CALCULATED_ARGS.alphabet = self.ACTIONS.alphabet(self.CALCULATED_ARGS.pattern_dict)
            except ValueError:
                self.CALCULATED_ARGS.err_list.append(('Error executing command \'alphabet\'', traceback.format_exc()))
        # for i in vars(self.CALCULATED_ARGS).items():
        #     print(i)

    def parse_arguments(self):
        """parse arguments and fill out the relevant Variable Class properties"""
        parser = argparse.ArgumentParser(prog=self.WEBSERVER_NAME_CAPITAL, description='GLOOME',
                                         usage='%(prog)s [options]')
        parser.add_argument('--msa_file', dest='MSA_FILE', type=str, required=True, help='Specify the msa file '
                            '(required).')
        parser.add_argument('--tree_file', dest='TREE_FILE', type=str, required=True, help='Specify the newick file '
                            '(required).')
        parser.add_argument('--with_internal_nodes', dest='with_internal_nodes', type=bool, required=False,
                            default=self.CURRENT_ARGS.get('with_internal_nodes', True), help=f'Specify the Newick file '
                            f'style (optional). Default is {self.CURRENT_ARGS.get("with_internal_nodes", True)}.')
        parser.add_argument('--sort_values_by', dest='sort_values_by', type=tuple, required=False,
                            default=self.CURRENT_ARGS.get('sort_values_by', ('child', 'Name')), help=f'Specify the '
                            f'columns by which you want to sort the values in the csv file. Possible options: ("Name", '
                            f'"Parent", "Distance to father", "child"). Default is '
                            f'{self.CURRENT_ARGS.get("sort_values_by", ("child", "Name"))}.')
        parser.add_argument('--categories_quantity', dest='categories_quantity', type=int, required=False,
                            default=self.CURRENT_ARGS.get('categories_quantity', 4), help=f'Specify categories '
                            f'quantity. Default is {self.CURRENT_ARGS.get("categories_quantity", 4)}.')
        parser.add_argument('--alpha', dest='alpha', type=float, required=False, default=self.CURRENT_ARGS.get('alpha',
                            0.5), help=f'Specify alpha. Default is {self.CURRENT_ARGS.get("alpha", 0.5)}.')
        parser.add_argument('--is_radial_tree', dest='is_radial_tree', type=bool, required=False,
                            default=self.CURRENT_ARGS.get('is_radial_tree', True), help=f'Specify beta. Default is '
                            f'{self.CURRENT_ARGS.get("is_radial_tree", True)}.')
        parser.add_argument('--show_distance_to_parent', dest='show_distance_to_parent', type=float, required=False,
                            default=self.CURRENT_ARGS.get('show_distance_to_parent', True), help=f'Specify beta. '
                            f'Default is {self.CURRENT_ARGS.get("show_distance_to_parent", True)}.')

        args = parser.parse_args()
        for arg_name, arg_value in vars(args).items():
            if arg_value is not None:
                if hasattr(self, arg_name.upper()):
                    setattr(self, arg_name.upper(), arg_value)
                if hasattr(self.CURRENT_ARGS, arg_name):
                    setattr(self.CURRENT_ARGS, arg_name, arg_value)
        return args
