import sys,os
from flask import jsonify,Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
app = Flask('test')
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'
app.config['TODOISM_ITEM_PER_PAGE'] = 2
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',prefix + os.path.join(os.path.dirname(app.root_path), 'data.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'axx'
db = SQLAlchemy(app)
CORS(app)


from  test import resources,auth,schemas,models,errors

