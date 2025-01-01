from flask import Flask, request, render_template, url_for, flash, jsonify
from tree import Tree
from os import getenv

import array_functions as af
import design_functions as df
import service_functions as serv_f
import statistical_functions as stat_f


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

err = [f'{df.key_design("Incorrect text of newick format. <br>Example of correct text of newick format", True, 13)}',
       f'{df.key_design("The length of the final sequence must match the number of leaves", True, 13)}',
       f'{df.key_design("The tree is not correct. <br>The tree should be binary", True, 13)}',
       f'{df.key_design("Incorrect Le and Gascuel matrix", True, 13)}']
ERRORS = {'incorrect_newick': f'<b>{err[0]}{df.value_design("((S1:0.3,S2:0.15):0.1,S3:0.4);", True, 14)}</b>',
          'incorrect_sequence': f'<b>{err[1]}</b>',
          'incorrect_tree': f'<b>{err[2]}</b>',
          'incorrect_lg_matrix': f'<b>{err[3]}</b>'}


@app.route('/')
@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html', menu=MENU, title=(':', f'  {MENU[0].get("name")}'))


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


@app.route('/compute_likelihood_of_tree', methods=['POST'])
def compute_likelihood_of_tree():
    if request.method == 'POST':
        newick_text = request.form.get('newickText')
        pattern_msa = request.form.get('patternMSA')

        if not Tree.check_newick(newick_text):
            result = ERRORS.get('incorrect_newick')
        elif (Tree(newick_text).get_node_count({'node_type': ['leaf']}) != len(pattern_msa.split('\n')) / 2 !=
              pattern_msa.count('>')):
            result = ERRORS.get('incorrect_sequence')
        elif not Tree(newick_text).check_tree_for_binary():
            result = ERRORS.get('incorrect_tree')
        else:
            statistics = serv_f.compute_likelihood_of_tree(newick_text, pattern_msa)
            result = df.result_design(statistics)

        return jsonify(message=result)