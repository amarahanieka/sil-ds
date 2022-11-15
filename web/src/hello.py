from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

df = pd.read_excel('notebook/data_penumpang_kapal.xlsx')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data_penumpang_kapal')
def data_penumpang_kapal():
    return render_template('data_penumpang_kapal.html', tables=[df.to_html(classes='data')])

@app.route('/prediksi_kepenuhan')
def prediksi_kepenuhan():
    return render_template('prediksi_kepenuhan.html')