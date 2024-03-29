#!/bin/python3
from constants import Constants
from db import (
    Database,
    create_client    
)
# third party lib's
import random
from bson.objectid import ObjectId
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
from flask_qrcode import QRcode
from werkzeug.utils import secure_filename
# std lib's
import string
from datetime import date
import time
import uuid
import urllib.parse
import threading
import certifi
import json
from functools import wraps

ALLOWED_EXTENSIONS = ['mp4', 'key']
ERR_CODES = [400, 401, 403, 404, 500, 502, 503, 504]
non_exist_situations = [None, False]

database_user = create_client('user')
database_reservation = create_client('reservation')
database_siparis = create_client('siparis')
database_roomswitch = create_client('room_switch')
site_link = "http://localhost:8080"

item_list = ['BURGER', 'LAZANYA', 'OMLET', 'SERPME_KAHVALTI', 'PORTAKAL_SUYU', 'AYRAN', 'SU']
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
        session_user = get_session_user()  
        if session_user == None:
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
    return database_user.find_one({
        '_id': user_id
    })
    '''
    YARDIMA İHTİYACIM VAR 3 GÜNDE BU GÖRDÜĞÜNÜZ BÜTÜN KODLARI YAZDIM PLS HELPPP!!!
        {
            kullanici_adi: yigit
            isim: Yiğit
            soyisim: GÜMÜŞ
            yas: 16
            tc: 12345678901
            tel: +90 552 354 8503
            admin: true
            sifre: 588 259 8353
        }
    '''

def get_user_from_id(user_id: str) -> dict:
    return database_user.find_one({
        "_id": user_id
    })

app = Flask(__name__, static_folder='gui_static', template_folder='gui_templates', instance_relative_config=True)
app.secret_key = 'yigitinsifresi'
qrcode = QRcode(app)

@app.route('/gonder/<string:email>', methods=["GET"])
def gonder(email: str):
    session_user = get_session_user()
    if (session_user == None) or (session_user['admin'] == False):
        return redirect('/giris')
    user = database_user.find_one({
        'email': email
    })
    siparis = database_siparis.find_one({
        '_id': user['_id']
    })
    if siparis not in non_exist_situations:
        database_siparis.delete_one(siparis)
        
        return redirect('/oda_servisi')
    else:
        return redirect('/oda_servisi')

@app.route('/oda_servisi', methods=["GET", "POST"])
def oda_servisi():
    session_user = get_session_user()
    if session_user == None:
        return redirect('/giris')
    if session_user['admin'] == True:
        all_orders = []
        all_orders_doc = database_siparis.find({})
        for order in all_orders_doc:
            order_user = database_user.find_one({
                '_id': order['_id']
            })

            room_no_switcher = database_roomswitch.find_one({
                '_id': session_user['_id']
            })

            room_no = room_no_switcher['main']

            del order['_id']
            
            all_orders.append({
                'whoose': order_user['email'],
                'order': order,
                'room_no': room_no
            })
            

        return render_template('admin_oda_servisi.html', user=session_user, all_orders=all_orders, len_of_order=len(all_orders))
    
    check_room = database_reservation.find_one({
        "whoose": session_user['_id']
    })
    if check_room in non_exist_situations:
        return redirect('/logout')
    odalar = []
    odalar_doc = database_reservation.find({
        'whoose': session_user['_id']
    })
    for oda in odalar_doc:
        odalar.append(oda['oda_no'])
    return render_template('oda_servisi.html', odalar=odalar, user=session_user, item_list=item_list)

@app.route('/oda_servisi/<string:item_id>', methods=["GET", "POST"])
def oda_servisi_pages(item_id: str):
    if item_id not in item_list:
        return redirect('/oda_servisi')
    session_user = get_session_user()
    if session_user == None:
        return redirect('/giris')
    
    if request.method == "POST":
        data = request.json
        quantity = data['quantity']
        result = database_siparis.find_one({
            '_id': session_user['_id']
        })
        if result in non_exist_situations:
            return redirect('/oda_servisi')
        if not result.get(item_id):

            database_siparis.update_one({
                '_id': session_user['_id']
            }, {
                '$set': {
                    f'{item_id}': int(quantity)
                }
            }, upsert=True)

        else:
            database_siparis.update_one({
                '_id': session_user['_id']
            }, {
                '$set': {
                    f'{item_id}': int(quantity) + result[item_id]
                }
            }, upsert=True)

        return redirect('/profile')

    if request.method == "GET":
        return render_template('oda_servisi_pages.html', item_id=item_id, user=session_user)   


def delete_users(uid: str):
    session_user = get_session_user()
    if (session_user == None) or (session_user['admin'] == False):
        return redirect('/giris')
    
    user = get_user_from_id(uid)
    if user == None:
        return redirect('/')
    
    print(user)
    
    if user['admin'] == True:
        return redirect('/')

    reservations_doc = database_reservation.find({
        'whoose': user['_id']
    })
    
    reservations = []
    for reservation in reservations_doc:
        reservations.append(reservation)
    
    today = date.today().strftime('%d.%m.%Y').split('.')
    
    for reservation in reservations:
        reservation_last_date = reservation['bitis_tarihi'].split('.')
        if today[2] > reservation_last_date[2]:
            drop_reservation(reservation)
        else:
            if today[1] > reservation_last_date[1]:
                drop_reservation(reservation)
            else:
                if today[0] > reservation_last_date[0]:
                    drop_reservation(reservation)
    
    result = database_reservation.find_one({
        'whoose': user['_id']
    })

    if result in non_exist_situations:
        database_user.delete_one({
            '_id': user['_id']
        })

        return redirect('/')

def drop_reservation(reservation: dict):
    database_reservation.delete_one(reservation)

@app.route('/odalar', methods=["GET", "POST"])
def oda_islemleri():
    if not is_logged():
        return redirect('/giris')
    session_user = get_session_user()
    
    if session_user['admin'] == True:
        reservations_doc = database_reservation.find({})
        whoose = []
        oda_bilgileri = []
        reservations = []
        for sayi in range(1, 51):
            oda_bilgileri.append({
                "oda_no": sayi,
                "is_full": False,
                "whoose": "OWNLESS"
            })
        for reservation in reservations_doc:
            reservations.append(reservation)
        
        for oda in reservations:
            query = database_user.find_one({
                '_id': oda['whoose']
            })

            oda_bilgileri[oda['oda_no'] - 1] = {
                "oda_no": oda['oda_no'],
                "whoose": query['email'],
                "is_full": True
            }

        return render_template('admin_odalar.html', oda_bilgileri = oda_bilgileri, user=session_user)
    else:
        reservations_cursor = database_reservation.find({
            "whoose": session_user['_id']
        })
        reservations = []
        if reservations_cursor not in non_exist_situations:
            for reservation in reservations_cursor:
                reservations.append(reservation)

            oda_bilgileri = []
            for index in range(len(reservations)):
                oda_bilgileri.append(reservations[index]['oda_no'])
        oda_sayisi = len(oda_bilgileri)
        return render_template('odalar.html', oda_sayisi = oda_sayisi, oda_bilgileri = oda_bilgileri, user=session_user)

@app.route('/oda_ayirt', methods=["GET", "POST"])
def oda_ayirt():
    oda_no = request.form['oda_no']
    oda_no = int(oda_no)
    session_user = get_session_user()
    if not (oda_no < 51 and oda_no > 0):
        return render_template('oda_degeri_yanlis.html', user=session_user)

    result = database_reservation.find_one({
        'oda_no': oda_no,
        'otel_ismi': 'Kodların Seyyahı'
    })
    if result in non_exist_situations:
        return render_template('oda_ayirt.html', oda_no=oda_no, user=session_user)
    else:
        return render_template('oda_dolu.html', user=session_user)

@app.route('/oda_ekle', methods=["POST", "GET"])
def oda_ekle():
    session_user = get_session_user()
    if (session_user == None) or (session_user['admin'] == False):
        return redirect('/giris')
    
    email = request.form['email']
    tc_kimlik_no = request.form['tc_kimlik_no']
    isim = request.form['isim']
    soyisim = request.form['soyisim']
    kullanici_adi = request.form['kullanici_adi']
    yas = request.form['yas']
    telefon_numarasi = request.form['telefon_numarasi']
    random_id = str(uuid.uuid4())
    
    chars = string.ascii_letters + string.digits + string.punctuation
    sifre = ""
    for _ in range(8):
        sifre += chars[random.randint(0, len(chars) - 1)]
    is_user_exist_email = database_user.find_one({
        'email': email,
    })

    is_user_exist_tc_kimlik_no = database_user.find_one({
        'tc_kimlik_no': tc_kimlik_no,
    })
    is_user_exist_kullanici_adi = database_user.find_one({
        'kullanici_adi': kullanici_adi,
    })
    is_user_exist_telefon_numarasi = database_user.find_one({
        'telefon_numarasi': telefon_numarasi
    })

    if (is_user_exist_email in non_exist_situations) and (is_user_exist_kullanici_adi in non_exist_situations) and (is_user_exist_tc_kimlik_no in non_exist_situations) and (is_user_exist_telefon_numarasi in non_exist_situations):
        database_user.insert_one({
            '_id': random_id,
            'email': email,
            'tc_kimlik_no': tc_kimlik_no,
            'isim': isim,
            'soyisim': soyisim,
            'kullanici_adi': kullanici_adi,
            'yas': yas,
            'telefon_numarasi': telefon_numarasi,
            'admin': False,
            'sifre': sifre
        })
        new_user = {
            '_id': random_id,
            'email': email,
            'tc_kimlik_no': tc_kimlik_no,
            'isim': isim,
            'soyisim': soyisim,
            'kullanici_adi': kullanici_adi,
            'yas': yas,
            'telefon_numarasi': telefon_numarasi,
            'admin': False,
            'sifre': sifre
        }
    else:
        return render_template('user_exist.html', user=session_user)
    run = True
    otel_name = "Kodların Seyyahı"
    while run:
        random_number = random.randint(1, 50)
        result = database_reservation.find_one({
            'oda_no': random_number
        })
        
        if result in non_exist_situations:
            
            database_reservation.insert_one({
                '_id': str(uuid.uuid4()),
                'whoose': new_user['_id'],
                'baslangic_tarihi': date.today().strftime('%d.%m.%Y'),
                'bitis_tarihi': '02.05.2023',
                'oda_no': random_number,
                'otel_ismi': otel_name,
            })

            database_roomswitch.insert_one({
                '_id': new_user['_id'],
                'main': random_number
            })


            run = False

    del run

    return render_template('token.html', user=session_user, new_user=new_user, site_link=site_link)

@app.route('/oda_sil', methods=['GET', 'POST'])
def oda_sil():
    session_user = get_session_user()
    if (session_user is  None) or (session_user['admin'] == False):
        return redirect('/giris')
    return render_template('oda_sil.html', user=session_user)

@app.route('/oda_satin_al', methods=["POST", "GET"])
def oda_satin_al():
    oda_no = request.form['oda_no']
    oda_no = int(oda_no)
    session_user = get_session_user()
    otel_name = "Kodların Seyyahı"
    random_id = str(uuid.uuid4())
    database_reservation.insert_one({
        '_id': random_id,
        'whoose': session_user['_id'],
        'baslangic_tarihi': '26.04.2023',
        'bitis_tarihi': '02.05.2023',
        'oda_no': oda_no,
        'otel_ismi': otel_name,
    })
    database_roomswitch.delete_one({
        '_id': session_user['_id']
    })

    database_roomswitch.insert_one({
        '_id': session_user['_id'],
        'main': oda_no
    })
    return redirect('/profile')

@app.route('/goto_user', methods=["POST"])
def goto_user():
    email = request.form['email']
    print(email)
    user = database_user.find_one({
        'email': email
    })
    if user:
        return redirect(f"/goto_user/{user['email']}")
    else:
        return redirect('/')
@app.route('/goto_user/<string:email>', methods=["GET"])
def goto_user_via_url(email: str):
    user = database_user.find_one({
        'email': email
    })

    return redirect(f"/profile/{user['_id']}")

@app.route('/profile/<string:uid>', methods=["GET"])
def profile_via_id(uid: str):
    session_user = get_session_user()
    if session_user == None:
        return redirect('/giris')
    
    if session_user['admin'] == True:
        user = get_user_from_id(uid)
        return render_template('profile.html', user = user)
    else:
        return render_template('/profile')

@app.route('/profile')
def profile():
    session_user = get_session_user()
    if session_user == None:
        return redirect('/giris')
    rezervasyonlari = database_reservation.find({
        'whoose': session_user['_id']
    })
    oda_nolar_list = []
    for data in rezervasyonlari:
        oda_nolar_list.append(data['oda_no'])
    
    oda_no_string = ""
    for oda_no in range(len(oda_nolar_list)):
        if oda_no == (len(oda_nolar_list) - 1):
            oda_no_string += f"{oda_nolar_list[oda_no]} nolu odalar."
            break
        oda_no_string += f"{oda_nolar_list[oda_no]}, "
    
    if len(oda_nolar_list) == 1:
        oda_no_string = f"{oda_nolar_list[0]} nolu oda."
    if len(oda_nolar_list) == 0:
        oda_no_string = "Henüz oda ayırtmamışsınız."
    session_user['oda_nolar'] = oda_no_string
    
    siparisler = database_siparis.find_one({
        '_id': session_user['_id']
    })
    if siparisler:
        session['siparis'] = siparisler
        del session['siparis']['_id']
        len_of_siparis = len(siparisler)
    else:
        session['siparis'] = None
        len_of_siparis = 0
    
    main_room = database_roomswitch.find_one({
        '_id': session_user['_id']
    })
    if main_room:
        main_room = main_room.get('main')
    else:
        main_room == "YOK"
    return render_template('profile.html', user=session_user, session=session, len_of_siparis=len_of_siparis,main_room=main_room)

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
    session_user = get_session_user()
    if session_user == None:
        return render_template('login.html')
    else:
        return redirect('/')

@app.route('/anasayfa/')
@app.route('/anasayfa')
@app.route('/index/')
@app.route('/index')
@app.route('/')
def index():
    if not is_logged():
        return redirect('/giris')
    
    session_user = get_session_user() 
    if session_user["admin"] == True:
        all_users = database_user.find({})
        for user in all_users:
            delete_users(user['_id'])
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
            '_id': random_id,
            'whoose': session_user['_id'],
            'baslangic_tarihi': baslangic_tarihi,
            'bitis_tarihi': bitis_tarihi,
            'oda_no': random.randint(1, 50),
            'otel_ismi': otel_name,
        })
    else:
        splitted_message = message.split(';') # SIPARIS:COLA|3;HAMBURGER|2
        siparis_nested_list = []
        
        for i in len(splitted_message):
            siparisler = splitted_message[i].split('|')
            siparis_nested_list[i] = [siparisler[0], int(siparisler[1])] # => [["COLA", 3], ["HAMBURGER",2]]
        
        database_siparis.insert_one({
            '_id': random_id,
            'whoose': session_user['_id'],
            'istek_siparis': siparis_nested_list,
        })

    out_format = f"{session_user['_id']}_{random_id}"
    complete_encryption(data, f'veri/{out_format}.mp4', f'veri/{out_format}.key')

    if os.fileexist(f'{out_format}.mp4') and os.fileexist(f'{out_format}.key'):
        return render_template('sifreleme_sonuc.html')
    else:
        return render_template('try_again.html')

@app.route('/api/cd/<string:data>', methods=["POST", "GET"])
def api_cd(data: str):
    global non_exist_situations
    if not is_logged():
        return redirect('/giris')

    session_user = get_session_user()
    if not session_user['admin']:
        return redirect('/')


    dosya_adi = data
    if allowed_file(dosya_adi):
        splitted_dosya_adi = dosya_adi.split('_')
        user_id = splitted_dosya_adi[0]
        case_id = splitted_dosya_adi[1]

        reservation_case = database_reservation.find_one({
            '_id': case_id,
            'whoose': user_id
        })

        siparis_case = database_siparis.find_one({
            '_id': case_id,
            'whoose': user_id
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

@app.route('/login/<string:username>/<string:password>')
def login_via_url(username: str, password: str):
    result = database_user.find_one({
        'kullanici_adi': username,
        'sifre': password
    })

    if result not in non_exist_situations:
        session['user_id'] = str(result['_id'])
        siparisler = database_siparis.find_one({
            'whoose': result['_id']
        })
        session['siparis'] = siparisler
        return redirect('/')
    else:
        return redirect('/giris')



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
            siparisler = database_siparis.find_one({
                'whoose': user['_id']
            })
            session['siparis'] = siparisler 
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
    if (is_user_exist in non_exist_situations):
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