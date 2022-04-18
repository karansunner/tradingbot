from flask import redirect, flash, render_template, url_for, Flask
from sqlalchemy import create_engine
import mysql.connector as sql

app = Flask(__name__)
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.secret_key = "secret123"

db_connection = sql.connect(
    host='localhost', database='ipbdam4', user='root', password='Ipbdam4.')
cursor = db_connection.cursor()

sql_transaction = """SELECT * FROM transaction ORDER BY id DESC"""
sql_balance_euro = """SELECT * FROM balance WHERE currency='euro'"""
sql_balance_btc = """SELECT * FROM balance WHERE currency='btc'"""

sql_aantal_gekocht = """SELECT COUNT(soort) FROM transaction WHERE soort = 'koop'"""
sql_aantal_verkocht = """SELECT COUNT(soort) FROM transaction WHERE soort = 'verkoop'"""
sql_aantal_shorts = """SELECT COUNT(soort) FROM transaction WHERE soort = 'short_gegaan'"""

cursor.execute(sql_transaction)
data = cursor.fetchall()
cursor.execute(sql_balance_btc)
btc = cursor.fetchone()[2]
cursor.execute(sql_balance_euro)
euro = cursor.fetchone()[2]

cursor.execute(sql_aantal_gekocht)
aantal_gekocht = cursor.fetchone()[0]
cursor.execute(sql_aantal_verkocht)
aantal_verkocht = cursor.fetchone()[0]
cursor.execute(sql_aantal_shorts)
aantal_shorts = cursor.fetchone()[0]

cursor.close()
db_connection.close()


winLoss = (euro - 10000)
avgWinLoss = (winLoss/len(data))

winLoss = round(winLoss, 3)
avgWinLoss = round(avgWinLoss, 3)


@app.route('/')
def home():
    return render_template('index.html', data=data, euro=euro, btc=btc, winLoss=winLoss, avgWinLoss=avgWinLoss, aantal_shorts=aantal_shorts, aantal_gekocht=aantal_gekocht, aantal_verkocht=aantal_verkocht)


@app.route('/candlestick')
def candlestick():
    return render_template('candlestickchart.html')


if __name__ == '__main__':
    app.run(debug=True)
