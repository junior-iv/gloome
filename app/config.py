import requests

from time import sleep
from utils import *
from script.service_functions import read_file, loads_json, create_file, result_design
from flask import url_for
from typing import Optional, Any, Set


SERVERS_RESULTS_DIR = path.join(STATIC_DIR, 'results')
SERVERS_LOGS_DIR = path.join(SERVERS_RESULTS_DIR, 'logs')
IN_DIR = path.join(SERVERS_RESULTS_DIR, 'in')
OUT_DIR = path.join(SERVERS_RESULTS_DIR, 'out')


class WebConfig:
    def __init__(self, **attributes):
        self.PARTITION = PARTITION
        self.MODULE_LOAD = MODULE_LOAD
        self.PRODJECT_DIR = PRODJECT_DIR
        self.ENVIRONMENT_DIR = ENVIRONMENT_DIR
        self.ENVIRONMENT_ACTIVATE = ENVIRONMENT_ACTIVATE

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

        self.CURRENT_ARGS = DEFAULT_ARGUMENTS
        self.CURRENT_ARGS.update(DEFAULT_FORM_ARGUMENTS)

        self.ACTIONS = ACTIONS
        self.DEFAULT_ACTIONS = DEFAULT_ACTIONS

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

        self.HISTORY = list()
        self.CURRENT_JOB = None
        self.OUTPUT_FILE = None
        self.MODE = None
        self.COMMAND_LINE = None

        # self.LOGGER = logger
        self.JOBS_NUMBER = JobsCounter()
        if USE_OLD_SUBMITER:
            self.SUBMITER = SlurmSubmiter()
        else:
            self.SUBMITER = SawSubmiter()

        if attributes:
            for key, value in attributes.items():
                if key == 'PROCESS_ID':
                    self.change_process_id(value)
                else:
                    setattr(self, key, value)
        if self.PROCESS_ID is None:
            self.change_process_id(get_new_process_id())

    def set_job_logger_info(self, log_msg: str):
        # self.LOGGER.info(log_msg)
        self.JOB_LOGGER.info(log_msg)

    def change_process_id(self, process_id: str):
        self.PROCESS_ID = process_id

        self.SERVERS_RESULTS_DIR = SERVERS_RESULTS_DIR
        self.SERVERS_LOGS_DIR = SERVERS_LOGS_DIR
        self.check_dir(self.SERVERS_LOGS_DIR)

        self.OUT_DIR = path.join(self.OUT_DIR, self.PROCESS_ID)
        self.IN_DIR = path.join(self.IN_DIR, self.PROCESS_ID)
        self.check_dir(self.IN_DIR)
        self.OUTPUT_FILE = path.join(self.OUT_DIR, f'result.json')

        self.MSA_FILE = path.join(self.IN_DIR, self.MSA_FILE_NAME)
        self.TREE_FILE = path.join(self.IN_DIR, self.TREE_FILE_NAME)

        self.CALCULATED_ARGS.file_path = self.OUT_DIR

        self.WEBSERVER_RESULTS_URL = path.join(WEBSERVER_RESULTS_URL, self.PROCESS_ID)
        self.WEBSERVER_LOG_URL = path.join(WEBSERVER_LOG_URL, self.PROCESS_ID)
        self.JOB_LOGGER = get_job_logger(f'{process_id}', self.SERVERS_LOGS_DIR)
        self.set_job_logger_info(f'\n\tPROCESS ID: {process_id}\n'
                                 f'\tSUBMITER: {self.SUBMITER}\n'
                                 # f'\tSERVERS_RESULTS_DIR: {self.SERVERS_RESULTS_DIR}\n'
                                 # f'\tSERVERS_LOGS_DIR: {self.SERVERS_LOGS_DIR}\n'
                                 # f'\tMSA_FILE: {self.MSA_FILE}\n'
                                 # f'\tTREE_FILE: {self.TREE_FILE}\n'
                                 # f'\tOUTPUT_FILE: {self.OUTPUT_FILE}\n'
                                 f'\tJOB_LOGGER: {self.JOB_LOGGER}\n'
                                 f'\tWEBSERVER_RESULTS_URL: {self.WEBSERVER_RESULTS_URL}\n'
                                 f'\tWEBSERVER_LOG_URL: {self.WEBSERVER_LOG_URL}\n')

    def arguments_filling(self, **arguments):
        dct = zip(('categoriesQuantity', 'alpha', 'pi1', 'coefficientBL', 'eMail', 'isOptimizePi',
                   'isOptimizePiAverage', 'isOptimizeBL', 'isOptimizeAlpha', 'isDoNotUseEMail'),
                  ('categories_quantity', 'alpha', 'pi_1', 'coefficient_bl', 'e_mail', 'is_optimize_pi',
                   'is_optimize_pi_average', 'is_optimize_bl', 'is_optimize_alpha', 'is_do_not_use_e_mail'),
                  ((int, ), (float, ), (float, ), (float, ), (str, ), (int, bool), (int, bool), (int, bool),
                   (int, bool), (int, bool)))
        for in_key, out_key, current_types in dct:
            current_value = arguments.get(in_key)
            if current_value is not None:
                for current_type in current_types:
                    current_value = current_type(current_value)
                self.CURRENT_ARGS.update({out_key: current_value})

        mode = arguments.get('mode')
        self.MODE = ' '.join(mode)
        self.CALCULATED_ARGS.newick_text = arguments.get('newickText')
        self.CALCULATED_ARGS.msa = arguments.get('msaText')
        self.set_job_logger_info(f'\n\tMODE: {self.MODE}\n'
                                 f'\tcategories_quantity: {self.CURRENT_ARGS.categories_quantity}\n'
                                 f'\talpha: {self.CURRENT_ARGS.alpha}\n'
                                 f'\tpi_1: {self.CURRENT_ARGS.pi_1}\n'
                                 f'\tcoefficient_bl: {self.CURRENT_ARGS.coefficient_bl}\n'
                                 f'\te_mail: {self.CURRENT_ARGS.e_mail}\n'
                                 f'\tis_optimize_pi: {self.CURRENT_ARGS.is_optimize_pi}\n'
                                 f'\tis_optimize_pi_average: {self.CURRENT_ARGS.is_optimize_pi_average}\n'
                                 f'\tis_optimize_alpha: {self.CURRENT_ARGS.is_optimize_alpha}\n'
                                 f'\tis_optimize_bl: {self.CURRENT_ARGS.is_optimize_bl}\n'
                                 f'\tis_do_not_use_e_mail: {self.CURRENT_ARGS.is_do_not_use_e_mail}\n'
                                 f'\tnewick_text: \n{self.CALCULATED_ARGS.newick_text}\n'
                                 f'\tmsa: \n{self.CALCULATED_ARGS.msa}\n')

    def texts_filling(self, replace_path: bool = True) -> None:
        if replace_path:
            self.replace_files_path()
        with open(self.TREE_FILE, 'r') as f:
            self.CALCULATED_ARGS.newick_text = f.read()
        with open(self.MSA_FILE, 'r') as f:
            self.CALCULATED_ARGS.msa = f.read()

    def replace_files_path(self) -> None:
        self.MSA_FILE = self.MSA_FILE.replace(STATIC_DIR, self.PRODJECT_DIR)
        self.TREE_FILE = self.TREE_FILE.replace(STATIC_DIR, self.PRODJECT_DIR)
        self.CALCULATED_ARGS.file_path = self.OUT_DIR.replace(STATIC_DIR, self.PRODJECT_DIR)

    def create_tmp_data_files(self, replace_path: bool = True) -> None:
        self.check_dir(self.CALCULATED_ARGS.file_path)

        create_file(self.MSA_FILE, self.CALCULATED_ARGS.msa)
        create_file(self.TREE_FILE, self.CALCULATED_ARGS.newick_text)

        if replace_path:
            self.replace_files_path()
        self.set_job_logger_info(f'Created msa file: {self.MSA_FILE}')
        self.set_job_logger_info(f'Created newick file: {self.TREE_FILE}')
        self.set_job_logger_info(f'Output files path: {self.CALCULATED_ARGS.file_path}')

    def create_command_line(self) -> None:
        self.COMMAND_LINE = (
            f'python {path.join(".", "script/main.py")} '
            f'--process_id {self.PROCESS_ID} '
            f'--msa_file {self.MSA_FILE} '
            f'--tree_file {self.TREE_FILE} '
            f'--categories_quantity {self.CURRENT_ARGS.categories_quantity} '
            f'--alpha {self.CURRENT_ARGS.alpha} '
            f'--pi_1 {self.CURRENT_ARGS.pi_1} '
            f'--coefficient_bl {self.CURRENT_ARGS.coefficient_bl} '
            f'--e_mail {self.CURRENT_ARGS.e_mail} '
            f'--is_optimize_pi {int(self.CURRENT_ARGS.is_optimize_pi)} '
            f'--is_optimize_pi_average {int(self.CURRENT_ARGS.is_optimize_pi_average)} '
            f'--is_optimize_alpha {int(self.CURRENT_ARGS.is_optimize_alpha)} '
            f'--is_optimize_bl {int(self.CURRENT_ARGS.is_optimize_bl)} '
            f'--is_do_not_use_e_mail {int(self.CURRENT_ARGS.is_do_not_use_e_mail)} '
            f'--mode {self.MODE}')
        self.set_job_logger_info(f'COMMAND_LINE: \n{self.COMMAND_LINE}')

    def get_request_body(self):
        # TODO think about job_name = f'gloome_{self.PROCESS_ID}_{self.JOBS_NUMBER.inc()}'
        # job_name = f'gloome_{self.PROCESS_ID}_{self.JOBS_NUMBER.inc()}'
        job_name = f'gloome_{self.PROCESS_ID}'
        # prefix = f'{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")}_{self.PROCESS_ID}_'
        prefix = f'{self.PROCESS_ID}_'
        tmp_dir = path.join(self.PRODJECT_DIR, 'tmp')
        cmd = (f'#!/bin/bash\n'
               f'source ~/.bashrc\n'
               f'cd /lsweb/rodion/gloome/\n'
               f'echo "Loading module..."\n'
               f'{self.MODULE_LOAD}\n'
               f'echo "Activating env..."\n'
               f'{self.ENVIRONMENT_ACTIVATE}\n'
               f'echo "Executing python script..."\n'
               f'{self.COMMAND_LINE}')
        job_slurm = {
                'name': job_name,
                'partition': self.PARTITION,
                'account': 'pupkoweb-users',
                'tasks': 1,
                'nodes': '1',
                'cpus_per_task': 1,
                'memory_per_node': {'number': 6144, 'set': True},
                'time_limit': {'number': 10080, 'set': True},
                'current_working_directory': tmp_dir,
                'standard_output': path.join(tmp_dir, f'{prefix}output.txt'),
                'standard_error': path.join(tmp_dir, f'{prefix}error.txt'),
                'environment': [
                    f'PATH={self.ENVIRONMENT_DIR}/bin:/powerapps/share/rocky8/mamba/mamba-1.5.8/condabin:'
                    f'mamba/condabin:/powerapps/share/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:'
                    f'/usr/local.cc/bin:/powerapps/share/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:'
                    f'/usr/local.cc/bin'
                ]
            }
        job_saw = {
                'script': cmd,
                'partition': self.PARTITION,
                'name': f'{job_name}',
                'tasks': 1,
                'nodes': 1,
                'cpus_per_task': 1,
                'memory_per_node': 6144,
                'current_working_directory': tmp_dir,
                'standard_output': path.join(tmp_dir, f'{prefix}output.txt'),
                'standard_error': path.join(tmp_dir, f'{prefix}error.txt'),
                'environment': [
                    f'PATH={self.ENVIRONMENT_DIR}/bin:/powerapps/share/rocky8/mamba/mamba-1.5.8/condabin:'
                    f'mamba/condabin:/powerapps/share/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:'
                    f'/usr/local.cc/bin:/powerapps/share/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:'
                    f'/usr/local.cc/bin'
                ]
            }
        body = {'SlurmSubmiter': {'script': cmd, 'job': job_slurm}, 'SawSubmiter': job_saw}

        return body.get(self.SUBMITER.get_name())

    def get_response_design(self, json_object: Optional[Any], action_name: str) -> Optional[Any]:
        if 'create_all_file_types' in action_name:
            json_object = self.link_design(json_object)
        # if 'draw_tree' not in action_name:
            json_object = result_design(json_object, change_value='compute_likelihood_of_tree' in action_name,
                                        change_value_style=False, change_key=True, change_key_style=False)
        return json_object

    def read_response(self) -> Any:
        file_contents = read_file(file_path=self.OUTPUT_FILE)
        json_object = loads_json(file_contents)
        action_name = json_object.get('action_name')
        data = json_object.get('data')

        if 'execute_all_actions' in action_name:
            for key, value in data.items():
                data.update({key: self.get_response_design(value, key)})
            pass
        else:
            data = self.get_response_design(data, action_name)

        data.update({'title': self.PROCESS_ID})
        data.update({'form_data': json_object.get('form_data')})

        return data

    def get_response(self) -> Optional[Any]:
        self.create_command_line()
        request_body = self.get_request_body()

        self.CURRENT_JOB = self.SUBMITER.submit_job(json=request_body).get('job_id', self.JOBS_NUMBER.value)
        self.HISTORY.append(self.CURRENT_JOB)
        self.set_job_logger_info(f'\nSubmit job (id: {self.CURRENT_JOB})'
                                 f'\nRequest body: {request_body}\n')

        job_state = self.SUBMITER.check_job_state(self, count=REQUESTS_NUMBER, waiting_time=REQUEST_WAITING_TIME)

        if job_state:
            self.set_job_logger_info(f'Result file: {self.OUTPUT_FILE}\n')
            return self.read_response()
        return ''

    @staticmethod
    def link_design(json_object: Any):
        for key, value in json_object.items():
            if key == 'execution_time':
                continue
            json_object.update(
                {f'{key}': [f'<a class="w-auto mw-auto form-control btn btn-outline-link rounded-pill" '
                            f'href="{url_for("get_file", file_path=value, mode="download")}" '
                            f'target="_blank">download</a>',
                            f'<a class="w-auto mw-auto form-control btn btn-outline-link rounded-pill" '
                            f'href="{url_for("get_file", file_path=value, mode="view")}" '
                            f'target="_blank">view</a>']})
        return json_object

    @staticmethod
    def check_dir(file_path: str, **kwargs):
        if not path.exists(file_path):
            makedirs(file_path, **kwargs)


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


class SawSubmiter:
    def __init__(self):
        self.current_user = USER_NAME
        self.bearer_token = TOKEN
        self.partition = PARTITION

        self.base_url_auth = 'https://saw.tau.ac.il'
        self.api = f"{self.base_url_auth}/slurmapi"

    def __str__(self) -> str:
        return self.get_name()

    def get_name(self) -> str:
        return f'{self.__class__.__name__}'

    def exec_request(self, url: str, method: str = 'GET', **kwargs):
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'X-USERNAME': self.current_user
            }
        response = requests.request(method, url, headers=headers, **kwargs)

        return response

    def get_list_jobs(self, **kwargs):
        """
                Query Parameters
                To avoid performance issues, at least one filter must be provided. The API does not allow unfiltered job
                listings.

            params = {
                'partition':    '(str) '    'Filter by partition name',
                'nodes':        '(str) '    'Filter by node name',
                'gres_used':    '(str) '    'Filter by GRES used',
                'job_user':     '(str) '    'Filter by the SLURM user who submitted the job',
                'job_state':    '(str) '    'Filter by job state (e.g. RUNNING, COMPLETED, FAILED, etc.)'
            }
        """
        url = f'{self.api}/jobs/'
        return self.exec_request(url, **kwargs)

    def get_job(self, job_id, **kwargs):
        """
            job_id = (int) ID of the job to retrieve from history
        """
        url = f'{self.api}/job/{job_id}/'
        return self.exec_request(url, **kwargs)

    def get_jobs_history(self, **kwargs):
        """
            params = {
                'users':                '(str) '    'CSV list of SLURM usernames',
                'account':              '(str) '    'CSV list of SLURM accounts',
                'state':                '(str) '    'CSV list of job states (e.g. COMPLETED, FAILED)',
                'partition':            '(str) '    'CSV list of partition names',
                'job_name':             '(str) '    'CSV list of job names',
                'start_time':           '(str) '    'Start time (e.g. 2024-01-01 or 2024-01-01T08:00)',
                'end_time':             '(str) '    'End time (e.g. 2024-03-01)',
                'skip_steps':           '(bool) '   'Whether to exclude step-level data (true or false)',
                'show_batch_script':    '(bool) '   'Whether to include the job script in the response',
                'show_job_environment': '(bool) '   'Whether to include the job environment in the response'
            }
        """
        url = f'{self.api}/jobs/history/'
        return self.exec_request(url, **kwargs)

    def get_job_history(self, job_id, **kwargs):
        """
            job_id = (int) ID of the job to retrieve from history
        """
        url = f'{self.api}/jobs/history/{job_id}/'
        return self.exec_request(url, **kwargs)

    def submit_job(self, **kwargs):
        """
            params = {
                'script':                       '(str, Required) '  'Bash script to execute. This script is
                                                'automatically wrapped with #!/bin/bash and source ~/.bashrc by the '
                                                'API, so you do not need to include them manually.',
                'partition':                    '(str, Required) '  'SLURM partition to use',
                'tasks':                        '(int) '            'Number of tasks (default: 1)',
                'name':                         '(str) '            'Job name (default: slurmapi_job)',
                'nodes':                        '(int) '            'Number of nodes (default: 1)',
                'cpus_per_task':                '(int) '            'CPUs per task (default: 2)',
                'memory_per_node':              '(int) '            'Memory per node in MB (default: 1024)',
                'standard_output':              '(str, Required) '  'Path for standard output',
                'standard_error':               '(str, Required) '  'Path for standard error',
                'current_working_directory':    '(str) '            'Working directory (default: /tmp/)',
                'environment':                  '(str, list) '      'Environment variables (optional)'
            }
        """
        url = f'{self.api}/job/submit/'
        response = self.exec_request(url, method='POST', **kwargs)
        if response.status_code == 200:
            return response.json()  # Assuming the token is returned in JSON format
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def check_job_state(self, conf: WebConfig, state: Union[Tuple[str, ...], List[str], Set[str], str] = 'COMPLETED',
                        count: int = 50, waiting_time: int = 10) -> str:
        while count:
            try:
                job_info = self.get_job(conf.CURRENT_JOB)
            except Exception:
                sleep(waiting_time)
                continue

            job_state = job_info.json().get('job_state', 'RUNNING')
            state_filter = ['FAILED']
            state_filter.append(state) if isinstance(state, str) else state_filter.extend(state)
            if job_state in state_filter:
                conf.set_job_logger_info(f'Job state: {job_state}')
                return job_state
            count -= 1
            sleep(waiting_time)
        return ''


class SlurmSubmiter:
    def __init__(self):
        self.current_user = USER_NAME
        self.api_key = SECRET_KEY

        self.base_url_auth = 'https://slurmtron.tau.ac.il'
        self.api = f'{self.base_url_auth}/slurmrestd'
        self.generate_token_url = f'{self.base_url_auth}/slurmapi/generate-token/'

    def __str__(self) -> str:
        return self.get_name()

    def get_name(self) -> str:
        return f'{self.__class__.__name__}'

    def generate_token(self):

        """
        Retrieves an API token for SLURM REST API access.

        Parameters:
        url (str): The URL endpoint for obtaining the API token.
        username (str): The username of the user requesting the token.
        api_key (str): The API key provided by the HPC team.

        Returns:
        str: The API token if the request is successful.

        Raises:
        Exception: If the request fails with a non-200 status code.
        """

        payload = {
            'username': self.current_user,
            'api_key': self.api_key
        }
        response = requests.post(self.generate_token_url, data=payload)

        if response.status_code == 200:
            return response.json()  # Assuming the token is returned in JSON format
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def get_token(self):
        return self.generate_token()['SlurmJWT']

    def exec_request(self, url, method: str = 'GET', **kwargs):
        headers = {
            'X-SLURM-USER-NAME': self.current_user,
            'X-SLURM-USER-TOKEN': self.get_token()
            }
        response = requests.request(method, url, headers=headers, **kwargs)

        return response

    def get_job_state(self, job_id):
        url = f'{self.api}/slurm/v0.0.41/job/{job_id}'

        return self.exec_request(url)

    def get_jobs_state(self):
        url = f'{self.api}/slurm/v0.0.41/jobs/state'

        return self.exec_request(url)

    def ping(self):
        url = f'{self.api}/slurm/v0.0.41/ping'
        return self.exec_request(url)

    def get_jobs(self):
        url = f'{self.api}/slurm/v0.0.41/jobs'

        return self.exec_request(url)

    def submit_job(self, payload, **kwargs):
        url = f'{self.api}/slurm/v0.0.41/job/submit'
        response = self.exec_request(url, method='POST', json=payload, **kwargs)
        if response.status_code == 200:
            return response.json()  # Assuming the token is returned in JSON format
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def check_job_state(self, conf: WebConfig, state: Union[Tuple[str, ...], List[str], Set[str], str] = 'COMPLETED',
                        count: int = 50, waiting_time: int = 10) -> bool:
        while count:
            try:
                job_info = self.get_job_state(conf.CURRENT_JOB)
            except Exception:
                sleep(waiting_time)
                continue

            job_state = ''.join(self.find_in_json(job_info.json(), key='job_state', return_dict=False))
            state_filter = ['FAILED']
            state_filter.append(state) if isinstance(state, str) else state_filter.extend(state)
            if job_state in state_filter:
                conf.set_job_logger_info(f'Job state: {job_state}')
                return job_state in state
            count -= 1
            sleep(waiting_time)
        return False

    @classmethod
    def find_in_json(cls, data: Any, key: Union[bool, int, float, str], value: Optional[Any] = None,
                     return_dict: bool = True) -> Optional[Union[bool, int, float, str]]:
        if isinstance(data, dict):
            if key in data:
                if value is None or data.get(key) == value:
                    return data if return_dict else data.get(key)
            for i in data.values():
                result = cls.find_in_json(i, key, value, return_dict)
                if result is not None:
                    return result
        elif isinstance(data, list):
            for i in data:
                result = cls.find_in_json(i, key, value, return_dict)
                if result is not None:
                    return result
        return None


class JobsCounter:
    def __init__(self, value: int = 0):
        self.value = value

    def inc(self):
        self.value += 1

        return self.value

    def dec(self):
        self.value -= 1

        return self.value
