import types

from os import getenv, path
from sys import argv
from script.tree import Tree
from script.service_functions import (check_data, create_all_file_types, compute_likelihood_of_tree, draw_tree,
                                      execute_all_actions)
from typing import List, Tuple, Union
from dotenv import load_dotenv

load_dotenv()
MODE = ('draw_tree', 'compute_likelihood_of_tree', 'create_all_file_types', 'execute_all_actions')
IS_PRODUCTION = True
MAX_CONTENT_LENGTH = 16 * 1000 * 1000 * 1000
PREFIX = '/'
APPLICATION_ROOT = PREFIX
DEBUG = not IS_PRODUCTION

SECRET_KEY = getenv('SECRET_KEY')
TOKEN = getenv('TOKEN')
PARTITION = getenv('PARTITION')
USE_OLD_SUBMITER = getenv('USE_OLD_SUBMITER')

LOGIN_NODE_URLS = getenv('LOGIN_NODE_URLS')
USER_NAME = getenv('USER_NAME')
USER_ID = getenv('USER_ID')
USER_PASSWORD = getenv('USER_PASSWORD')
ADMIN_EMAIL = getenv('ADMIN_EMAIL')
SMTP_SERVER = getenv('SMTP_SERVER')

DEV_EMAIL = getenv('DEV_EMAIL')
ADMIN_USER_NAME = getenv('ADMIN_USER_NAME')
ADMIN_PASSWORD = getenv('ADMIN_PASSWORD')
SEND_EMAIL_DIR_IBIS = getenv('SEND_EMAIL_DIR_IBIS')
OWNER_EMAIL = getenv('OWNER_EMAIL')

PREFERRED_URL_SCHEME = 'https'
WEBSERVER_NAME_CAPITAL = 'Gloome'
WEBSERVER_NAME = 'gloome.tau.ac.il'
WEBSERVER_URL = f'{PREFERRED_URL_SCHEME}://{WEBSERVER_NAME}'
WEBSERVER_RESULTS_URL = path.join(WEBSERVER_URL, 'results')
WEBSERVER_LOG_URL = path.join(WEBSERVER_URL, 'logs')

WEBSERVER_TITLE = '<b>GLOOME Server - Gain Loss Mapping Engine</b>'
MODULE_LOAD = 'module load mamba/mamba-1.5.8'
PRODJECT_DIR = '/lsweb/rodion/gloome'
ENVIRONMENT_DIR = path.join(PRODJECT_DIR, 'gloome_env2')
ENVIRONMENT_ACTIVATE = f'mamba activate {ENVIRONMENT_DIR}'

BIN_DIR = path.dirname(path.abspath(__file__))
SCRIPT_DIR = path.join(BIN_DIR, 'script')
SRC_DIR = path.join(BIN_DIR, 'src')
INITIAL_DATA_DIR = path.join(SRC_DIR, 'initial_data')
SERVERS_RESULTS_DIR = path.join(BIN_DIR, 'results')
IN_DIR = path.join(SERVERS_RESULTS_DIR, 'in')
OUT_DIR = path.join(SERVERS_RESULTS_DIR, 'out')
SERVERS_LOGS_DIR = path.join(BIN_DIR, 'logs')
APP_DIR = path.join(BIN_DIR, 'app')
TMP_DIR = path.join(BIN_DIR, 'tmp')
TEMPLATES_DIR = path.join(APP_DIR, 'templates')
STATIC_DIR = path.join(APP_DIR, 'static')
ERROR_TEMPLATE = path.join(TEMPLATES_DIR, '404.html')

MSA_FILE_NAME = 'msa_file.msa'
TREE_FILE_NAME = 'tree_file.tree'

REQUESTS_NUMBER = 100
REQUEST_WAITING_TIME = 30


class Actions:

    def __init__(self, **attributes):
        if attributes:
            for key, value in attributes.items():
                if type(value) is types.FunctionType:
                    setattr(self, key, value)


class CalculatedArgs:
    err_list: List[Union[Tuple[str, ...], str]]

    def __init__(self, **attributes):
        self.err_list = []
        if attributes:
            for key, value in attributes.items():
                setattr(self, key, value)


class DefaultArgs:
    def __init__(self, **attributes):
        if attributes:
            for key, value in attributes.items():
                setattr(self, key, value)

    def get(self, attribute_name, default=None):
        if hasattr(self, attribute_name):
            return getattr(self, attribute_name)
        else:
            return default

    def update(self, *args, **kwargs):
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)
        if args:
            for arg in args:
                if isinstance(arg, dict):
                    for key, value in arg.items():
                        setattr(self, key, value)


COMMAND_LINE = argv

DEFAULT_ARGUMENTS = DefaultArgs(**{
    'with_internal_nodes': True,
    # 'sort_values_by': ['child', 'Name'],
    'sep': '\t'
    })

DEFAULT_FORM_ARGUMENTS = {
    'categories_quantity': 4,
    'alpha': 0.5,
    'pi_1': 0.5
    }

ACTIONS = Actions(**{
                     'check_data': check_data,
                     'check_tree': Tree.rename_nodes,
                     'set_tree_data': Tree.set_tree_data,
                     'compute_likelihood_of_tree': compute_likelihood_of_tree,
                     'calculate_tree_for_fasta': Tree.calculate_tree_for_fasta,
                     'calculate_ancestral_sequence': Tree.calculate_ancestral_sequence,
                     'draw_tree': draw_tree,
                     'create_all_file_types': create_all_file_types,
                     'execute_all_actions': execute_all_actions
                     })

VALIDATION_ACTIONS = {
    'check_data': True,
    'check_tree': True
    }

DEFAULT_ACTIONS = {
    'set_tree_data': True,
    'calculate_tree_for_fasta': False,
    'compute_likelihood_of_tree': False,
    'calculate_ancestral_sequence': False,
    'draw_tree': False,
    'create_all_file_types': False,
    'execute_all_actions': False
    }


CALCULATED_ARGS = CalculatedArgs(**{
                                    'file_path': None,
                                    'newick_text': None,
                                    'msa': None,
                                    'newick_tree': None
                                    })

USAGE = ''' 
            Required parameters:
                    --msa_file <type=str>
                        Specify the msa filepath.
                    --tree_file <type=str>
                        Specify the tree filepath.
            Optional parameters:
                    --mode <type=str>
                        Execution mode style. Possible options: ('draw_tree', 'compute_likelihood_of_tree', 
                        'create_all_file_types', 'execute_all_actions'). Default is 'execute_all_actions'.
                    --with_internal_nodes <type=bool> 
                        Specify the Newick file type. Default is True.
                    --categories_quantity <type=int>
                        Specify categories quantity. Default is 4.
                    --alpha <type=float>
                        Specify alpha. Default is 0.5.
                    --pi_1 <type=float> 
                        Specify pi_1. Default is 0.5.
        '''
# --sort_values_by <type=str>
#     Specify the columns by which you want to sort the values in the csv file.
#     Possible options: ('Name', 'Parent', 'Distance to parent', 'Children'). Default is 'child' 'Name'.

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
