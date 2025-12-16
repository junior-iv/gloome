import traceback
import multiprocessing as mp

from typing import Tuple, Optional, Any
from flask import request, Response, jsonify
from os import path

from app.config import WebConfig, TMP_DIR, current_time
from script.service_functions import get_variables, check_data, get_error, loads_json

JOB_STATUS = {}
JOB_RESULTS = {}


def run_job(process_id, kwargs, mode):
    conf = WebConfig(PROCESS_ID=process_id)
    conf.JOB_LOGGER.info(f'\n\ttry to run request\n')

    try:
        conf.arguments_filling(**kwargs, mode=mode)
        conf.create_tmp_data_files()
        result = conf.get_response()
        JOB_RESULTS[process_id] = result
        JOB_STATUS[process_id] = 'finished'
    except Exception:
        exception_text = traceback.format_exc()
        header = f'\n\t--- EXCEPTION at execute_request ---'
        f'\n\tCURRENT_TIME: {current_time()}'
        f'\n\tCURRENT_JOB: {conf.CURRENT_JOB}'
        f'\n\tPROCESS_ID: {conf.PROCESS_ID}\n'
        conf.JOB_LOGGER.info(f'{header}{exception_text}')
        wright_log(file_path=path.join(TMP_DIR, f'execute_request_{conf.PROCESS_ID}_route_debug.log'),
                   header=header, exception_text=exception_text)
        JOB_RESULTS[process_id] = {"error": exception_text}
        JOB_STATUS[process_id] = "failed"

        raise  # Re-raise to still return 500


def start_background_job(kwargs, mode):
    # job_id = uuid.uuid4().hex
    process_id = WebConfig.get_new_process_id()

    JOB_STATUS[process_id] = 'running'
    p = mp.Process(target=run_job, args=(process_id, kwargs, mode))
    p.start()
    return process_id


def wright_log(file_path: str, header: str, exception_text: str) -> None:
    with open(file_path, 'r', encoding='utf-8') as file:
        old_content = file.read()
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(header)
        file.write(exception_text)
        file.write(old_content)


def read_json(json_string: str) -> Any:
    try:
        result = loads_json(json_string)
    except Exception:
        wright_log(file_path=path.join(TMP_DIR, f'read_json_route_debug.log'),
                   header=f'\n\n--- [{current_time()}] Exception at execute_request ---\n',
                   exception_text=traceback.format_exc())
        raise  # Re-raise to still return 500

    return Response(response=jsonify(message=result).response, status=200, mimetype='application/json')


def get_response(process_id: int) -> Any:
    conf = WebConfig(PROCESS_ID=process_id)
    conf.JOB_LOGGER.info(f'\n\ttry to get response\n')

    try:
        conf.texts_filling()
        result = conf.read_response()
    except Exception:
        exception_text = traceback.format_exc()
        header = f'\n\t--- EXCEPTION at get_response ---'
        f'\n\tCURRENT_TIME: {current_time()}'
        f'\n\tPROCESS_ID: {conf.PROCESS_ID}\n'
        conf.JOB_LOGGER.info(f'{header}{exception_text}')
        wright_log(file_path=path.join(TMP_DIR, f'get_response_{conf.PROCESS_ID}_route_debug.log'),
                   header=header, exception_text=exception_text)
        raise  # Re-raise to still return 500

    return result


def set_response_structure(data: Any, success: bool) -> Any:
    if success:
        return {'success': success, 'data': data}
    else:
        return {'success': success, 'error': {'message': data}}


def execute_request(mode: Optional[Tuple[str, ...]] = None) -> Response:
    if request.method == 'POST':
        args = get_variables(dict(request.form))
        err_list = check_data(*args)
        kwargs = dict(request.form)

        if err_list:
            return Response(response=jsonify(set_response_structure(get_error(err_list), False)).response, status=400,
                            mimetype='application/json')

        process_id = start_background_job(kwargs, mode)

        return Response(response=jsonify(set_response_structure({"processID": process_id}, True)).response, status=202,
                        mimetype='application/json')

# def execute_request(mode: Optional[Tuple[str, ...]] = None) -> Response:
#     if request.method == 'POST':
#         args = get_variables(dict(request.form))
#         err_list = check_data(*args)
#         kwargs = dict(request.form)
#         if err_list:
#             status = 400
#             result = get_error(err_list)
#         else:
#             status = 200
#             conf = WebConfig()
#             conf.JOB_LOGGER.info(f'\n\ttry to run request\n')
#
#             try:
#                 conf.arguments_filling(**kwargs, mode=mode)
#                 conf.create_tmp_data_files()
#                 result = conf.get_response()
#             except Exception:
#                 exception_text = traceback.format_exc()
#                 header = f'\n\t--- EXCEPTION at execute_request ---'
#                 f'\n\tCURRENT_TIME: {current_time()}'
#                 f'\n\tCURRENT_JOB: {conf.CURRENT_JOB}'
#                 f'\n\tPROCESS_ID: {conf.PROCESS_ID}\n'
#                 conf.JOB_LOGGER.info(f'{header}{exception_text}')
#                 wright_log(file_path=path.join(TMP_DIR, f'execute_request_{conf.PROCESS_ID}_route_debug.log'),
#                            header=header, exception_text=exception_text)
#                 raise  # Re-raise to still return 500
#
#         return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')
