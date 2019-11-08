import json
import time
import tornado.web

from settings import debugMode,configFolder
from utils.app import GTFSstats
from utils.gtfsimportexport import backupDB, purgeDB, importGTFS
from utils.logmessage import logmessage
from utils.password import decrypt
from utils.piwiktracking import logUse
from utils.upload import uploadaFile


class AppDatabaseBlank(tornado.web.RequestHandler):
    def get(self):
        # API/app/database/blank?pw=${pw}
        start = time.time()
        logmessage('\ngtfsBlankSlate GET call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return

        # take backup first, if we're not in debug mode.
        if not debugMode:
            backupDB()
            finalmessage = '<font color=green size=6>&#10004;</font> Took a backup and cleaned out the DB.'
        else:
            finalmessage = '<font color=green size=6>&#10004;</font> Cleaned out the DB.'

        # outsourced purging DB to a function
        purgeDB()

        self.write(finalmessage)
        end = time.time()
        logmessage("gtfsBlankSlate GET call took {} seconds.".format(round(end-start,2)))
        logUse('gtfsBlankSlate')


class AppDatabaseGTFSImport(tornado.web.RequestHandler):
    def post(self):
        # API/app/database/gtfs/import?pw=${pw}
        start = time.time()
        logmessage('\nAPI/app/database/gtfs/import GET call')
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
        logmessage("API/app/database/gtfs/import POST call took {} seconds.".format( round(end-start,2) ))
        logUse('gtfsImportZip')


class AppConfig(tornado.web.RequestHandler):
        def get(self):
            # get the Argument that User had passed as name in the get request
            # userInput=self.get_argument('name')
            logmessage('\nAPI/app/Config GET call')
            self.set_header("Content-Type", "application/x-json")
            with open(configFolder + 'apikeys.json') as f:
                    apikeys = json.load(f)
                    self.write(apikeys)

        def post(self):
            logmessage('\nAPI/app/Config POST call')
            with open(configFolder + 'apikeys.json','w') as f:
                f.write(self.request.body.decode('UTF-8'))
                self.write(json.dumps({'status': 'ok', 'data': []}))


class Appstats(tornado.web.RequestHandler):
    def get(self):
        # API/stats
        start = time.time()
        logmessage('\nstats GET call')
        stats = GTFSstats()

        self.write(json.dumps(stats))
        end = time.time()
        logmessage("stats GET call took {} seconds.".format(round(end - start, 2)))
        logUse('stats')