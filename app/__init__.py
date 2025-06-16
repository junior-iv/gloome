from flask import Flask, request, render_template, jsonify, send_file, Response, redirect, url_for
from SharedConsts import MENU, DEFAULT_FORM_ARGUMENTS, INITIAL_DATA_DIR, PROGRESS_BAR
from config import FlaskConfig
from os import path
from http_utils import *

# import warnings
# from werkzeug.middleware.proxy_fix import ProxyFix

# TODO think about it
# warnings.filterwarnings("ignore")
app = Flask(__name__)
# TODO think about it
# app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
# app.config.update(MAX_CONTENT_LENGTH=16 * 1024 * 1024,
#                   SECRET_KEY=getenv('SECRET_KEY'),
#                   DEBUG=True)
# app.config.update(**conf.FLASK_CONFIG)
app.config.from_object(FlaskConfig())
# app.config['APPLICATION_ROOT'] = args_config.APPLICATION_ROOT
# app.config['PREFERRED_URL_SCHEME'] = 'https'
# app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
# app.config['UPLOAD_FOLDERS_ROOT_PATH'] = WEBSERVER_RESULTS_DIR # path to folder
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 * 1000 # MAX file size to upload
# app.config['RECAPTCHA_SITE_KEY'] = os.getenv('RECAPTCHA_SITE_KEY')
# app.config['RECAPTCHA_SECRET_KEY'] = os.getenv('RECAPTCHA_SECRET_KEY')
# process_id2update = []

# app.config['PREFERRED_URL_SCHEME'] = PREFERRED_URL_SCHEME
# app.config['DEBUG'] = DEBUG
# app.config['SECRET_KEY'] = SECRET_KEY
# app.config['UPLOAD_FOLDERS_ROOT_PATH'] = CONSTS.WEBSERVER_RESULTS_DIR # path to folder
# app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH # MAX file size to upload
# app.config['use_reloader']=False
# app.config['RECAPTCHA_SITE_KEY'] = getenv('RECAPTCHA_SITE_KEY')
# app.config['RECAPTCHA_SECRET_KEY'] = getenv('RECAPTCHA_SECRET_KEY')
# recaptcha = ReCaptcha(app) # Create a ReCaptcha object by passing in 'app' as parameter


@app.route('/')
@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html', menu=MENU, progress_bar=PROGRESS_BAR,
                           title=(':', f'  {MENU[0].get("name")}'), **DEFAULT_FORM_ARGUMENTS)


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
    print('type(request)')
    print(type(request))
    return execute_response(design=True, mode=('create_all_file_types', ))


@app.route('/draw_tree', methods=['POST'])
def draw_tree():
    print('type(request)')
    print(type(request))
    return execute_response(design=False,  mode=('draw_tree', ))


@app.route('/compute_likelihood_of_tree', methods=['POST'])
def compute_likelihood_of_tree():
    print('type(request)')
    print(type(request))
    return execute_response(design=True, mode=('compute_likelihood_of_tree', ))


#
# @app.route('/get_progress', methods=['POST'])
# def get_progress():
#     if request.method == 'POST':
#         current_progress = request.form.get('current_progress')
#         current_progress
#         result = request.form.get('current_progress')
#         print(result)
#         return jsonify(message=result)


@app.route('/test', methods=['POST'])
def test():
    if request.method == 'POST':
        result = request.form.get('testData')
        print(result)
        return jsonify(message=result)


if __name__ == '__main__':
    app.run(debug=True, port=4000)
