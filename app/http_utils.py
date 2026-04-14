import traceback
import multiprocessing as mp

from app.app import *
from app.config import *
from gloome.services.service_functions import (get_variables, check_data, get_error, loads_json, read_file,
                                               del_bootstrap_values)


def write_end_file(process_id: Union[int, str], completed: bool, result_dir: Path) -> Path:
    file_path = result_dir.joinpath(f'GLOOME_{process_id}.END_{"OK" if completed else "FAIL"}')
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write('')

    return file_path


def get_job_status(process_id: Union[int, str], result: bool = True) -> Dict[str, Any]:
    conf = WebConfig(PROCESS_ID=process_id)
    if not conf.OUT_DIR.exists():
        job_status = {'error': 'unknown job'}
    else:
        ok_file_path = conf.OUT_DIR.joinpath(f'GLOOME_{process_id}.END_OK')
        fail_file_path = conf.OUT_DIR.joinpath(f'GLOOME_{process_id}.END_FAIL')
        if ok_file_path.exists() and not fail_file_path.exists():
            job_status = {'status': 'finished'}
            if result:
                job_status.update(result=loads_json(read_file(file_path=conf.OUTPUT_FILE)))
        elif not ok_file_path.exists() and fail_file_path.exists():
            job_status = {'status': 'failed'}
        else:
            job_status = {'status': 'running'}
    return job_status


def run_job(process_id, mode, **kwargs):
    conf = WebConfig(PROCESS_ID=process_id)
    conf.JOB_LOGGER.info(f'\n\ttry to run request\n')

    try:
        conf.arguments_filling(mode=mode, **kwargs)
        conf.create_tmp_data_files()
        conf.get_response()
        write_end_file(process_id, True, conf.OUT_DIR)
    except Exception:
        exception_text = traceback.format_exc()
        header = f'\n\t--- EXCEPTION at execute_request ---'
        f'\n\tCURRENT_TIME: {current_time()}'
        f'\n\tCURRENT_JOB: {conf.CURRENT_JOB}'
        f'\n\tPROCESS_ID: {conf.PROCESS_ID}\n'
        conf.JOB_LOGGER.info(f'{header}{exception_text}')
        write_log(file_path=TMP_DIR.joinpath(f'execute_request_{conf.PROCESS_ID}_route_debug.log'), header=header,
                  exception_text=exception_text)
        write_end_file(process_id, False, conf.OUT_DIR)
        raise  # Re-raise to still return 500


def start_background_job(mode, **kwargs):
    process_id = get_new_process_id()

    p = mp.Process(target=run_job, kwargs={'process_id': process_id, 'mode': mode, **kwargs})
    p.start()
    return process_id


def write_log(file_path: Path, header: str = '', exception_text: str = '') -> None:
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as file:
            old_content = file.read()
    else:
        old_content = ''
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(header)
        file.write(exception_text)
        file.write(old_content)


def read_json(json_string: str) -> Any:
    try:
        result = loads_json(json_string)
    except Exception:
        write_log(file_path=TMP_DIR.joinpath(f'read_json_route_debug.log'),
                  header=f'\n\n--- [{current_time()}] Exception at execute_request ---\n',
                  exception_text=traceback.format_exc())
        raise  # Re-raise to still return 500

    return Response(response=jsonify(message=result).response, status=200, mimetype='application/json')


def get_response(process_id: int) -> Any:
    conf = WebConfig(PROCESS_ID=process_id)

    try:
        conf.texts_filling()
        result = conf.read_response()
    except Exception:
        exception_text = traceback.format_exc()
        header = f'\n\t--- EXCEPTION at get_response ---'
        f'\n\tCURRENT_TIME: {current_time()}'
        f'\n\tPROCESS_ID: {conf.PROCESS_ID}\n'
        conf.JOB_LOGGER.info(f'{header}{exception_text}')
        write_log(file_path=TMP_DIR.joinpath(f'get_response_{conf.PROCESS_ID}_route_debug.log'),
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
        kwargs = dict(request.form)
        kwargs.update({'newickText': del_bootstrap_values(kwargs.get('newickText', ''))})
        args = get_variables(kwargs)
        err_list = check_data(*args)

        if err_list:
            return Response(response=jsonify(set_response_structure(get_error(err_list), False)).response, status=400,
                            mimetype='application/json')
        else:
            kwargs.update({'newickText': Tree.get_root_by_midpoint(kwargs.get('newickText', ''))})

        process_id = start_background_job(mode=mode, **kwargs)

        return Response(response=jsonify(set_response_structure({"processID": process_id}, True)).response, status=202,
                        mimetype='application/json')
