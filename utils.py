import datetime
import logging
import pickle
import re

from enum import Enum
from os import chdir, system, makedirs
from consts import *
from time import time
from random import randint

LOGGER_LEVEL_JOB_MANAGE_THREAD_SAFE = logging.DEBUG
LOGGER_LEVEL_JOB_MANAGE_API = logging.DEBUG
BIN_DIR = path.dirname(path.abspath(__file__))
# BIN_DIR = path.dirname(path.dirname(path.abspath(sys.argv[0])))
SERVER_DIR = BIN_DIR


def init_dir_path():
    path2change = SERVER_DIR
    chdir(path2change)


init_dir_path()
logging_file_name = path.join('logs/', datetime.datetime.now().strftime('%Y_%m_%d_%H_%M.log'))
FORMAT = '%(asctime)s[%(levelname)s][%(filename)s][%(funcName)s]: %(message)s'
formatter = logging.Formatter('%(asctime)s[%(levelname)s][%(filename)s][%(funcName)s]: %(message)s')
logging.basicConfig(filename=logging_file_name, level=logging.WARNING, format=FORMAT)
logger = logging.getLogger('main')


class State(Enum):
    Running = 1
    Finished = 2
    Crashed = 3
    Waiting = 4
    Init = 5
    Queue = 6
    NotExists = 7
    Error = 8

    def str(self):
        return {
            State.Running: 'RUNNING',
            State.Crashed: 'FAILED',
            State.Error: 'ERROR',
            State.Finished: 'FINISHED',
            State.Waiting: 'WAITING',
            State.Init: 'INIT',
            State.Queue: 'IN QUEUE',
            State.NotExists: 'NOT EXISTS'
        }[self]


def send_email_old(smtp_server, sender, receiver, subject='', content=''):
    from email.mime.text import MIMEText
    from smtplib import SMTP
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    s = SMTP(smtp_server)
    s.send_message(msg)
    s.quit()


def send_email(smtp_server, sender, receiver, subject='', content=''):
    cmd = (f'sendemail -f {sender} -t {receiver} -u \'{subject}\' -m \'{content}\' -s {SMTP_SERVER} '
           f'-o tls=yes -xu {sender} -xp {ADMIN_PASSWORD}')
    system(cmd)


def current_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S %Y-%m-%d")


# def remove_job_from_running_log(run_number):
#     with open(CONSTS.PEPITOPE_RUNNING_JOBS, "r+") as f:
#         d = f.readlines()
#         f.seek(0)
#         for i in d:
#             if not run_number in i:
#                 f.write(i)
#         f.truncate()
#     f.close()
#

# def write_daily_test(run_number, status):
#     date = datetime.datetime.today().strftime('%d%m%Y')
#     results_url = f'http://pepitope.tau.ac.il/results/{run_number}/output.html'
#     with open(path.join(CONSTS.DAILY_TEST_DIR, f'pepitope_{date}.txt'), "w") as f:
#         f.write(f'{status},{results_url}')
#     f.close()


def save_obj(obj, file_path):
    with open(file_path, "wb") as f:
        pickle.dump(obj, f)
    f.close()


def load_obj(file_path):
    with open(file_path, "rb") as f:
        obj = pickle.load(f)
    f.close()
    return obj


def join_list(current_list):
    join_str = ''
    comma = ''
    for n in current_list:
        join_str = join_str + comma + str(n)
        comma = ','
    return join_str


# used by Job_Manager
def dict_key_defined_not_empty(key, form):
    if key not in form.keys():
        return False
    return form[key] != ''


def dict_file_defined_not_empty(key, files):
    if key not in files:
        return False
    return files[key].filename != ''
    # return files[key] != ''


def dict_key_value(key, value, form):
    if key not in form.keys():
        return False
    return form[key] == value


def str_defined_and_not_equal_char(line, ch):
    if not line or line == '':
        return False
    if line[0] != ch:
        return True
    else:
        return False


def check_for_spam(file_name, working_dir):  # check the input for the possible of spammer
    try:
        with open(file_name, "r") as f:
            is_spam = 0
            for line in f:
                if re.search('href\s*\=\s*', line):
                    is_spam = 1
                    break
                if re.search('http.*?\:\/\/', line):
                    is_spam = 1
                    break
        f.close()
        if is_spam:
            with open(path.join(working_dir, file_name)) as f_out:
                pass
            f_out.close()
        return is_spam

    except:
        raise Exception(f"checkForSpam can\'t open file: '{file_name}'", "sys")


def save_file_to_disk(wd, current_logger, file, file_name_on_disk=None):
    current_logger.info('Saving FILE to disk')

    current_logger.info(f'Uploaded file name is:{file.filename}')

    data_path = path.join(f'{wd}/{file_name_on_disk}')
    file.save(data_path)

    '''
    data = form[form_field_name]
    logger.info(f'{uploaded_file_name} first 100 chars are: {data[:100]}\n')

    if file_name_on_disk is None:
        file_name_on_disk = uploaded_file_name
    data_path = path.join(f'{wd}/{file_name_on_disk}')

    with open(data_path, 'wb') as data_f:
        data_f.write(data)
    data_f.close()
    '''

    current_logger.info(f'Uploaded data was saved to {data_path} successfully\n')

    return data_path, file_name_on_disk


def save_text_to_disk(form, wd, current_logger, form_field_name, file_name_on_disk):
    current_logger.info(f'Saving TEXT to disk')

    data = form[form_field_name].rstrip()
    current_logger.info(f'first 100 chars are: {data[:100]}\n')

    data_path = path.join(f'{wd}/{file_name_on_disk}')
    with open(data_path, 'w') as data_f:
        data_f.write(data)
    data_f.close()

    logger.info(f'Uploaded data was saved to {data_path} successfully\n')

    return data_path


def peek_form(form, files, current_logger):
    # logger = logging.getLogger('cgi')
    # for debugging
    sorted_form_keys = sorted(form.keys())
    current_logger.info(f'These are the keys that the CGI received:\n{"; ".join(sorted_form_keys)}\n\n')
    current_logger.info('Form values are:\n')
    for key in sorted_form_keys:
        current_logger.info(f'{key} = {form[key]}')
    if files:
        if 'usrSeq_File' in files:
            file = files['usrSeq_File']
            if file and file.filename != '':
                current_logger.info(f'usrSeq_File = {file.filename}')
            '''
            if form[key].filename:
                logger.info(f'100 first characters of {key} = {form[key][:100]}\n')
            else:
                logger.info(f'{key} = {form[key]}\n')
            '''


def is_float(string):
    try:
        val = float(string)
        return True
    except ValueError:
        return False


def print_remove_site_selection_mask(sp_res_file):
    return_str = ''
    Cutoff_Removed_Pos_Hash = {}
    count_lines = 0
    with open(sp_res_file, 'r') as f:
        for line in f:
            count_lines = count_lines + 1
            line = line.strip()
            if re.search('^[0-9]+', line):
                line_array = line.split()
                if is_float(line_array[2]):
                    score = "{:.3f}".format(float(line_array[2]))
                    # if score == 'nan':
                    #   continue
                    if score in Cutoff_Removed_Pos_Hash.keys():
                        Cutoff_Removed_Pos_Hash[score] = Cutoff_Removed_Pos_Hash[score] + 1
                    else:
                        Cutoff_Removed_Pos_Hash[score] = 1

    f.close()

    return_str = '<select name="cutoff" id="cutoff">'
    for cutoff in sorted(Cutoff_Removed_Pos_Hash.keys()):
        res_bellow_Cutoof = 0
        for score in Cutoff_Removed_Pos_Hash.keys():
            if score < cutoff:
                res_bellow_Cutoof += int(Cutoff_Removed_Pos_Hash[score])
        res_remain_precent = "{:.1f}".format((1 - (res_bellow_Cutoof / count_lines)) * 100)
        if res_remain_precent != '100.0' and res_remain_precent != '0.0' and cutoff != 'nan':
            return_str += f'<option value="{cutoff}">{cutoff} ({res_remain_precent}% of residues remain)</option>'

    return return_str


def print_remove_site_selection_box(sp_res_file, msa_length):
    # return_str = ''
    Cutoff_Removed_Pos_Hash = {}
    with open(sp_res_file, 'r') as f:
        for line in f:
            line = line.strip()
            if re.search('^[0-9]+', line):
                line_array = line.split()
                if is_float(line_array[1]):
                    score = "{:.3f}".format(float(line_array[1]))
                    # if score == 'nan':
                    #   continue
                    if score in Cutoff_Removed_Pos_Hash.keys():
                        Cutoff_Removed_Pos_Hash[score] = Cutoff_Removed_Pos_Hash[score] + 1
                    else:
                        Cutoff_Removed_Pos_Hash[score] = 1

    f.close()
    # KSENIA
    return_str = '<select name="Col_Cutoff" id="Col_Cutoff">'
    for cutoff in sorted(Cutoff_Removed_Pos_Hash.keys()):
        col_bellow_Cutoof = 0
        for score in Cutoff_Removed_Pos_Hash.keys():
            if score < cutoff:
                col_bellow_Cutoof += int(Cutoff_Removed_Pos_Hash[score])
        col_remain_precent = "{:.1f}".format((1 - (col_bellow_Cutoof / msa_length)) * 100)
        if col_remain_precent != '100.0' and col_remain_precent != '0.0' and cutoff != 'nan':
            return_str += f'<option value="{cutoff}">{cutoff} ({col_remain_precent}% of columns remain)</option>'

    return return_str


def print_remove_seq_selection_box(sp_res_file, msa_depth):
    return_str = ''
    Cutoff_Removed_Pos_Hash = {}
    with open(sp_res_file, 'r') as f:
        for line in f:
            line = line.strip()
            if re.search('^[0-9]+', line):
                line_array = line.split()
                if is_float(line_array[1]):
                    score = "{:.3f}".format(float(line_array[1]))
                    if score in Cutoff_Removed_Pos_Hash.keys():
                        Cutoff_Removed_Pos_Hash[score] = Cutoff_Removed_Pos_Hash[score] + 1
                    else:
                        Cutoff_Removed_Pos_Hash[score] = 1

    f.close()

    return_str = '<select name="Seq_Cutoff" id="Seq_Cutoff">'
    for cutoff in sorted(Cutoff_Removed_Pos_Hash.keys()):
        seq_bellow_Cutoof = 0
        for score in Cutoff_Removed_Pos_Hash.keys():
            if score < cutoff:
                seq_bellow_Cutoof += int(Cutoff_Removed_Pos_Hash[score])
        seq_remain_precent = "{:.1f}".format((1 - (seq_bellow_Cutoof / msa_depth)) * 100)
        if seq_remain_precent != '100.0' and seq_remain_precent != '0.0' and cutoff != 'nan':
            return_str += f'<option value="{cutoff}">{cutoff} ({seq_remain_precent}% of sequences remain)</option>'

    return return_str


def print_SuperMSA_selection(AltMSA_list):
    Default_number_of_alternative_MSA_to_concat = 20

    try:
        with open(AltMSA_list, 'r') as f:

            return_str = "<select name=\"NumOfMSAs\" id=\"NumOfMSAs\">"
            AltMSA_to_Concat_including_baseMSA = 0

            for line in f:

                AltMSA_to_Concat_including_baseMSA += 1
                AltMSA_to_Concat = AltMSA_to_Concat_including_baseMSA - 1
                if AltMSA_to_Concat > 0:
                    if AltMSA_to_Concat == Default_number_of_alternative_MSA_to_concat:
                        return_str += (f"<option selected=\"selected\" value=\"{AltMSA_to_Concat_including_baseMSA}\">"
                                       f"{AltMSA_to_Concat}</option> ")
                    else:
                        return_str += (f"<option value=\"{AltMSA_to_Concat_including_baseMSA}\">{AltMSA_to_Concat}"
                                       f"</option> ")

            return_str += "</select>"

            f.close()
            return return_str
    except:
        raise Exception(f"print_SuperMSA_selection: Can't open the list with AltMSA file: '{AltMSA_list}'", "sys")


def file_exists_not_empty(filename):
    if not path.exists(filename):
        return False
    else:
        if path.getsize(filename) > 0:
            return True
        else:
            return False


def convert_fs_to_lower_case(file):
    try:
        with open(file, 'r') as f:
            content = f.read()
        f.close()
    except:
        return f'convert_fs_to_lower_case: Fail to open {file} for reading'

    try:
        with open(file, 'r') as f:
            for line in f:
                if line[0] == '>':
                    f.write(line)
                else:
                    f.write(line.lower())
        f.close()
    except:
        f'convert_fs_to_lower_case: Fail to open {file} for writing'

    return 'OK'


def convert_fs_to_upper_case(file):
    try:
        with open(file, 'r') as f:
            content = f.read()
        f.close()
    except:
        return f'convert_fs_to_upper_case: Fail to open {file} for reading'

    try:
        with open(file, 'r') as f:
            for line in f:
                if line[0] == '>':
                    f.write(line)
                else:
                    f.write(line.upper())
        f.close()
    except:
        f'convert_fs_to_upper_case: Fail to open {file} for writing'

    return 'OK'


def get_job_logger(job_id, server_logs_dir):
    if not path.exists(server_logs_dir):
        makedirs(server_logs_dir)
    current_logger = logging.getLogger(job_id)
    current_logger.setLevel(logging.INFO)  # or whatever
    if len(current_logger.handlers) == 0:
        log_file = path.join(server_logs_dir, f'{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")}_{job_id}.log')
        handler = logging.FileHandler(log_file, 'w', 'utf-8')  # or whatever
        handler.setFormatter(formatter)
        current_logger.addHandler(handler)
        current_logger.propagate = False
    return current_logger


def get_new_process_id():
    time_str = str(round(time()))
    rand_str = str(randint(1000, 9999))
    return f'{time_str}{rand_str}'
