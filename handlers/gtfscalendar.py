import datetime
import json
import time

import tornado.web

from utils.logmessage import logmessage
from utils.password import decrypt
from utils.tables import readColumnDB, readColumnsDB, readTableDB, replaceTableDB


class calendar(tornado.web.RequestHandler):
    def get(self):
        # API/calendar?current=y
        start = time.time() # time check
        logmessage('\ncalendar GET call')
        current = self.get_argument('current',default='')

        if current.lower() == 'y':
            calendarJson = calendarCurrent().to_json(orient='records', force_ascii=False)
        else:
            calendarJson = readTableDB('calendar').to_json(orient='records', force_ascii=False)
        self.write(calendarJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("calendar GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        # API/calendar?pw=${pw}
        start = time.time() # time check
        logmessage('\ncalendar POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        calendarData = json.loads( self.request.body.decode('UTF-8') )

        #csvwriter(calendarData,'calendar.txt')
        replaceTableDB('calendar', calendarData)

        self.write('Saved Calendar data to DB.')
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("calendar POST call took {} seconds.".format(round(end-start,2)))


class gtfscalendar(tornado.web.RequestHandler):
    # /API/gtfs/calendar AND /API/gtfs/calendar/{service_id}
    def get(self, service_id=None):
        if service_id:
            start = time.time()
            logmessage('\n/API/gtfs/calendar/{} GET call'.format(service_id))
            agencyJson = readTableDB('calendar', key='service_id', value=service_id).to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/calendar/{} GET call took {} seconds.".format(service_id, round(end - start, 2)))
        else:
            start = time.time()
            logmessage('\n/API/gtfs/calendar GET call')
            agencyJson = readTableDB('calendar').to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/calendar GET call took {} seconds.".format(round(end - start, 2)))

    def post(self):
        # /API/gtfs/calendar AND /API/gtfs/calendar/{service_id}
        if self.request.body:
            start = time.time()
            logmessage('\n/API/gtfs/calendar POST call')
            pw = self.get_argument('pw', default='')
            if not decrypt(pw):
                self.set_status(400)
                self.write("Error: invalid password.")
                return
            # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
            data = json.loads(self.request.body.decode('UTF-8'))

            if replaceTableDB('calendar', data):  # replaceTableDB(tablename, data)
                self.write('Saved Agency data to DB.')
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/calendar POST call took {} seconds.".format(round(end - start, 2)))
        else:
            self.write("Error: Saving table data")

class gtfscalendarlistids(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/calendar/list/id
        start = time.time()
        logmessage('\n/API/gtfs/calendar/list/id GET call')
        listCollector = set()
        listCollector.update(readColumnDB('calendar', 'service_id'))
        # to do: find out why this function is only looking at stops table
        List = list(listCollector)
        List.sort()
        self.write(json.dumps(List))
        end = time.time()
        logmessage("\n/API/gtfs/calendar/list/id GET call took {} seconds.".format(round(end - start, 2)))

class gtfscalendarcurrent(tornado.web.RequestHandler):
    # /API/gtfs/calendar AND /API/gtfs/calendar/{service_id}
    def get(self, service_id=None):
        start = time.time()
        logmessage('\n/API/gtfs/calendar/current GET call')
        agencyJson = calendarCurrent().to_json(orient='records', force_ascii=False)
        self.write(agencyJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("/API/gtfs/calendar/current GET call took {} seconds.".format(round(end - start, 2)))

def calendarCurrent():
    calendarDF = readTableDB('calendar')
    today = float( '{:%Y%m%d}'.format(datetime.datetime.now()) )
    logmessage(today)
    calendarDF.end_date = calendarDF.end_date.astype(float)
    return calendarDF[ calendarDF.end_date >= today ]