import datetime

import tornado.web
import tornado.ioloop
import time
import os
import json

from utils.gtfsimportexport import importGTFS, exportGTFS
from utils.logmessage import logmessage
from utils.password import decrypt
from utils.piwiktracking import logUse
from utils.upload import uploadaFile
from settings import exportFolder

class gtfsImportZip(tornado.web.RequestHandler):
    def post(self):
        # API/gtfsImportZip?pw=${pw}
        start = time.time()
        logmessage('\ngtfsImportZip GET call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return

        zipname = uploadaFile( self.request.files['gtfsZipFile'][0] )
        if importGTFS(zipname):
            self.write(zipname)
        else:
            self.set_status(400)
            self.write("Error: invalid GTFS feed.")

        end = time.time()
        logmessage("gtfsImportZip POST call took {} seconds.".format( round(end-start,2) ))
        logUse('gtfsImportZip')


class commitExport(tornado.web.RequestHandler):
    def get(self):
        # API/commitExport?commit=${commit}
        start = time.time()
        logmessage('\ncommitExport GET call')
        commit = self.get_argument('commit', default='')
        if not len(commit):
            self.set_status(400)
            self.write("Error: invalid commit name.")
            return
        commitFolder = exportFolder + '{:%Y-%m-%d-}'.format(datetime.datetime.now()) + commit + '/'
        finalmessage = exportGTFS(commitFolder)
        # this is the main function. it's in GTFSserverfunctions.py

        self.write(finalmessage)
        end = time.time()
        logmessage("commitExport GET call took {} seconds.".format(round(end-start,2)))
        logUse('commitExport')


class pastCommits(tornado.web.RequestHandler):
    def get(self):
        # API/pastCommits
        start = time.time()
        logmessage('\npastCommits GET call')
        dirnames = []
        for root, dirs, files in os.walk(exportFolder):
            for folder in dirs:
                if os.path.isfile(exportFolder + folder + '/gtfs.zip'):
                    dirnames.append(folder)
        if not len(dirnames):
            self.set_status(400)
            self.write("No past commits found.")
            return

        # reversing list, from
        dirnames = dirnames[::-1]
        writeback = { "commits": dirnames }
        self.write(json.dumps(writeback))
        end = time.time()
        logmessage("pastCommits GET call took {} seconds.".format(round(end-start,2)))