import tornado.web
import tornado.ioloop
import time
import json

from utils.logmessage import logmessage
from utils.tables import readTableDB,replaceTableDB,readColumnDB,readColumnsDB
from utils.password import decrypt


class gtfsfeedinfo(tornado.web.RequestHandler):
    # /API/gtfs/feedinfo
    def get(self):
        start = time.time()
        logmessage('\n/API/gtfs/feedinfo GET call')
        agencyJson = readTableDB('feed_info').to_json(orient='records', force_ascii=False)
        self.write(agencyJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("/API/gtfs/feedinfo GET call took {} seconds.".format(round(end - start, 2)))

    def post(self):
        # /API/gtfs/agency AND /API/gtfs/agency/{Agency_id}
        if self.request.body:
            start = time.time()
            logmessage('\n/API/gtfs/feedinfo POST call')
            pw = self.get_argument('pw', default='')
            if not decrypt(pw):
                self.set_status(400)
                self.write("Error: invalid password.")
                return
            # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
            data = json.loads(self.request.body.decode('UTF-8'))

            if replaceTableDB('feed_info', data):  # replaceTableDB(tablename, data)
                self.write('Saved Agency data to DB.')
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/feedinfo POST call took {} seconds.".format(round(end - start, 2)))
        else:
            self.write("Error: Saving table data")
