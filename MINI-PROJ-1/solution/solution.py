from flask import Flask
from flask.templating import render_template
app = Flask(__name__)

@app.route('/')
@app.route('/solution/')
def solution():
    return render_template("solution.html")


if __name__ == "__main__":
    app.run(debug=True)