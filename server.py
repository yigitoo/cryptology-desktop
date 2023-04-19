#!/bin/python3
from constants import Constants
from db import (
    Database,
    create_client    
)
# third party lib's
import webview
from cli import complete_encryption, complete_decryption
import os
import requests
import os
from flask import (
    Flask,
    request,
    render_template,
    flash,
    url_for,
    session,
    redirect,
    jsonify,
    send_from_directory
)
import bcrypt
import pymongo
from werkzeug.utils import secure_filename
# std lib's
import time
import uuid
import urllib.parse
import threading
import certifi
import json
from functools import wraps

ALLOWED_EXTENSIONS = ['mp4', 'key']
ERR_CODES = [400, 401, 403, 404, 500, 502, 503, 504]

database_user = create_client()
msg_template = """
<center>
    <h1 style="font-size:60px;">
        <u>
            {msg}
        </u>!
    <h1>
</center>
"""
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if is_logged() is not True:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return ('.' in filename) and (filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)

def is_logged() -> bool:
    if 'user_id' not in session:
        return False
    else:
        return True
    
@login_required
def get_session_user() -> dict:
    if 'user_id' not in session:
        return None
    user_id = session['user_id']
    # fetch the user from database somehow
    user = database_user.find_one({
        '_id': user_id
    })
    return user

@login_required
def get_user_from_id(user_id: str) -> dict:
    return database_user.find_one({
        "_id": user_id
    })


app = Flask(__name__, static_folder='gui_static', template_folder='gui_templates', instance_relative_config=True)
app.secret_key = 'yigitinsifresi'

@login_required
@app.route('/modify_json/<string:fte>/<string:key>/<string:out>/', methods=["GET"])
def modify_json(fte, key, out):
    dictionary = {
        "fileToEncrypt": fte,
        "outVideoFile": out,
        "keyFile": key
    }
    json_object = json.dumps(dictionary, indent=4)
    with open("config.json", "w") as outfile:
        outfile.write(json_object)
    
    return redirect("/islemler")

@app.route('/giris')
def giris():
    return render_template('login.html')

@login_required
@app.route('/anasayfa/')
@app.route('/anasayfa')
@app.route('/index/')
@app.route('/index')
@app.route('/', methods=["GET", "POST"])
def ui():
    if is_logged():
        elist = open('db/maillist.csv','r').read().replace(' ','\n')
        return render_template('ui.html', elist=elist)
    else:
        return redirect('/giris')

@app.route('/api/ce/<string:data>', methods=["GET"])
@login_required
def api_ce(data):
    unescaped_data = urllib.parse.unquote(data)
    random_id = uuid.uuid4()
    complete_encryption(unescaped_data, f'{random_id}.mp4', f'{random_id}.key')

    outVideo = ""
    with open('config.json', encoding="utf8") as file:
        json_data = json.load(file)
        outVideo = json_data['outVideoFile']
    if os.fileexist(outVideo):
        return render_template('template.html')
    else:
        return render_template('trysgain.html')
    
@app.route('/api/cd/', methods=["POST", "GET"])
@login_required
def api_cd():
    dosya = request.files['fileupload']
    if allowed_file(dosya.filename):
        # efendim patent //_()_\\
        print(" \\=[[.]-[.]]=\\ ")

@app.route('/login', methods=['POST', 'GET'])
def login():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = request.json
        # Get the user's information from the request
        username = data['username']
        password = data['password']
        # Retrieve the user from the database
        user = database_user.find_one({'kullanici_adi': username})
        # Check that the user exists and the password is correct
        if user and (user['sifre'] == password):
            # Add the user's id to the session
            session['user_id'] = str(user['_id'])
            
            return render_template('login_success.html')
        else:
            return render_template('login_error.html')
    else:
        username = request.form['username']
        password = request.form['password']
        user = database_user.find_one({'kullanici_adi': username})
        if user and (user['sifre'] == password):
            # Add the user's id to the session
            session['user_id'] = str(user['_id'])
            
            return render_template('login_success.html')
        else:
            return render_template('login_error.html')

@app.route('/register', methods=['POST','GET'])
def register():
    # Gönderilen isteğe bağlı kullanıcı parametrelerini eklemek.
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    adaNo = request.form['adaNo']
    parselNo = request.form['parselNo']
    ilTercihi = request.form['ilTercihi']

    # Şifreyi hashleyip veritabanına eklemek için
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Kullanıcı veritabanına ekleme kısmı
    is_user_exist = database_user.find_one({"email": email})
    not_exist_situtations = [None, False]
    if (is_user_exist in not_exist_situtations):
        database_user.insert_one({
            ######################################################
            'username': username,                                #
            'password': hashed_password,                         #
            'email': email,                                      #
            'adaNo': adaNo,                                      #
            'parselNo': parselNo,                                #
            '_id': str(uuid.uuid4()),                            #
            'il': ilTercihi,                                     #
            'user_photos': []                                    #
            ######################################################
        })
        user = database_user.find_one({'email': email})
        session['user_id'] = str(user['_id'])
        return redirect('/')

    else:
        return render_template('user_exist.html')
    
@app.route('/logout', methods=['GET'])
@login_required
def logout():
    # Remove the user's id from the session
    session.pop('user_id', None)
    return render_template('logout.html')
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=1, threaded=False)