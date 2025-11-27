from os import getenv, path, scandir
from sys import argv
from typing import List, Tuple, Union
from dotenv import load_dotenv
from types import FunctionType, MethodType

from script.tree import Tree
from script.service_functions import (check_data, create_all_file_types, compute_likelihood_of_tree, draw_tree,
                                      execute_all_actions, recompile_json)

load_dotenv()
MODE = ('draw_tree', 'compute_likelihood_of_tree', 'create_all_file_types', 'execute_all_actions')
IS_PRODUCTION = True
MAX_CONTENT_LENGTH = 16 * 1000 * 1000 * 1000
PREFIX = '/'
APPLICATION_ROOT = PREFIX
DEBUG = not IS_PRODUCTION

# ADMIN_EMAIL = 'juniorrr.iv@gmail.com'
# # ADMIN_EMAIL = 'sgloome@gmail.com'
# SMTP_SERVER = 'smtp.gmail.com'
# # SMTP_PORT = 465
# ADMIN_PASSWORD = 'debe eenr qyfr jmdr'
# # ADMIN_PASSWORD = 'W7wp.N2WaqmT%f'
# # SMTP_PORT = 587

PREFERRED_URL_SCHEME = 'https'
WEBSERVER_NAME_CAPITAL = 'Gloome'
SERVER_NAME = 'gloome.tau.ac.il'
WEBSERVER_URL = f'{PREFERRED_URL_SCHEME}://{SERVER_NAME}'
WEBSERVER_RESULTS_URL = path.join(WEBSERVER_URL, 'results')
WEBSERVER_LOG_URL = path.join(WEBSERVER_URL, 'logs')

WEBSERVER_TITLE = '<b>GLOOME Server - Gain Loss Mapping Engine</b>'
MODULE_LOAD = 'module load mamba/mamba-1.5.8'
# PRODJECT_DIR = '/lsweb/rodion/gloome'
# PRODJECT_DIR = '/gloome'
# SLURM_PRODJECT_DIR = '/gloome'

BIN_DIR = path.dirname(path.abspath(__file__))

ENVIRONMENT_DIR = path.join(BIN_DIR, 'gloome_env2')
ENVIRONMENT_ACTIVATE = f'mamba activate {ENVIRONMENT_DIR}'

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
REQUEST_WAITING_TIME = 20

# IS_LOCAL = request.remote_addr in ('127.0.0.1', '::1')
# IS_LOCAL = 'powerslurm' not in socket.gethostname()

if not path.exists(path.join(BIN_DIR, '.env')):
    SECRET_KEY = ''
    TOKEN = ''
    PARTITION = ''
    USE_OLD_SUBMITER = 0

    LOGIN_NODE_URLS = ''
    USER_NAME = ''
    USER_ID = ''
    USER_PASSWORD = ''
    ADMIN_EMAIL = ''
    SMTP_SERVER = ''
    SMTP_PORT = 0

    DEV_EMAIL = ''
    ADMIN_USER_NAME = ''
    ADMIN_PASSWORD = ''
    SEND_EMAIL_DIR_IBIS = ''
    OWNER_EMAIL = ''
else:
    SECRET_KEY = getenv('SECRET_KEY')
    TOKEN = getenv('TOKEN')
    ACCOUNT = getenv('ACCOUNT')
    PARTITION = getenv('PARTITION')
    USE_OLD_SUBMITER = int(getenv('USE_OLD_SUBMITER'))

    LOGIN_NODE_URLS = getenv('LOGIN_NODE_URLS')
    USER_NAME = getenv('USER_NAME')
    USER_ID = getenv('USER_ID')
    USER_PASSWORD = getenv('USER_PASSWORD')
    ADMIN_EMAIL = getenv('ADMIN_EMAIL')
    SMTP_SERVER = getenv('SMTP_SERVER')
    SMTP_PORT = int(getenv('SMTP_PORT'))

    DEV_EMAIL = getenv('DEV_EMAIL')
    ADMIN_USER_NAME = getenv('ADMIN_USER_NAME')
    ADMIN_PASSWORD = getenv('ADMIN_PASSWORD')
    SEND_EMAIL_DIR_IBIS = getenv('SEND_EMAIL_DIR_IBIS')
    OWNER_EMAIL = getenv('OWNER_EMAIL')


class FlaskConfig:

    # RECAPTCHA_SITE_KEY: str
    # RECAPTCHA_SECRET_KEY: str
    SECRET_KEY: str
    DEBUG: bool
    PREFERRED_URL_SCHEME: str
    SERVER_NAME = str
    APPLICATION_ROOT = str
    # UPLOAD_FOLDERS_ROOT_PATH: str
    MAX_CONTENT_LENGTH: int

    def __init__(self, **attributes):
        self.SECRET_KEY = SECRET_KEY
        self.DEBUG = DEBUG
        self.PREFERRED_URL_SCHEME = PREFERRED_URL_SCHEME
        self.SERVER_NAME = SERVER_NAME
        self.APPLICATION_ROOT = APPLICATION_ROOT
        self.MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
        if attributes:
            for key, value in attributes.items():
                setattr(self, key, value)


class Actions:

    def __init__(self, **attributes):
        if attributes:
            for key, value in attributes.items():
                if type(value) in (FunctionType, MethodType):
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

    def update(self, *args, **kwargs) -> None:
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)
        if args:
            for arg in args:
                if isinstance(arg, dict):
                    for key, value in arg.items():
                        setattr(self, key, value)


COMMAND_LINE = argv

DEFAULT_FORM_ARGUMENTS = {
    'categories_quantity': 4,
    'alpha': 0.5,
    'pi_1': 0.5,
    'coefficient_bl': 1.0,
    'e_mail': '',
    'is_optimize_pi': True,
    'is_optimize_pi_average': False,
    'is_optimize_alpha': True,
    'is_optimize_bl': True,
    'is_do_not_use_e_mail': True
    }

DEFAULT_ARGUMENTS = DefaultArgs(**{
    'with_internal_nodes': True,
    'sep': '\t'
    })

DEFAULT_ARGUMENTS.update(DEFAULT_FORM_ARGUMENTS)

ACTIONS = Actions(**{
                     'check_data': check_data,
                     'check_tree': Tree.rename_nodes,
                     'set_tree_data': Tree.set_tree_data,
                     'compute_likelihood_of_tree': compute_likelihood_of_tree,
                     'calculate_tree_for_fasta': Tree.calculate_tree_for_fasta,
                     'calculate_ancestral_sequence': Tree.calculate_ancestral_sequence,
                     'draw_tree': draw_tree,
                     'create_all_file_types': create_all_file_types,
                     'execute_all_actions': execute_all_actions,
                     'recompile_json': recompile_json
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
    'execute_all_actions': False,
    'recompile_json': False
    }


CALCULATED_ARGS = CalculatedArgs(**{
                                    'file_path': None,
                                    'newick_text': None,
                                    'msa': None,
                                    'newick_tree': None
                                    })

USAGE = '''\tRequired parameters:
\t\t--msa_file <type=str>
\t\t\tSpecify the msa filepath.
\t\t--tree_file <type=str>
\t\t\tSpecify the newick filepath.
\tOptional parameters:
\t\t--out_dir <type=str>
\t\t\tSpecify the outdir path.
\t\t--process_id <type=str>
\t\t\tSpecify a process ID or it will be generated automatically.
\t\t--mode <type=str>
\t\t\tExecution mode style. Possible options: ('draw_tree', 'compute_likelihood_of_tree', 
\t\t\t'create_all_file_types', 'execute_all_actions'). Default is 'execute_all_actions'.
\t\t--with_internal_nodes <type=int> 
\t\t\tSpecify the tree has internal nodes. Default is 1.
\t\t--categories_quantity <type=int>
\t\t\tSpecify categories quantity. Default is 4.
\t\t--alpha <type=float>
\t\t\tSpecify alpha. Default is 0.5.
\t\t--pi_1 <type=float> 
\t\t\tSpecify pi_1. Default is 0.5.
\t\t--coefficient_bl <type=float> 
\t\t\tSpecify coefficient_bl. Default is 1.0.
\t\t--e_mail <type=str> 
\t\t\tSpecify e_mail. Default is ''.
\t\t--is_optimize_pi <type=int> 
\t\t\tSpecify is_optimize_pi. Default is 1.
\t\t--is_optimize_pi_average <type=int> 
\t\t\tSpecify is_optimize_pi_average. Default is 0.
\t\t--is_optimize_alpha <type=int> 
\t\t\tSpecify is_optimize_alpha. Default is 1.
\t\t--is_optimize_bl <type=int> 
\t\t\tSpecify is_optimize_bl. Default is 1.
\t\t--is_do_not_use_e_mail <type=int> 
\t\t\tSpecify is_do_not_use_e_mail. Default is 1.
\t\t--is_request <type=int> 
\t\t\tSpecify is_request (technical parameter, do not change).'''

MENU = ({'name': 'Home', 'url': 'index',
         'submenu': ()
         },
        {'name': 'Overview', 'url': 'overview',
         'submenu': ()
         },
        {'name': 'Faq', 'url': 'faq',
         'submenu': ()
         },
        {'name': 'Gallery', 'url': 'gallery',
         'submenu': ()
         },
        {'name': 'Source code', 'url': 'source_code',
         'submenu': ()
         },
        {'name': 'Citing & credits', 'url': 'citing_and_credits',
         'submenu': ()
         }
        )
