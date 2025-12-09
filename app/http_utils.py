import traceback

from typing import Tuple, Optional, Any
from flask import request, Response, jsonify
from os import path

from app.config import WebConfig, SERVERS_LOGS_DIR
from script.service_functions import get_variables, check_data, get_error, loads_json

# LOG_PATH = '/var/www/vhosts/gloome.tau.ac.il/logs'
# HTTPDOCS_PATH = '/var/www/vhosts/gloome.tau.ac.il/httpdocs/'


def read_json(json_string: str) -> Any:
    try:
        result = loads_json(json_string)
    except Exception:
        with open(path.join(SERVERS_LOGS_DIR, f'read_json_Route_debug.log'), 'a') as f:
            f.write(f'\n\n--- Exception at execute_request ---\n')
            f.write(traceback.format_exc())
        raise  # Re-raise to still return 500

    return Response(response=jsonify(message=result).response, status=200, mimetype='application/json')


def get_response(process_id: int) -> Any:
    conf = WebConfig(PROCESS_ID=process_id)
    try:
        conf.texts_filling()
        result = conf.read_response()
    except Exception:
        conf.JOB_LOGGER.info(traceback.format_exc())
        with open(path.join(SERVERS_LOGS_DIR, f'get_response_{conf.PROCESS_ID}_route_debug.log'), 'a') as f:
            f.write(f'\n\n--- Exception at execute_request ---\n')
            f.write(traceback.format_exc())
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

            try:
                conf.arguments_filling(**kwargs, mode=mode)
                conf.create_tmp_data_files()
                result = conf.get_response()
            except Exception:
                conf.JOB_LOGGER.info(traceback.format_exc())
                with open(path.join(SERVERS_LOGS_DIR, f'execute_request_{conf.CURRENT_JOB}_{conf.PROCESS_ID}'
                          f'_Route_debug.log'), 'a') as f:
                    f.write(f'\n\n--- Exception at execute_request ---\n')
                    f.write(traceback.format_exc())
                raise  # Re-raise to still return 500

        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')
