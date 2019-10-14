import tornado.web
import tornado.ioloop
import time
from utils.logmessage import logmessage

class allStops(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        logmessage('\nallStops GET call')

        allStopsJson = readTableDB('stops').to_json(orient='records', force_ascii=False)
        self.write(allStopsJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("allStops GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        start = time.time()
        logmessage('\nallStops POST call')
        pw=self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads( self.request.body.decode('UTF-8') )

        if replaceTableDB('stops', data): #replaceTableDB(tablename, data)
            self.write('Saved stops data to DB.')
        else:
            self.set_status(400)
            self.write("Error: Could not save to DB.")
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("allStops POST call took {} seconds.".format(round(end-start,2)))

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def options(self):
        # no body
        self.set_status(204)
        self.finish()


class allStopsKeyed(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        logmessage('\nallStopsKeyed GET call')
        stopsDF = readTableDB('stops')
        # putting in a check for empty df, because set_index() errors out with empty df.
        if len(stopsDF):
            keyedStopsJson = stopsDF.set_index('stop_id').to_json(orient='index', force_ascii=False)
            # change index to stop_id and make json keyed by index
        else : keyedStopsJson = '{}'

        self.write(keyedStopsJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("allStopsKeyed GET call took {} seconds.".format(round(end-start,2)))