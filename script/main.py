from os import path as ospath
from sys import path as syspath

# Path to the project root
root_path = ospath.abspath(ospath.dirname(ospath.dirname(__file__)))
if root_path not in syspath:
    syspath.insert(0, root_path)

# Path to the script folder
script_path = ospath.abspath(ospath.dirname(__file__))
if script_path not in syspath:
    syspath.insert(0, script_path)

from script.config import Config

if __name__ == '__main__':
    config = Config()
    config.check_and_set_input_and_output_variables()
    config.execute_calculation()
