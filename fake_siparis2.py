import pymongo
import certifi
import uuid
import random
db_link = "mongodb+srv://yigit:yigitinsifresi@projectdatabasegalbul.ixx82u7.mongodb.net/test"
cacert = certifi.where()
client = pymongo.MongoClient(db_link, tlsCAFile=cacert, tlsAllowInvalidCertificates=False)
databases = client.cryptology
random_id = str(uuid.uuid4())
databases.siparis.insert_one({
"_id": "19072079-6792-4ab0-9928-99edad3bb49b",
})
