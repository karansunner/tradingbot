from flask import redirect, flash, render_template, url_for, Flask
from sqlalchemy import create_engine
import mysql.connector as sql

app = Flask(__name__)
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.secret_key = "secret123"

db_connection = sql.connect(
    host='localhost', database='ipbdam4', user='root', password='Ipbdam4.')
cursor = db_connection.cursor()

sql_transaction = """SELECT * FROM transaction"""
sql_balance_euro = """SELECT * FROM balance WHERE currency='euro'"""
sql_balance_btc = """SELECT * FROM balance WHERE currency='btc'"""

cursor.execute(sql_transaction)
data = cursor.fetchall()
cursor.execute(sql_balance_btc)
btc = cursor.fetchone()[2]
cursor.execute(sql_balance_euro)
euro = cursor.fetchone()[2]
cursor.close()
db_connection.close()


@app.route('/')
def home():
    return render_template('flask.html', data=data, euro=euro, btc=btc)


@app.route('/candlestick')
def candlestick():
    return render_template('candlestickchart.html')


if __name__ == '__main__':
    app.run(debug=True)
