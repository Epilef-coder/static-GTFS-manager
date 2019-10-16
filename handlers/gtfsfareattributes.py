import json
import time

import tornado.web

from utils.logmessage import logmessage
from utils.password import decrypt
from utils.tables import readTableDB, replaceTableDB, readColumnDB


class gtfsfareattributes(tornado.web.RequestHandler):
    #/API/gtfs/fareattributes AND /API/gtfs/fareattributes/{fare_id}
    def get(self, fare_id=None):
        if fare_id:
            start = time.time()
            logmessage('\n/API/gtfs/fareattributes/{} GET call'.format(fare_id))
            fareAttributesJson = readTableDB('fare_attributes', key='fare_id', value=fare_id).to_json(orient='records', force_ascii=False)
            self.write(fareAttributesJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/fareattributes/{} GET call took {} seconds.".format(fare_id,round(end-start,2)))
        else:
            start = time.time()
            logmessage('\nfareAttributes GET call')
            fareAttributesJson = readTableDB('fare_attributes').to_json(orient='records', force_ascii=False)
            self.write(fareAttributesJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("fareAttributes GET call took {} seconds.".format(round(end - start, 2)))

    def post(self):
        # API/fareAttributes
        start = time.time()
        logmessage('\n/API/gtfs/fareattributes POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads( self.request.body.decode('UTF-8') )

        # writing back to db
        if replaceTableDB('fare_attributes', data): #replaceTableDB(tablename, data)
            self.write('Saved Fare Attributes data to DB.')
        else:
            self.set_status(400)
            self.write("Error: could not save to DB.")
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("/API/gtfs/fareattributes POST call took {} seconds.".format(round(end-start,2)))

class gtfsfareattributeslistids(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/agency/list/id
        start = time.time()
        logmessage('\n/API/gtfs/fareattributes/list/id GET call')
        listCollector = set()
        listCollector.update(readColumnDB('fare_attributes', 'fare_id'))
        # to do: find out why this function is only looking at stops table
        List = list(listCollector)
        List.sort()
        self.write(json.dumps(List))
        end = time.time()
        logmessage("\n/API/gtfs/agency/list/id GET call took {} seconds.".format(round(end - start, 2)))
