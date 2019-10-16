import json

import tornado.web
import tornado.ioloop
import time

from utils.logmessage import logmessage
from utils.password import decrypt
from utils.tables import readTableDB, replaceTableDB


class stopTimes(tornado.web.RequestHandler):
    def get(self):
        # API/stopTimes?trip=${trip_id}&route=${route_id}&direction=${direction_id}
        start = time.time()
        logmessage('\nstopTimes GET call')
        trip_id = self.get_argument('trip', default='')
        route_id = self.get_argument('route', default='')
        direction_id = int(self.get_argument('direction',default=0))
        returnMessage = ''

        if not ( len(trip_id) and len(route_id) ):
            self.set_status(400)
            self.write("Error: Invalid trip or route ID given.")
            return

        tripInTrips = readTableDB('trips', 'trip_id', trip_id)
        if not len(tripInTrips):
            self.set_status(400)
            self.write("Error: Please save this trip to DB in the Trips tab first.")
            return

        stoptimesDf = readTableDB('stop_times', 'trip_id', trip_id)
        # this will simply be empty if the trip doesn't exist yet

        stoptimesArray = stoptimesDf.to_dict(orient='records')

        if len(stoptimesArray):
            returnMessage = 'Loaded timings from stop_times table.'
            newFlag = False
        else:
            returnMessage = 'This trip is new. Loading default sequence, please fill in timings and save to DB.'
            newFlag = True

        returnJson = {'data':stoptimesArray, 'message':returnMessage, 'newFlag':newFlag }
        # let's send back not just the array but even the message to display.
        logmessage('returnJson.message:',returnJson['message'])

        self.write(json.dumps(returnJson))
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("stopTimes GET call took {} seconds.".format(round(end-start,2)))


    def post(self):
        # ${APIpath}stopTimes?pw=${pw}&trip=${trip_id}
        start  = time.time() # time check, from https://stackoverflow.com/a/24878413/4355695
        logmessage('\nstopTimes POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        trip_id = self.get_argument('trip', default='')
        if not len(trip_id) :
            self.set_status(400)
            self.write("Error: invalid trip_id.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        timingsData = json.loads( self.request.body.decode('UTF-8') )

        # heres where all the action happens:
        result = replaceTableDB('stop_times', timingsData, key='trip_id', value=trip_id)

        if result:
            self.write('Changed timings data for trip '+trip_id)
        else:
            self.set_status(400)
            self.write("Some error happened.")

        end = time.time()
        logmessage("stopTimes POST call took {} seconds.".format(round(end-start,2)))


class gtfsstoptimes(tornado.web.RequestHandler):
    # /API/gtfs/stoptimes AND /API/gtfs/stoptimes/{trip_id}
    def get(self, trip_id=None):
        if trip_id:
            start = time.time()
            logmessage('\n/API/gtfs/stoptimes/{} GET call'.format(trip_id))
            agencyJson = readTableDB('stop_times', key='trip_id', value=trip_id).to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/stoptimes/{} GET call took {} seconds.".format(trip_id, round(end - start, 2)))
        else:
            start = time.time()
            logmessage('\n/API/gtfs/stoptimes GET call')
            agencyJson = readTableDB('stop_times').to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/stoptimes GET call took {} seconds.".format(round(end - start, 2)))

    def post(self, trip_id=None):
        # /API/gtfs/stoptimes/{trip_id}
        if self.request.body:
            if trip_id:
                start = time.time()
                logmessage('\n/API/gtfs/stoptimes/{} POST call'.format(trip_id))
                pw = self.get_argument('pw', default='')
                if not decrypt(pw):
                    self.set_status(400)
                    self.write("Error: invalid password.")
                    return
                # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
                data = json.loads(self.request.body.decode('UTF-8'))

                if replaceTableDB('stop_times', data, key='trip_id', value=trip_id):  # replaceTableDB(tablename, data)
                    self.write('Saved Agency data to DB.')
                # time check, from https://stackoverflow.com/a/24878413/4355695
                end = time.time()
                logmessage("/API/gtfs/trips POST call took {} seconds.".format(round(end - start, 2)))
        else:
            self.write("Error: Saving table data")

