import tornado.web
import tornado.ioloop
import time
import json

from utils.logmessage import logmessage
from utils.tables import readTableDB,replaceTableDB,readColumnDB,readColumnsDB
from utils.password import decrypt

class gtfstranlations(tornado.web.RequestHandler):
    # /API/gtfs/agency AND /API/gtfs/agency/{Agency_id}
    def get(self, trans_id=None):
        if trans_id:
            start = time.time()
            logmessage('\n/API/gtfs/tranlations/{} GET call'.format(trans_id))
            agencyJson = readTableDB('tranlations', key='trans_id', value=trans_id).to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/tranlations/{} GET call took {} seconds.".format(trans_id, round(end - start, 2)))
        else:
            start = time.time()
            logmessage('\n/API/gtfs/tranlations GET call')
            agencyJson = readTableDB('tranlations').to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/tranlations GET call took {} seconds.".format(round(end - start, 2)))

    def post(self):
        # /API/gtfs/tranlations AND /API/gtfs/tranlations/trans_id}
        if self.request.body:
            start = time.time()
            logmessage('\n/API/gtfs/tranlations POST call')
            pw = self.get_argument('pw', default='')
            if not decrypt(pw):
                self.set_status(400)
                self.write("Error: invalid password.")
                return
            # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
            data = json.loads(self.request.body.decode('UTF-8'))

            if replaceTableDB('tranlations', data):  # replaceTableDB(tablename, data)
                self.write('Saved tranlations data to DB.')
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/agency POST call took {} seconds.".format(round(end - start, 2)))
        else:
            self.write("Error: Saving table data")