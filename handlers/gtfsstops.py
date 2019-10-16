import json

import tornado.web
import tornado.ioloop
import time
from utils.logmessage import logmessage
from utils.password import decrypt
from utils.tables import readTableDB, replaceTableDB, readColumnDB, readColumnsDB


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


class gtfsstops(tornado.web.RequestHandler):
    # /API/gtfs/stop AND /API/gtfs/stop/{stop_id}
    def get(self, stop_id=None):
        if stop_id:
            start = time.time()
            logmessage('\n/API/gtfs/stop/{} GET call'.format(stop_id))
            stopJson = readTableDB('stops', key='stop_id', value=stop_id).to_json(orient='records', force_ascii=False)
            self.write(stopJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/stop/{} GET call took {} seconds.".format(stop_id, round(end - start, 2)))
        else:
            start = time.time()
            logmessage('\n/API/gtfs/stop GET call')
            agencyJson = readTableDB('stops').to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/stop GET call took {} seconds.".format(round(end - start, 2)))

    def post(self):
        # /API/gtfs/stop AND /API/gtfs/stop/{Agency_id}
        if self.request.body:
            start = time.time()
            logmessage('\n/API/gtfs/stop POST call')
            pw = self.get_argument('pw', default='')
            if not decrypt(pw):
                self.set_status(400)
                self.write("Error: invalid password.")
                return
            # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
            data = json.loads(self.request.body.decode('UTF-8'))

            if replaceTableDB('stops', data):  # replaceTableDB(tablename, data)
                self.write('Saved stops data to DB.')
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/agency POST call took {} seconds.".format(round(end - start, 2)))
        else:
            self.write("Error: Saving table data")

class gtfsstopslistids(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/stop/list/id
        start = time.time()
        logmessage('\n/API/gtfs/stop/list/id GET call')
        listCollector = set()
        listCollector.update(readColumnDB('stops', 'stop_id'))
        # to do: find out why this function is only looking at stops table
        List = list(listCollector)
        List.sort()
        self.write(json.dumps(List))
        end = time.time()
        logmessage("\n/API/gtfs/stop/list/id GET call took {} seconds.".format(round(end - start, 2)))

class gtfsstoplistidnames(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/stop/list/idname
        start = time.time()
        logmessage('\n/API/gtfs/stop/list/idname GET call')
        columns = ['stop_id','stop_name']
        agencyJson = readColumnsDB('stops',columns).to_json(orient='records', force_ascii=False)
        self.write(agencyJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("/API/gtfs/stop/list/idname GET call took {} seconds.".format(round(end - start, 2)))


class  gtfsstoplistzoneid(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/stop/list/zoneid
        start = time.time()
        logmessage('\n/API/gtfs/stop/list/zoneid GET call')

        zoneCollector = set()
        zoneCollector.update( readColumnDB('stops','zone_id') )
        # to do: find out why this function is only looking at stops table
        zoneList = list(zoneCollector)
        zoneList.sort()
        self.write(json.dumps(zoneList))
        end = time.time()
        logmessage("zoneIdList GET call took {} seconds.".format(round(end-start,2)))