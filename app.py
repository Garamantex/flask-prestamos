from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import User

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/menu-manager')
def menu_manager():
    return render_template('menu-manager.html')

@app.route('/menu-salesman')
def menu_salesman():
    return render_template('menu-salesman.html')

@app.route('/create-client')
def createClient():
    return render_template('create-client.html')

@app.route('/renewal')
def renewal():
    return render_template('renewal.html')

@app.route('/box')
def box():
    return render_template('box.html')

@app.route('/create-box')
def CreateBox():
    return render_template('create-box.html')

@app.route('/box-archive')
def boxArchive():
    return render_template('box-archive.html')

@app.route('/box-detail')
def boxDetail():
    return render_template('box-detail.html')

@app.route('/approval-expenses')
def approvalAxpenses():
    return render_template('approval-expenses.html')

@app.route('/morosos')
def morosos():
    return render_template('morosos.html')

@app.route('/wallet')
def wallet():
    return render_template('wallet.html')

@app.route('/wallet-detail')
def walletDetail():
    return render_template('wallet-detail.html')

@app.route('/credit-detail')
def creditDetail():
    return render_template('credit-detail.html')

@app.route('/create-user')
def createUser():
    return render_template('create-user.html')

@app.route('/user-list')
def userList():
    return render_template('user-list.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/bills')
def bills():
    return render_template('bills.html')

@app.route('/income')
def income():
    return render_template('income.html')

@app.route('/outcome')
def outcome():
    return render_template('outcome.html')

if __name__ == '__main__':
    app.run(debug=True)
