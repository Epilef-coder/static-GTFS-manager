from utils.logmessage import logmessage
from utils.tables import tinyDBopen, readTableDB, readColumnDB
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


def extractSequencefromGTFS(route_id):
	# idea: scan for the first trip matching a route_id, in each direction, and get its sequence from stop_times.
	# In case it hasn't been provisioned yet in stop_times, will return empty arrays.

	tripsdf = readTableDB('trips', key='route_id', value=route_id)
	if not len(tripsdf):
		logmessage('extractSequencefromGTFS: no trips found for {}. Skipping.'.format(route_id))
		return [ [], [] ]

	if 'direction_id' not in tripsdf.columns:
		logmessage('extractSequencefromGTFS: Trips table doesn\'t have any direction_id column. Well, its optional.. taking the first trip only for route {}.'.format(route_id))
		oneTrip0 = tripsdf.iloc[0].trip_id
		oneTrip1 = None

	else:
		dir0df = tripsdf[ tripsdf.direction_id == '0'].copy().reset_index(drop=True).trip_id
		oneTrip0 = dir0df.iloc[0] if len(dir0df) else tripsdf.iloc[0].trip_id
		# using first trip's id as default, for cases where direction_id is blank.

		dir1df = tripsdf[ tripsdf.direction_id == '1'].copy().reset_index(drop=True).trip_id
		oneTrip1 = dir1df.iloc[0] if len(dir1df) else None
		# reset_index: re-indexes as 0,1,... from https://stackoverflow.com/a/20491748/4355695

		del dir0df
		del dir1df
	del tripsdf

	if oneTrip0:
		array0 = readColumnDB('stop_times','stop_id', key='trip_id', value=oneTrip0)
		logmessage('extractSequencefromGTFS: Loading sequence for route {}, onward direction from trip {}:\n{}'.format(route_id,oneTrip0,str(list(array0[:50])) ))
	else:
		array0 = []
		logmessage('No onward sequence found for route {}'.format(route_id))

	if oneTrip1:
		array1 = readColumnDB('stop_times','stop_id', key='trip_id', value=oneTrip1)
		logmessage('extractSequencefromGTFS: Loading sequence for route {}, return direction from trip {}:\n{}'.format(route_id,oneTrip1,str(list(array1[:50])) ))
	else:
		array1 = []
		logmessage('No return sequence found for route {}'.format(route_id))


	sequence = [array0, array1]
	return sequence