from flask import Flask

app = Flask(__name__)


@app.route('/')
@app.route('/main')
def main_page():
    return open('static/templates/main.html').read()
