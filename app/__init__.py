from script import design_functions as df, service_functions as sf
from flask import Flask, request, render_template, jsonify, send_file, Response
from script.tree import Tree
from script.config import Config
from os import path
# from SharedConsts import *

# import warnings
# from werkzeug.middleware.proxy_fix import ProxyFix

# TODO think about it
# warnings.filterwarnings("ignore")
conf = Config()

app = Flask(__name__)
# TODO think about it
# app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
# app.config.update(MAX_CONTENT_LENGTH=16 * 1024 * 1024,
#                   SECRET_KEY=getenv('SECRET_KEY'),
#                   DEBUG=True)
app.config.update(**conf.FLASK_CONFIG)
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
    return render_template('index.html', menu=conf.MENU, progress_bar=conf.PROGRESS_BAR,
                           title=(':', f'  {conf.MENU[0].get("name")}'), **conf.DEFAULT_FORM_ARGUMENTS)


@app.route('/overview', methods=['GET'])
def overview():
    return render_template('overview.html', menu=conf.MENU, title=(':', f'  {conf.MENU[1].get("name")}'))


@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html', menu=conf.MENU, title=(':', f'  {conf.MENU[2].get("name")}'))


@app.route('/gallery', methods=['GET'])
def gallery():
    return render_template('gallery.html', menu=conf.MENU, title=(':', f'  {conf.MENU[3].get("name")}'))


@app.route('/source_code', methods=['GET'])
def source_code():
    return render_template('source_code.html', menu=conf.MENU, title=(':', f'  {conf.MENU[4].get("name")}'))


@app.route('/citing_and_credits', methods=['GET'])
def citing_and_credits():
    return render_template('citing_and_credits.html', menu=conf.MENU, title=(':', f'  {conf.MENU[5].get("name")}'))


@app.route('/get_exemple', methods=['GET'])
def get_exemple():
    if request.method == 'GET':
        mode = request.args.get('mode', '')
        result = []
        for i in (f'msa/patternMSA{mode}.msa', f'tree/newickTree{mode}.tree'):
            full_file_name = f'{conf.INITIAL_DATA_DIR}/{i}'
            with open(full_file_name, 'r') as f:
                result.append(f.read())

        return jsonify(message=result)


@app.route('/get_file', methods=['GET'])
def get_file():
    if request.method == 'GET':
        file_path = conf.SERVERS_RESULTS_DIR + request.args.get('file_path', '')
        mode = request.args.get('mode', 'view')
        file_exists = path.exists(file_path)
        as_attachment = mode == 'download' and file_exists
        file_path = file_path if file_exists else conf.ERROR_TEMPLATE
        if mode == 'view':
            j = file_path[::-1].find('.')
            file_extension = file_path[-j:]
            if file_extension in ('txt', 'csv', 'tree', 'dot', 'fasta'):
                return send_file(file_path, as_attachment=as_attachment, mimetype='text/plain;charset=UTF-8')

        return send_file(file_path, as_attachment=as_attachment)


@app.route('/create_all_file_types', methods=['POST'])
def create_all_file_types():
    if request.method == 'POST':
        newick_text, pattern_msa, categories_quantity, alpha, is_radial_tree, show_distance_to_parent = (
            sf.get_tree_variables(dict(request.form)))
        beta = alpha
        err_list = sf.check_form(newick_text, pattern_msa)

        if err_list:
            status = 400
            result = sf.get_error(err_list)
        else:
            status = 200
            rate_vector = Tree.get_gamma_distribution_categories_vector(categories_quantity, alpha, beta)
            file_list = sf.create_all_file_types(newick_text, pattern_msa, conf.SERVERS_RESULTS_DIR, rate_vector)
            result = df.result_design(file_list)

        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')


@app.route('/draw_tree', methods=['POST'])
def draw_tree():
    if request.method == 'POST':
        newick_text, pattern_msa, categories_quantity, alpha, is_radial_tree, show_distance_to_parent = (
            sf.get_tree_variables(dict(request.form)))
        beta = alpha
        err_list = sf.check_form(newick_text, pattern_msa)

        if err_list:
            status = 400
            result = sf.get_error(err_list)
        else:
            status = 200
            rate_vector = Tree.get_gamma_distribution_categories_vector(categories_quantity, alpha, beta)
            result = []
            newick_tree = Tree.rename_nodes(newick_text)
            pattern_dict = newick_tree.get_pattern_dict(pattern_msa)
            alphabet = Tree.get_alphabet_from_dict(pattern_dict)
            newick_tree.calculate_tree_for_fasta(pattern_dict, alphabet, rate_vector)
            newick_tree.calculate_ancestral_sequence()
            result.append(newick_tree.get_json_structure())
            result.append(newick_tree.get_json_structure(return_table=True))
            result.append(Tree.get_columns_list_for_sorting())
            size_factor = min(1 + newick_tree.get_node_count({'node_type': ['leaf']}) // 7, 3)
            result.append([size_factor, int(is_radial_tree), int(show_distance_to_parent)])

        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')


@app.route('/compute_likelihood_of_tree', methods=['POST'])
def compute_likelihood_of_tree():
    if request.method == 'POST':
        newick_text, pattern_msa, categories_quantity, alpha, is_radial_tree, show_distance_to_parent = (
            sf.get_tree_variables(dict(request.form)))
        beta = alpha
        err_list = sf.check_form(newick_text, pattern_msa)

        if err_list:
            status = 400
            result = sf.get_error(err_list)
        else:
            status = 200
            rate_vector = Tree.get_gamma_distribution_categories_vector(categories_quantity, alpha, beta)
            statistics = sf.compute_likelihood_of_tree(newick_text, pattern_msa, rate_vector)
            result = df.result_design(statistics)

        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')

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
