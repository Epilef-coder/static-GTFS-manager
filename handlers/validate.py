from io import StringIO

import sys
import time
import tornado.web
import tornado.ioloop

from utils.transitfeed import feedvalidator
from utils.logmessage import logmessage
from settings import exportFolder

class googlevalidate(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        # API/commitExport?commit=${commit}

        # Validate based on patch from: https://github.com/pecalleja/transitfeed/releases/tag/python3
        # adapted from https://github.com/ed-g/transitfeed_web/blob/1e9be7152823641c450612b27cace99a1efe0b4f/transitfeed_web/run_transitfeed_web_server.py
        # with open(exportFolder + '2019-06-14-backup-0932/gtfs.zip', mode='rb') as file:  # b is important -> binary
        #     fileContent = file.read()
        #
        #
        # gtfs_file = StringIO()
        # gtfs_file.write(fileContent)  # binary content in r.content
        # gtfs_file.seek(0)  # rewind.

        # Pretend to pass command-line arguments to feedvalidator. It returns an
        # "options" object which is used to configure to the validation function.
        save_argv = sys.argv  # save actual argv
        sys.argv = ['fakeout-argv-for-feedparser.py', 'fake-placeholder-gtfs-file.zip']
        options = feedvalidator.ParseCommandLineArguments()[1]
        sys.argv = save_argv  # restore argv

        output_file = StringIO()
        feedvalidator.RunValidationOutputToFile(exportFolder + '2019-06-14-backup-0932/gtfs.zip', options, output_file)

        # return output_file.getvalue()
        self.write(output_file.getvalue())
        end = time.time()
        logmessage("commitExport GET call took {} seconds.".format(round(end-start,2)))
