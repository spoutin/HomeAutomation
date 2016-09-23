from elasticsearch import Elasticsearch
import configparser
import baseObject
import re

class es(object):

    def __init__(self):
        self.enabled = False
        try:
            config = configparser.ConfigParser()
            config.read(baseObject.get_script_path()+'/config/elasticsearch.ini')
            self.host = config['elasticsearch']['host']
            self.port = config['elasticsearch']['port']
            self.es = Elasticsearch(self.host + ':' + self.port)
            self.enabled = True

            self.default_index = {
                "settings": {
                    "number_of_shards": 1},
                "mappings": {
                    "_default_": {
                        "_timestamp": {
                            "enabled": True,
                        }
                    }
                }
            }

        except:
            pass

    def add(self, index, name, message):
        index = re.sub('[^A-Za-z0-9]+', '', index).lower()
        msg = {key: str(value) for key, value in message.items()}
        if self.enabled:
            try:
                if not self.es.indices.exists(index):
                    self.es.indices.create(index=index, body=self.default_index)
                self.es.index(index=index, doc_type=name, body=msg)
            except:  # error, ignore adding to elasticsearch
                pass

    def index_maker(self, index):
        pass
