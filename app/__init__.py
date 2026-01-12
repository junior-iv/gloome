from app.http_utils import *


@application.route('/')
@application.route('/index', methods=['GET'])
def index():
    return render_template('index.html', menu=MENU, title=(':', f'  {MENU[0].get("name")}'), **DEFAULT_FORM_ARGUMENTS)


@application.route('/results/<process_id>', methods=['GET'])
def get_results(process_id):
    return render_template('index.html', menu=MENU, title=(':', ), data=get_response(process_id=process_id))


@application.route('/logs/<process_id>', methods=['GET'])
def get_logs(process_id):
    return send_file(path.join(SERVERS_LOGS_DIR, f'{process_id}.log'), as_attachment=False, mimetype='text/html')


@application.route('/job_status/<process_id>', methods=['GET'])
def job_status(process_id):
    status = get_job_status(process_id)

    return jsonify(status)


@application.route('/read_json_file', methods=['POST'])
def read_json_file():
    json_string = request.form.get('json_string', None) if request.method == 'POST' else None

    return read_json(json_string=json_string)


@application.route('/overview', methods=['GET'])
def overview():
    return render_template('overview.html', menu=MENU, title=(':', f'  {MENU[1].get("name")}'))


@application.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html', menu=MENU, title=(':', f'  {MENU[2].get("name")}'))


@application.route('/gallery', methods=['GET'])
def gallery():
    return render_template('gallery.html', menu=MENU, title=(':', f'  {MENU[3].get("name")}'))


@application.route('/source_code', methods=['GET'])
def source_code():
    return render_template('source_code.html', menu=MENU, title=(':', f'  {MENU[4].get("name")}'))


@application.route('/citing_and_credits', methods=['GET'])
def citing_and_credits():
    return render_template('citing_and_credits.html', menu=MENU, title=(':', f'  {MENU[5].get("name")}'))


@application.route('/get_exemple', methods=['GET'])
def get_exemple():
    if request.method == 'GET':
        mode = request.args.get('mode', '')
        result = []
        for i in (f'msa/patternMSA{mode}.msa', f'tree/newickTree{mode}.tree'):
            full_file_name = f'{INITIAL_DATA_DIR}/{i}'
            with open(full_file_name, 'r') as f:
                result.append(f.read().strip())

        return jsonify(message=result)
#
#
# @app.route('/send_reports', methods=['GET'])
# def send_reports():
#     if request.method == 'GET':
#
#         return send_report()


@application.route('/get_file', methods=['GET'])
def get_file():
    if request.method == 'GET':
        file_path = request.args.get('file_path', '')
        if request.args.get('mode', 'view') == 'view':
            file_extension = path.splitext(file_path)[1][1:]
            if file_extension in ('html', 'htm'):
                return send_file(file_path, as_attachment=False, mimetype='text/html')
            elif file_extension in ('txt', 'nwk', 'tree', 'dot', 'fasta', 'log', 'csv', 'tsv'):
                return send_file(file_path, as_attachment=False, mimetype='text/plain')
            # elif file_extension in ('csv', ):
            #     return send_file(file_path, as_attachment=False, mimetype='text/csv')
            # elif file_extension in ('tsv', ):
            #     return send_file(file_path, as_attachment=False, mimetype='text/tab-separated-values')
            elif file_extension in ('png', ):
                return send_file(file_path, as_attachment=False, mimetype='image/png')
            elif file_extension in ('svg', ):
                return send_file(file_path, as_attachment=False, mimetype='image/svg+xml')
            elif file_extension in ('jpeg', 'jpg'):
                return send_file(file_path, as_attachment=False, mimetype='image/jpeg')
            elif file_extension in ('json', ):
                return send_file(file_path, as_attachment=False, mimetype='application/json')
            elif file_extension in ('zip', ):
                return send_file(file_path, as_attachment=False, mimetype='application/zip')
            elif file_extension in ('rar', ):
                return send_file(file_path, as_attachment=False, mimetype='application/x-rar-compressed')
            elif file_extension in ('7z', ):
                return send_file(file_path, as_attachment=False, mimetype='application/x-7z-compressed')
            elif file_extension in ('gz', 'tgz'):
                return send_file(file_path, as_attachment=False, mimetype='application/gzip')
            elif file_extension in ('tar', ):
                return send_file(file_path, as_attachment=False, mimetype='application/x-tar')
            elif file_extension in ('pdf', ):
                return send_file(file_path, as_attachment=False, mimetype='application/pdf')
            elif file_extension in ('doc', 'dot', 'wiz'):
                return send_file(file_path, as_attachment=False, mimetype='application/msword')
            elif file_extension in ('docx', ):
                return send_file(file_path, as_attachment=False,
                                 mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            elif file_extension in ('xls', 'xlt', 'xla'):
                return send_file(file_path, as_attachment=False, mimetype='application/vnd.ms-excel')
            elif file_extension in ('xlsx', ):
                return send_file(file_path, as_attachment=False,
                                 mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            elif file_extension in ('ppt', 'pps', 'pps'):
                return send_file(file_path, as_attachment=False, mimetype='application/vnd.ms-powerpoint')
            elif file_extension in ('pptx', ):
                return send_file(file_path, as_attachment=False,
                                 mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
            elif file_extension in ('ppsx', ):
                return send_file(file_path, as_attachment=False,
                                 mimetype='application/vnd.openxmlformats-officedocument.presentationml.slideshow')

        return send_file(file_path, as_attachment=True)


@application.route('/create_all_file_types', methods=['POST'])
def create_all_file_types():
    return execute_request(mode=('create_all_file_types', ))


@application.route('/draw_tree', methods=['POST'])
def draw_tree():
    return execute_request(mode=('draw_tree', ))


@application.route('/compute_likelihood_of_tree', methods=['POST'])
def compute_likelihood_of_tree():
    return execute_request(mode=('compute_likelihood_of_tree', ))


@application.route('/execute_all_actions', methods=['POST'])
def execute_all_actions():
    return execute_request(mode=('execute_all_actions', ))


@application.route('/test', methods=['POST'])
def test():
    if request.method == 'POST':
        result = request.form.get('testData')
        print(result)
        return jsonify(message=result)
