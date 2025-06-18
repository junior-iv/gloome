from SharedConsts import *
from utils import *
from typing import Optional, Type, ClassVar


SERVERS_RESULTS_DIR = path.join(STATIC_DIR, 'results')
# SERVERS_LOGS_DIR = path.join(STATIC_DIR, 'logs')
SERVERS_LOGS_DIR = path.join(STATIC_DIR, 'logs')
# SERVERS_LOGS_DIR = path.join(STATIC_DIR, 'logs')


class WebConfig:
    PREFERRED_URL_SCHEME: str
    WEBSERVER_NAME_CAPITAL: str
    WEBSERVER_NAME: str
    WEBSERVER_URL: str
    WEBSERVER_TITLE: str
    WEBSERVER_DIR: str
    WEBSERVER_STATIC_DIR: str
    MODULE_LOAD: str
    PRODJECT_DIR: str
    ENVIRONMENT_DIR: str
    ENVIRONMENT_ACTIVATE: str
    BIN_DIR: str
    SCRIPT_DIR: str
    SRC_DIR: str
    INITIAL_DATA_DIR: str
    SERVERS_RESULTS_DIR: str
    APP_DIR: str
    TEMPLATES_DIR: str
    ERROR_TEMPLATE: str
    MSA_FILE_NAME: str
    TREE_FILE_NAME: str
    INPUT_DIR_NAME: str
    OUTPUT_DIR_NAME: str

    PROCESS_ID: Optional[str]
    JOB_ID: Optional[str]
    SERVERS_INPUT_DIR: Optional[str]
    INPUT_MSA_FILE: Optional[str]
    INPUT_TREE_FILE: Optional[str]
    SERVERS_OUTPUT_DIR: Optional[str]
    WEBSERVER_RESULTS_URL: Optional[str]
    WEBSERVER_LOG_URL: Optional[str]
    SERVERS_LOGS_DIR: Optional[str]
    JOB_LOGGER: Optional['logging']
    LOGGER: Optional['logging']

    def __init__(self, **attributes):
        self.PREFERRED_URL_SCHEME = PREFERRED_URL_SCHEME
        self.WEBSERVER_NAME_CAPITAL = WEBSERVER_NAME_CAPITAL
        self.WEBSERVER_NAME = WEBSERVER_NAME
        self.WEBSERVER_URL = WEBSERVER_URL
        self.WEBSERVER_TITLE = WEBSERVER_TITLE
        self.WEBSERVER_DIR = WEBSERVER_DIR
        self.WEBSERVER_STATIC_DIR = WEBSERVER_STATIC_DIR
        self.MODULE_LOAD = MODULE_LOAD
        self.PRODJECT_DIR = PRODJECT_DIR
        self.ENVIRONMENT_DIR = ENVIRONMENT_DIR
        self.ENVIRONMENT_ACTIVATE = ENVIRONMENT_ACTIVATE
        self.BIN_DIR = BIN_DIR
        self.SCRIPT_DIR = SCRIPT_DIR
        self.SRC_DIR = SRC_DIR
        self.INITIAL_DATA_DIR = INITIAL_DATA_DIR
        self.SERVERS_RESULTS_DIR = SERVERS_RESULTS_DIR
        self.APP_DIR = APP_DIR
        self.TEMPLATES_DIR = TEMPLATES_DIR
        self.ERROR_TEMPLATE = ERROR_TEMPLATE

        self.MSA_FILE_NAME = MSA_FILE_NAME
        self.TREE_FILE_NAME = TREE_FILE_NAME
        self.INPUT_DIR_NAME = INPUT_DIR_NAME
        self.OUTPUT_DIR_NAME = OUTPUT_DIR_NAME

        self.PROCESS_ID = None
        self.JOB_ID = None
        self.SERVERS_INPUT_DIR = None
        self.INPUT_MSA_FILE = None
        self.INPUT_TREE_FILE = None
        self.SERVERS_OUTPUT_DIR = None
        self.WEBSERVER_RESULTS_URL = None
        self.WEBSERVER_LOG_URL = None
        self.SERVERS_LOGS_DIR = None
        self.JOB_LOGGER = None
        self.LOGGER = logger

        if attributes:
            for key, value in attributes.items():
                if key == 'PROCESS_ID':
                    self.change_process_id(value)
                else:
                    setattr(self, key, value)
        if self.PROCESS_ID is None:
            self.change_process_id(get_new_process_id())

    def set_job_logger_info(self, log_msg: str):
        self.LOGGER.info(log_msg)
        self.JOB_LOGGER.info(log_msg)

    def change_process_id(self, process_id: str):
        self.PROCESS_ID = process_id

        self.SERVERS_RESULTS_DIR = path.join(SERVERS_RESULTS_DIR, self.PROCESS_ID)
        self.SERVERS_INPUT_DIR = path.join(self.SERVERS_RESULTS_DIR, INPUT_DIR_NAME)
        self.check_dir(self.SERVERS_INPUT_DIR)
        self.INPUT_MSA_FILE = path.join(self.SERVERS_INPUT_DIR, self.MSA_FILE_NAME)
        self.INPUT_TREE_FILE = path.join(self.SERVERS_INPUT_DIR, self.TREE_FILE_NAME)
        self.SERVERS_OUTPUT_DIR = path.join(self.SERVERS_RESULTS_DIR, OUTPUT_DIR_NAME)
        self.check_dir(self.SERVERS_OUTPUT_DIR)
        self.SERVERS_LOGS_DIR = SERVERS_LOGS_DIR

        self.WEBSERVER_RESULTS_URL = path.join(WEBSERVER_RESULTS_URL, self.PROCESS_ID)
        self.WEBSERVER_LOG_URL = path.join(WEBSERVER_LOG_URL, self.PROCESS_ID)
        self.JOB_LOGGER = get_job_logger(f'f{process_id}', self.SERVERS_LOGS_DIR)
        self.set_job_logger_info(f'process_id = {process_id}')

    @staticmethod
    def check_dir(file_path: str):
        if not path.exists(file_path):
            makedirs(file_path)


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
        self.SERVER_NAME = WEBSERVER_NAME
        self.APPLICATION_ROOT = APPLICATION_ROOT
        self.MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
        if attributes:
            for key, value in attributes.items():
                setattr(self, key, value)
