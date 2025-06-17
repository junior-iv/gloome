# from utils import get_new_process_id
# from SharedConsts import SERVERS_RESULTS_DIR, OUTPUT_DIR_NAME
from config import WebConfig
from script.service_functions import (get_tree_variables, check_form, get_error, create_tmp_data_files, result_design,
                                      execute_function_with_delay, read_file, loads_json, dumps_json)
from script.submit_slurm import submit_job_to_q, get_job_info, get_jobs_info
from typing import Callable, Any, Union, List, Tuple, Dict, Optional, Type
from time import sleep
from flask import url_for, request, Response, jsonify
import os
import traceback


def json_find(data, key: Union[bool, int, float, str], value: Optional[Union[bool, int, float, str]] = None,
              return_dict: bool = True) -> Optional[Union[bool, int, float, str]]:
    if isinstance(data, dict):
        if key in data:
            if value is None or data.get(key) == value:
                return data if return_dict else data.get(key)
        for i in data.values():
            result = json_find(i, key, value, return_dict)
            if result is not None:
                return result
    elif isinstance(data, list):
        for i in data:
            result = json_find(i, key, value, return_dict)
            if result is not None:
                return result
    return None


def find_dict_in_iterable(iterable: List[Dict[str, Union[str, List[str]]]], key: str, value: str
                          ) -> Dict[str, Union[str, List[str]]]:
    for index, dictionary in enumerate(iterable):
        if key in dictionary and (True if value is None else dictionary[key] == value):
            return dictionary


def link_design(json_objct: Any, design: bool = False):
    for key, value in json_objct:
        if key == 'execution_time':
            continue
        # value = os.path.basename(value)
        json_objct.update({f'{key}': f'<a mx-2 class="w-auto mw-auto form-control btn btn-outline-link rounded-pill" '
                                     f'href="{url_for("get_file", file_path=value, mode="download")}" '
                                     f'target="_blank"><h7>download</h7></a>\t'
                                     f'<a mx-2 class="w-auto mw-auto form-control btn btn-outline-link rounded-pill" '
                                     f'href="{url_for("get_file", file_path=value, mode="view")}" '
                                     f'target="_blank"><h7>view</h7></a>'})
    return result_design(json_objct) if design else json_objct


def execute_response(design: bool = False, mode: Optional[Tuple[str, ...]] = None) -> Response:
    if request.method == 'POST':
        args = get_tree_variables(dict(request.form))
        err_list = check_form(args[0], args[1])

        if err_list:
            status = 400
            result = get_error(err_list)
        else:
            status = 200
            try:
                result = get_response(*args, design=design, mode=mode)
                print(result)
            except Exception as e:
                with open("/var/www/vhosts/gloomedev.tau.ac.il/httpdocs/tmp/route_debug.log", "a") as f:
                    f.write(f"\n\n--- Exception at /draw_tree ---\n")
                    f.write(traceback.format_exc())
                raise  # Re-raise to still return 500

        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')


def check_job_state(config, job_id: int, state: str = 'COMPLETED', count: int = 50,
                    waiting_time: int = 10) -> bool:
    while count:
        try:
            job_info = get_job_info(job_id)
        except Exception as e:
            sleep(waiting_time)
            continue

        job_state = json_find(job_info, key='job_state', return_dict=False)
        if 'FAILED' in job_state or state in job_state:
            config.set_job_logger_info(f'job_state = {job_state}')
            print(job_state)
            return state in job_state
        count -= 1
        sleep(waiting_time)

    return False


def execute_function_until_condition(func: Callable, condition: Any):
    result = ''
    return result


def get_response(newick_text: str, pattern_msa: str, categories_quantity: str, alpha: str, is_radial_tree: str,
                 show_distance_to_parent: str, design: bool = False, mode: Optional[Tuple[str, ...]] = None
                 ) -> Optional[str]:
    config = WebConfig()
    mode_str = 'draw_tree' if mode is None else ' '.join(mode)
    # process_id = get_new_process_id() if process_id is None else process_id
    file_names = create_tmp_data_files(pattern_msa, newick_text, config.SERVERS_INPUT_DIR)
    # print(file_names)
    # '/var/www/vhosts/gloomedev.tau.ac.il/httpdocs/results'
    # file_names = ('/lsweb/rodion/gloome/src/initial_data/msa/patternMSA0.msa',
    #               '/lsweb/rodion/gloome/src/initial_data/tree/newickTree0.tree')
    bin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(bin_dir)
    print(bin_dir)
    cmd = (f'python {os.path.join(".", "script/main.py")} --process_id {config.PROCESS_ID} --msa_file {file_names[0]} '
           f'--tree_file {file_names[1]} --categories_quantity {categories_quantity} --alpha {alpha} '
           f'--is_radial_tree {is_radial_tree} --show_distance_to_parent {show_distance_to_parent} '
           f'--mode {mode_str}')
    print(cmd)
    # file_path = os.path.join(str(os.path.join(SERVERS_RESULTS_DIR, process_id)), OUTPUT_DIR_NAME)
    job_id = submit_job_to_q(config, cmd)
    print(job_id)
    if check_job_state(config, job_id):
        config.set_job_logger_info(f'job_id - {job_id} state is COMPLETED')
        print('>', job_id, 'COMPLETED')
        file_name = f'{mode_str.split(sep=" ")[0]}.json'
        file_contents = read_file(file_path=os.path.join(config.SERVERS_OUTPUT_DIR, file_name))
        if 'file' in file_name:
            file_contents = dumps_json(link_design(loads_json(file_contents), design))
        return file_contents
    return None
    # print('result')
    # print(file_path)

    # job_info = get_job_info(job_id)
    # print(job_info)
    #
    # result = json_find(job_info, key='job_id', value=job_id)
    # print('result')
    # print(result)
    #
    # # job_id = 4062390
    # jobs_info = get_jobs_info()
    # print(jobs_info)
    #
    # result = execute_function_with_delay(get_job_info, 10, 6,
    #                                      **{'data': result, 'key': 'job_id', 'value': job_id, 'return_dict': False})
    # result = execute_function_with_delay(get_job_info, 10, 6, **{'job_id': job_id})
    # result = json_find(result, key='job_state', return_dict=True)
    # print('result')
    # print(result)
    # print('result')
    # print(result)
    # result = json_find(result, key='job_id', value=job_id, return_dict=False)
    # print('result')
    # print(result)

    # import subprocess
    # # print(subprocess.check_output(cmd))
    # # subprocess.getoutput(cmd)
    # print(subprocess.getoutput(cmd))
    # file_path = os.path.join(SERVERS_RESULTS_DIR, process_id)
    # file_path = os.path.join(str(file_path), OUTPUT_DIR_NAME)

    # return execute_function_with_delay(read_file, 60, **{'file_path': file_path})
