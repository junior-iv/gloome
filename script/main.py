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

from config import Config

if __name__ == '__main__':
    config = Config()
    import json
    with open(f'/var/www/vhosts/gloomedev.tau.ac.il/httpdocs/tmp/kwargs_route_debug.log', 'a') as f:
        f.write(f'\n\n--- vars(config.CURRENT_ARGS) ---\n')
        f.write(json.dumps(vars(config.CURRENT_ARGS)))
    config.check_and_set_input_and_output_variables()
    with open(f'/var/www/vhosts/gloomedev.tau.ac.il/httpdocs/tmp/kwargs_route_debug.log', 'a') as f:
        f.write(f'\n\n--- vars(config.CURRENT_ARGS) ---\n')
        f.write(json.dumps(vars(config.CURRENT_ARGS)))
    config.execute_calculation()
