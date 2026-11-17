from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, render_template, send_file, url_for, request, Response, jsonify

app = Flask(__name__)
app.config.from_pyfile('flask_config.py')
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


if __name__ == '__main__':
    app.run()
