from flask import Flask
from sqlalchemy import create_engine
import psycopg2
from sqlalchemy.engine import create_engine
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey, Sequence
from sqlalchemy.types import *
import CFModel


app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/hello')
def hello():
    return 'Hello World'

if __name__ == '__main__':
    #app.run(debug=True, host="0.0.0.0", port=5000)
    cf = CFModel()
    print(cf.user_vec[2])
   



'''
    print("connect...")
    engine = create_engine('postgresql://lyj:l@localhost:5432/dbtest')
    print("connected")
    metadata = MetaData()
    metadata.bind = engine

    book_table = Table('book', metadata,
    	Column('id', Integer, Sequence('seq_pk'), primary_key=True),
    	Column('title', Unicode(255), nullable=False),
    	)
    metadata.create_all(checkfirst=True)
'''