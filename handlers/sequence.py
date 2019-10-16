import json
import time

import tornado.web

from settings import sequenceDBfile
from utils.logmessage import logmessage
from utils.password import decrypt
from utils.sequence import sequenceFull, extractSequencefromGTFS
from utils.tables import sequenceReadDB, sequenceSaveDB


class defaultsequencebyroute(tornado.web.RequestHandler):
    # /API/defaultsequence/route/{route_id]
    def get(self, route_id=None):
        if route_id:
            start = time.time()
            logmessage('\n/API/defaultsequence/{} GET call'.format(route_id))
            sequence = sequenceFull(sequenceDBfile, route_id)
            returnjson = {'sequence': sequence}
            self.write(returnjson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/defaultsequence/{} GET call took {} seconds.".format(route_id, round(end - start, 2)))


class defaultsequence(tornado.web.RequestHandler):
    def get(self, route_id=None):
        if route_id:
            # API/defaultsequence/{route_id}
            start = time.time()
            logmessage('\nAPI/defaultsequence/{} GET call',route_id)

            if not len(route_id):
                self.set_status(400)
                self.write("Error: invalid route.")
                return

            #to do: first check in sequence db. If not found there, then for first time, scan trips and stop_times to load sequence. And store that sequence in sequence db so that next time we fetch from there.

            sequence = sequenceReadDB(sequenceDBfile, route_id)
            # read sequence db and return sequence array. If not found in db, return false.

            message = '<span class="alert alert-success">Loaded default sequence for this route from DB.</span>'

            if not sequence:
                logmessage('sequence not found in sequence DB file, so extracting from gtfs tables instead.')
                # Picking the first trip instance for each direction of the route.
                sequence = extractSequencefromGTFS(route_id)

                if sequence == [ [], [] ] :
                    message = '<span class="alert alert-info">This seems to be a new route. Please create a sequence below and save to DB.</span>'
                else:
                    message = '<span class="alert alert-warning">Loaded a computed sequence from existing trips. Please finalize and save to DB.</span>'

                # we have computed a sequence from the first existing trip's entry in trips and stop_times tables for that route (one sequence for each direction)
                # Passing it along. Let the user finalize it and consensually save it.

            # so either way, we now have a sequence array.

            returnJson = { 'data':sequence, 'message':message }
            self.write(json.dumps(returnJson))
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("sequence GET call took {} seconds.".format(round(end-start,2)))

    #using same API endpoint, post request for saving.
    def post(self, route_id=None):
        if route_id:
            # ${APIpath}sequence?pw=${pw}&route=${selected_route_id}&shape0=${chosenShape0}&shape1=${chosenShape1}
            start = time.time()
            logmessage('\nsequence POST call')
            pw = self.get_argument('pw',default='')
            if not decrypt(pw):
                self.set_status(400)
                self.write("Error: invalid password.")
                return
            shape0 = self.get_argument('shape0', default='')
            shape1 = self.get_argument('shape1', default='')

            if not len(route_id):
                self.set_status(400)
                self.write("Error: invalid route.")
                return

            # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
            data = json.loads( self.request.body.decode('UTF-8') )

            '''
            This is what the data would look like: [
                ['ALVA','PNCU','CPPY','ATTK','MUTT','KLMT','CCUV','PDPM','EDAP','CGPP','PARV','JLSD','KALR','LSSE','MGRD'],
                ['MACE','MGRD','LSSE','KALR','JLSD','PARV','CGPP','EDAP','PDPM','CCUV','KLMT','MUTT','ATTK','CPPY','PNCU','ALVA']
            ];
            '''
            # to do: the shape string can be empty. Or one of the shapes might be there and the other might be an empty string. Handle it gracefully.
            # related to https://github.com/WRI-Cities/static-GTFS-manager/issues/35
            # and : https://github.com/WRI-Cities/static-GTFS-manager/issues/38
            shapes = [shape0, shape1]

            if sequenceSaveDB(sequenceDBfile, route_id, data, shapes):
                self.write('saved sequence to sequence db file.')
            else:
                self.set_status(400)
                self.write("Error, could not save to sequence db for some reason.")
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("API/sequence POST call took {} seconds.".format(round(end-start,2)))