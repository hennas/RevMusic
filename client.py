import json
from flask_cors import CORS
from flask import Flask, render_template

app = Flask(__name__, static_folder='static')
# SOURCE: https://stackoverflow.com/questions/19962699/flask-restful-cross-domain-issue-with-angular-put-options-methods
CORS(app, resources={r"*": {"origins": "*", "allow_headers": "*", "expose_headers": "*"}})


@app.route('/', methods=['GET']) 
def index():
    """
    This is the entrypoint to the client, so using the client starts here
    """
    return app.send_static_file('html/index.html')


# This starts the client
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)