import json

import tornado.web
import tornado.ioloop
import time

from settings import sequenceDBfile
from utils.logmessage import logmessage
from utils.password import decrypt
from utils.tables import readTableDB, replaceTableDB, readColumnDB, readColumnsDB


class tripIdList(tornado.web.RequestHandler):
    def get(self):
        # API/tripIdList
        start = time.time()
        logmessage('\ntripIdList GET call')
        trip_id_list = readColumnDB('trips','trip_id')

        self.write(json.dumps(trip_id_list))
        # db.close()
        end = time.time()
        logmessage("tripIdList GET call took {} seconds.".format(round(end-start,2)))


class gtfstripsbyroute(tornado.web.RequestHandler):
    def get(self, route_id=None):
        # /API/gtfs/trips/route/{route_id}
        if route_id:
            start = time.time()
            logmessage('\n/API/gtfs/trips/route/{} GET call'.format(route_id))
            if not len(route_id):
                self.set_status(400)
                self.write("Error: invalid route.")
                return
            agencyJson = readTableDB('trips', key='route_id', value=route_id).to_json(orient='records', force_ascii=False)
            # tripsArray = readTableDB('trips', key='route_id', value=route_id).to_dict(orient='records')
            #
            # # also read sequence for that route and send.
            # sequence = sequenceFull(sequenceDBfile, route_id)
            # # if there is no sequence saved yet, sequence=False which will be caught on JS side to inform the user and disable new trips creation.
            #
            # returnJson = {'trips':tripsArray, 'sequence':sequence }

            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/trips/route/{} GET call took {} seconds.".format(route_id, round(end-start,2)))

    def post(self):
        start  = time.time() # time check, from https://stackoverflow.com/a/24878413/4355695
        # ${APIpath}trips?pw=${pw}&route=${trip_id}
        logmessage('\ntrips POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        trip_id = self.get_argument('route',default='')
        if not len(trip_id) :
            self.set_status(400)
            self.write("Error: invalid trip_id.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        tripsData = json.loads( self.request.body.decode('UTF-8') )

        # heres where all the action happens:
        result = replaceTableDB('trips', tripsData, key='trip_id', value=trip_id)

        if result:
            self.write('Saved trips data for route '+trip_id)
        else:
            self.set_status(400)
            self.write("Some error happened.")

        end = time.time()
        logmessage("trips POST call took {} seconds.".format(round(end-start,2)))
        

class gtfstrips(tornado.web.RequestHandler):
    # /API/gtfs/trips AND /API/gtfs/trips/{trip_id}
    def get(self, trip_id=None):
        if trip_id:
            start = time.time()
            logmessage('\n/API/gtfs/trips/{} GET call'.format(trip_id))
            agencyJson = readTableDB('trips', key='trip_id', value=trip_id).to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/trips/{} GET call took {} seconds.".format(trip_id, round(end - start, 2)))
        else:
            start = time.time()
            logmessage('\n/API/gtfs/trips GET call')
            agencyJson = readTableDB('trips').to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/trips GET call took {} seconds.".format(round(end - start, 2)))

    def post(self):
        # /API/gtfs/trips AND /API/gtfs/trips/{trip_id}
        if self.request.body:
            start = time.time()
            logmessage('\n/API/gtfs/trips POST call')
            pw = self.get_argument('pw', default='')
            if not decrypt(pw):
                self.set_status(400)
                self.write("Error: invalid password.")
                return
            # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
            data = json.loads(self.request.body.decode('UTF-8'))

            if replaceTableDB('trips', data):  # replaceTableDB(tablename, data)
                self.write('Saved Agency data to DB.')
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/trips POST call took {} seconds.".format(round(end - start, 2)))
        else:
            self.write("Error: Saving table data")


class gtfstripslistids(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/trips/list/id
        start = time.time()
        logmessage('\n/API/gtfs/trips/list/id GET call')
        listCollector = set()
        listCollector.update(readColumnDB('trips', 'trip_id'))
        # to do: find out why this function is only looking at stops table
        List = list(listCollector)
        List.sort()
        self.write(json.dumps(List))
        end = time.time()
        logmessage("\n/API/gtfs/trips/list/id GET call took {} seconds.".format(round(end - start, 2)))
