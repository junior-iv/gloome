import traceback
import zlib
import multiprocessing as mp

from html import escape

from app.app import *
from app.config import *
from gloome.services.service_functions import (get_variables, check_data, get_error, loads_json, read_file,
                                               del_bootstrap_values, get_rooting_info)


def write_end_file(process_id: Union[int, str], process_status: str, result_dir: Path, message: str = '') -> Path:
    """Marks the job as finished; for END_FAIL the file holds the error message shown to the user."""
    file_path = result_dir.joinpath(f'GLOOME_{process_id}.END_{process_status}')
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(message)

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
            job_status = {'status': 'failed', 'error': read_fail_message(fail_file_path, conf)}
        else:
            job_status = {'status': 'running'}
    return job_status


def read_fail_message(fail_file_path: Path, conf: WebConfig) -> str:
    try:
        message = read_file(file_path=fail_file_path).strip()
    except Exception:
        message = ''
    message = escape(message or 'The job failed.').replace('\n', '<br>')

    return (f'{message}<br>Process ID: {conf.PROCESS_ID}. Details are in the <a href="{conf.LOG_URL}" target="_blank">'
            f'job log</a>.')


def run_job(process_id, mode, **kwargs):
    conf = WebConfig(PROCESS_ID=process_id)
    conf.JOB_LOGGER.info(f'\n\ttry to run request\n')

    try:
        conf.arguments_filling(mode=mode, **kwargs)
        conf.create_tmp_data_files()
        process_status = conf.get_response()
        write_end_file(process_id, process_status, conf.OUT_DIR, conf.FAIL_MESSAGE if process_status == 'FAIL' else '')
    except Exception:
        exception_text = traceback.format_exc()
        header = f'\n\t--- EXCEPTION at execute_request ---'
        f'\n\tCURRENT_TIME: {current_time()}'
        f'\n\tCURRENT_JOB: {conf.CURRENT_JOB}'
        f'\n\tPROCESS_ID: {conf.PROCESS_ID}\n'
        conf.JOB_LOGGER.info(f'{header}{exception_text}')
        write_log(file_path=TMP_DIR.joinpath(f'execute_request_{conf.PROCESS_ID}_route_debug.log'), header=header,
                  exception_text=exception_text)
        write_end_file(process_id, 'FAIL', conf.OUT_DIR,
                       conf.FAIL_MESSAGE or 'An internal server error occurred while processing the job.')
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


def get_all_leaves(data: str) -> Any:
    try:
        rooting_info = get_rooting_info(del_bootstrap_values(data)) if data else {'leaves': [], 'rooted': None}
        result = set_response_structure(rooting_info, True)
        status = 200
    except Exception:
        result = set_response_structure(
            get_error([(f'TREE error', f'Wrong Phylogenetic tree format. Please provide a tree in Newick format.')]),
            False)
        status = 400

    return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')


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


COMPRESSED_TEXT_FIELDS = ('newickText', 'msaText')
MAX_DECOMPRESSED_TEXT_SIZE = 1024 ** 3  # 1 GiB per field; guards against gzip bombs


def read_form() -> Dict[str, str]:
    """The posted form fields. The front end sends large MSA / tree texts gzipped as file parts (to stay under
    the proxy's request-size limit); they are decompressed back into plain text fields here.
    get_variables / check_data read the fields by position and the form always starts with newickText, msaText,
    so those two are put first whether they came as text fields or as (compressed) file parts."""
    kwargs = {}
    for field in COMPRESSED_TEXT_FIELDS:
        uploaded = request.files.get(field)
        if uploaded is None:
            if field in request.form:
                kwargs[field] = request.form[field]
            continue
        decompressor = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)  # gzip container
        data = decompressor.decompress(uploaded.read(), MAX_DECOMPRESSED_TEXT_SIZE)
        if decompressor.unconsumed_tail:
            raise ValueError(f'{field} is larger than {MAX_DECOMPRESSED_TEXT_SIZE:,} bytes after decompression')
        if not decompressor.eof:
            raise ValueError(f'{field}: the compressed data is truncated')
        kwargs[field] = data.decode('utf-8')
    for key, value in request.form.items():
        kwargs.setdefault(key, value)
    return kwargs


def execute_request(mode: Optional[Tuple[str, ...]] = None) -> Response:
    if request.method == 'POST':
        try:
            kwargs = read_form()
        except (zlib.error, ValueError, UnicodeDecodeError) as e:
            return Response(response=jsonify(set_response_structure(f'Could not read the uploaded data: {e}',
                                                                    False)).response,
                            status=400, mimetype='application/json')
        kwargs.update({'newickText': del_bootstrap_values(kwargs.get('newickText', ''))})
        args = get_variables(kwargs)
        err_list = check_data(*args)

        if err_list:
            return Response(response=jsonify(set_response_structure(get_error(err_list), False)).response, status=400,
                            mimetype='application/json')
        # else:
        #     kwargs.update({'newickText': Tree.set_root(kwargs.get('newickText', ''))})

        process_id = start_background_job(mode=mode, **kwargs)

        return Response(response=jsonify(set_response_structure({"processID": process_id}, True)).response, status=202,
                        mimetype='application/json')
