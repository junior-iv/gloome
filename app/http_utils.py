import traceback

from typing import Tuple, Optional, Any
from flask import request, Response, jsonify
from os import path

from app.config import WebConfig
from script.service_functions import get_variables, check_data, get_error, loads_json

LOG_PATH = '/var/www/vhosts/gloome.tau.ac.il/logs'
HTTPDOCS_PATH = '/var/www/vhosts/gloome.tau.ac.il/httpdocs/'


def read_json(json_string: str) -> Any:
    try:
        result = loads_json(json_string)

        if (result.get('action_name') in ('execute_all_actions', 'create_all_file_types') and
                result.get('create_all_file_types', None) is not None):
            result.pop('create_all_file_types')
            result.update({'error_message': 'Cannot create file links locally'})
    except Exception:
        with open(path.join(LOG_PATH, f'read_json_Route_debug.log'), 'a') as f:
            f.write(f'\n\n--- Exception at execute_request ---\n')
            f.write(traceback.format_exc())
        raise  # Re-raise to still return 500

    return Response(response=jsonify(message=result).response, status=200, mimetype='application/json')


def get_response(process_id: int) -> Any:
    conf = WebConfig(PROCESS_ID=process_id)
    conf.texts_filling()
    try:
        result = conf.read_response()
    except Exception:
        conf.set_job_logger_info(traceback.format_exc())
        with open(path.join(LOG_PATH, f'get_response_{conf.PROCESS_ID}_route_debug.log'), 'a') as f:
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
            conf.arguments_filling(**kwargs, mode=mode)
            # conf.create_tmp_data_files()

            with open(path.join(LOG_PATH, f'file_path_{conf.PROCESS_ID}.log'),
                      'a') as f:
                f.write(f'\n--- file_path ---\n')
                f.write(f'\n--- MSA_FILE ---\n{conf.MSA_FILE}\n')
                f.write(f'\n--- TREE_FILE ---\n{conf.TREE_FILE}\n')
                f.write(f'\n--- CALCULATED_ARGS.file_path ---\n{conf.CALCULATED_ARGS.file_path}\n')

            try:
                conf.create_tmp_data_files()
            except Exception:
                with open(path.join(LOG_PATH, f'create_data_files_{conf.PROCESS_ID}.log'),
                          'a') as f:
                    f.write(f'\n\n--- Exception at create_data_files ---\n')
                    f.write(traceback.format_exc())

            with open(path.join(LOG_PATH, f'file_path_{conf.PROCESS_ID}.log'),
                      'a') as f:
                f.write(f'\n--- file_path_3 ---\n')
                f.write(f'\n--- MSA_FILE ---\n{conf.MSA_FILE}\n')
                f.write(f'\n--- TREE_FILE ---\n{conf.TREE_FILE}\n')
                f.write(f'\n--- CALCULATED_ARGS.file_path ---\n{conf.CALCULATED_ARGS.file_path}\n')

            try:
                result = conf.get_response()
            except Exception:
                conf.set_job_logger_info(traceback.format_exc())
                with open(path.join(LOG_PATH, f'execute_request_{conf.CURRENT_JOB}_{conf.PROCESS_ID}_Route_debug.log'),
                          'a') as f:
                    f.write(f'\n\n--- Exception at execute_request ---\n')
                    f.write(traceback.format_exc())
                raise  # Re-raise to still return 500

        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')
