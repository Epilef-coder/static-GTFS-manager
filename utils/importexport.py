from collections import OrderedDict

import pandas as pd
import xmltodict

from settings import uploadFolder, xmlFolder
from utils.logmessage import logmessage


def csvwriter( array2write, filename, keys=None ):
	# 15.4.18: Changing to use pandas instead of csv.DictWriter. Solves https://github.com/WRI-Cities/static-GTFS-manager/issues/3
	df = pd.DataFrame(array2write)
	df.to_csv(filename, index=False, columns=keys)
	logmessage( 'Created', filename )


def diagnoseXMLs(weekdayXML, sundayXML, depot=None) :
	try:
		weekdayReport = '<p>Weekday XML: <a target="_blank" href="' + uploadFolder + weekdayXML + '">' + weekdayXML + '&#x2197;</a></p>'
		sundayReport = '<p>Sunday XML: <a target="_blank" href="' + uploadFolder + sundayXML + '">' + sundayXML + '&#x2197;</a></p>'
		weekdaySchedules = []
		sundaySchedules = []
		fullStopsList = set()

		# depot trip checking:
		dropDepotTrips = 0

		if depot:
			depotsList = depot.split(',')
		else:
			depotsList = []
		logmessage('Depot stations: ' + str(depotsList) )
		# logic: if first stop or last stop is in depotsList, then increment dropDepotTrips counter.

		# 1. before processing XMLs, lets get the mapped stops list from the resident stations.csv
		mappedStopsList = readStationsCSV(xmlFolder + 'stations.csv')


		# 2. Loading Weekday XML file.
		with open( uploadFolder + weekdayXML , encoding='utf8' ) as fd:
			fileholder = xmltodict.parse(fd.read(), attr_prefix='')
		# trips_from_xml = fileholder['ROOT']['SCHEDULE']['TRIPS']['TRIP']
		scheduleHolder = fileholder['ROOT']['SCHEDULE']
		# whether the node is single or repeating in the XML, convert it so that it becomes a list to iterate through
		if type(scheduleHolder) == type(OrderedDict()) :
			scheduleHolder = [scheduleHolder]
			# this makes a single schedule compatible with multiple schedule entries in xml

		logmessage(str(len(scheduleHolder)) + ' route(s) found in ' + weekdayXML)

		for schedule in scheduleHolder:
			schedule_name = schedule['NAME']
			stopsList = set()
			directions = set()
			vehicles = set()
			timesList = set()
			for trip in schedule['TRIPS']['TRIP']:
				timesList.add(trip['ENTRY_TIME'])
				directions.add(trip['DIRECTION'])
				vehicles.add(trip['SERVICE_ID'])
				# check if first or last stop is in depotsList
				if (trip['STOP'][0]['TOP'] in depotsList) or ( trip['STOP'][-1]['TOP'] in depotsList ):
					dropDepotTrips += 1
				for stop in trip['STOP']:
					stopsList.add(stop['TOP'])
			fullStopsList.update(stopsList)

			# sorting: https://www.tutorialspoint.com/python/list_sort.htm
			sortedTimesList = list(timesList)
			sortedTimesList.sort()

			weekdayReport += '<p><b>Schedule: ' + schedule_name + '</b>'
			weekdayReport += '<br>Trips: ' + str( len( schedule['TRIPS']['TRIP'] ))
			weekdayReport += '<br>Vehicles: ' + str( len( vehicles ))
			weekdayReport += '<br>Directions: ' + str( len( directions ))
			weekdayReport += '<br>First trip: ' + sortedTimesList[0]
			weekdayReport += '<br>Last trip: ' + sortedTimesList[-1] + '</p>'
			weekdaySchedules.append(schedule_name)


		################
		# 3. Loading Sunday XML file.
		with open( uploadFolder + sundayXML , encoding='utf8' ) as fd:
			fileholder = xmltodict.parse(fd.read(), attr_prefix='')
		# trips_from_xml = fileholder['ROOT']['SCHEDULE']['TRIPS']['TRIP']
		scheduleHolder = fileholder['ROOT']['SCHEDULE']
		# whether the node is single or repeating in the XML, convert it so that it becomes a list to iterate through
		if type(scheduleHolder) == type(OrderedDict()) :
			scheduleHolder = [scheduleHolder]
			# this makes a single schedule compatible with multiple schedule entries in xml

		logmessage(str(len(scheduleHolder)) + ' route(s) found in ' + sundayXML)

		for schedule in scheduleHolder:
			schedule_name = schedule['NAME']
			stopsList = set()
			directions = set()
			vehicles = set()
			timesList = set()
			for trip in schedule['TRIPS']['TRIP']:
				timesList.add(trip['ENTRY_TIME'])
				directions.add(trip['DIRECTION'])
				vehicles.add(trip['SERVICE_ID'])
				# check if first or last stop is in depotsList
				if (trip['STOP'][0]['TOP'] in depotsList) or ( trip['STOP'][-1]['TOP'] in depotsList ):
					dropDepotTrips += 1
				for stop in trip['STOP']:
					stopsList.add(stop['TOP'])
			fullStopsList.update(stopsList)

			sortedTimesList = list(timesList)
			sortedTimesList.sort()

			sundayReport += '<p><b>Schedule: ' + schedule_name + '</b>'
			sundayReport += '<br>Trips: ' + str( len( schedule['TRIPS']['TRIP'] ))
			sundayReport += '<br>Vehicles: ' + str( len( vehicles ))
			sundayReport += '<br>Directions: ' + str( len( directions ))
			sundayReport += '<br>First trip: ' + sortedTimesList[0]
			sundayReport += '<br>Last trip: ' + sortedTimesList[-1] + '</p>'
			sundaySchedules.append(schedule_name)

		############
		# 4. Calculate missing stops and write verbose.
		check = len(fullStopsList - mappedStopsList)

		if not check:
			missingStopsReport = '<p><font color="green"><b><font size="6">&#10004;</font> All internal stops are mapped!</b></font><br>We are good to proceed to step 3.</p>';
			stationsStatus = missingStopsReport
			allStopsMappedFlag = True
		else :
			missingListing = ''
			for item in (fullStopsList - mappedStopsList):
				missingListing += '<li>' + item + '</li>'
			missingStopsReport = '<p><font color="red"><b><font size="5">&#10008;</font>  ' + str(check) + ' stop(s) are missing</b></font> from the stations mapping list.<br>Proceed to step 2, and ensure that the following internal station names are present under either <b><i>up_id</i></b> or <b><i>down_id</i></b> columns, with the corresponding columns filled properly:<br><b><ul>' + missingListing + '</ul></b></p>'
			stationsStatus = '<p><font color="red"><b><font size="5">&#10008;</font>  ' + str(check) + ' stop(s) are missing</b></font> from the stations mapping list.<br>Ensure that the following internal station names are present under either <b><i>up_id</i></b> or <b><i>down_id</i></b> columns, with the corresponding columns filled in properly:<br><b><ul>' + missingListing + '</ul></b></p>'
			allStopsMappedFlag = False

		#########
		# 5. putting the report together in HTML
		diagBox = '<small><div class="row"><div class="col">' + weekdayReport + '</div><div class="col">' + sundayReport + '</div></div></small>' + '<hr>' + missingStopsReport

		#########
		# 6. Appending
		dropDepotTripsText = '<div class="alert alert-warning">Note: Total <u><b>' + str(dropDepotTrips) + '</b> trips will be dropped</u> from the XMLs as they are depot trips, ie, they originate from or terminate at the depot station (chosen in step 2).</div>'
		diagBox += dropDepotTripsText
		stationsStatus += dropDepotTripsText

		#########
		# 6. Return a dict
		return { 'report':diagBox, 'stationsStatus':stationsStatus, 'weekdaySchedules':weekdaySchedules,
		'sundaySchedules':sundaySchedules, 'allStopsMappedFlag':allStopsMappedFlag }
	except:
		return False


def csvunpivot(filename, keepcols, var_header, value_header, sortby):
	# brought in from xml2GTFS functions.py
	fares_pivoted = pd.read_csv(filename, encoding='utf8')
	logmessage( 'Loading and unpivoting',filename)
	fares_unpivoted = pd.melt(fares_pivoted, id_vars=keepcols, var_name=var_header, value_name=value_header).sort_values(by=sortby)

	# rename header 'Stations' to 'origin_id', from https://stackoverflow.com/questions/11346283/renaming-columns-in-pandas/
	# and drop all rows having NaN values. from https://stackoverflow.com/a/13434501/4355695
	fares_unpivoted_clean = fares_unpivoted.rename(columns={'Stations': 'origin_id'}).dropna()
	# 4.9.18: returns a dataframe now
	return fares_unpivoted_clean


def readStationsCSV(csvfile = xmlFolder + 'stations.csv'):
	'''
	This is for KMRL Metro file import
	'''
	stations = pd.read_csv(csvfile)

	# load up_id and down_id columns, but removing blank/null values. From https://stackoverflow.com/a/22553757/4355695
	upList = stations[stations['up_id'].notnull()]['up_id']
	downList = stations[stations['down_id'].notnull()]['down_id']

	mappedStopsList = set() # non-repeating list. Silently drops any repeating values getting added.
	mappedStopsList.update( upList )
	mappedStopsList.update( downList )
	return mappedStopsList