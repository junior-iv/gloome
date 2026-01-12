from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, render_template, send_file, url_for, request, Response, jsonify

application = Flask(__name__)
application.config.from_pyfile('flask_config.py')
application.wsgi_app = ProxyFix(application.wsgi_app, x_proto=1, x_host=1)


if __name__ == '__main__':
    application.run()
