from utils.logmessage import logmessage
from utils.tables import tinyDBopen
from tinydb import Query

def sequenceFull(sequenceDBfile, route_id):
	# 20.4.18 : writing this to pass on shapes data too. in future, change things on JS end and merge the sequenceReadDB function with this.
	db = tinyDBopen(sequenceDBfile)
	Item = Query()
	sequenceItem = db.search(Item['route_id'] == route_id)
	db.close()

	if sequenceItem == []:
		return False

	sequenceArray = sequenceItem[0]
	logmessage('Got the sequence from sequence db file.')
	return sequenceArray