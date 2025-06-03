import types
from os import getenv, path, makedirs
from sys import argv
from script.tree import Tree
from script.service_functions import check_data, ERR, create_all_file_types, compute_likelihood_of_tree, draw_tree
from typing import List, Tuple, Union
# PREFIX = '/gloome'
# MODE = ('create_all_file_types', 'draw_tree', compute_likelihood_of_tree)
MODE = ('create_all_file_types', 'draw_tree', 'compute_likelihood_of_tree')
IS_PRODUCTION = True
MAX_CONTENT_LENGTH = 16 * 1000 * 1000 * 1000
PREFIX = '/'
APPLICATION_ROOT = PREFIX
DEBUG = not IS_PRODUCTION
SECRET_KEY = getenv('SECRET_KEY')
PREFERRED_URL_SCHEME = 'https'
WEBSERVER_NAME_CAPITAL = 'Gloome'
WEBSERVER_NAME = 'gloome.tau.ac.il'
WEBSERVER_URL = f'{PREFERRED_URL_SCHEME}://{WEBSERVER_NAME}'
WEBSERVER_TITLE = '<b>GLOOME Server - Gain Loss Mapping Engine</b>'


class FlaskConfig:

    # RECAPTCHA_SITE_KEY: str = getenv('RECAPTCHA_SITE_KEY')
    # RECAPTCHA_SECRET_KEY: str = getenv('RECAPTCHA_SECRET_KEY')
    SECRET_KEY: str
    DEBUG: bool
    PREFERRED_URL_SCHEME: str
    SERVER_NAME = str
    APPLICATION_ROOT = str
    # UPLOAD_FOLDERS_ROOT_PATH: str = WEBSERVER_RESULTS_DIR
    MAX_CONTENT_LENGTH: int

    def __init__(self, **attributes):
        self.SECRET_KEY = SECRET_KEY
        self.DEBUG = DEBUG
        self.PREFERRED_URL_SCHEME = PREFERRED_URL_SCHEME
        self.SERVER_NAME = WEBSERVER_NAME
        self.APPLICATION_ROOT = APPLICATION_ROOT
        self.MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
        if attributes:
            for key, value in attributes.items():
                setattr(self, key, value)


class Actions:

    def __init__(self, **attributes):
        if attributes:
            for key, value in attributes.items():
                if type(value) is types.FunctionType:
                    setattr(self, key, value)

    # # def __setattr__(self, key, value):
    # #     if hasattr(self, key):
    # #         object.__setattr__(self, key, value)
    # #
    # def __getattr__(self, item):
    #     if hasattr(self, item):
    #         return getattr(self, item)


class CalculatedArgs:
    err_list: List[Union[Tuple[str, ...], str]]

    def __init__(self, **attributes):
        self.err_list = []
        if attributes:
            for key, value in attributes.items():
                setattr(self, key, value)


LOGIN_NODE_URLS = getenv('LOGIN_NODE_URLS')
USERNAME = getenv('USERNAME')
USER_ID = getenv('USER_ID')
PASSWORD = getenv('PASSWORD')
ADMIN_EMAIL = getenv('ADMIN_EMAIL')
SMTP_SERVER = getenv('SMTP_SERVER')

DEV_EMAIL = getenv('DEV_EMAIL')
ADMIN_USER_NAME = getenv('ADMIN_USER_NAME')
ADMIN_PASSWORD = getenv('ADMIN_PASSWORD')
SEND_EMAIL_DIR_IBIS = getenv('SEND_EMAIL_DIR_IBIS')
OWNER_EMAIL = getenv('OWNER_EMAIL')

# this_file_path = path.abspath(__file__)
# Bin = f'{path.dirname(this_file_path)}/script'
# script_path = path.abspath(__file__)
# Bin = f"{path.dirname(script_path)}/script" #path to the script folder
# BIN_DIR = path.dirname(Bin)  #main project folder
# COMMAND_LINE = path.abspath(__file__)
COMMAND_LINE = argv
BIN_DIR = path.dirname(path.abspath(__file__))
# print(BIN_DIR)
# # BIN_DIR = path.dirname(path.dirname(argv[0]))
SCRIPT_DIR = path.join(BIN_DIR, 'script')
SRC_DIR = path.join(BIN_DIR, 'src')
INITIAL_DATA_DIR = path.join(SRC_DIR, 'initial_data')
SERVERS_RESULTS_DIR = path.join(BIN_DIR, 'results')
SERVERS_LOGS_DIR = path.join(BIN_DIR, 'logs')
APP_DIR = path.join(BIN_DIR, 'app')
TEMPLATES_DIR = path.join(APP_DIR, 'templates')
ERROR_TEMPLATE = path.join(TEMPLATES_DIR, '404.html')

WEBSERVER_RESULTS_DIR = SERVERS_RESULTS_DIR
WEBSERVER_LOGS_DIR = SERVERS_LOGS_DIR
# WEBSERVER_HTML_DIR = f'/var/www/html/{WEBSERVER_NAME}/ver2'

WEBSERVER_RESULTS_URL = path.join(WEBSERVER_URL, 'results')
WEBSERVER_LOG_URL = path.join(WEBSERVER_URL, 'logs')
MSA_FILE_NAME = 'msa_file.msa'
TREE_FILE_NAME = 'tree_file.tree'
INPUT_DIR_NAME = 'INPUT'
OUTPUT_DIR_NAME = 'OUTPUT'

DEFAULT_ARGUMENTS = {
    'with_internal_nodes': True,
    'sort_values_by': ('child', 'Name'),
    'sep': '\t'
    }

DEFAULT_FORM_ARGUMENTS = {
    'categories_quantity': 4,
    'alpha': 0.5,
    'is_radial_tree': False,
    'show_distance_to_parent': False
    }

ACTIONS = Actions(**{
                     'check_data': check_data,
                     'check_tree': Tree.check_tree,
                     'rename_nodes': Tree.rename_nodes,
                     'rate_vector': Tree.get_gamma_distribution_categories_vector,
                     'pattern_dict': Tree.get_pattern_dict,
                     'alphabet': Tree.get_alphabet_from_dict,
                     'compute_likelihood_of_tree': compute_likelihood_of_tree,
                     'calculate_tree_for_fasta': Tree.calculate_tree_for_fasta,
                     'calculate_ancestral_sequence': Tree.calculate_ancestral_sequence,
                     'draw_tree': draw_tree,
                     'create_all_file_types': create_all_file_types
                     })

VALIDATION_ACTIONS = {
    'check_data': True,
    'check_tree': True
    }

DEFAULT_ACTIONS = {
    'rename_nodes': True,
    'rate_vector': True,
    'pattern_dict': True,
    'alphabet': True,
    'compute_likelihood_of_tree': False,
    'calculate_tree_for_fasta': False,
    'calculate_ancestral_sequence': False,
    'draw_tree': False,
    'create_all_file_types': False
    }


CALCULATED_ARGS = CalculatedArgs(**{
                                    'file_path': None,
                                    'rate_vector': None,
                                    'newick_text': None,
                                    'pattern_msa': None,
                                    'newick_tree': None,
                                    'pattern_dict': None,
                                    'alphabet': None
                                    })

USAGE = ''' 
            Required parameters:
                    --msa_file <msa filepath>
                    --tree_file <newick filepath>
            Optional parameters:
                    --with_internal_nodes <type=bool> default=True
                    --sort_values_by <type=tuple> default=('child', 'Name')
                    --categories_quantity <type=int> default=4
                    --alpha <type=float> default=0.5
                    --is_radial_tree <type=bool> default=True
                    --show_distance_to_parent <type=bool> default=True
            '''

MENU = ({'name': 'HOME', 'url': 'index',
         'submenu': ()
         },
        {'name': 'OVERVIEW', 'url': 'overview',
         'submenu': ()
         },
        {'name': 'FAQ', 'url': 'faq',
         'submenu': ()
         },
        {'name': 'GALLERY', 'url': 'gallery',
         'submenu': ()
         },
        {'name': 'SOURCE CODE', 'url': 'source_code',
         'submenu': ()
         },
        {'name': 'CITING & CREDITS', 'url': 'citing_and_credits',
         'submenu': ()
         }
        )

PROGRESS_BAR = {'value': 0, 'status': 'active'}
