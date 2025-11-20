import argparse
import traceback

from sys import exit
from utils import *
from typing import Dict
# from flask import request


class Config:
    def __init__(self, **attributes):
        self.MODE = MODE
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
        self.IS_LOCAL = IS_LOCAL

        self.ACTIONS = ACTIONS
        self.VALIDATION_ACTIONS = VALIDATION_ACTIONS
        self.DEFAULT_ACTIONS = DEFAULT_ACTIONS

        self.CURRENT_ARGS = DEFAULT_ARGUMENTS
        # self.CURRENT_ARGS.update(DEFAULT_FORM_ARGUMENTS)

        self.MSA_FILE_NAME = MSA_FILE_NAME
        self.TREE_FILE_NAME = TREE_FILE_NAME

        self.CALCULATED_ARGS = CALCULATED_ARGS
        self.MENU = MENU

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

        # self.LOGGER = logger
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

        self.CALCULATED_ARGS.file_path = self.OUT_DIR

        self.WEBSERVER_RESULTS_URL = path.join(WEBSERVER_RESULTS_URL, self.PROCESS_ID)
        self.WEBSERVER_LOG_URL = path.join(WEBSERVER_LOG_URL, self.PROCESS_ID)
        self.JOB_LOGGER = get_job_logger(f'{process_id}', self.SERVERS_LOGS_DIR)
        # self.set_job_logger_info(f'PROCESS ID: {process_id}\n'
        #                          f'\tSERVERS_RESULTS_DIR: {self.SERVERS_RESULTS_DIR}\n'
        #                          f'\tSERVERS_LOGS_DIR: {self.SERVERS_LOGS_DIR}\n'
        #                          f'\tMSA_FILE: {self.MSA_FILE}\n'
        #                          f'\tTREE_FILE: {self.TREE_FILE}\n'
        #                          f'\tJOB_LOGGER: {self.JOB_LOGGER}\n'
        #                          f'\tWEBSERVER_RESULTS_URL: {self.WEBSERVER_RESULTS_URL}\n'
        #                          f'\tWEBSERVER_LOG_URL: {self.WEBSERVER_LOG_URL}\n')

    def set_job_logger_info(self, log_msg: str):
        # self.LOGGER.info(log_msg)
        self.JOB_LOGGER.info(log_msg)

    def check_and_set_input_and_output_variables(self):
        """get variables from input arguments and fill out the Variable Class properties"""
        if len(self.COMMAND_LINE) < 5:
            # print(len(self.COMMAND_LINE))
            print('\tAt least two required parameters --msa_file --tree_file', self.USAGE, sep='\n')
            exit()

        if len(self.COMMAND_LINE) > 4 and self.COMMAND_LINE[1].startswith('-') and self.COMMAND_LINE[3].startswith('-'):
            if not self.check_arguments_for_errors():
                for error_type, error in self.CALCULATED_ARGS.err_list:
                    print(f'{error_type}: {error}')
                print(self.USAGE)
                exit()

    def get_form_data(self) -> Dict[str, Union[str, int]]:
        form_data = {'msaText': self.CALCULATED_ARGS.msa,
                     'newickText': self.CALCULATED_ARGS.newick_text,
                     'isOptimizePi': int(self.CURRENT_ARGS.is_optimize_pi),
                     'isOptimizePiAverage': int(self.CURRENT_ARGS.is_optimize_pi_average),
                     'isOptimizeAlpha': int(self.CURRENT_ARGS.is_optimize_alpha),
                     'isOptimizeBL': int(self.CURRENT_ARGS.is_optimize_bl),
                     'isDoNotUseEMail': int(self.CURRENT_ARGS.is_do_not_use_e_mail),
                     'coefficientBL': self.CURRENT_ARGS.coefficient_bl,
                     'pi1': self.CURRENT_ARGS.pi_1,
                     'alpha': self.CURRENT_ARGS.alpha,
                     'categoriesQuantity': self.CURRENT_ARGS.categories_quantity,
                     'eMail': self.CURRENT_ARGS.e_mail}
        return form_data

    def execute_action(self, func, *args, **kwargs):
        try:
            val = func(*args, **kwargs)
            self.set_job_logger_info(f'Successfully Command \'{func.__name__}\' executed successfully. -> {val}')
        except ValueError:
            format_exc = f'{traceback.format_exc()}'
            self.set_job_logger_info(f'Failed to execute the command \'{func.__name__}\' -> {format_exc}')
            self.CALCULATED_ARGS.err_list.append((f'Failed to execute the command \'{func.__name__}\'', format_exc))

    def execute_calculation(self):
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('calculate_tree_for_fasta', False):
            self.execute_action(self.ACTIONS.calculate_tree_for_fasta, self.CALCULATED_ARGS.newick_tree)
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('calculate_ancestral_sequence', False):
            self.execute_action(self.ACTIONS.calculate_ancestral_sequence, self.CALCULATED_ARGS.newick_tree)
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('draw_tree', False):
            self.execute_action(self.ACTIONS.draw_tree, file_path=self.OUT_DIR, create_new_file=True,
                                form_data=self.get_form_data(), newick_tree=self.CALCULATED_ARGS.newick_tree)
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('compute_likelihood_of_tree', False):
            self.execute_action(self.ACTIONS.compute_likelihood_of_tree, file_path=self.OUT_DIR, create_new_file=True,
                                form_data=self.get_form_data(), newick_tree=self.CALCULATED_ARGS.newick_tree)
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('create_all_file_types', False):
            self.execute_action(self.ACTIONS.create_all_file_types, file_path=self.OUT_DIR, create_new_file=True,
                                form_data=self.get_form_data(), newick_tree=self.CALCULATED_ARGS.newick_tree,
                                log_file=self.JOB_LOGGER.handlers[-1].baseFilename)
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('execute_all_actions', False):
            self.execute_action(self.ACTIONS.execute_all_actions, file_path=self.OUT_DIR, create_new_file=True,
                                form_data=self.get_form_data(), newick_tree=self.CALCULATED_ARGS.newick_tree,
                                log_file=self.JOB_LOGGER.handlers[-1].baseFilename)
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('recompile_json', False):
            self.execute_action(self.ACTIONS.recompile_json, output_file=path.join(self.OUT_DIR, 'result.json'),
                                process_id=self.PROCESS_ID, is_local=self.IS_LOCAL)
        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('send_results_email', False):
            self.execute_action(self.ACTIONS.send_results_email, results_dir=self.SERVERS_RESULTS_DIR, is_error=False,
                                log_file=self.JOB_LOGGER.handlers[-1].baseFilename, excluded=('.json', '.zip'),
                                receiver=self.CURRENT_ARGS.e_mail, name=self.PROCESS_ID)
        if self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('send_results_email', False):
            self.execute_action(self.ACTIONS.send_results_email, results_dir=self.SERVERS_RESULTS_DIR, is_error=True,
                                log_file=self.JOB_LOGGER.handlers[-1].baseFilename, excluded=('.json', '.zip'),
                                receiver=self.CURRENT_ARGS.e_mail, name=self.PROCESS_ID)

    def check_arguments_for_errors(self) -> bool:
        if path.isfile(self.TREE_FILE):
            with open(self.TREE_FILE, 'r') as f:
                self.CALCULATED_ARGS.newick_text = f.read()
        else:
            self.CALCULATED_ARGS.err_list.append((f'The File does not exist',
                                                  f'File "{self.TREE_FILE}" does not exist '))

        if path.isfile(self.MSA_FILE):
            with open(self.MSA_FILE, 'r') as f:
                self.CALCULATED_ARGS.msa = f.read()
        else:
            self.CALCULATED_ARGS.err_list.append((f'The File does not exist',
                                                  f'File "{self.MSA_FILE}" does not exist '))

        if not self.CALCULATED_ARGS.err_list and self.VALIDATION_ACTIONS.get('check_data', False):
            self.CALCULATED_ARGS.err_list += self.ACTIONS.check_data(self.CALCULATED_ARGS.newick_text,
                                                                     self.CALCULATED_ARGS.msa,
                                                                     self.CURRENT_ARGS.categories_quantity,
                                                                     self.CURRENT_ARGS.alpha,
                                                                     self.CURRENT_ARGS.pi_1,
                                                                     self.CURRENT_ARGS.coefficient_bl,
                                                                     self.CURRENT_ARGS.e_mail,
                                                                     self.CURRENT_ARGS.is_optimize_pi,
                                                                     self.CURRENT_ARGS.is_optimize_pi_average,
                                                                     self.CURRENT_ARGS.is_optimize_alpha,
                                                                     self.CURRENT_ARGS.is_optimize_bl,
                                                                     self.CURRENT_ARGS.is_do_not_use_e_mail)

        if not self.CALCULATED_ARGS.err_list and self.VALIDATION_ACTIONS.get('check_tree', False):
            try:
                self.CALCULATED_ARGS.newick_tree = self.ACTIONS.check_tree(self.CALCULATED_ARGS.newick_text)
            except ValueError:
                self.CALCULATED_ARGS.err_list.append((f'TREE error', f'Wrong Phylogenetic tree format.'))

        if not self.CALCULATED_ARGS.err_list and self.DEFAULT_ACTIONS.get('set_tree_data', False):
            try:
                self.ACTIONS.set_tree_data(self.CALCULATED_ARGS.newick_tree, msa=self.CALCULATED_ARGS.msa,
                                           categories_quantity=self.CURRENT_ARGS.categories_quantity,
                                           alpha=self.CURRENT_ARGS.alpha, pi_1=self.CURRENT_ARGS.pi_1,
                                           coefficient_bl=self.CURRENT_ARGS.coefficient_bl,
                                           is_optimize_pi=self.CURRENT_ARGS.is_optimize_pi,
                                           is_optimize_pi_average=self.CURRENT_ARGS.is_optimize_pi_average,
                                           is_optimize_alpha=self.CURRENT_ARGS.is_optimize_alpha,
                                           is_optimize_bl=self.CURRENT_ARGS.is_optimize_bl)
            except ValueError:
                self.CALCULATED_ARGS.err_list.append((f'MSA error',
                                                      f'Wrong MSA format. Please provide MSA in FASTA format.'))

        if not self.CALCULATED_ARGS.err_list and (self.CURRENT_ARGS.is_optimize_pi_average or
                                                  self.CURRENT_ARGS.is_optimize_pi):
            try:
                self.CURRENT_ARGS.pi_1 = self.CALCULATED_ARGS.newick_tree.pi_1
            except ValueError:
                self.CALCULATED_ARGS.err_list.append((f'Strange error',
                                                      f'Strange error.'))

        if not self.CALCULATED_ARGS.err_list and self.CURRENT_ARGS.is_optimize_alpha:
            try:
                self.CURRENT_ARGS.alpha = self.CALCULATED_ARGS.newick_tree.alpha
            except ValueError:
                self.CALCULATED_ARGS.err_list.append((f'Strange error',
                                                      f'Strange error.'))

        if not self.CALCULATED_ARGS.err_list and self.CURRENT_ARGS.is_optimize_bl:
            try:
                self.CURRENT_ARGS.coefficient_bl = self.CALCULATED_ARGS.newick_tree.coefficient_bl
            except ValueError:
                self.CALCULATED_ARGS.err_list.append((f'Strange error',
                                                      f'Strange error.'))

        if self.CALCULATED_ARGS.err_list:
            self.set_job_logger_info(f'Error list: \n{self.CALCULATED_ARGS.err_list}')
        else:
            self.set_job_logger_info(f'Verification completed successfully')

        return not self.CALCULATED_ARGS.err_list

    def parse_arguments(self):
        """parse arguments and fill out the relevant Variable Class properties"""
        parser = argparse.ArgumentParser(prog=self.WEBSERVER_NAME_CAPITAL, description='GLOOME',
                                         usage='%(prog)s [options]')
        parser.add_argument('--msa_file', dest='MSA_FILE', type=str, required=True, help=f'Specify the msa filepath '
                            f'(required).')
        parser.add_argument('--tree_file', dest='TREE_FILE', type=str, required=True, help=f'Specify the newick '
                            f'filepath (required).')
        parser.add_argument('--out_dir', dest='OUT_DIR', type=str, required=True, help=f'Specify the outdir path '
                            f'(optional).')
        parser.add_argument('--process_id', dest='process_id', type=str, required=False, default=self.PROCESS_ID,
                            help=f'Specify a process ID or it will be generated automatically (optional).')
        parser.add_argument('--mode', dest='mode', required=False, action="extend", nargs="+", type=str,
                            help=f'Execution mode style (optional). Possible options: ("draw_tree", '
                            f'"compute_likelihood_of_tree", "create_all_file_types", "execute_all_actions"). '
                            f'Default is {self.MODE[3:]}.')
        parser.add_argument('--with_internal_nodes', dest='with_internal_nodes', type=int, required=False,
                            default=self.CURRENT_ARGS.with_internal_nodes, help=f'Specify the tree has internal nodes '
                            f'(optional). Default is {self.CURRENT_ARGS.with_internal_nodes}.')
        parser.add_argument('--categories_quantity', dest='categories_quantity', type=int, required=False,
                            default=int(self.CURRENT_ARGS.categories_quantity), help=f'Specify categories quantity '
                            f'(optional). Default is {int(self.CURRENT_ARGS.categories_quantity)}.')
        parser.add_argument('--alpha', dest='alpha', type=float, required=False, default=self.CURRENT_ARGS.alpha,
                            help=f'Specify alpha (optional). Default is {self.CURRENT_ARGS.alpha}.')
        parser.add_argument('--pi_1', dest='pi_1', type=float, required=False, default=self.CURRENT_ARGS.pi_1,
                            help=f'Specify pi_1 (optional). Default is {self.CURRENT_ARGS.pi_1}.')
        parser.add_argument('--coefficient_bl', dest='coefficient_bl', type=float, required=False,
                            help=f'Specify coefficient_bl (optional). Default is {self.CURRENT_ARGS.coefficient_bl}.',
                            default=self.CURRENT_ARGS.coefficient_bl)
        parser.add_argument('--e_mail', dest='e_mail', type=str, required=False,
                            help=f'Specify e_mail (optional). Default is {self.CURRENT_ARGS.e_mail}.',
                            default=self.CURRENT_ARGS.e_mail)
        parser.add_argument('--is_optimize_pi', dest='is_optimize_pi', type=int, required=False,
                            help=f'Specify is_optimize_pi (optional). Default is '
                            f'{int(self.CURRENT_ARGS.is_optimize_pi)}.', default=int(self.CURRENT_ARGS.is_optimize_pi))
        parser.add_argument('--is_optimize_pi_average', dest='is_optimize_pi_average', type=int,
                            required=False, help=f'Specify is_optimize_pi_average (optional). Default is '
                            f'{int(self.CURRENT_ARGS.is_optimize_pi_average)}.',
                            default=int(self.CURRENT_ARGS.is_optimize_pi_average))
        parser.add_argument('--is_optimize_alpha', dest='is_optimize_alpha', type=int, required=False,
                            help=f'Specify is_optimize_alpha (optional). Default is '
                            f'{int(self.CURRENT_ARGS.is_optimize_alpha)}.',
                            default=int(self.CURRENT_ARGS.is_optimize_alpha))
        parser.add_argument('--is_optimize_bl', dest='is_optimize_bl', type=int, required=False,
                            help=f'Specify is_optimize_bl (optional). Default is '
                            f'{int(self.CURRENT_ARGS.is_optimize_bl)}.', default=int(self.CURRENT_ARGS.is_optimize_bl))
        parser.add_argument('--is_do_not_use_e_mail', dest='is_do_not_use_e_mail', type=int, required=False,
                            help=f'Specify is_do_not_use_e_mail (optional). Default is '
                            f'{int(self.CURRENT_ARGS.is_do_not_use_e_mail)}.',
                            default=int(self.CURRENT_ARGS.is_do_not_use_e_mail))

        args = parser.parse_args()

        for arg_name, arg_value in vars(args).items():
            if arg_value is not None:
                if arg_name == 'process_id':
                    if arg_value != self.PROCESS_ID:
                        self.change_process_id(arg_value)
                elif arg_name == 'mode':
                    setattr(self, arg_name.upper(), tuple(arg_value))
                elif arg_name in ('with_internal_nodes', 'is_optimize_pi', 'is_optimize_pi_average',
                                  'is_optimize_alpha', 'is_optimize_bl', 'is_do_not_use_e_mail'):
                    if hasattr(self.CURRENT_ARGS, arg_name):
                        setattr(self.CURRENT_ARGS, arg_name, bool(arg_value))
                else:
                    if hasattr(self, arg_name.upper()):
                        setattr(self, arg_name.upper(), arg_value)
                    if hasattr(self.CURRENT_ARGS, arg_name):
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
        if self.IS_LOCAL:
            self.DEFAULT_ACTIONS.update({'recompile_json': True})
        if not self.IS_LOCAL and not self.CURRENT_ARGS.is_do_not_use_e_mail and self.CURRENT_ARGS.e_mail:
            self.DEFAULT_ACTIONS.update({'send_results_email': True})

        return args

    @staticmethod
    def check_dir(file_path: str, **kwargs):
        if not path.exists(file_path):
            makedirs(file_path, **kwargs)
