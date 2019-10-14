import tornado.web
import tornado.ioloop
import time
import json

from utils.logmessage import logmessage
from utils.tables import readTableDB,readColumnDB,replaceTableDB

class routes(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        logmessage('\nroutes GET call')

        allRoutesJson = readTableDB('routes').to_json(orient='records', force_ascii=False)
        self.write(allRoutesJson)
        end = time.time()
        logmessage("routes GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        start = time.time()
        logmessage('\nroutes POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads( self.request.body.decode('UTF-8') )
        # writing back to db now
        if replaceTableDB('routes', data): #replaceTableDB(tablename, data)
            self.write('Saved routes data to DB')
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("routes POST call took {} seconds.".format(round(end-start,2)))


class routeIdList(tornado.web.RequestHandler):
    def get(self):
        # API/routeIdList
        start = time.time()
        logmessage('\nrouteIdList GET call')
        #routesArray = readTableDB('routes')
        #route_id_list = [ n['route_id'] for n in routesArray ]

        route_id_list = readColumnDB('routes','route_id')
        self.write(json.dumps(route_id_list))
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("routeIdList GET call took {} seconds.".format(round(end-start,2)))