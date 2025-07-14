import json

from app.config import WebConfig
from script.service_functions import get_variables, check_data, get_error
from typing import Tuple, Optional, Any
from flask import request, Response, jsonify
import traceback


def get_response(process_id: int) -> Any:
    conf = WebConfig(PROCESS_ID=process_id)
    conf.texts_filling()
    try:
        result = jsonify(message=conf.read_response()).response
    except Exception:
        conf.set_job_logger_info(traceback.format_exc())
        with open(f'/var/www/vhosts/gloomedev.tau.ac.il/httpdocs/tmp/{conf.CURRENT_JOB}_{conf.PROCESS_ID}_'
                  f'route_debug.log', 'a') as f:
            f.write(f'\n\n--- Exception at /draw_tree ---\n')
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
            conf.create_tmp_data_files()
            try:
                result = conf.get_response()
            except Exception:
                conf.set_job_logger_info(traceback.format_exc())
                with open(f'/var/www/vhosts/gloomedev.tau.ac.il/httpdocs/tmp/{conf.CURRENT_JOB}_{conf.PROCESS_ID}_'
                          f'route_debug.log', 'a') as f:
                    f.write(f'\n\n--- Exception at /draw_tree ---\n')
                    f.write(traceback.format_exc())
                raise  # Re-raise to still return 500

        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')
