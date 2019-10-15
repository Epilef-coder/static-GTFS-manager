import json

import tornado.web

from utils.logmessage import logmessage
from utils.password import decrypt


class frequencies(tornado.web.RequestHandler):
    def get(self):
        # ${APIpath}frequencies
        start = time.time()
        logmessage('\nfrequencies GET call')

        freqJson = readTableDB('frequencies').to_json(orient='records', force_ascii=False)
        self.write(freqJson)
        end = time.time()
        logmessage("frequences GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        # ${APIpath}frequencies
        start = time.time()
        logmessage('\nfrequencies POST call')
        pw=self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads( self.request.body.decode('UTF-8') )

        if replaceTableDB('frequencies', data): #replaceTableDB(tablename, data)
            self.write('Saved frequencies data to DB.')
        else:
            self.set_status(400)
            self.write("Error: Could not save to DB.")
        end = time.time()
        logmessage("frequencies POST call took {} seconds.".format(round(end-start,2)))