from flask import Flask
from flask.templating import render_template
app = Flask(__name__)


# Refer to https://flask.palletsprojects.com/en/2.0.x/quickstart/


@app.route('/')
@app.route('/views/')
def index():
    return render_template("your_code.html") 

if __name__ == "__main__":
    app.run(debug=True)