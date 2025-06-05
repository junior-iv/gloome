import requests
from os.path import normpath, basename, dirname
from os import getenv

api_key = '1AH2K82lOqM59yyn6u37bUrZjtkJaE9N7bZA8kGTX_NjbMD9dpsyCxc-YOOZIZILJFs'
current_user = 'gloome'
# current_user = getenv('USERNAME')
# api_key = getenv('SECRET_KEY')
PASSWORD = getenv('PASSWORD')

# Base URL for authentication and token generation
base_url_auth = 'https://slurmtron.tau.ac.il'
generate_token_url = f"{base_url_auth}/slurmapi/generate-token/"


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
    base_url = f"{base_url_auth}/slurmrestd"
    jwt_token = generate_jwt_token(current_user, api_key)['SlurmJWT']

    return base_url, jwt_token


def get_jobs_result(jwt_token, job_url):
    headers = {
        'X-SLURM-USER-NAME': current_user,
        'X-SLURM-USER-TOKEN': jwt_token
        }

    jobs_request = requests.get(
        job_url,
        headers=headers)
    jobs_result = jobs_request.json()
    print(jobs_result)
    return jobs_result


def get_job_info(job_id):
    base_url, jwt_token = get_url_token()
    job_url = f'{base_url}/slurm/v0.0.41/job/{job_id}'

    return get_jobs_result(jwt_token, job_url)


def slurm_ping():
    base_url, jwt_token = get_url_token()
    job_url = f'{base_url}/slurm/v0.0.41/ping'

    return get_jobs_result(jwt_token, job_url)


def get_jobs():
    base_url, jwt_token = get_url_token()
    job_url = f'{base_url}/slurm/v0.0.41/jobs'

    return get_jobs_result(jwt_token, job_url)


def get_jobs_info():
    base_url, jwt_token = get_url_token()

    job_url = f'{base_url}/slurm/v0.0.41/jobs/state'

    return get_jobs_result(jwt_token, job_url)


def submit_job_to_Q(wd, cmd):
    # current_user = getpass.getuser()
    # api url
    base_url = f"{base_url_auth}/slurmrestd"
    # auth token
    jwt_token = generate_jwt_token(current_user, api_key)['SlurmJWT']

    # job submission url
    job_url = f'{base_url}/slurm/v0.0.41/job/submit'
    # Auth Headers
    headers = {
        'X-SLURM-USER-NAME': current_user,
        'X-SLURM-USER-TOKEN': jwt_token
        }

    jobID = basename(dirname(normpath(wd)))
    # jobID = basename(normpath(wd))
    jobName = f'gloome_{jobID}'
    print(jobID, jobName, sep='\n')

    jobs_request = requests.post(
        job_url,
        headers=headers,
        json={
            "script": "#!/bin/bash\nsource ~/.bashrc\n%s\n" %(cmd),
            "job": {

                "partition": "pupkoweb",
                "tasks": 1,
                "name": jobName,
                "account": "pupkoweb-users",
                "nodes": "1",
                             # how much CPU you need
                "cpus_per_task": 4,
                             # How much Memory you need per node, in MB
                "memory_per_node": {
                    "number": 256,
                    "set": True,
                    "infinite": False
                    },
                "time_limit": {
                    "number": 600,
                    "set": True,
                    "infinite": False
                    },
                "current_working_directory": "/tmp/",
                "standard_output": "/tmp/output.txt",
                "environment": [
                    ("PATH=/lsweb/rodion/gloome/gloome_env/bin:/powerapps/share/rocky8/mamba/mamba-1.5.8/condabin:"
                     "mamba/condabin:/powerapps/share/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/usr/"
                     "local.cc/bin:/mathematica/vers/11.2")
                    ,
                    ("LD_LIBRARY_PATH=/usr/lib64/atlas:/usr/lib64/mysql:/lib:/lib64:/lib/sse2:/lib/i686:/lib64/sse2:"
                     "/lib64/tls"),
                    ("MODULEPATH=/powerapps/share/Modules/Centos7/modulefiles:/powerapps/share/Modules/Rocky8/"
                     "modulefiles:/powerapps/share/Modules/Rocky9/modulefiles:$MODULEPATH")
                     ],
                 },
    })
    
    jobs_result = jobs_request.json()
    return jobs_result
    # '''
    # for key, value in jobs_result.items():
    #     print(key, value)
    # '''
    # if 'result' in jobs_result:
    #     if 'job_id' in jobs_result['result']:
    #         return (str(jobs_result['result']['job_id']))
    #
    # return ''
    # print (jobs_result['result']['job_id'])
