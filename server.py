#!/bin/python3
from constants import Constants
from db import (
    Database,
    create_client    
)
# third party lib's
import random
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
not_exist_situtations = [None, False]

database_user = create_client('user')
database_reservation = create_client('reservation')
database_siparis = create_client('siparis')

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
            return redirect('/giris')
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return ('.' in filename) and (filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)

def is_logged() -> bool:
    if 'user_id' not in session:
        return False
    else:
        return True
    

def get_session_user() -> dict:
    if 'user_id' not in session:
        return None
    user_id = session['user_id']
    # fetch the user from database somehow
    user = database_user.find_one({
        '_id': user_id
    })
    return user

def get_user_from_id(user_id: str) -> dict:
    return database_user.find_one({
        "_id": user_id
    })

app = Flask(__name__, static_folder='gui_static', template_folder='gui_templates', instance_relative_config=True)
app.secret_key = 'yigitinsifresi'

@app.route('/modify_json/<string:fte>/<string:key>/<string:out>/', methods=["GET"])
def modify_json(fte, key, out):
    if not is_logged():
        return redirect('/giris')
    
    session_user = get_session_user()
    if not session_user['admin']:
        return redirect('/')

    dictionary = {
        "fileToEncrypt": fte,
        "outVideoFile": out,
        "keyFile": key
    }
    json_object = json.dumps(dictionary, indent=4)
    with open("config.json", "w") as outfile:
        outfile.write(json_object)
    
    return redirect("/islemler")

@app.route('/islemler')
def islemler():
    if not is_logged():
        return redirect('/giris')
    
    session_user = get_session_user()
    if not session_user['admin']:
        return redirect('/')

    return render_template('islemler.html')

@app.route('/giris')
def giris():
    return render_template('login.html')

@app.route('/anasayfa/')
@app.route('/anasayfa')
@app.route('/index/')
@app.route('/index')
@app.route('/')
def index():
    if not is_logged():
        return redirect('/giris')
    
    session_user = get_user_from_id(session['user_id'])
    if session_user['admin']:
        elist = open('db/maillist.csv','r').read().replace(' ','\n')
        return render_template('admin_index.html', elist=elist)
    else:
        return render_template('index.html', user=session_user) 
    
@app.route('/admin/anasayfa/')
@app.route('/admin/anasayfa')
@app.route('/admin/index/')
@app.route('/admin/index')
@app.route('/admin/')
@app.route('/admin', methods=["GET", "POST"])
def admin_index():
    if not is_logged():
        return redirect('/giris')
    
    session_user = get_session_user()
    time.sleep(1.5)
    if not session_user['admin']:
        return redirect('/')

    elist = open('db/maillist.csv','r').read().replace(' ','\n')
    return render_template('admin_index.html', elist=elist)

@app.route('/api/ce/')
@app.route('/api/ce', methods=["POST"])
def api_ce(data):
    if not is_logged():
        return redirect('/giris')
    
    session_user = get_session_user()
    if not session_user['admin']:
        return redirect('/')

    session_user = get_session_user()
    random_id = str(uuid.uuid4())
    data = ""
    
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json_req = request.json
        data = json_req['message']
    else:
        data = request.form['message']
    
    splitted_data = data.split(':')
    operation = splitted_data[0]
    message = splitted_data[1]

    if operation.upper() == "RESERVATION":
        splitted_message = message.split(';')
        baslangic_tarihi = splitted_message[0]
        bitis_tarihi = splitted_message[1]
        otel_name = splitted_message[2]
        database_reservation.insert_one({
            '_id': session_user['_id'],
            'case_id': random_id,
            'baslangic_tarihi': baslangic_tarihi,
            'bitis_tarihi': bitis_tarihi,
            'oda_no': random.randint(181, 1453),
            'otel_ismi': otel_name,
        })
    else:
        splitted_message = message.split(';') # SIPARIS:COLA|3;HAMBURGER|2
        siparis_nested_list = []
        for i in len(splitted_message):
            siparisler = splitted_message[i].split('|')
            siparis_nested_list[i] = [siparisler[0], int(siparisler[1])] # => [["COLA", 3], ["HAMBURGER",2]]
        
        database_siparis.insert_one({
            '_id': session_user['_id'],
            'case_id': random_id,
            'istek_siparis': siparis_nested_list,
        })

    out_format = f"{session_user['_id']}_{random_id}"
    complete_encryption(data, f'{out_format}.mp4', f'{out_format}.key')

    if os.fileexist(f'{out_format}.mp4') and os.fileexist(f'{out_format}.key'):
        return render_template('sifreleme_sonuc.html')
    else:
        return render_template('try_again.html')

@app.route('/api/cd/')
@app.route('/api/cd', methods=["POST", "GET"])
def api_cd():
    if not is_logged():
        return redirect('/giris')
    
    session_user = get_session_user()
    if not session_user['admin']:
        return redirect('/')


    global not_exist_situtations
    dosya = request.files['fileupload']
    dosya_adi = dosya.filename
    if allowed_file(dosya_adi):
        splitted_dosya_adi = dosya_adi.split('_')
        user_id = splitted_dosya_adi[0]
        case_id = splitted_dosya_adi[1]

        reservation_case = database_reservation.find_one({
            '_id': user_id,
            'case_id': case_id
        })

        siparis_case = database_siparis.find_one({
            '_id': user_id,
            'case_id': case_id
        })

        # efendim patient //_()_\\
        print(*"\\DEŞİFRELENİYOR...\\")
        if reservation_case in [None, False]:
            siparis_hashmap = {}
            for siparis in siparis_case['istek_siparis']:  # => [["COLA", 3], ["HAMBURGER",2]]
                siparis_hashmap[siparis[0]] = siparis[1]
            
            return jsonify({
                'type': 'SIPARIS',
                'data': siparis_hashmap
            })

        else:
            return jsonify({
                'type': 'RESERVATION',
                'data': reservation_case
            })
    else:
        render_template('try_again.html')

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
    isim = request.form['isim']
    soyisim = request.form['soyisim']
    yas = request.form['yas']
    tc_kimlik_no = request.form['tc_kimlik_no']
    telefon_numarasi = request.form['telefon_numarasi']

    # Kullanıcı veritabanına ekleme kısmı
    is_user_exist = database_user.find_one({
        "email": email,
        "tc_kimlik_no": tc_kimlik_no,
        "telefon_numarasi": telefon_numarasi,
    })
    if (is_user_exist in not_exist_situtations):
        database_user.insert_one({
            ######################################################
            'kullanici_adi': username,                           #
            'sifre': password,                                   #
            'email': email,                                      #
            '_id': str(uuid.uuid4()),                            #
            'isim': isim,                                        #
            'soyisim': soyisim,                                  #
            'admin': False,                                      #
            'yas': yas,                                          #
            'tc_kimlik_no': tc_kimlik_no,                        #
            'telefon_numarasi': telefon_numarasi                 #
            ######################################################
        })

        user = database_user.find_one({'email': email})
        session['user_id'] = str(user['_id'])
        return redirect('/')

    else:
        return render_template('user_exist.html')
    
@app.route('/logout', methods=['GET'])
def logout():
    # Remove the user's id from the session
    session.pop('user_id', None)
    return render_template('logout.html')
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=1, threaded=False)