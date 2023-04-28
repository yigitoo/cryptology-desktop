import pymongo
import certifi
import uuid
import random
db_link = "mongodb+srv://yigit:yigitinsifresi@projectdatabasegalbul.ixx82u7.mongodb.net/test"
cacert = certifi.where()
client = pymongo.MongoClient(db_link, tlsCAFile=cacert, tlsAllowInvalidCertificates=False)
databases = client.cryptology
random_id = str(uuid.uuid4())
databases.user.insert_one({
  "_id": random_id,
  "email": "caliyaren67@gmail.com",
  "isim": "Yaren",
  "kullanici_adi": "yaren",
  "sifre": "templekiller",
  "soyisim": "ÇALI",
  "yas": 17,
  "tc_kimlik_no": "12345678111",
  "telefon_numarasi": "+90 552 354 8503",
  "admin": False
})

import os
os.system(f'touch "19072079-6792-4ab0-9928-99edad3bb49b_{random_id}".mp4')
os.system(f'touch "19072079-6792-4ab0-9928-99edad3bb49b_{random_id}".key')
