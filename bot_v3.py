###
# imports en instellingen
###
import talib
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
from binance.client import Client
import mysql.connector as sql
import plotly.graph_objects as go
pd.options.mode.chained_assignment = None   # default='warn'

###
# connectie maken met mysql (om dataframes weg te schrijven)
###
my_conn = create_engine("mysql+mysqldb://root:Ipbdam4.@localhost/ipbdam4")
api_key = 'aXwZIou0oBBlA6K9RWaniRPpBvLRLz1Yi8eBb9P6fKEVHm84T50Iaoab05zt9o4r'
api_secret = 'jwrIenEPTo4oQxcHcAprgLPdIzHkbUGfGUs37Sz1MrybMotSdPIKSWWEhPOCkDpI'
client = Client(api_key, api_secret)

###
# connectie maken met mysql (updaten/ophalen variabelen uit  tabellen)
###
db_connection = sql.connect(
    host='localhost', database='ipbdam4', user='root', password='Ipbdam4.')
cursor = db_connection.cursor()

euro_balance_sql = '''select * from balance where id=0'''
btc_balance_sql = '''select * from balance where id=1'''
status_sql = '''select * from state'''
sql_figuur = """SELECT * FROM transaction"""
short_balance_btc_sql = """SELECT * from short WHERE id=1"""
short_balance_eur_sql = """SELECT * from short WHERE id=0"""
short_close_sql = """SELECT * FROM short WHERE id=2"""

cursor.execute(sql_figuur)
candle_data = cursor.fetchall()  # global var (data om candlestick te maken)

cursor.execute(status_sql)
state = cursor.fetchone()[1]  # globale var

cursor.execute(euro_balance_sql)
euro_balance = cursor.fetchone()[2]  # globale var

cursor.execute(btc_balance_sql)
btc_balance = cursor.fetchone()[2]  # globale var

cursor.execute(short_balance_btc_sql)
short_btc_balance = cursor.fetchone()[2]  # globale var

cursor.execute(short_balance_eur_sql)
short_eur_balance = cursor.fetchone()[2]  # globale var

cursor.execute(short_close_sql)
short_close = cursor.fetchone()[2]  # globale var

cursor.close()
db_connection.close()

###
# functies voor candlestick definities
###


def bullMarubozu(dataframe):
    return float(dataframe.open) == float(dataframe.low) and float(dataframe.close) == float(dataframe.high)


def bearMarubozu(dataframe):
    return float(dataframe.open) == float(dataframe.high) and float(dataframe.close) == float(dataframe.low)


def bullLongCandle(dataframe):
    return ((float(dataframe.close) > float(dataframe.open)) and ((float(dataframe.close) - float(dataframe.open))/(0.001 + float(dataframe.high) - float(dataframe.low)) > 0.6))


def bearLongCandle(dataframe):
    return ((float(dataframe.open) > float(dataframe.close)) and ((float(dataframe.open) - float(dataframe.close))/(0.001 + float(dataframe.high) - float(dataframe.low)) > 0.6))


def dragonflyDoji(dataframe):
    return ((float(dataframe.high) - float(dataframe.low)) > 3 * abs(float(dataframe.open) - float(dataframe.close))) and ((float(dataframe.close) - float(dataframe.low)) > 0.8*(float(dataframe.high) - float(dataframe.low))) and ((float(dataframe.open) - float(dataframe.low)) > 0.8*(float(dataframe.high) - float(dataframe.low)))


def gravestoneDoji(dataframe):
    if talib.CDLGRAVESTONEDOJI(dataframe.open, dataframe.high, dataframe.low, dataframe.close)[0] == -100:
        return True

###
# functie om dataframe weg te schrijven naar database
###


def wegschrijven_db(dataframe, tabel):
    dataframe.to_sql(con=my_conn, name=tabel,
                     if_exists='append', index=False)

###
# functie om waardes in dataframe in te vullen
###


def toevoegen(dataframe, kolom, waarde):
    dataframe.loc[0, kolom] = waarde

###
# functie om de bitcoin en euro balance te updaten in de database
###


def saldo_updaten(euro_balance, btc_balance):
    db_connection = sql.connect(
        host='localhost', database='ipbdam4', user='root', password='Ipbdam4.')
    cursor = db_connection.cursor()
    saldo_update_euro_sql = f'''UPDATE balance SET balance = {euro_balance} WHERE currency="euro"'''
    saldo_update_btc_sql = f'''UPDATE balance SET balance = {btc_balance} WHERE currency="btc"'''
    cursor.execute(saldo_update_euro_sql)
    cursor.execute(saldo_update_btc_sql)
    db_connection.commit()
    cursor.close()
    db_connection.close()

###
# functie om variabelen in tabel short te updaten
###


def short_saldo_updaten(short_eur_balance, short_btc_balance, short_close):
    db_connection = sql.connect(
        host='localhost', database='ipbdam4', user='root', password='Ipbdam4.')
    cursor = db_connection.cursor()
    short_eur_update_sql = f"""UPDATE short SET waarde = {short_btc_balance} WHERE short_variabelen='short_btc'"""
    short_btc_update_sql = f"""UPDATE short SET waarde = {short_eur_balance} WHERE short_variabelen='short_eur'"""
    short_close_update_sql = f"""UPDATE short SET waarde = {short_close} WHERE short_variabelen='short_close'"""
    cursor.execute(short_eur_update_sql)
    cursor.execute(short_btc_update_sql)
    cursor.execute(short_close_update_sql)
    db_connection.commit()
    cursor.close()
    db_connection.close()

###
# functie om de status te updaten in de database (gekocht, verkocht, short_gegaan, short_voltooid)
###


def status_updaten(status):
    db_connection = sql.connect(
        host='localhost', database='ipbdam4', user='root', password='Ipbdam4.')
    cursor = db_connection.cursor()
    state_update_sql = f"""UPDATE state SET state = '{status}' WHERE id=0"""
    cursor.execute(state_update_sql)
    db_connection.commit()
    cursor.close()
    db_connection.close()

###
# functie om Bitcoin te kopen
###


def kopen(dataframe):
    global euro_balance, btc_balance
    price = float(dataframe.close)
    date = dataframe.date
    pattern = dataframe.Candlestick
    aantal_btc = (100/price)
    open = dataframe.open
    close = dataframe.close
    high = dataframe.high
    low = dataframe.low
    euro_balance -= 100
    btc_balance += aantal_btc
    transaction_dict = {
        'date_time': date,
        'soort': 'koop',
        'price': price,
        'bitcoin': aantal_btc,
        'pattern': pattern,
        'open': open,
        'low': low,
        'high': high,
        'close': close
    }
    transaction_df = pd.DataFrame.from_dict(transaction_dict)
    wegschrijven_db(transaction_df, 'transaction')
    saldo_updaten(euro_balance, btc_balance)
    status_updaten('gekocht')

###
# functie om de bitcoin te verkopen
###


def verkopen(dataframe):
    global euro_balance, btc_balance
    oude_btc_balance = btc_balance
    price = float(dataframe.close)
    date = dataframe.date
    open = dataframe.open
    close = dataframe.close
    low = dataframe.low
    high = dataframe.high
    pattern = dataframe.Candlestick
    euro_balance += btc_balance * float(dataframe.close)
    btc_balance -= btc_balance
    transaction_dict = {
        'date_time': date,
        'soort': 'verkoop',
        'price': price,
        'bitcoin': oude_btc_balance,
        'pattern': pattern,
        'open': open,
        'low': low,
        'high': high,
        'close': close
    }
    transaction_df = pd.DataFrame.from_dict(transaction_dict)
    wegschrijven_db(transaction_df, 'transaction')
    saldo_updaten(euro_balance, btc_balance)
    status_updaten('verkocht')


###
# functie waarmee short wordt gegaan
###

def short_verkopen(dataframe):
    global short_btc_balance, short_eur_balance, euro_balance, btc_balance
    short_close = float(dataframe.close)
    short_btc_balance += abs((100 / short_close))
    short_eur_balance += 100
    euro_balance += 100
    btc_balance -= abs((100 / short_close))

    price = float(dataframe.close)
    date = dataframe.date
    open = dataframe.open
    close = dataframe.close
    low = dataframe.low
    high = dataframe.high
    pattern = dataframe.Candlestick

    transaction_dict = {
        'date_time': date,
        'soort': 'short_gegaan',
        'price': price,
        'bitcoin': short_btc_balance,
        'pattern': pattern,
        'open': open,
        'low': low,
        'high': high,
        'close': close
    }
    transaction_df = pd.DataFrame.from_dict(transaction_dict)
    wegschrijven_db(transaction_df, 'transaction')
    short_saldo_updaten(short_eur_balance, short_btc_balance, short_close)
    saldo_updaten(euro_balance, btc_balance)
    status_updaten('short_gegaan')


###
# functie om de short actie te vooltooien
###
def short_voltooien(dataframe):
    global btc_balance, euro_balance, short_eur_balance, short_btc_balance
    btc_balance += short_btc_balance
    euro_balance -= (short_btc_balance * float(dataframe.close))

    price = float(dataframe.close)
    date = dataframe.date
    open = dataframe.open
    close = dataframe.close
    low = dataframe.low
    high = dataframe.high
    pattern = dataframe.Candlestick

    transaction_dict = {
        'date_time': date,
        'soort': 'short_voltooid',
        'price': price,
        'bitcoin': short_btc_balance,
        'pattern': pattern,
        'open': open,
        'low': low,
        'high': high,
        'close': close
    }
    transaction_df = pd.DataFrame.from_dict(transaction_dict)
    wegschrijven_db(transaction_df, 'transaction')
    short_saldo_updaten(0, 0, 0)
    saldo_updaten(euro_balance, btc_balance)
    status_updaten('short_voltooid')

###
# functie om de candlestick te herkennen en vervolgens te kopen/verkopen/short gaan/short voltooien/niks doen
###


def welk_Candlestick(dataframe):
    global state
    if bullMarubozu(dataframe):
        toevoegen(dataframe, 'Candlestick', 'Bull_Marubozu')
        toevoegen(dataframe, 'Advise', 'Kopen')
        wegschrijven_db(dataframe, 'hloc')
        if state == 'verkocht' or state == 'None' or state == 'short_voltooid':
            kopen(dataframe)
        elif state == 'gekocht':
            verkopen(dataframe)
        elif state == 'short_gegaan':
            short_voltooien(dataframe)

    elif bearMarubozu(dataframe):
        toevoegen(dataframe, 'Candlestick', 'Bear_Marubozu')
        toevoegen(dataframe, 'Advise', 'Verkopen')
        wegschrijven_db(dataframe, 'hloc')
        if state == 'gekocht':
            verkopen(dataframe)
        elif state == 'verkocht':
            short_verkopen(dataframe)
        elif state == 'short_gegaan':
            short_voltooien(dataframe)
        elif state == 'None':
            short_verkopen(dataframe)

    elif bullLongCandle(dataframe):
        toevoegen(dataframe, 'Candlestick', 'Bull_Long_Candle')
        toevoegen(dataframe, 'Advise', 'Kopen')
        wegschrijven_db(dataframe, 'hloc')
        if state == 'verkocht' or state == 'None' or state == 'short_voltooid':
            kopen(dataframe)
        elif state == 'gekocht':
            verkopen(dataframe)
        elif state == 'short_gegaan':
            short_voltooien(dataframe)

    elif bearLongCandle(dataframe):
        toevoegen(dataframe, 'Candlestick', 'Bear_Long_Candle')
        toevoegen(dataframe, 'Advise', 'Verkopen')
        wegschrijven_db(dataframe, 'hloc')
        if state == 'gekocht':
            verkopen(dataframe)
        elif state == 'verkocht':
            short_verkopen(dataframe)
        elif state == 'short_gegaan':
            short_voltooien(dataframe)
        elif state == 'None':
            short_verkopen(dataframe)

    elif dragonflyDoji(dataframe):
        toevoegen(dataframe, 'Candlestick', 'Dragonfly_Doji')
        toevoegen(dataframe, 'Advise', 'Kopen')
        wegschrijven_db(dataframe, 'hloc')
        if state == 'verkocht' or state == 'None' or state == 'short_voltooid':
            kopen(dataframe)
        elif state == 'gekocht':
            verkopen(dataframe)
        elif state == 'short_gegaan':
            short_voltooien(dataframe)

    elif gravestoneDoji == 100:
        toevoegen(dataframe, 'Candlestick', 'Gravestone_Doji')
        toevoegen(dataframe, 'Advise', 'Verkopen')
        wegschrijven_db(dataframe, 'hloc')
        if state == 'gekocht':
            verkopen(dataframe)
        elif state == 'verkocht':
            short_verkopen(dataframe)
        elif state == 'short_gegaan':
            short_voltooien(dataframe)
        elif state == 'None':
            short_verkopen(dataframe)

    else:
        toevoegen(dataframe, 'Candlestick', 'GEEN_PATROON')
        toevoegen(dataframe, 'Advise', 'Niks doen')
        wegschrijven_db(dataframe, 'hloc')
        if state == 'short_gegaan':
            short_voltooien(dataframe)
        elif state == 'gekocht':
            verkopen(dataframe)


###
# als het 21:00 uur is, wordt alle Bitcoin verkocht
# schduler runt het script 10 seconden voor elk uurinterval, daarom tijd==20
###
tijd = datetime.now().hour

if tijd == 20:
    data = client.get_historical_klines('BTCEUR', '1h', '1 hour ago')
    euro_balance += float(data[0][4]) * btc_balance
    btc_balance -= btc_balance
    saldo_updaten(euro_balance, btc_balance)
    status_updaten('None')

###
# tussen 09:00 en 21:00 wordt elk uur nieuwe data opgehaald en wordt er gehandeld
###
if 10 <= tijd < 20:
    data = client.get_historical_klines('BTCEUR', '1h', '1 hour ago')
    for kolom in data:
        del kolom[5:]
        kolom[0] = datetime.fromtimestamp(kolom[0]/1000)
    df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close'])

    df['Candlestick'] = ''
    df['Advise'] = ''

    welk_Candlestick(df)


candles_df = pd.DataFrame(candle_data, columns=[
    'id', 'date_time', 'soort', 'price', 'bitcoin', 'pattern', 'open', 'low', 'high', 'close'])

fig = go.Figure(data=[go.Candlestick(x=candles_df.date_time,
                open=candles_df.open,
                high=candles_df.high,
                low=candles_df.low,
                close=candles_df.close)])

fig.update_layout(
    title='BTC-EUR Candlestick',
    yaxis_title='Price',
    xaxis_title='Date'
)
path = r'C:\Users\Majd\Desktop\bot\templates\candlestickchart.html'
fig.write_html(path)
