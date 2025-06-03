from utils import get_new_process_id
from SharedConsts import SERVERS_RESULTS_DIR, OUTPUT_DIR_NAME
from typing import Callable
from script.design_functions import *
from script.service_functions import (get_tree_variables, check_form, get_error, create_tmp_data_files,
                                      execute_function_with_delay, read_file)
from script.submit_slurm import submit_job_to_Q
import os


def execute_response(request, response: Callable, jsonify: Callable, design: Optional[bool] = None) -> str:
    if request.method == 'POST':
        args = get_tree_variables(dict(request.form))
        err_list = check_form(args[0], args[1])

        if err_list:
            status = 400
            result = get_error(err_list)
        else:
            status = 200
            result = get_response(*args, process_id=get_new_process_id())
            result = result_design(result) if design else result

        return response(response=jsonify(message=result).response, status=status, mimetype='application/json')


def get_response(newick_text: str, pattern_msa: str, categories_quantity: str, alpha: str, is_radial_tree: str,
                 show_distance_to_parent: str, process_id: Optional[str] = None) -> str:
    # mode = ("draw_tree", ) if mode is None else mode
    process_id = get_new_process_id() if process_id is None else process_id
    file_names = create_tmp_data_files(pattern_msa, newick_text)
    # file_names = 'src/initial_data/msa/patternMSA0.msa', 'src/initial_data/tree/newickTree0.tree'
    bin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(bin_dir)
    print(bin_dir)
    cmd = (f'module load mamba/mamba-1.5.8; '
           f'mamba activate /lsweb/rodion/gloome/gloome_env/;'
           f'python {os.path.join(".", "script/main.py")} --process_id {process_id} --msa_file {file_names[0]} '
           f'--tree_file {file_names[1]} --categories_quantity {categories_quantity} --alpha {alpha} '
           f'--is_radial_tree {is_radial_tree} --show_distance_to_parent {show_distance_to_parent} ')
           # f'--mode "{mode}"')
    print(cmd)
    file_path = os.path.join(SERVERS_RESULTS_DIR, process_id)
    file_path = os.path.join(str(file_path), OUTPUT_DIR_NAME)
    result = submit_job_to_Q(file_path, cmd)
    print('result')
    print(result)

    # import subprocess
    # # print(subprocess.check_output(cmd))
    # # subprocess.getoutput(cmd)
    # print(subprocess.getoutput(cmd))
    # file_path = os.path.join(SERVERS_RESULTS_DIR, process_id)
    # file_path = os.path.join(str(file_path), OUTPUT_DIR_NAME)

    return read_file(file_path=file_path)
    # return execute_function_with_delay(read_file, 60, **{'file_path': file_path})
