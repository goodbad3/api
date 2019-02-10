from flask import jsonify,Flask
app = Flask(__name__)
@app.route('/')
def index():
	return jsonify({message='hello world'})