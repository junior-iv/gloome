import design_functions as df
import service_functions as sf
from flask import Flask, request, render_template, url_for, flash, jsonify, send_file, Response
from tree import Tree
from os import getenv, path

DATA_PATH = ('src/initial_data', 'src/result_data', 'templates/404.html')
RATE_VECTOR = (0.2, 0.7, 1.3, 1.8, )

app = Flask(__name__)
app.config.update(MAX_CONTENT_LENGTH=16 * 1024 * 1024,
                  SECRET_KEY=getenv('SECRET_KEY'),
                  DEBUG=True)

MENU = ({'name': 'HOME', 'url': 'index',
         'submenu': ()
         },
        {'name': 'OVERVIEW', 'url': 'overview',
         'submenu': ()
         },
        {'name': 'FAQ', 'url': 'faq',
         'submenu': ()
         },
        {'name': 'GALLERY', 'url': 'gallery',
         'submenu': ()
         },
        {'name': 'SOURCE CODE', 'url': 'source_code',
         'submenu': ()
         },
        {'name': 'CITING & CREDITS', 'url': 'citing_and_credits',
         'submenu': ()
         }
        )


@app.route('/')
@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html', menu=MENU, newick_tree='', title=(':', f'  {MENU[0].get("name")}'))


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
            full_file_name = f'{DATA_PATH[0]}/{i}'
            with open(full_file_name, 'r') as f:
                result.append(f.read())

        return jsonify(message=result)


@app.route('/get_file', methods=['GET'])
def get_file():
    if request.method == 'GET':
        file_path = DATA_PATH[1] + request.args.get('file_path', '')
        mode = request.args.get('mode', 'view')
        file_exists = path.exists(file_path)
        as_attachment = mode == 'download' and file_exists
        file_path = file_path if file_exists else DATA_PATH[2]
        if mode == 'view':
            j = file_path[::-1].find('.')
            file_extension = file_path[-j:]
            if file_extension in ('txt', 'csv', 'tree', 'dot', 'fasta'):
                return send_file(file_path, as_attachment=as_attachment, mimetype='text/plain;charset=UTF-8')

        return send_file(file_path, as_attachment=as_attachment)


@app.route('/create_all_file_types', methods=['POST'])
def create_all_file_types():
    if request.method == 'POST':
        newick_text = request.form.get('newickText')
        pattern_msa = request.form.get('patternMSA')
        err_list = sf.check_form(newick_text, pattern_msa)

        if err_list:
            status = 400
            result = sf.get_error(err_list)
        else:
            status = 200
            file_list = sf.create_all_file_types(newick_text, pattern_msa, DATA_PATH[1], RATE_VECTOR)
            result = df.result_design(file_list)

        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')


@app.route('/draw_tree', methods=['POST'])
def draw_tree():
    if request.method == 'POST':
        newick_text = request.form.get('newickText')
        pattern_msa = request.form.get('patternMSA')
        err_list = sf.check_form(newick_text, pattern_msa)

        if err_list:
            status = 400
            result = sf.get_error(err_list)
        else:
            status = 200
            result = []
            newick_tree = Tree.rename_nodes(newick_text)
            pattern_dict = newick_tree.get_pattern_dict(pattern_msa)
            alphabet = Tree.get_alphabet_from_dict(pattern_dict)
            newick_tree.calculate_tree_for_fasta(pattern_dict, alphabet, RATE_VECTOR)
            newick_tree.calculate_ancestral_sequence()
            result.append(newick_tree.get_json_structure())
            result.append(newick_tree.get_json_structure(return_table=True))
            result.append(Tree.get_columns_list_for_sorting())

        # return jsonify(message=result)
        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')


@app.route('/compute_likelihood_of_tree', methods=['POST'])
def compute_likelihood_of_tree():
    if request.method == 'POST':
        newick_text = request.form.get('newickText')
        pattern_msa = request.form.get('patternMSA')
        err_list = sf.check_form(newick_text, pattern_msa)

        if err_list:
            status = 400
            result = sf.get_error(err_list)
        else:
            status = 200
            statistics = sf.compute_likelihood_of_tree(newick_text, pattern_msa, RATE_VECTOR)
            result = df.result_design((statistics))

        return Response(response=jsonify(message=result).response, status=status, mimetype='application/json')


@app.route('/test', methods=['POST'])
def test():
    if request.method == 'POST':
        result = request.form.get('testData')
        print(result)
        return jsonify(message=result)


if __name__ == '__main__':
    app.run(port=3000, debug=True)
