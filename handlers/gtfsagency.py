import tornado.web
import tornado.ioloop
import time
import json

from utils.logmessage import logmessage
from utils.tables import readTableDB,replaceTableDB,readColumnDB,readColumnsDB
from utils.password import decrypt

class agency(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        logmessage('\nagency GET call')
        agencyJson = readTableDB('agency').to_json(orient='records', force_ascii=False)
        self.write(agencyJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("agency GET call took {} seconds.".format(round(end -start ,2)))

    def post(self):
        start = time.time()
        logmessage('\nagency POST call')
        pw = self.get_argument('pw' ,default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads( self.request.body.decode('UTF-8') )

        if replaceTableDB('agency', data):  # replaceTableDB(tablename, data)
            self.write('Saved Agency data to DB.')
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("saveAgency POST call took {} seconds.".format(round(end -start ,2))
)

class gtfsagency(tornado.web.RequestHandler):
    # /API/gtfs/agency AND /API/gtfs/agency/{Agency_id}
    def get(self, agency_id=None):
        if agency_id:
            start = time.time()
            logmessage('\n/API/gtfs/agency/{} GET call'.format(agency_id))
            agencyJson = readTableDB('agency', key='agency_id', value=agency_id).to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/agency/{} GET call took {} seconds.".format(agency_id, round(end - start, 2)))
        else:
            start = time.time()
            logmessage('\n/API/gtfs/agency GET call')
            agencyJson = readTableDB('agency').to_json(orient='records', force_ascii=False)
            self.write(agencyJson)
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/agency GET call took {} seconds.".format(round(end - start, 2)))

    def post(self):
        # /API/gtfs/agency AND /API/gtfs/agency/{Agency_id}
        if self.request.body:
            start = time.time()
            logmessage('\n/API/gtfs/agency POST call')
            pw = self.get_argument('pw', default='')
            if not decrypt(pw):
                self.set_status(400)
                self.write("Error: invalid password.")
                return
            # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
            data = json.loads(self.request.body.decode('UTF-8'))

            if replaceTableDB('agency', data):  # replaceTableDB(tablename, data)
                self.write('Saved Agency data to DB.')
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/agency POST call took {} seconds.".format(round(end - start, 2)))
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

class gtfsagencylistids(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/agency/list/id
        start = time.time()
        logmessage('\n/API/gtfs/agency/list/id GET call')
        listCollector = set()
        listCollector.update(readColumnDB('agency', 'agency_id'))
        # to do: find out why this function is only looking at stops table
        List = list(listCollector)
        List.sort()
        self.write(json.dumps(List))
        end = time.time()
        logmessage("\n/API/gtfs/agency/list/id GET call took {} seconds.".format(round(end - start, 2)))

class gtfsagencylistidnames(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/agency/list/idname
        start = time.time()
        logmessage('\n/API/gtfs/agency/list/idname GET call')
        columns = ['agency_id','agency_name']
        agencyJson = readColumnsDB('agency',columns).to_json(orient='records', force_ascii=False)
        self.write(agencyJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("/API/gtfs/agency/list/idname GET call took {} seconds.".format(round(end - start, 2)))