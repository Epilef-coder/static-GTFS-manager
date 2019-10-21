import datetime
import json
import os
import shutil
import uuid
from io import StringIO

import sys
import time
import tornado.web
import tornado.ioloop

from utils.gtfsimportexport import exportGTFS
#  This is a custom version of the transitfeed validator because the published version does not support python 3
from utils.transitfeed import feedvalidator
from utils.logmessage import logmessage
from settings import exportFolder, reportFolder


class googlevalidate(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        # API/commitExport?commit=${commit}
        googletransitenabled = self.get_argument('googletransit', default='')
        savereport = self.get_argument('savereport', default='')
        # Validate based on patch from: https://github.com/pecalleja/transitfeed/releases/tag/python3
        # adapted from https://github.com/ed-g/transitfeed_web/blob/1e9be7152823641c450612b27cace99a1efe0b4f/transitfeed_web/run_transitfeed_web_server.py
        # Make a export of the current gtfs files to a temp folder
        tempfilename = str(uuid.uuid4())
        commitFolder = exportFolder + tempfilename + '/'
        exportGTFS(commitFolder)

        # Pretend to pass command-line arguments to feedvalidator. It returns an
        # "options" object which is used to configure to the validation function.
        save_argv = sys.argv  # save actual argv
        sys.argv = ['fakeout-argv-for-feedparser.py', 'fake-placeholder-gtfs-file.zip']
        options = feedvalidator.ParseCommandLineArguments()[1]
        if bool(googletransitenabled):
            options.extension = 'extensions.googletransit'
        sys.argv = save_argv  # restore argv

        output_file = StringIO()
        feedvalidator.RunValidationOutputToFile(commitFolder + '/gtfs.zip', options, output_file)
        resultreport = output_file.getvalue()
        # return output_file.getvalue()
        self.write(resultreport)

        end = time.time()
        logmessage("commitExport GET call took {} seconds.".format(round(end-start,2)))
        # Save the files to validation reports location
        if bool(savereport):
            if not os.path.exists(reportFolder):
                os.makedirs(reportFolder)
            f = open(reportFolder + '/' + tempfilename + '.html', "w", encoding='utf8')
            f.write(resultreport)
            f.close()
        # Remove the custom older.
        output_file.close()
        shutil.rmtree(commitFolder)

class pastreportsgtfsvalidate(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        if os.path.exists(reportFolder):
            ListReports = os.listdir(reportFolder)
        else:
            ListReports = {}
        self.write(json.dumps(ListReports))

        end = time.time()
        logmessage("commitExport GET call took {} seconds.".format(round(end-start,2)))
