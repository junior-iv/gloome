import traceback

from typing import Tuple, Optional, Any
from flask import request, Response, jsonify
from os import path

from app.config import WebConfig, TMP_DIR, current_time, SERVERS_LOGS_DIR
from script.service_functions import get_variables, check_data, get_error, loads_json

# LOG_PATH = '/var/www/vhosts/gloome.tau.ac.il/logs'
# HTTPDOCS_PATH = '/var/www/vhosts/gloome.tau.ac.il/httpdocs/'


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
    conf.JOB_LOGGER.info(f'\n\n\tattempt/start execution of the "get_response" function'
                         f'\n\tCURRENT_TIME: {current_time()}\n'
                         f'\n\tPROCESS_ID: {conf.PROCESS_ID}\n')
    try:
        conf.texts_filling()
        result = conf.read_response()
    except Exception:
        exception_text = traceback.format_exc()
        header = f'\n\n\t--- EXCEPTION at get_response ---'
        f'\n\tCURRENT_TIME: {current_time()}\n'
        f'\n\tPROCESS_ID: {conf.PROCESS_ID}\n'
        conf.JOB_LOGGER.info(f'{header}{exception_text}')
        wright_log(file_path=path.join(TMP_DIR, f'get_response_{conf.PROCESS_ID}_route_debug.log'),
                   header=header, exception_text=exception_text)
        raise  # Re-raise to still return 500

    return result


def execute_request(mode: Optional[Tuple[str, ...]] = None) -> Response:
    if request.method == 'POST':
        args = get_variables(dict(request.form))
        err_list = check_data(*args)
        kwargs = dict(request.form)
        if err_list:
            status = 400
            result = get_error(err_list)
        else:
            status = 200
            conf = WebConfig()

            conf.JOB_LOGGER.info(f'\n\n\tattempt/start execution of the "execute_request" function'
                                 f'\n\tCURRENT_TIME: {current_time()}\n'
                                 f'\n\tPROCESS_ID: {conf.PROCESS_ID}\n')
            try:
                conf.arguments_filling(**kwargs, mode=mode)
                conf.create_tmp_data_files()
                result = conf.get_response()
            except Exception:
                exception_text = traceback.format_exc()
                header = f'\n\n--- EXCEPTION at execute_request ---\n'
                f'CURRENT_TIME: {current_time()}\n'
                f'CURRENT_JOB: {conf.CURRENT_JOB}\n'
                f'PROCESS_ID: {conf.PROCESS_ID}\n'
                conf.JOB_LOGGER.info(f'{header}{exception_text}')
                wright_log(file_path=path.join(TMP_DIR, f'execute_request_{conf.PROCESS_ID}_route_debug.log'),
                           header=header, exception_text=exception_text)
                raise  # Re-raise to still return 500

        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')
