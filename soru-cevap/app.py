from flask import Flask, render_template

app = Flask(__name__)
title = "KODLARIN SEYYAHI | SORU-CEVAP BONUSU"

@app.route('/')
def index():
    return render_template('index.html', TITLE=title)

@app.route('/getstat')
def getstat():
    return render_template('getstat.html')
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000, debug=1)
