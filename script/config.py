import argparse
import traceback
import socket
from script.service_functions import ERR
from sys import exit
from utils import *


class Config:
    def __init__(self, **attributes):
        # self.DEFAULT_ARGUMENTS = DEFAULT_ARGUMENTS
        # self.PREFIX = PREFIX
        # self.APPLICATION_ROOT = APPLICATION_ROOT
        self.MODE = MODE
        self.DEFAULT_FORM_ARGUMENTS = DEFAULT_FORM_ARGUMENTS
        self.COMMAND_LINE = COMMAND_LINE

        self.BIN_DIR = BIN_DIR
        self.SCRIPT_DIR = SCRIPT_DIR
        self.INITIAL_DATA_DIR = INITIAL_DATA_DIR
        self.SRC_DIR = SRC_DIR
        self.APP_DIR = APP_DIR
        self.TMP_DIR = TMP_DIR
        self.TEMPLATES_DIR = TEMPLATES_DIR
        self.IN_DIR = IN_DIR
        self.OUT_DIR = OUT_DIR
        self.ERROR_TEMPLATE = ERROR_TEMPLATE

        self.IS_PRODUCTION = IS_PRODUCTION
        self.IS_LOCAL = 'powerslurm' not in socket.gethostname()

        self.ACTIONS = ACTIONS
        self.VALIDATION_ACTIONS = VALIDATION_ACTIONS
        self.DEFAULT_ACTIONS = DEFAULT_ACTIONS

        self.CURRENT_ARGS = DEFAULT_ARGUMENTS
        self.CURRENT_ARGS.update(DEFAULT_FORM_ARGUMENTS)

        self.MSA_FILE_NAME = MSA_FILE_NAME
        self.TREE_FILE_NAME = TREE_FILE_NAME

        self.CALCULATED_ARGS = CALCULATED_ARGS
        self.MENU = MENU
        self.PROGRESS_BAR = PROGRESS_BAR

        self.PREFERRED_URL_SCHEME = PREFERRED_URL_SCHEME
        self.WEBSERVER_NAME_CAPITAL = WEBSERVER_NAME_CAPITAL
        self.WEBSERVER_NAME = WEBSERVER_NAME
        self.WEBSERVER_URL = WEBSERVER_URL
        self.WEBSERVER_TITLE = WEBSERVER_TITLE

        self.PROCESS_ID = None
        self.SERVERS_RESULTS_DIR = None
        self.SERVERS_LOGS_DIR = None
        self.MSA_FILE = None
        self.TREE_FILE = None
        self.JOB_LOGGER = None
        self.WEBSERVER_RESULTS_URL = None
        self.WEBSERVER_LOG_URL = None

        self.LOGGER = logger
        self.USAGE = USAGE

        if attributes:
            for key, value in attributes.items():
                if key == 'PROCESS_ID':
                    self.change_process_id(value)
                else:
                    setattr(self, key, value)
        if len(self.COMMAND_LINE) > 4 and self.COMMAND_LINE[1].startswith('-') and self.COMMAND_LINE[3].startswith(
                '-'):
            self.parse_arguments()

        if not self.PROCESS_ID:
            self.change_process_id(get_new_process_id())

    def change_process_id(self, process_id: str):
        self.PROCESS_ID = process_id

        self.SERVERS_RESULTS_DIR = SERVERS_RESULTS_DIR
        self.SERVERS_LOGS_DIR = SERVERS_LOGS_DIR
        self.check_dir(self.SERVERS_LOGS_DIR)

        self.OUT_DIR = path.join(self.OUT_DIR, self.PROCESS_ID)
        self.check_dir(self.OUT_DIR)
        self.IN_DIR = path.join(self.IN_DIR, self.PROCESS_ID)

        self.MSA_FILE = path.join(self.IN_DIR, self.MSA_FILE_NAME)
        self.TREE_FILE = path.join(self.IN_DIR, self.TREE_FILE_NAME)

        self.CALCULATED_ARGS.file_path = self.OUT_DIR

        self.WEBSERVER_RESULTS_URL = path.join(WEBSERVER_RESULTS_URL, self.PROCESS_ID)
        self.WEBSERVER_LOG_URL = path.join(WEBSERVER_LOG_URL, self.PROCESS_ID)
        self.JOB_LOGGER = get_job_logger(f'f{process_id}', self.SERVERS_LOGS_DIR)
        self.set_job_logger_info(f'PROCESS ID: {process_id}\n'
                                 f'\tSERVERS_RESULTS_DIR: {self.SERVERS_RESULTS_DIR}\n'
                                 f'\tSERVERS_LOGS_DIR: {self.SERVERS_LOGS_DIR}\n'
                                 f'\tMSA_FILE: {self.MSA_FILE}\n'
                                 f'\tTREE_FILE: {self.TREE_FILE}\n'
                                 f'\tJOB_LOGGER: {self.JOB_LOGGER}\n'
                                 f'\tWEBSERVER_RESULTS_URL: {self.WEBSERVER_RESULTS_URL}\n'
                                 f'\tWEBSERVER_LOG_URL: {self.WEBSERVER_LOG_URL}\n')

    def set_job_logger_info(self, log_msg: str):
        self.LOGGER.info(log_msg)
        self.JOB_LOGGER.info(log_msg)

    def check_and_set_input_and_output_variables(self):
        """get variables from input arguments and fill out the Variable Class properties"""
        if len(self.COMMAND_LINE) < 5:
            print(len(self.COMMAND_LINE))
            print('At least two required parameters --msa_file --tree_file.' + self.USAGE)
            exit()

        if len(self.COMMAND_LINE) > 4 and self.COMMAND_LINE[1].startswith('-') and self.COMMAND_LINE[3].startswith('-'):
            self.check_arguments_for_errors()

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
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('draw_tree', False):
            try:
                func = self.ACTIONS.draw_tree
                val = func(newick_tree=self.CALCULATED_ARGS.newick_tree, file_path=self.OUT_DIR)
                self.set_job_logger_info(f'Successfully completed \'draw_tree\' -> {val}')
            except ValueError:
                format_exc = f'{traceback.format_exc()}'
                self.set_job_logger_info(f'Error executing command \'draw_tree\' -> {format_exc}')
                self.CALCULATED_ARGS.err_list.append((f'Error executing command \'draw_tree\'', format_exc))
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('compute_likelihood_of_tree', False):
            try:
                func = self.ACTIONS.compute_likelihood_of_tree
                val = func(newick_tree=self.CALCULATED_ARGS.newick_tree, pattern=self.CALCULATED_ARGS.pattern_dict,
                           file_path=self.OUT_DIR, rate_vector=self.CALCULATED_ARGS.rate_vector)
                self.set_job_logger_info(f'Successfully completed \'compute_likelihood_of_tree\' -> {val}')
            except ValueError:
                format_exc = f'{traceback.format_exc()}'
                self.set_job_logger_info(f'Error executing command \'compute_likelihood_of_tree\' -> {format_exc}')
                self.CALCULATED_ARGS.err_list.append((f'Error executing command \'compute_likelihood_of_tree\'',
                                                      format_exc))
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('create_all_file_types', False):
            try:
                func = self.ACTIONS.create_all_file_types
                val = func(newick_tree=self.CALCULATED_ARGS.newick_tree, pattern=self.CALCULATED_ARGS.pattern_dict,
                           file_path=self.OUT_DIR, rate_vector=self.CALCULATED_ARGS.rate_vector,
                           alphabet=self.CALCULATED_ARGS.alphabet)
                self.set_job_logger_info(f'Successfully completed \'create_all_file_types\' -> {val}')
            except ValueError:
                format_exc = f'{traceback.format_exc()}'
                self.set_job_logger_info(f'Error executing command \'create_all_file_types\' -> {format_exc}')
                self.CALCULATED_ARGS.err_list.append((f'Error executing command \'create_all_file_types\'', format_exc))
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('execute_all_actions', False):
            try:
                func = self.ACTIONS.execute_all_actions
                val = func(newick_tree=self.CALCULATED_ARGS.newick_tree, pattern=self.CALCULATED_ARGS.pattern_dict,
                           file_path=self.OUT_DIR, rate_vector=self.CALCULATED_ARGS.rate_vector,
                           alphabet=self.CALCULATED_ARGS.alphabet)
                self.set_job_logger_info(f'Successfully completed \'execute_all_actions\' -> {val}')
            except ValueError:
                format_exc = f'{traceback.format_exc()}'
                self.set_job_logger_info(f'Error executing command \'execute_all_actions\' -> {format_exc}')
                self.CALCULATED_ARGS.err_list.append((f'Error executing command \'execute_all_actions\'', format_exc))

    def check_arguments_for_errors(self):
        if path.isfile(self.TREE_FILE):
            with open(self.TREE_FILE, 'r') as f:
                self.CALCULATED_ARGS.newick_text = f.read()
        else:
            self.CALCULATED_ARGS.err_list.append((f'The File does not exist',
                                                  f'File "{self.TREE_FILE}" does not exist '))
        if path.isfile(self.MSA_FILE):
            with open(self.MSA_FILE, 'r') as f:
                self.CALCULATED_ARGS.pattern_msa = f.read()
        else:
            self.CALCULATED_ARGS.err_list.append((f'The File does not exist',
                                                  f'File "{self.MSA_FILE}" does not exist '))

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

    def parse_arguments(self):
        """parse arguments and fill out the relevant Variable Class properties"""
        parser = argparse.ArgumentParser(prog=self.WEBSERVER_NAME_CAPITAL, description='GLOOME',
                                         usage='%(prog)s [options]')
        parser.add_argument('--msa_file', dest='MSA_FILE', type=str, required=True, help='Specify the msa file '
                            '(required).')
        parser.add_argument('--tree_file', dest='TREE_FILE', type=str, required=True, help='Specify the newick file '
                            '(required).')
        parser.add_argument('--process_id', dest='process_id', type=str, required=False, default=self.PROCESS_ID,
                            help=f'Process id (optional). Default is {self.PROCESS_ID}.')
        parser.add_argument('--mode', dest='mode', required=False, action="extend", nargs="+", type=str,
                            help=f'Execution mode style (optional). Possible options: ("draw_tree", '
                            f'"compute_likelihood_of_tree", "create_all_file_types", "execute_all_actions"). Default '
                            f'is {self.MODE[:1]}.')
        parser.add_argument('--with_internal_nodes', dest='with_internal_nodes', type=bool, required=False,
                            default=self.CURRENT_ARGS.get('with_internal_nodes', True), help=f'Specify the Newick file '
                            f'style (optional). Default is {self.CURRENT_ARGS.get("with_internal_nodes", True)}.')
        parser.add_argument('--sort_values_by', dest='sort_values_by', required=False, action="extend", nargs="+",
                            type=str, help=f'Specify the columns by which you want to sort the values in the csv file. '
                            f'Possible options: ("Name", "Parent", "Distance to father", "child"). Default is '
                            f'{self.CURRENT_ARGS.get("sort_values_by", ("child", "Name"))}.')
        parser.add_argument('--categories_quantity', dest='categories_quantity', type=int, required=False,
                            default=self.CURRENT_ARGS.get('categories_quantity', 4), help=f'Specify categories '
                            f'quantity. Default is {self.CURRENT_ARGS.get("categories_quantity", 4)}.')
        parser.add_argument('--alpha', dest='alpha', type=float, required=False, default=self.CURRENT_ARGS.get('alpha',
                            0.5), help=f'Specify alpha. Default is {self.CURRENT_ARGS.get("alpha", 0.5)}.')
        args = parser.parse_args()

        for arg_name, arg_value in vars(args).items():
            if arg_value is not None:
                if arg_name == 'process_id':
                    if arg_value != self.PROCESS_ID:
                        self.change_process_id(arg_value)
                elif arg_name == 'mode':
                    setattr(self, arg_name.upper(), tuple(arg_value))
                else:
                    if hasattr(self, arg_name.upper()):
                        setattr(self, arg_name.upper(), arg_value)
                    if hasattr(self.CURRENT_ARGS, arg_name):
                        if arg_name == 'sort_values_by':
                            setattr(self.CURRENT_ARGS, arg_name, tuple(arg_value))
                        else:
                            setattr(self.CURRENT_ARGS, arg_name, arg_value)

        self.DEFAULT_ACTIONS.update({'compute_likelihood_of_tree': False,
                                     'calculate_tree_for_fasta': False,
                                     'calculate_ancestral_sequence': False,
                                     'draw_tree': False,
                                     'create_all_file_types': False,
                                     'execute_all_actions': False})

        if 'compute_likelihood_of_tree' in self.MODE:
            self.DEFAULT_ACTIONS.update({'compute_likelihood_of_tree': True})
        if 'draw_tree' in self.MODE:
            self.DEFAULT_ACTIONS.update({'calculate_tree_for_fasta': True,
                                         'calculate_ancestral_sequence': True,
                                         'draw_tree': True})
        if 'create_all_file_types' in self.MODE:
            self.DEFAULT_ACTIONS.update({'calculate_tree_for_fasta': True,
                                         'calculate_ancestral_sequence': True,
                                         'create_all_file_types': True})
        if 'execute_all_actions' in self.MODE:
            self.DEFAULT_ACTIONS.update({'calculate_tree_for_fasta': True,
                                         'calculate_ancestral_sequence': True,
                                         'execute_all_actions': True})

        return args

    @staticmethod
    def check_dir(file_path: str, **kwargs):
        if not path.exists(file_path):
            makedirs(file_path, **kwargs)
