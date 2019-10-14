import tornado.web
import tornado.ioloop
import time
from utils.logmessage import logmessage

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


class trips(tornado.web.RequestHandler):
    def get(self):
        # API/trips?route=${route_id}
        start = time.time()
        logmessage('\ntrips GET call')
        route_id = self.get_argument('route', default='')
        if not len(route_id):
            self.set_status(400)
            self.write("Error: invalid route.")
            return

        tripsArray = readTableDB('trips', key='route_id', value=route_id).to_dict(orient='records')

        # also read sequence for that route and send.
        sequence = sequenceFull(sequenceDBfile, route_id)
        # if there is no sequence saved yet, sequence=False which will be caught on JS side to inform the user and disable new trips creation.

        returnJson = {'trips':tripsArray, 'sequence':sequence }

        self.write(json.dumps(returnJson))
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("trips GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        start  = time.time() # time check, from https://stackoverflow.com/a/24878413/4355695
        # ${APIpath}trips?pw=${pw}&route=${route_id}
        logmessage('\ntrips POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        route_id = self.get_argument('route',default='')
        if not len(route_id) :
            self.set_status(400)
            self.write("Error: invalid route_id.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        tripsData = json.loads( self.request.body.decode('UTF-8') )

        # heres where all the action happens:
        result = replaceTableDB('trips', tripsData, key='route_id', value=route_id)

        if result:
            self.write('Saved trips data for route '+route_id)
        else:
            self.set_status(400)
            self.write("Some error happened.")

        end = time.time()
        logmessage("trips POST call took {} seconds.".format(round(end-start,2)))