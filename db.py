import pymongo
import certifi
import logging

def create_client(cluster_name: str = "user"): 
    db_link = "mongodb+srv://yigit:yigitinsifresi@projectdatabasegalbul.ixx82u7.mongodb.net/test"
    cacert = certifi.where()
    client = pymongo.MongoClient(db_link, tlsCAFile=cacert, tlsAllowInvalidCertificates=False)
    databases = client.cryptology
    return databases[cluster_name]


class Database:
    global database
    def __init__(self):
        logging.basicConfig(filename='db.log', encoding='utf-8', level=logging.DEBUG)
        self.db_link = "mongodb+srv://yigit:yigitinsifresi@projectdatabasegalbul.ixx82u7.mongodb.net/test"
        self.cacert = certifi.where()
        self.client = pymongo.MongoClient(self.db_link, tlsCAFile=self.cacert, tlsAllowInvalidCertificates=False)
        self.databases = self.client.cryptology
        self.database = None
        self.current_db = None
        result = self.choose_db("users")

        if result[0] is True:
            logging.info(f"Connected to Database: {result[1]}!")
        del result

    def choose_db(self, dbName: str = "users"):
        self.database = self.databases[dbName]
        self.current_db = dbName
        logging.info("Connecting database...")
        return [True, dbName]
    
    def find_data(self, filter_query: str = {}):
        result = self.database.find_one(filter_query)
        if result:
            logging.info(f"Found an document: {result}")
            return result
        else:
            logging.warn(f"Cannot found anything from that_query: {filter_query}\non{self.current_db}")

    def find_multiple_data(self, filter_query: str = {}):
        result = self.database.find(filter_query)
        if result:
            logging.info(f"Found documents:")
            logging.info(f"-----------------")
            for index, doc in result:
                logging.info(f"{index}: {doc}")
            logging.info(f"-----------------")
            return result
        else:
            logging.warn(f"Cannot found anything from that_query: {filter_query}\non{self.current_db}")


    def add_data(self, dictionary: dict):
        self.database.insert_one(dictionary)
        logging.info("Successfuly inserted data!")
        logging.info(f"inserted data: {dictionary}")

    def add_many_data(self, dictionary_list: list[dict]):
        self.database.insert(dictionary_list)
        logging.info("Succesfully inserted datalist")

    def delete_data(self, filter_query: dict):
        self.database.delete_one(filter_query)
        logging.info("Successfully delete data!")
        logging.warn(f"about relatively: {filter_query}")
        
    def delete_all_db(self):
        logging.warn("You requested deleting all db!")
        logging.warn("Are you sure? [y/yes|n/no]")
        choose = input()
        logging.info(f"you choose: {choose}")
        if choose.lower() in ["y", "yes"]:
            self.database.delete_many({})
            logging.info("Deleted all db!")
        else:
            logging.info("Aborting deleting db!")