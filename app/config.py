import requests

from os import scandir
from time import sleep
from typing import Set, Any, Optional, Dict

from smtplib import SMTP, SMTP_SSL
from ssl import create_default_context
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from utils import *
from script.service_functions import read_file, loads_json, create_file, get_variables, check_data, get_error
from app.flask_app import *


class WebConfig:
    def __init__(self, **attributes):
        self.ACCOUNT = ACCOUNT
        self.PARTITION = PARTITION
        self.MODULE_LOAD = MODULE_LOAD
        self.ENVIRONMENT_DIR = ENVIRONMENT_DIR
        self.ENVIRONMENT_ACTIVATE = ENVIRONMENT_ACTIVATE

        self.BIN_DIR = BIN_DIR
        self.IN_DIR = IN_DIR
        self.OUT_DIR = OUT_DIR

        self.CURRENT_ARGS = DEFAULT_ARGUMENTS

        self.MSA_FILE_NAME = MSA_FILE_NAME
        self.TREE_FILE_NAME = TREE_FILE_NAME

        self.CALCULATED_ARGS = CALCULATED_ARGS

        self.USE_ATTACHMENTS = False

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
            self.change_process_id()

    def change_process_id(self, process_id: Optional[str] = None):
        self.PROCESS_ID = self.get_new_process_id() if process_id is None else process_id

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
        self.JOB_LOGGER = get_job_logger(f'{self.PROCESS_ID}', self.SERVERS_LOGS_DIR)
        if process_id is None:
            self.JOB_LOGGER.info(f'\n\tcreate a new instance of the WebConfig class'
                                 f'\n\tPROCESS ID: {self.PROCESS_ID}'
                                 f'\n\tSUBMITER: {self.SUBMITER}'
                                 f'\n\tWEBSERVER_RESULTS_URL: {self.WEBSERVER_RESULTS_URL}'
                                 f'\n\tWEBSERVER_LOG_URL: {self.WEBSERVER_LOG_URL}\n')

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
        self.JOB_LOGGER.info(f'\n\tpopulate arguments from web page data'
                             f'\n\tMODE: {self.MODE}'
                             f'\n\tcategories_quantity: {self.CURRENT_ARGS.categories_quantity}'
                             f'\n\talpha: {self.CURRENT_ARGS.alpha}'
                             f'\n\tpi_1: {self.CURRENT_ARGS.pi_1}'
                             f'\n\tcoefficient_bl: {self.CURRENT_ARGS.coefficient_bl}'
                             f'\n\te_mail: {self.CURRENT_ARGS.e_mail}'
                             f'\n\tis_optimize_pi: {self.CURRENT_ARGS.is_optimize_pi}'
                             f'\n\tis_optimize_pi_average: {self.CURRENT_ARGS.is_optimize_pi_average}'
                             f'\n\tis_optimize_alpha: {self.CURRENT_ARGS.is_optimize_alpha}'
                             f'\n\tis_optimize_bl: {self.CURRENT_ARGS.is_optimize_bl}'
                             f'\n\tis_do_not_use_e_mail: {self.CURRENT_ARGS.is_do_not_use_e_mail}'
                             f'\n\tnewick_text: {self.CALCULATED_ARGS.newick_text}'
                             f'\n\tmsa: {self.CALCULATED_ARGS.msa}\n')

    def texts_filling(self) -> None:
        # def texts_filling(self, replace_path: bool = True) -> None:
        # if replace_path:
        #     self.replace_files_path()
        with open(self.TREE_FILE, 'r') as f:
            self.CALCULATED_ARGS.newick_text = f.read().strip()
        with open(self.MSA_FILE, 'r') as f:
            self.CALCULATED_ARGS.msa = f.read().strip()

    def create_tmp_data_files(self) -> None:
        self.check_dir(self.CALCULATED_ARGS.file_path)

        create_file(self.MSA_FILE, self.CALCULATED_ARGS.msa)
        create_file(self.TREE_FILE, self.CALCULATED_ARGS.newick_text)

        self.JOB_LOGGER.info(f'\n\tcreate input data files'
                             f'\n\tCreated msa file: {self.MSA_FILE}'
                             f'\n\tCreated newick file: {self.TREE_FILE}'
                             f'\n\tOutput files path: {self.CALCULATED_ARGS.file_path}\n')

    def create_command_line(self) -> None:
        if self.CURRENT_ARGS.e_mail:
            e_mail = f'--e_mail {self.CURRENT_ARGS.e_mail} '
            is_do_not_use_e_mail = f'--is_do_not_use_e_mail {int(self.CURRENT_ARGS.is_do_not_use_e_mail)} '
        else:
            e_mail = is_do_not_use_e_mail = ''
        self.COMMAND_LINE = (
            f'python {path.join(".", "script/main.py")} '
            f'--process_id {self.PROCESS_ID} '
            f'--msa_file {self.MSA_FILE} '
            f'--tree_file {self.TREE_FILE} '
            f'--categories_quantity {self.CURRENT_ARGS.categories_quantity} '
            f'--alpha {self.CURRENT_ARGS.alpha} '
            f'--pi_1 {self.CURRENT_ARGS.pi_1} '
            f'--coefficient_bl {self.CURRENT_ARGS.coefficient_bl} '
            f'{e_mail}'
            f'--is_optimize_pi {int(self.CURRENT_ARGS.is_optimize_pi)} '
            f'--is_optimize_pi_average {int(self.CURRENT_ARGS.is_optimize_pi_average)} '
            f'--is_optimize_alpha {int(self.CURRENT_ARGS.is_optimize_alpha)} '
            f'--is_optimize_bl {int(self.CURRENT_ARGS.is_optimize_bl)} '
            f' {is_do_not_use_e_mail} '
            f'--mode {self.MODE}')
        self.JOB_LOGGER.info(f'\n\tcreate a command line: '
                             f'\n\tCOMMAND_LINE: {self.COMMAND_LINE}\n')

    def get_request_body(self):
        # TODO think about job_name = f'gloome_{self.PROCESS_ID}_{self.JOBS_NUMBER.inc()}'
        # job_name = f'gloome_{self.PROCESS_ID}_{self.JOBS_NUMBER.inc()}'
        job_name = f'gloome_{self.PROCESS_ID}'
        # prefix = f'{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")}_{self.PROCESS_ID}_'
        prefix = f'{self.PROCESS_ID}_'
        tmp_dir = path.join(self.BIN_DIR, 'tmp')
        cmd = (f'#!/bin/bash\n'
               f'source ~/.bashrc\n'
               f'cd {self.BIN_DIR}\n'
               f'echo "Loading module..."\n'
               f'{self.MODULE_LOAD}\n'
               f'echo "Activating env..."\n'
               f'{self.ENVIRONMENT_ACTIVATE}\n'
               f'echo "Executing python script..."\n'
               f'{self.COMMAND_LINE}')
        job_slurm = {'script': cmd,
                     'job': {
                         'name': job_name,
                         'partition': self.PARTITION,
                         'account': self.ACCOUNT,
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
                             f'/usr/local.cc/bin:/powerapps/share/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:'
                             f'/usr/sbin:/usr/local.cc/bin'
                         ]
                     }}
        job_saw = {
                'script': cmd,
                'partition': self.PARTITION,
                'qos': 'owner',
                'name': f'{job_name}',
                'tasks': 1,
                'nodes': 1,
                'cpus_per_task': 1,
                'memory_per_node': 6144,
                'time_limit': 10080,
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
        body = {'SlurmSubmiter': job_slurm, 'SawSubmiter': job_saw}

        return body.get(self.SUBMITER.get_name())
    #
    # def get_response_design(self, json_object: Optional[Any], action_name: str) -> Optional[Any]:
    #     if 'create_all_file_types' in action_name:
    #         json_object = self.link_design(json_object)
    #     # if 'draw_tree' not in action_name:
    #         json_object = result_design(json_object, change_value='compute_likelihood_of_tree' in action_name,
    #                                     change_value_style=False, change_key=True, change_key_style=False)
    #     return json_object
    #
    # def create_response(self) -> Any:
    #     file_contents = read_file(file_path=self.OUTPUT_FILE)
    #     json_object = loads_json(file_contents)
    #     action_name = json_object.pop('action_name')
    #     data = json_object.pop('data')
    #
    #     if 'execute_all_actions' in action_name:
    #         for key, value in data.items():
    #             data.update({key: get_response_design(value, key)})
    #         pass
    #     else:
    #         data = get_response_design(data, action_name)
    #
    #     data.update({'title': self.PROCESS_ID})
    #     data.update({'form_data': json_object.pop('form_data')})
    #     data.update({'action_name': action_name})
    #     create_file(file_path=self.OUTPUT_FILE, data=data)
    #
    #     return data

    def read_response(self) -> Any:
        file_contents = read_file(file_path=self.OUTPUT_FILE)
        json_object = loads_json(file_contents)

        return json_object

    def get_response(self) -> Optional[Any]:
        self.create_command_line()
        request_body = self.get_request_body()

        self.CURRENT_JOB = self.SUBMITER.submit_job(json=request_body).get('job_id', self.JOBS_NUMBER.value)
        self.HISTORY.append(self.CURRENT_JOB)
        self.JOB_LOGGER.info(f'\n\tregarding the request being processed'
                             f'\n\tSubmit job (id: {self.CURRENT_JOB})'
                             f'\n\tRequest body: {request_body}\n')

        job_state = self.SUBMITER.check_job_state(self, count=REQUESTS_NUMBER, waiting_time=REQUEST_WAITING_TIME)

        mail_sender = MailSenderSMTPLib(name=WEBSERVER_NAME_CAPITAL)
        if job_state == 'COMPLETED' and self.CURRENT_ARGS.e_mail and not self.CURRENT_ARGS.is_do_not_use_e_mail:
            mail_sender.send_results_email(results_files_dir=self.OUT_DIR, use_attachments=self.USE_ATTACHMENTS,
                                           is_error=False, log_file=self.JOB_LOGGER.handlers[-1].baseFilename,
                                           included=('.json', '.zip', '.log', '.html', '.png', 'tsv'),
                                           receiver=self.CURRENT_ARGS.e_mail, name=self.PROCESS_ID)
        if job_state == 'FAILED' and self.CURRENT_ARGS.e_mail and not self.CURRENT_ARGS.is_do_not_use_e_mail:
            mail_sender.send_results_email(results_files_dir=self.OUT_DIR, is_error=True, name=self.PROCESS_ID,
                                           log_file=self.JOB_LOGGER.handlers[-1].baseFilename, included=('.log', ),
                                           receiver=self.CURRENT_ARGS.e_mail, use_attachments=self.USE_ATTACHMENTS)
        if job_state:
            self.JOB_LOGGER.info(f'\n\tJob state: {job_state}\n')
            # self.JOB_LOGGER.info(f'\n\tResult file: {self.OUTPUT_FILE}\n')
            if job_state == 'COMPLETED':
                recompile_json(self.OUTPUT_FILE, self.PROCESS_ID, True)
            # if any((self.CURRENT_ARGS.is_optimize_pi_average, self.CURRENT_ARGS.is_optimize_pi,
            #         self.CURRENT_ARGS.is_optimize_alpha, self.CURRENT_ARGS.is_optimize_bl)):
            #     file_contents = read_file(file_path=self.OUTPUT_FILE)
            #     form_data = loads_json(file_contents).form_data
            #     # self.JOB_LOGGER.info(f'\n\tresults of optimizing π1'
            #     #                      f'\n\tπ1: {self.CALCULATED_ARGS.newick_tree.pi_1}\n')
            #     # self.JOB_LOGGER.info(f'\n\tresults of optimizing α'
            #     #                      f'\n\tα: {self.CALCULATED_ARGS.newick_tree.alpha}\n')
            #     # self.JOB_LOGGER.info(f'\n\tresults of optimizing branch lengths coefficient'
            #     #                      f'\n\tbranch lengths coefficient '
            #     #                      f'{self.CALCULATED_ARGS.newick_tree.coefficient_bl}\n')

            return self.read_response()
        return ''

    @staticmethod
    def check_dir(file_path: str, **kwargs):
        if not path.exists(file_path):
            makedirs(file_path, **kwargs)

    @staticmethod
    def get_new_process_id():
        time_str = str(round(time()))
        rand_str = str(randint(1000, 9999))
        return f'{time_str}{rand_str}'


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
                # conf.JOB_LOGGER.info(f'\n\tJob state: {job_state}\n')
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
        self.version = self.get_version()

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

    def get_version(self, last_version: bool = True):
        versions_info = self.get_versions_info()
        versions = sorted({re.search(r'(v\d+\.\d+\.\d+)', k).group(1)
                           for k in versions_info.json().get('paths').keys()})

        return versions[-1] if last_version else versions

    def get_versions_info(self):
        url = f'{self.api}/openapi/v3'

        return self.exec_request(url)

    def get_job_state(self, job_id):
        url = f'{self.api}/slurm/{self.version}/job/{job_id}'

        return self.exec_request(url)

    def get_jobs_state(self):
        url = f'{self.api}/slurm/{self.version}/jobs/state'

        return self.exec_request(url)

    def ping(self):
        url = f'{self.api}/slurm/{self.version}/ping'
        return self.exec_request(url)

    def get_jobs(self):
        url = f'{self.api}/slurm/{self.version}/jobs'

        return self.exec_request(url)

    def submit_job(self, json, **kwargs):
        url = f'{self.api}/slurm/{self.version}/job/submit'
        response = self.exec_request(url, method='POST', json=json, **kwargs)
        if response.status_code == 200:
            return response.json()  # Assuming the token is returned in JSON format
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def check_job_state(self, conf: WebConfig, state: Union[Tuple[str, ...], List[str], Set[str], str] = 'COMPLETED',
                        count: int = 50, waiting_time: int = 10) -> str:
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
                conf.JOB_LOGGER.info(f'\n\tJob state: {job_state}\n')
                return job_state
            count -= 1
            sleep(waiting_time)
        return ''

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


class MailSenderSMTPLib:
    name: str
    sender: str
    receiver: str
    smtp_server: str
    smtp_port: int
    password: str
    report_receivers: List[str]
    out_dir: str
    results: str
    sender_logger: Any

    def __init__(self, **attributes):
        self.sender = ADMIN_EMAIL
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.password = ADMIN_PASSWORD
        self.report_receivers = REPORT_RECEIVERS
        self.log_files_dir = SERVERS_LOGS_DIR
        self.out_dir = OUT_DIR
        self.results = WEBSERVER_RESULTS_URL
        self.receiver = ''
        self.name = ''

        self.set_attributes(**attributes)
        self.sender_logger = get_job_logger(f'{self.name} {self.sender}', SERVERS_LOGS_DIR)

    def set_attributes(self, **attributes) -> None:
        if attributes:
            for key, value in attributes.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    def create_attachments(self, attachment_path: str, message: MIMEMultipart, use_attachments: bool = False):
        if use_attachments:
            self.add_attachment_to_email(attachment_path, message)
            return ''
        else:
            mode = 'view' if (path.splitext(attachment_path)[-1][1:] in
                              ('txt', 'csv', 'tsv', 'nwk', 'tree', 'dot', 'fasta', 'log', 'png', 'svg', 'jpeg', 'jpg',
                               'html', 'htm', 'json', 'zip', 'rar', '7z', 'gz', 'tgz', 'tar', 'pdf', 'doc', 'dot',
                               'wiz', 'docx', 'xls', 'xlt', 'xla', 'xlsx', 'ppt', 'pps', 'pps', 'pptx', 'ppsx'
                               )) else 'download'
            return (f'\n<a href="{url_for(endpoint="get_file", file_path=attachment_path, mode=mode, _external=True)}" '
                    f'target="_blank">{path.basename(attachment_path)}</a>')

    def send_email(self, subject: str, attachments: Union[Tuple[str, ...], List[str], Dict[str, Tuple[str, ...]],
                   Dict[str, List[str]], str], body: str, use_attachments: bool = False, receiver: Optional[str] = None
                   ) -> None:
        message = MIMEMultipart()
        message["From"] = self.sender
        message["To"] = self.receiver if receiver is None else receiver
        message["Subject"] = subject

        if isinstance(attachments, (tuple, list)):
            for attachment_path in attachments:
                body += f'<br>{self.create_attachments(attachment_path, message, use_attachments)}'
        elif isinstance(attachments, dict):
            for key, value in attachments.items():
                body += f'<br>{key}:'
                for attachment_path in value:
                    if key == 'successful runs':
                        attachment_path = self.create_link_to_results(attachment_path)
                    else:
                        attachment_path = self.create_attachments(attachment_path, message, use_attachments)
                    body += f'<br>{attachment_path}'
        elif isinstance(attachments, str):
            body += f'<br>{self.create_attachments(attachments, message, use_attachments)}'
        self.sender_logger.info(body)
        message.attach(MIMEText(body, 'html'))

        if self.smtp_port == 587:
            with SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=create_default_context())
                server.login(self.sender, self.password)
                server.send_message(message)
        elif self.smtp_port == 465:
            with SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.send_message(message)
        elif self.smtp_port == 0:
            with SMTP(self.smtp_server) as server:
                server.send_message(message)
        elif self.smtp_port == -1:
            with SMTP_SSL(self.smtp_server) as server:
                server.send_message(message)

    def send_results_email(self, results_files_dir: str, log_file: str, excluded: Union[Tuple[str, ...], List[str], str,
                           None] = None, included: Union[Tuple[str, ...], List[str], str, None] = None, is_error:
                           bool = False, use_attachments: bool = False, **kwargs) -> None:
        self.set_attributes(**kwargs)
        status = 'failed!' if is_error else 'completed'
        subject = f'{WEBSERVER_NAME_CAPITAL} job {self.name} by {self.receiver} has {status}'
        body = f'{subject}\n'
        attachments = [log_file]
        with scandir(results_files_dir) as entries:
            for entry in entries:
                self.add_attachment_to_list(entry, results_files_dir, attachments, excluded, included)
        self.send_email(subject, attachments, body, use_attachments)

    def send_log_files_list(self, start_date: float, end_date: float, excluded: Union[Tuple[str, ...],
                            List[str], str, None] = None, included: Union[Tuple[str, ...], List[str], str, None] = None,
                            use_attachments: bool = False, **kwargs) -> None:
        self.set_attributes(**kwargs)
        subject = f'{WEBSERVER_NAME_CAPITAL} Daily Jobs Report'
        body = f'{subject}\n'
        attachments = {'successful runs': [], 'failed runs': [], 'incomplete runs': []}
        with scandir(self.log_files_dir) as entries:
            for entry in entries:
                if start_date <= entry.stat().st_ctime < end_date:
                    process_id = path.splitext(entry.name)[0]
                    if path.exists(path.join(path.join(self.out_dir, process_id), f'GLOOME_{process_id}.END_FAIL')):
                        self.add_attachment_to_list(entry, self.log_files_dir, attachments.get('failed runs'),
                                                    excluded, included)
                    elif path.exists(path.join(path.join(self.out_dir, process_id), f'GLOOME_{process_id}.END_OK')):
                        attachments.get('successful runs').append(f'{self.results}/{process_id}')
                    else:
                        self.add_attachment_to_list(entry, self.log_files_dir, attachments.get('incomplete runs'),
                                                    excluded, included)
        for receiver in self.report_receivers:
            self.send_email(subject, attachments, body, use_attachments, receiver)

    @staticmethod
    def create_link_to_results(result_path):
        return f'\n<a href="{result_path}" target="_blank">{result_path}</a>'

    @staticmethod
    def add_attachment_to_list(entry, current_dir: str, attachments: List[str], excluded: Union[Tuple[str, ...],
                               List[str], str, None] = None, included: Union[Tuple[str, ...], List[str], str, None] =
                               None) -> None:
        includ = (included is None or entry.name in included or path.splitext(entry.name)[-1] in included
                  or path.splitext(entry.name)[-1][1:] in included)
        exclud = (excluded is not None and (entry.name in excluded or path.splitext(entry.name)[-1] in excluded
                  or path.splitext(entry.name)[-1][1:] in excluded))
        if entry.is_file() and not exclud and includ:
            attachments.append(path.join(current_dir, entry))

    @staticmethod
    def add_attachment_to_email(attachment_path, message) -> None:
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read().strip())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {path.basename(attachment_path)}",
        )
        message.attach(part)


class JobsCounter:
    def __init__(self, value: int = 0):
        self.value = value

    def inc(self):
        self.value += 1

        return self.value

    def dec(self):
        self.value -= 1

        return self.value
