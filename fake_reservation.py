import pymongo
import certifi
import uuid
import random
db_link = "mongodb+srv://yigit:yigitinsifresi@projectdatabasegalbul.ixx82u7.mongodb.net/test"
cacert = certifi.where()
client = pymongo.MongoClient(db_link, tlsCAFile=cacert, tlsAllowInvalidCertificates=False)
databases = client.cryptology
random_id = str(uuid.uuid4())
databases.reservation.insert_one({
"whoose": "19072079-6792-4ab0-9928-99edad3bb49b",
"_id": random_id,
"baslangic_tarihi": '21.04.2023',
'bitis_tarihi': '26.04.2023',
'oda_no': random.randint(1,50),
'otel_ismi': 'Kodların Seyyahı'
})

import os
os.system(f'touch "19072079-6792-4ab0-9928-99edad3bb49b_{random_id}".mp4')
os.system(f'touch "19072079-6792-4ab0-9928-99edad3bb49b_{random_id}".key')
