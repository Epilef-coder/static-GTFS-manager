import json
import time
import tornado.web

from utils.logmessage import logmessage
from utils.password import decrypt
from utils.tables import replaceTableDB, readTableDB, readColumnDB


class gtfsfrequencies(tornado.web.RequestHandler):
    # /API/gtfs/frequencies AND /API/gtfs/frequencies/{trip_id}
    def get(self, trip_id=None):
        if trip_id:
            start = time.time()
            logmessage('\nAPI/gtfs/frequencies/{} GET call'.format(trip_id))
            freqJson = readTableDB('frequencies', key='trip_id', value=trip_id).to_json(orient='records', force_ascii=False)
            self.write(freqJson)
            end = time.time()
            logmessage("API/gtfs/frequencies GET call took {} seconds.".format(round(end-start,2)))
        else:
            start = time.time()
            logmessage('\nAPI/gtfs/frequencies/{} GET call'.format(trip_id))
            freqJson = readTableDB('frequencies').to_json(orient='records', force_ascii=False)
            self.write(freqJson)
            end = time.time()
            logmessage("API/gtfs/frequencies GET call took {} seconds.".format(round(end - start, 2)))

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


class gtfsfrequencieslistids(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/agency/list/id
        start = time.time()
        logmessage('\n/API/gtfs/agency/list/id GET call')
        listCollector = set()
        listCollector.update(readColumnDB('frequencies', 'trip_id'))
        # to do: find out why this function is only looking at stops table
        List = list(listCollector)
        List.sort()
        self.write(json.dumps(List))
        end = time.time()
        logmessage("\n/API/gtfs/agency/list/id GET call took {} seconds.".format(round(end - start, 2)))
