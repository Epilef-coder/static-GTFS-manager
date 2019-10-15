import datetime
import json
import time

import tornado.web

from utils.logmessage import logmessage
from utils.password import decrypt
from utils.tables import readColumnDB, readColumnsDB, readTableDB, replaceTableDB

class gtfscalendardates(tornado.web.RequestHandler):
    # /API/gtfs/calendar_dates AND /API/gtfs/calendar_dates/{service_id}
    def get(self, service_id=None):
        if service_id:
            start = time.time()
            logmessage('\n/API/gtfs/calendar_dates/{} GET call'.format(service_id))
            agencyJson = readTableDB('calendar_dates', key='service_id', value=service_id).to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/calendar_dates/{} GET call took {} seconds.".format(service_id, round(end - start, 2)))
        else:
            start = time.time()
            logmessage('\n/API/gtfs/calendar_dates GET call')
            agencyJson = readTableDB('calendar_dates').to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/calendar_dates GET call took {} seconds.".format(round(end - start, 2)))

    def post(self):
        # /API/gtfs/calendar_dates AND /API/gtfs/calendar_dates/{service_id}
        if self.request.body:
            start = time.time()
            logmessage('\n/API/gtfs/calendar_dates POST call')
            pw = self.get_argument('pw', default='')
            if not decrypt(pw):
                self.set_status(400)
                self.write("Error: invalid password.")
                return
            # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
            data = json.loads(self.request.body.decode('UTF-8'))

            if replaceTableDB('calendar_dates', data):  # replaceTableDB(tablename, data)
                self.write('Saved calendar_dates data to DB.')
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/calendar_dates POST call took {} seconds.".format(round(end - start, 2)))
        else:
            self.write("Error: Saving table data")

class gtfscalendardateslistids(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/calendar_dates/list/id
        start = time.time()
        logmessage('\n/API/gtfs/calendar_dates/list/id GET call')
        listCollector = set()
        listCollector.update(readColumnDB('calendar_dates', 'service_id'))
        # to do: find out why this function is only looking at stops table
        List = list(listCollector)
        List.sort()
        self.write(json.dumps(List))
        end = time.time()
        logmessage("\n/API/gtfs/calendar_dates/list/id GET call took {} seconds.".format(round(end - start, 2)))
