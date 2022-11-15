from flask import Flask, render_template, request
import pandas as pd
import datetime as dt
import numpy as np
from collections import Counter

app = Flask(__name__)

# read the data as a dataframe
df = pd.read_excel('notebook/data_penumpang_kapal.xlsx')

# ds functions
total_kb = df.groupby('tanggal')['kapal_berangkat'].sum()
total_kb = total_kb.reset_index()
total_kt = df.groupby('tanggal')['kapal_tiba'].sum()
total_kt = total_kt.reset_index()
total_kt.columns = ['tanggal', 'kapal_tiba']
total_pn = df.groupby('tanggal')['penumpang_naik'].sum()
total_pn = total_pn.reset_index()
total_pn.columns = ['tanggal', 'penumpang_naik']
total_pt = df.groupby('tanggal')['penumpang_turun'].sum()
total_pt = total_pt.reset_index()
total_pt.columns = ['tanggal', 'penumpang_turun']
merge1 = pd.merge(total_kb, total_kt, on='tanggal', how='inner')
merge2 = pd.merge(merge1, total_pn, on='tanggal', how='inner')
data_fix = pd.merge(merge2, total_pt, on='tanggal', how='inner')

data_fix['week'] = data_fix['tanggal'].dt.week % 53 + 1
data_fix['month'] = data_fix['tanggal'].dt.month
data_fix['total_penumpang'] = data_fix['penumpang_naik'] + data_fix['penumpang_turun']

data_fix['season'] = data_fix['total_penumpang'].apply(lambda x: 'high' if x > 1438 else ('normal' if x > 1011 else 'low'))

week_rec = data_fix.groupby('week')['season'].agg(pd.Series.mode)
month_rec = data_fix.groupby('month')['season'].agg(pd.Series.mode)
day_rec = data_fix.groupby('tanggal')['season'].agg(pd.Series.mode)

def predict_season(day, month):
    datetimenya = dt.date(2021, month, day)
    dayofyear = datetimenya.timetuple().tm_yday-1
    week = datetimenya.isocalendar()[1]
    season = []
    try:
        season.append(day_rec[dayofyear])
    except:
        pass
    try:
        season.append(week_rec[week])
    except:
        pass
    try:
        season.append(month_rec[month])
    except:
        pass
    season = np.array(season, dtype=object)
    for i in season:
        if type(i) == np.ndarray:
            season = np.append(season, i)
    cleaned = []
    for i in season:
        if type(i) == str:
            cleaned.append(i)
    return Counter(cleaned).most_common(1)[0][0]  

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data_penumpang_kapal')
def data_penumpang_kapal():
    return render_template('data_penumpang_kapal.html', tables=[df.to_html(classes='data')])

@app.route('/prediksi_kepenuhan', methods=['GET', 'POST'])
def prediksi_kepenuhan(season=None, day=None, month_name=None, year=None):
    date = request.form.get('date')
    if date:
        month = date.split('-')[1]
        day = date.split('-')[2]
        year = date.split('-')[0]
        season = predict_season(int(day), int(month))
        month_name = dt.date(1900, int(month), 1).strftime('%B')
    return render_template('prediksi_kepenuhan.html', season=season, day=day, month=month_name, year=year)