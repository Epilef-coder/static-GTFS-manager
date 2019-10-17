import json
import time

import tornado.web

from utils.logmessage import logmessage
from utils.password import decrypt
from utils.renamedelete import GetAllIds, replaceIDfunc, diagnoseIDfunc, deleteID


class gtfsrenamelistAllids(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/rename/listid
        # a Master API call for fetching all id's!
        start = time.time()
        logmessage('\nlistAll GET call')
        returnJson = json.dumps(GetAllIds())
        self.write(returnJson)
        end = time.time()
        logmessage("listAll GET call took {} seconds.".format(round(end-start,2)))


class gtfsdeletelistAllids(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/delete/listid
        # a Master API call for fetching all id's!
        start = time.time()
        logmessage('\nlistAll GET call')
        returnJson = json.dumps(GetAllIds())
        self.write(returnJson)
        end = time.time()
        logmessage("listAll GET call took {} seconds.".format(round(end-start,2)))


class gtfsReplaceID(tornado.web.RequestHandler):
    def get(self,key=None):
        if key:
            # ${APIpath}replaceID?pw=pw&key=key&valueFrom=valueFrom&valueTo=valueTo
            start = time.time()
            logmessage('\nreplaceID POST call')
            pw = self.get_argument('pw',default='')
            if not decrypt(pw):
                self.set_status(400)
                self.write("Error: invalid password.")
                return

            valueFrom = self.get_argument('valueFrom', default='')
            valueTo = self.get_argument('valueTo', default='')
            # tableKeys = json.loads( self.request.body.decode('UTF-8') )
            # tablekeys: [ {'table':'stops','key':'stop_id'},{...}]

            if not ( len(valueFrom) and len(valueTo) and len(key) ):
                self.set_status(400)
                self.write("Error: Invalid parameters.")
                return

            # main function:
            returnMessage = replaceIDfunc(key,valueFrom,valueTo)

            self.write(returnMessage)

            end = time.time()
            logmessage("replaceID POST call took {} seconds.".format(round(end-start,2)))


class gtfsdeletediag(tornado.web.RequestHandler):
    def get(self, column=None):
        if column:
            # ${APIpath}diagnoseID?column=column&value=value
            start = time.time()
            logmessage('\ndiagnoseID GET call')

            value = self.get_argument('value', default='')

            if not ( len(column) and len(value) ):
                self.set_status(400)
                self.write("Error: invalid parameters.")
                return
            returnMessage = diagnoseIDfunc(column,value)
            self.write(returnMessage)

            end = time.time()
            logmessage("diagnoseID GET call took {} seconds.".format(round(end-start,2)))


class gtfsdeleteByKey(tornado.web.RequestHandler):
    def get(self, column=None):
        if column:
            # ${APIpath}deleteByKey?pw=pw&key=key&value=value&tables=table1,table2
            start = time.time()
            logmessage('\ndeleteByKey GET call')
            pw = self.get_argument('pw',default='')
            if not decrypt(pw):
                self.set_status(400)
                self.write("Error: invalid password.")
                return

            value = self.get_argument('value', default='')
            if not ( len(column) and len(value) ):
                logmessage("API/deleteByKey : Error: invalid parameters.")
                self.set_status(400)
                self.write("Error: invalid parameters.")
                return

            returnMessage = deleteID(column,value)
            self.write(returnMessage)

            end = time.time()
            logmessage("deleteByKey GET call took {} seconds.".format(round(end-start,2)))