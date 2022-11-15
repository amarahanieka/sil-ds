from flask import Flask, render_template, request
import pandas as pd
import datetime as dt
import numpy as np
from collections import Counter
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

app = Flask(__name__)

# read the data as a dataframe
df = pd.read_excel('notebook/data_penumpang_kapal.xlsx')

# based on pelabuhan functions
total_kbp = df.groupby('pelabuhan')['kapal_berangkat'].sum()
total_kbp = total_kbp.reset_index()
total_ktp = df.groupby('pelabuhan')['kapal_tiba'].sum()
total_ktp = total_ktp.reset_index()
total_ktp.columns = ['pelabuhan', 'kapal_tiba']
total_pnp = df.groupby('pelabuhan')['penumpang_naik'].sum()
total_pnp = total_pnp.reset_index()
total_pnp.columns = ['pelabuhan', 'penumpang_naik']
total_ptp = df.groupby('pelabuhan')['penumpang_turun'].sum()
total_ptp = total_ptp.reset_index()
total_ptp.columns = ['pelabuhan', 'penumpang_turun']
merge1p = pd.merge(total_kbp, total_ktp, on='pelabuhan', how='inner')
merge2p = pd.merge(merge1p, total_pnp, on='pelabuhan', how='inner')
data_fixp = pd.merge(merge2p, total_ptp, on='pelabuhan', how='inner')
data_df = data_fixp[['kapal_berangkat', 'kapal_tiba', 'penumpang_naik', 'penumpang_turun']]
scaler = StandardScaler()
data_df_scaled = scaler.fit_transform(data_df)
kmeans = KMeans(n_clusters=2, max_iter=50)
kmeans.fit(data_df_scaled)
data_fixp['Cluster'] = kmeans.labels_

# data that have cluster 0
data_fixp0 = data_fixp[data_fixp['Cluster'] == 0]
pelabuhan0 = data_fixp0['pelabuhan'].values.tolist()
# data that have cluster 1
data_fixp1 = data_fixp[data_fixp['Cluster'] == 1]
pelabuhan1 = data_fixp1['pelabuhan'].values.tolist()

# based on tanggal functions
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

data_fix['week'] = data_fix['tanggal'].dt.isocalendar().week % 53 + 1
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

@app.route('/track_focus', methods=['GET', 'POST'])
def track_focus(pelabuhan=None, status=None):
    button1 = request.form.get('button1')
    if button1 == 'add':
        pelabuhan=pelabuhan0
    elif button1 == 'subs':
        pelabuhan=pelabuhan1
    else:
        pelabuhan=None
    return render_template('track_focus.html', status=button1, pelabuhan=pelabuhan)