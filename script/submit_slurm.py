import requests
import datetime
from os.path import normpath, basename, dirname
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# api_key = '1AH2K82lOqM59yyn6u37bUrZjtkJaE9N7bZA8kGTX_NjbMD9dpsyCxc-YOOZIZILJFs'
# current_user = 'gloome'
current_user = getenv('USER_NAME')
api_key = getenv('SECRET_KEY')
USER_PASSWORD = getenv('USER_PASSWORD')

# Base URL for authentication and token generation
base_url_auth = 'https://slurmtron.tau.ac.il'
generate_token_url = f"{base_url_auth}/slurmapi/generate-token/"
base_url = f"{base_url_auth}/slurmrestd"


def generate_jwt_token(user, key):

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
        'username': user,
        'api_key': key
    }
    print(payload)
    response = requests.post(generate_token_url, data=payload)

    print(response.status_code)
    print(response.json())
    if response.status_code == 200:
        return response.json()  # Assuming the token is returned in JSON format
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")


def get_url_token():
    return generate_jwt_token(current_user, api_key)['SlurmJWT']


def get_request_result(jwt_token, job_url):
    headers = {
        'X-SLURM-USER-NAME': current_user,
        'X-SLURM-USER-TOKEN': jwt_token
        }

    request_result = requests.get(
        job_url,
        headers=headers)
    print(request_result)
    return request_result.json()


def get_job_info(job_id):
    slurm_url = f'{base_url}/slurm/v0.0.41/job/{job_id}'

    return get_request_result(get_url_token(), slurm_url)


def get_jobs_info():
    slurm_url = f'{base_url}/slurm/v0.0.41/jobs/state'

    return get_request_result(get_url_token(), slurm_url)


def slurm_ping():
    slurm_url = f'{base_url}/slurm/v0.0.41/ping'

    return get_request_result(get_url_token(), slurm_url)


def get_jobs():
    slurm_url = f'{base_url}/slurm/v0.0.41/jobs'

    return get_request_result(get_url_token(), slurm_url)


def submit_job_to_q(config, cmd):
    # process_id = config.PROCESS_ID
    job_url = f'{base_url}/slurm/v0.0.41/job/submit'
    headers = {
        'X-SLURM-USER-NAME': current_user,
        'X-SLURM-USER-TOKEN': get_url_token()
        }

    job_name = f'gloome_{config.PROCESS_ID}'
    print(config.PROCESS_ID, job_name, sep='\n')
    prefix = f'{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")}_{config.PROCESS_ID}_'
    print(cmd)

    jobs_request = requests.post(
        job_url,
        headers=headers,
        json={
            'script': (
                f'#!/bin/bash\n'
                f'source ~/.bashrc\n'
                f'cd /lsweb/rodion/gloome/\n'
                f'echo "Loading module..."\n'
                f'{config.MODULE_LOAD}\n'
                f'echo "Activating env..."\n'
                f'{config.ENVIRONMENT_ACTIVATE}\n'
                f'echo "Executing python script..."\n'
                f'{cmd}'
                # f'echo "cmd completed successfully, REST API request completed successfully" > /lsweb/rodion/gloome/tmp/{prefix}slurm_api_request_result.txt'
            ),

            'job': {
                'name': job_name,
                'partition': 'pupkoweb',
                'account': 'pupkoweb-users',
                'tasks': 1,
                'nodes': '1',
                'cpus_per_task': 1,
                'memory_per_node': {'number': 6144, 'set': True},
                'time_limit': {'number': 10080, 'set': True},
                'current_working_directory': f'{config.PRODJECT_DIR}tmp/',
                'standard_output': f'{config.PRODJECT_DIR}tmp/{prefix}output.txt',
                'standard_error': f'{config.PRODJECT_DIR}tmp/{prefix}error.txt',

                'environment': [
                    f'PATH={config.ENVIRONMENT_DIR}/bin:/powerapps/share/rocky8/mamba/mamba-1.5.8/condabin:'
                    f'mamba/condabin:/powerapps/share/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:'
                    f'/usr/local.cc/bin:/powerapps/share/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:'
                    f'/usr/local.cc/bin'
                ],
            },
        }
    )

    jobs_result = jobs_request.json()

    print(jobs_result)

    if 'result' in jobs_result:
        if 'job_id' in jobs_result['result']:
            return str(jobs_result['result']['job_id'])

    return ''
