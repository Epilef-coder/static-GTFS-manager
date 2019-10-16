import tornado.web
import tornado.ioloop
import time
import json

from utils.logmessage import logmessage
from utils.password import decrypt
from utils.tables import readTableDB, readColumnDB, replaceTableDB, readColumnsDB


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


class gtfsroutes(tornado.web.RequestHandler):
    # /API/gtfs/routes AND /API/gtfs/routes/{route_id}
    def get(self, route_id=None):
        if route_id:
            start = time.time()
            logmessage('\n/API/gtfs/routes/{} GET call'.format(route_id))
            agencyJson = readTableDB('routes', key='route_id', value=route_id).to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/routes/{} GET call took {} seconds.".format(route_id, round(end - start, 2)))
        else:
            start = time.time()
            logmessage('\n/API/gtfs/route GET call')
            agencyJson = readTableDB('routes').to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/route GET call took {} seconds.".format(round(end - start, 2)))

    def post(self):
        # /API/gtfs/routes AND /API/gtfs/routes/{route_id}
        if self.request.body:
            start = time.time()
            logmessage('\n/API/gtfs/route POST call')
            pw = self.get_argument('pw', default='')
            if not decrypt(pw):
                self.set_status(400)
                self.write("Error: invalid password.")
                return
            # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
            data = json.loads(self.request.body.decode('UTF-8'))

            if replaceTableDB('routes', data):  # replaceTableDB(tablename, data)
                self.write('Saved Agency data to DB.')
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/route POST call took {} seconds.".format(round(end - start, 2)))
        else:
            self.write("Error: Saving table data")

    # def put(self, id):
    # 	if self.request.body:
    # 		item = get_json_arg(self.request.body, ['name'])
    # 		Items.update_single('name', item['name'], int(id))
    # 		self.json_response({'message': 'item updated'})
    # 	else:
    # 		self.json_error()
    #
    # def delete(self, id):
    # 	Items.delete_single(id)
    # 	message = {'message': 'Item with id {} was deleted'.format(id)}
    # 	self.json_response(message)

class gtfsrouteslistids(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/routes/list/id
        start = time.time()
        logmessage('\n/API/gtfs/route/list/id GET call')
        listCollector = set()
        listCollector.update(readColumnDB('routes', 'route_id'))
        # to do: find out why this function is only looking at stops table
        List = list(listCollector)
        List.sort()
        self.write(json.dumps(List))
        end = time.time()
        logmessage("\n/API/gtfs/route/list/id GET call took {} seconds.".format(round(end - start, 2)))

class gtfsrouteslistidnames(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/route/list/idname
        start = time.time()
        logmessage('\n/API/gtfs/route/list/idname GET call')
        columns = ['route_id','route_short_name']
        agencyJson = readColumnsDB('routes',columns).to_json(orient='records', force_ascii=False)
        self.write(agencyJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("/API/gtfs/route/list/idname GET call took {} seconds.".format(round(end - start, 2)))