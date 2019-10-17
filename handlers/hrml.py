import json
import time

import tornado.web

from utils.hrmlcsv2gtfs import hydGTFSfunc
from utils.logmessage import logmessage
from utils.password import decrypt


class hrmlhydGTFS(tornado.web.RequestHandler):
    def post(self):
        start = time.time()
        logmessage('\nhydGTFS POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return

        files = self.request.files
        #print(files)

        # Getting POST form input data, from https://stackoverflow.com/a/32418838/4355695
        #formdata = self.request.body_arguments() # that didn't work
        payload = json.loads( self.get_body_argument("payload", default=None, strip=False) )
        #print(payload)

        returnJson = hydGTFSfunc(files, payload)

        #returnMessage = {'status':'Feature Under Construction!'}
        self.write(returnJson)

        end = time.time()
        logmessage("hydGTFS POST call took {} seconds.".format(round(end-start,2)))