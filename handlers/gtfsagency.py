import tornado.web
import tornado.ioloop
import time
from utils.logmessage import logmessage
from utils.tables import readTableDB

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