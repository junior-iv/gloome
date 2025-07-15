from flask import Flask, render_template, send_file, json
# , Response, redirect, url_for, request, jsonify)
from SharedConsts import MENU, DEFAULT_FORM_ARGUMENTS, INITIAL_DATA_DIR
from config import FlaskConfig
from os import path
from sys import path as sys_path

root_path = path.abspath(path.dirname(path.dirname(__file__)))
if root_path not in sys_path:
    sys_path.insert(0, root_path)

# Path to the script folder
script_path = path.abspath(path.dirname(__file__))
if script_path not in sys_path:
    sys_path.insert(0, script_path)

from http_utils import *
app = Flask(__name__)
app.config.from_object(FlaskConfig())


@app.route('/')
@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html', menu=MENU, title=(':', f'  {MENU[0].get("name")}'), **DEFAULT_FORM_ARGUMENTS)


@app.route('/results/<process_id>', methods=['GET'])
def get_results(process_id):
    data = get_response(process_id)
    try:
        result = render_template('index.html', menu=MENU, title=data.get('title'), data=json.loads(json.dumps(data)))
    except Exception:
        with open(f'/var/www/vhosts/gloomedev.tau.ac.il/httpdocs/tmp/err.log', 'a') as f:
            f.write(f'\n\n--- Exception at /draw_tree ---\n')
            f.write(traceback.format_exc())
        raise  # Re-raise to still return 500

    return result


@app.route('/overview', methods=['GET'])
def overview():
    return render_template('overview.html', menu=MENU, title=(':', f'  {MENU[1].get("name")}'))


@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html', menu=MENU, title=(':', f'  {MENU[2].get("name")}'))


@app.route('/gallery', methods=['GET'])
def gallery():
    return render_template('gallery.html', menu=MENU, title=(':', f'  {MENU[3].get("name")}'))


@app.route('/source_code', methods=['GET'])
def source_code():
    return render_template('source_code.html', menu=MENU, title=(':', f'  {MENU[4].get("name")}'))


@app.route('/citing_and_credits', methods=['GET'])
def citing_and_credits():
    return render_template('citing_and_credits.html', menu=MENU, title=(':', f'  {MENU[5].get("name")}'))


@app.route('/get_exemple', methods=['GET'])
def get_exemple():
    if request.method == 'GET':
        mode = request.args.get('mode', '')
        result = []
        for i in (f'msa/patternMSA{mode}.msa', f'tree/newickTree{mode}.tree'):
            full_file_name = f'{INITIAL_DATA_DIR}/{i}'
            with open(full_file_name, 'r') as f:
                result.append(f.read())

        return jsonify(message=result)


@app.route('/get_file', methods=['GET'])
def get_file():
    if request.method == 'GET':
        file_path = request.args.get('file_path', '')
        mode = request.args.get('mode', 'view')
        file_exists = path.exists(file_path)
        as_attachment = mode == 'download' and file_exists
        file_path = file_path
        if mode == 'view':
            j = file_path[::-1].find('.')
            file_extension = file_path[-j:]
            if file_extension in ('txt', 'csv', 'tree', 'dot', 'fasta'):
                return send_file(file_path, as_attachment=as_attachment, mimetype='text/plain;charset=UTF-8')

        return send_file(file_path, as_attachment=as_attachment)


@app.route('/create_all_file_types', methods=['POST'])
def create_all_file_types():
    return execute_request(mode=('create_all_file_types', ))


@app.route('/draw_tree', methods=['POST'])
def draw_tree():
    return execute_request(mode=('draw_tree', ))


@app.route('/compute_likelihood_of_tree', methods=['POST'])
def compute_likelihood_of_tree():
    return execute_request(mode=('compute_likelihood_of_tree', ))


@app.route('/execute_all_actions', methods=['POST'])
def execute_all_actions():
    return execute_request(mode=('execute_all_actions', ))


@app.route('/test', methods=['POST'])
def test():
    if request.method == 'POST':
        result = request.form.get('testData')
        print(result)
        return jsonify(message=result)


if __name__ == '__main__':
    app.run(debug=True, port=4000)
