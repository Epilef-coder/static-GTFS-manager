import json

import tornado.web

from utils.logmessage import logmessage
from utils.password import decrypt


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