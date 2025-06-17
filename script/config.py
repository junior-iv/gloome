import argparse
import os.path
import shutil
import traceback
import socket
from shutil import copy, make_archive
from SharedConsts import *
from utils import *
# from json import dumps
# from typing import Set
# import socket


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
        self.TEMPLATES_DIR = TEMPLATES_DIR
        self.ERROR_TEMPLATE = ERROR_TEMPLATE

        self.IS_PRODUCTION = IS_PRODUCTION
        # self.IS_LOCAL = False
        self.IS_LOCAL = 'powerslurm' not in socket.gethostname()
        self.MSA_FILE_NAME = MSA_FILE_NAME
        self.TREE_FILE_NAME = TREE_FILE_NAME

        self.ACTIONS = ACTIONS
        self.VALIDATION_ACTIONS = VALIDATION_ACTIONS
        self.DEFAULT_ACTIONS = DEFAULT_ACTIONS

        self.CURRENT_ARGS = DEFAULT_ARGUMENTS
        self.CURRENT_ARGS.update(DEFAULT_FORM_ARGUMENTS)

        self.MSA_FILE = None
        self.TREE_FILE = None

        self.CALCULATED_ARGS = CALCULATED_ARGS
        self.MENU = MENU
        self.PROGRESS_BAR = PROGRESS_BAR

        self.WEBSERVER_NAME_CAPITAL = WEBSERVER_NAME_CAPITAL
        self.WEBSERVER_NAME = WEBSERVER_NAME
        self.WEBSERVER_URL = WEBSERVER_URL
        self.WEBSERVER_TITLE = WEBSERVER_TITLE
        self.WEBSERVER_RESULTS_URL = WEBSERVER_RESULTS_URL
        self.WEBSERVER_LOG_URL = WEBSERVER_LOG_URL

        self.PROCESS_ID = None
        self.SERVERS_RESULTS_DIR = None
        self.SERVERS_LOGS_DIR = None
        self.SERVERS_INPUT_DIR = None
        self.INPUT_MSA_FILE = None
        self.INPUT_TREE_FILE = None
        self.SERVERS_OUTPUT_DIR = None
        self.JOB_LOGGER = None

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

        self.SERVERS_RESULTS_DIR = path.join(SERVERS_RESULTS_DIR, f'{self.PROCESS_ID}_out')
        self.SERVERS_INPUT_DIR = path.join(str(self.SERVERS_RESULTS_DIR), INPUT_DIR_NAME)
        self.INPUT_MSA_FILE = path.join(self.SERVERS_INPUT_DIR, self.MSA_FILE_NAME)
        self.INPUT_TREE_FILE = path.join(self.SERVERS_INPUT_DIR, self.TREE_FILE_NAME)
        self.SERVERS_OUTPUT_DIR = path.join(str(self.SERVERS_RESULTS_DIR), OUTPUT_DIR_NAME)
        self.SERVERS_LOGS_DIR = SERVERS_LOGS_DIR

        self.CALCULATED_ARGS.file_path = self.SERVERS_RESULTS_DIR

        self.WEBSERVER_RESULTS_URL = path.join(WEBSERVER_RESULTS_URL, self.PROCESS_ID)
        self.WEBSERVER_LOG_URL = path.join(WEBSERVER_LOG_URL, self.PROCESS_ID)

        # if not path.exists(self.SERVERS_RESULTS_DIR):
        #     makedirs(self.SERVERS_RESULTS_DIR)
        # shutil.copytree(path.join(SERVERS_RESULTS_DIR, self.PROCESS_ID), self.SERVERS_RESULTS_DIR, dirs_exist_ok=False)
        # if not path.exists(self.SERVERS_INPUT_DIR):
        #     makedirs(self.SERVERS_INPUT_DIR)
        if not path.exists(self.SERVERS_OUTPUT_DIR):
            makedirs(self.SERVERS_OUTPUT_DIR)
        # shutil.copytree(path.join(path.join(SERVERS_RESULTS_DIR, self.PROCESS_ID), INPUT_DIR_NAME),
        #                 self.SERVERS_INPUT_DIR, dirs_exist_ok=True)

        self.JOB_LOGGER = get_job_logger(f'b{process_id}', self.SERVERS_LOGS_DIR)
        self.set_job_logger_info(f'process_id = {process_id}')

    def set_job_logger_info(self, log_msg: str):
        self.LOGGER.info(log_msg)
        self.JOB_LOGGER.info(log_msg)

    def check_and_set_input_and_output_variables(self):
        """get variables from input arguments and fill out the Variable Class properties"""
        if len(self.COMMAND_LINE) < 5:
            print(len(self.COMMAND_LINE))
            print('At least two required parameters --msa_file --tree_file.' + self.USAGE)
            sys.exit()

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
                self.ACTIONS.draw_tree(newick_tree=self.CALCULATED_ARGS.newick_tree,
                                       file_path=self.SERVERS_OUTPUT_DIR,
                                       is_radial_tree=self.CURRENT_ARGS.get('is_radial_tree'),
                                       show_distance_to_parent=self.CURRENT_ARGS.get('show_distance_to_parent'))
                self.set_job_logger_info(f'Successfully completed \'draw_tree\' -> {self.ACTIONS.draw_tree}')
            except ValueError:
                format_exc = f'{traceback.format_exc()}'
                self.set_job_logger_info(f'Error executing command \'draw_tree\' -> {format_exc}')
                self.CALCULATED_ARGS.err_list.append((f'Error executing command \'draw_tree\'', format_exc))
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('compute_likelihood_of_tree', False):
            try:
                self.ACTIONS.compute_likelihood_of_tree(newick_tree=self.CALCULATED_ARGS.newick_tree,
                                                        pattern=self.CALCULATED_ARGS.pattern_dict,
                                                        file_path=self.SERVERS_OUTPUT_DIR,
                                                        rate_vector=self.CALCULATED_ARGS.rate_vector)
                self.set_job_logger_info(f'Successfully completed \'compute_likelihood_of_tree\' -> '
                                         f'{self.ACTIONS.compute_likelihood_of_tree}')
            except ValueError:
                format_exc = f'{traceback.format_exc()}'
                self.set_job_logger_info(f'Error executing command \'compute_likelihood_of_tree\' -> {format_exc}')
                self.CALCULATED_ARGS.err_list.append((f'Error executing command \'compute_likelihood_of_tree\'',
                                                      format_exc))
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('create_all_file_types', False):
            try:
                self.ACTIONS.create_all_file_types(newick_tree=self.CALCULATED_ARGS.newick_tree,
                                                   pattern=self.CALCULATED_ARGS.pattern_dict,
                                                   file_path=self.SERVERS_OUTPUT_DIR,
                                                   rate_vector=self.CALCULATED_ARGS.rate_vector,
                                                   alphabet=self.CALCULATED_ARGS.alphabet)
                self.set_job_logger_info(f'Successfully completed \'create_all_file_types\' -> '
                                         f'{self.ACTIONS.create_all_file_types}')
                archive_name = os.path.join(os.path.dirname(self.SERVERS_OUTPUT_DIR), f'{self.PROCESS_ID}')
                self.set_job_logger_info(f'archive_name (zip) = {archive_name}')
                make_archive(archive_name, 'zip', self.SERVERS_OUTPUT_DIR, '.')
            except ValueError:
                format_exc = f'{traceback.format_exc()}'
                self.set_job_logger_info(f'Error executing command \'create_all_file_types\' -> {format_exc}')
                self.CALCULATED_ARGS.err_list.append((f'Error executing command \'create_all_file_types\'', format_exc))

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
                            help=f'Execution mode style (optional). Possible options: '
                            f'("draw_tree", compute_likelihood_of_tree", "create_all_file_types"). Default is '
                            f'{self.MODE[:1]}.')
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
        parser.add_argument('--is_radial_tree', dest='is_radial_tree', type=bool, required=False,
                            default=self.CURRENT_ARGS.get('is_radial_tree', True), help=f'Specify beta. Default is '
                            f'{self.CURRENT_ARGS.get("is_radial_tree", True)}.')
        parser.add_argument('--show_distance_to_parent', dest='show_distance_to_parent', type=float, required=False,
                            default=self.CURRENT_ARGS.get('show_distance_to_parent', True), help=f'Specify beta. '
                            f'Default is {self.CURRENT_ARGS.get("show_distance_to_parent", True)}.')
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
                                     'create_all_file_types': False})

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
        return args
