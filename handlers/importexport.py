import datetime

import tornado.web
import tornado.ioloop
import time
import os
import json

from utils.gtfsimportexport import exportGTFS
from utils.logmessage import logmessage
from utils.piwiktracking import logUse
from settings import exportFolder

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
        finalmessage = exportGTFS(commit)
        # this is the main function. it's in utils/gtfsimportexport.py

        self.write(finalmessage['message'])
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