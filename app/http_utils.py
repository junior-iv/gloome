from app.config import WebConfig
from script.service_functions import get_tree_variables, check_form, get_error
from typing import Tuple, Optional
from flask import request, Response, jsonify
import traceback


def execute_response(design: bool = False, mode: Optional[Tuple[str, ...]] = None) -> Response:
    if request.method == 'POST':
        args = get_tree_variables(dict(request.form))
        err_list = check_form(args[0], args[1])
        kwargs = dict(request.form)

        if err_list:
            status = 400
            result = get_error(err_list)
        else:
            status = 200
            conf = WebConfig()
            conf.arguments_filling(**kwargs, mode=mode)
            conf.check_arguments_for_errors()
            conf.create_tmp_data_files()
            try:
                result = conf.get_response(design)
                print(result)
            except Exception as e:
                conf.set_job_logger_info(traceback.format_exc())
                with open(f'/var/www/vhosts/gloomedev.tau.ac.il/httpdocs/tmp/{conf.CURRENT_JOB}_route_debug.log', 'a') as f:
                    f.write(f"\n\n--- Exception at /draw_tree ---\n")
                    f.write(traceback.format_exc())
                raise  # Re-raise to still return 500

        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')
