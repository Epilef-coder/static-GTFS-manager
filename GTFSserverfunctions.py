'''
GTFSserverfunctions.py
this file is to be inline included in the main script. Seriously, I do not want to keep declaring import statements everywhere.


import tornado.web
import tornado.ioloop
import json
import os
import time, datetime

import xmltodict
import pandas as pd
from collections import OrderedDict
import zipfile, zlib
from tinydb import TinyDB, Query
from tinydb.operations import delete
import webbrowser
from Cryptodome.PublicKey import RSA #uses pycryptodomex package.. disambiguates from pycrypto, pycryptodome
import shutil # used in fareChartUpload to fix header if changed
import pathlib
from math import sin, cos, sqrt, atan2, radians # for lat-long distance calculations
# import requests # nope, not needed for now
from json.decoder import JSONDecodeError # used to catch corrupted DB file when tinyDB loads it.
import signal, sys # for catching Ctrl+C and exiting gracefully.
import gc # garbage collector, from https://stackoverflow.com/a/1316793/4355695
import csv
import numpy as np
import io # used in hyd csv import

# to do: how to get these variables declared in the other file to be recognized here?

global uploadFolder
global xmlFolder
global logFolder
global configFolder
global dbFolder
global exportFolder

global sequenceDBfile
global passwordFile
global chunkRulesFile
global configFile

if __name__ == "__main__":
	print("Don't run this, run GTFSManager.py.")

'''
from utils.logmessage import logmessage

def csvwriter( array2write, filename, keys=None ):
	# 15.4.18: Changing to use pandas instead of csv.DictWriter. Solves https://github.com/WRI-Cities/static-GTFS-manager/issues/3
	df = pd.DataFrame(array2write)
	df.to_csv(filename, index=False, columns=keys)
	logmessage( 'Created', filename )


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


###########################

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
##############################

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

##############################

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

##############################

def get_sec(time_str):
	h, m, s = time_str.split(':')
	return int(h) * 3600 + int(m) * 60 + int(s)

def lat_long_dist(lat1,lon1,lat2,lon2):
	# function for calculating ground distance between two lat-long locations
	R = 6373.0 # approximate radius of earth in km. 

	lat1 = radians( float(lat1) )
	lon1 = radians( float(lon1) )
	lat2 = radians( float(lat2) )
	lon2 = radians( float(lon2) )

	dlon = lon2 - lon1
	dlat = lat2 - lat1

	a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))

	distance = float(format( R * c , '.2f' )) #rounding. From https://stackoverflow.com/a/28142318/4355695
	return distance

def intcheck(s):
	s = s.strip()
	return int(s) if s else ''


def geoJson2shape(route_id, shapefile, shapefileRev=None):
	with open(shapefile, encoding='utf8') as f:
		# loading geojson, from https://gis.stackexchange.com/a/73771/44746
		data = json.load(f)
	logmessage('Loaded',shapefile)
		
	output_array = []
	try:
		coordinates = data['features'][0]['geometry']['coordinates']
	except:
		logmessage('Invalid geojson file ' + shapefile)
		return False

	prevlat = coordinates[0][1]
	prevlon = coordinates[0][0]
	dist_traveled = 0
	i = 0
	for item in coordinates:
		newrow = OrderedDict()
		newrow['shape_id'] = route_id + '_0'
		newrow['shape_pt_lat'] = item[1]
		newrow['shape_pt_lon'] = item[0]
		calcdist = lat_long_dist(prevlat,prevlon,item[1],item[0])
		dist_traveled = dist_traveled + calcdist
		newrow['shape_dist_traveled'] = dist_traveled
		i = i + 1
		newrow['shape_pt_sequence'] = i
		output_array.append(newrow.copy())
		prevlat = item[1]
		prevlon = item[0]
	
	# Reverse trip now.. either same shapefile in reverse or a different shapefile	
	if( shapefileRev ):
		with open(shapefileRev, encoding='utf8') as g:
			data2 = json.load(g)
		logmessage('Loaded',shapefileRev)
		try:
			coordinates = data2['features'][0]['geometry']['coordinates']
		except:
			logmessage('Invalid geojson file ' + shapefileRev)
			return False
	else:
		coordinates.reverse()
	
	prevlat = coordinates[0][1]
	prevlon = coordinates[0][0]
	dist_traveled = 0
	i = 0
	for item in coordinates:
		newrow = OrderedDict()
		newrow['shape_id'] = route_id + '_1'
		newrow['shape_pt_lat'] = item[1]
		newrow['shape_pt_lon'] = item[0]
		calcdist = lat_long_dist(prevlat,prevlon,item[1],item[0])
		dist_traveled = float(format( dist_traveled + calcdist , '.2f' )) 
		newrow['shape_dist_traveled'] = dist_traveled
		i = i + 1
		newrow['shape_pt_sequence'] = i
		output_array.append(newrow.copy())
		prevlat = item[1]
		prevlon = item[0]
	
	return output_array

def serviceIdsFunc():
	calendarDF = readTableDB('calendar')
	collectorSet = set()
	if len(calendarDF):
		collectorSet.update( calendarDF['service_id'].tolist() )
		# service_id_list = calendarDF['service_id'].tolist()
	
	calendarDatesDF = readTableDB('calendar_dates')
	if len(calendarDatesDF):
		collectorSet.update( calendarDatesDF['service_id'].tolist() )

	return list(collectorSet)


#################################################3

def replaceIDfunc(key,valueFrom,valueTo):
	returnList = []
	# to do: wean off tableKeys, bring in the deleteRules.csv code blocks from diagnose, delete functions.
	
	# load the delete config file
	content = ''
	deleteRulesDF = pd.read_csv(configFolder + 'deleteRules.csv', dtype=str).fillna('')
	deleteRulesDF.query('key == "{}"'.format(key), inplace=True)
	if len(deleteRulesDF):
		deleteRulesDF.reset_index(drop=True,inplace=True)
	else:
		logmessage('No deleteRules found for column',key)
		content = 'No deleteRules found for this column.'

	if debugMode: logmessage(deleteRulesDF)

	for i,row in deleteRulesDF.iterrows():
		searchColumn = row.column_name if len(row.column_name) else row.key
		
		if row.table in chunkRules.keys():
			# chunked table
			filesLoop = replaceIDChunk(valueFrom,valueTo,row.table,searchColumn)
			# doesn't do actualy replacing yet, but edits the lookup json if needed 
			# and returns the list of files to be worked on.
			if not filesLoop: continue

		else:
			# normal table
			filesLoop = [ row.table + '.h5' ]

		for h5File in filesLoop:
			replacingStatus = replaceTableCell(h5File,searchColumn,valueFrom,valueTo)
			if replacingStatus:
				returnList.append(replacingStatus)

	# hey, don't forget sequence db!
	if key in ['shape_id', 'stop_id', 'route_id']:
		sDb = tinyDBopen(sequenceDBfile)
		sItem = Query()
		rows = sDb.all()
		somethingEditedFlag = False
		for row in rows:

			if key == 'shape_id':
				editedFlag = False
				if row.get('shape0') == valueFrom :
					row['shape0'] = valueTo
					editedFlag = True
				if row.get('shape1') == valueFrom :
					row['shape1'] = valueTo
					editedFlag = True
				
				if editedFlag:
					a = 'Replaced shape_id = {} with {} in sequence DB for route {}'\
						.format(valueFrom,valueTo,row.get('route_id') )
					logmessage('replaceIDfunc:',a) 
					returnList.append(a)
					somethingEditedFlag = True

			if key == 'stop_id':
				editedFlag = False
				if valueFrom in row['0']:
					row['0'][:] = [ x if (x != valueFrom) else valueTo for x in row['0']  ]
					editedFlag = True
				
				if valueFrom in row['1']:
					row['1'][:] = [ x if (x != valueFrom) else valueTo for x in row['1'] ]
					editedFlag = True
				
				if editedFlag:
					a = 'Replaced stop_id = {} with {} in sequence DB for route {}'.format(valueFrom,valueTo,row['route_id'])
					logmessage('replaceIDfunc:',a)
					returnList.append(a)
					somethingEditedFlag = True

			if key == 'route_id':
				if row.get('route_id') == valueFrom:
					row['route_id'] = valueTo
					a = 'Replaced route_id = {} with {} in sequence DB'\
						.format(valueFrom,valueTo )
					logmessage('replaceIDfunc:',a) 
					returnList.append(a)
					somethingEditedFlag = True
		
		if somethingEditedFlag: sDb.write_back(rows) # write updated data back only if you've edited something, else don't bother.
		sDb.close();

	returnMessage = 'Success.<br>' + '<br>'.join(returnList)
	return returnMessage

######################
def replaceIDChunk(valueFrom,valueTo,tablename,column):
	'''
	replaceIDChunk: this function finds the relevant chunks where replacement is to be done, and passes back the filenames in a list.
	It does NOT do the actual replacing in the .h5 file. That is done by the subsequently called replaceTableCell function.
	But it does edit the lookup JSON in case the column to be edited is the primary column of the chunked table. (like: stop_times > trip_id)
	'''
	# do NOT call any other function for replacing db etc now!
	# first, figure out if this is a key column or other column
	if column == chunkRules[tablename]['key']:
		if debugMode: logmessage('replaceIDChunk: {} is the primary key. So, we need only load its corresponding chunk.'.format(column))

		# find the chunk that has valueFrom
		h5File = findChunk(valueFrom,tablename)
		if not h5File:
			logmessage('replaceIDChunk: No entry in lookupJSON for {} .'.format(valueFrom))
			return False
		filesLoop = [ h5File ]

		# replace it in the json too.
		lookupJSONFile = chunkRules[tablename]['lookup']
		with open(dbFolder + lookupJSONFile) as f:
			table_lookup = json.load(f)

		table_lookup[valueTo] = h5File # make a new key-value pair
		table_lookup.pop(valueFrom,None) # delete old key which is getting replaced
		
		with open(dbFolder + lookupJSONFile, 'w') as outfile:
			json.dump(table_lookup, outfile, indent=2)
		logmessage('replaceIDChunk: replaced {} with {} in lookupJSON {}'\
			.format( valueFrom,valueTo,lookupJSONFile  ))	
		# replacing lookupJSON done.

	else:
		if debugMode: logmessage('replaceIDChunk: {} is NOT the primary key ({}). So, we have to loop through all the chunks.'.format(column,chunkRules[tablename]['key']))
		filesLoop = findFiles(dbFolder, ext='.h5', prefix=tablename, chunk='y')
		if debugMode: logmessage('replaceIDChunk: filesLoop:',filesLoop)

	return filesLoop


def replaceTableCell(h5File,column,valueFrom,valueTo):
	returnStatus = False
	# check if file exists.
	if not os.path.exists(dbFolder + h5File):
		logmessage('replaceTableCell: {} not found.'.format(h5File))
		return False
	
	try:
		df = pd.read_hdf(dbFolder + h5File).fillna('').astype(str)
	except (KeyError, ValueError) as e:
		df = pd.DataFrame()
		logmessage('Note: {} does not have any data.'.format(h5File))
	if column not in df.columns:
		if debugMode: logmessage('replaceTableCell: column {} not found in {}. Skipping this one.'\
			.format(column,h5file) )
		return False

	count = len( df[df[column] == valueFrom ])
	if count:
		# the replacing:
		df[column].replace(to_replace=str(valueFrom), value=str(valueTo), inplace=True )
		# hey lets do this for the ordinary tables too!
		logmessage('replaceTableCell: replaced {} instances of "{}" with "{}" in {} column in {}'\
			.format(count,valueFrom,valueTo,column,h5File) )
		# write it back
		df.to_hdf(dbFolder + h5File,'df', format='table', mode='w', complevel=1)
		returnStatus = 'Replaced {} instances of "{}" with "{}" in {} column in {}'\
			.format(count,valueFrom,valueTo,column,h5File)
	else:
		pass
		#returnStatus = 'Nothing found in {} for {}="{}"'.format(h5File,column,valueFrom)

	del df
	return returnStatus

###################

def diagnoseIDfunc(column,value):
	'''
	function to take column, value and find its occurence throughout the DB, and return the tables the value appears in.
	'''
	# load the delete config file
	content = ''
	deleteRulesDF = pd.read_csv(configFolder + 'deleteRules.csv', dtype=str).fillna('')
	deleteRulesDF.query('key == "{}"'.format(column), inplace=True)
	if len(deleteRulesDF):
		deleteRulesDF.reset_index(drop=True,inplace=True)
	else:
		logmessage('No deleteRules found for column',column)
		content = 'No deleteRules found for this column.'

	if debugMode: logmessage(deleteRulesDF)

	counter = 1
	for i,row in deleteRulesDF.iterrows():
		dbPresent = findFiles(dbFolder, ext='.h5', prefix=row.table, chunk='all')
		if dbPresent:
			searchColumn = row.column_name if len(row.column_name) else row.key
			
			if row.table not in chunkRules.keys():
				df = readTableDB(row.table, key=searchColumn, value=value)
			else:
				if searchColumn == chunkRules[row.table].get('key'):
					df = readTableDB(row.table, key=searchColumn, value=value)
				else:
					df = readChunkTableDB(row.table, key=searchColumn, value=value)

			if len(df):
				content += '{}] {} rows to {} in table "{}":\n'\
					.format(counter,len(df),row.action,row.table)
				content += df.to_csv(index=False, sep='\t')
				content += '\n' + '#'*100 + '\n'
				counter += 1
	return content


def deleteID(column,value):
	'''
	Note: this is a container function. 
	The actual deleting is taking place in deleteInTable() func below.
	'''
	content = ''

	# special case: if its a route_id or a calendar service_id, have to delete all the trips under it first, so their respective entries in stop_times are deleted too.
	if column in ['route_id','service_id']:
		tripsList = readColumnDB(tablename='trips', column='trip_id', key=column, value=value)
		message = 'deleteID: Deleting {} trips first under {}="{}"'.format(len(tripsList),column,value) 
		logmessage(message)
		content += message + '<br>'
		content += ''.join([deleteID('trip_id',trip_id) for trip_id in tripsList]) + '<br>'

	# load deleteRules csv from config folder
	deleteRulesDF = pd.read_csv(configFolder + 'deleteRules.csv', dtype=str).fillna('')
	deleteRulesDF.query('key == "{}"'.format(column), inplace=True)
	if len(deleteRulesDF):
		deleteRulesDF.reset_index(drop=True,inplace=True)
	else:
		logmessage('No deleteRules found for column',column)
		content = 'No deleteRules found for column {}.'.format(column)
		return content
	
	if debugMode: logmessage(deleteRulesDF)

	for i,row in deleteRulesDF.iterrows():
		dbPresent = findFiles(dbFolder, ext='.h5', prefix=row.table, chunk='all')
		if dbPresent:
			searchColumn = row.column_name if len(row.column_name) else row.key
			
			content += deleteInTable(tablename=row.table, key=searchColumn, value=value, action=row.action)

	# sequence DB
	content += sequenceDel(column,value)

	return content

def deleteInTable(tablename, key, value, action="delete"):
	if tablename not in chunkRules.keys():
		# its not a chunked table
		h5Files = [tablename + '.h5']
		# since we've composed this filename, check if file exists.
		if not os.path.exists(dbFolder + h5Files[0]):
			logmessage('deleteInTable: {} not found.'.format(h5Files[0]))
			return ''
	else:
		# its a chunked table
		if key == chunkRules[tablename].get('key'):
			h5Files = [findChunk(value, tablename)]
			
			# delete it in the lookup json too.
			lookupJSONFile = chunkRules[tablename]['lookup']
			with open(dbFolder + lookupJSONFile) as f:
				table_lookup = json.load(f)

			table_lookup.pop(value,None) # delete old key which is getting replaced
			
			with open(dbFolder + lookupJSONFile, 'w') as outfile:
				json.dump(table_lookup, outfile, indent=2)

		else:
			# list all the chunks
			h5Files = findFiles(dbFolder, ext='.h5', prefix=tablename, chunk='y')

	# now in h5Files we have which all files to process.
	returnMessage = ''
	for h5File in h5Files:
		try:
			df = pd.read_hdf(dbFolder + h5File).fillna('').astype(str)
		except (KeyError, ValueError) as e:
			df = pd.DataFrame()
			logmessage('Note: {} does not have any data.'.format(h5File))

		# check if given column is present in table or not
		if key not in df.columns:
			logmessage('deleteInTable: Column {} not found in {}. Skipping.'.format(key,h5File) )
			continue

		numDel = len(df.query('{} == "{}"'.format(key,value)) )
		if not numDel: continue

		if action == 'delete':
			df.query('{} != "{}"'.format(key,value), inplace=True)
			df.reset_index(drop=True, inplace=True)
			
			returnMessage += 'Deleted {} rows with {}="{}" in table: {}<br>'.format(numDel,key,value,tablename)
		else: # for zap
			df[key] = df[key].apply(lambda x: '' if x==value else x)
			# zap all occurences of value in the column [key] to blank. leave all other values as-is
			returnMessage += 'Zapped {} occurences of {}="{}" in table: {}<br>'.format(numDel,key,value,tablename)
		
		# commenting out while developing
		df.to_hdf(dbFolder+h5File, 'df', format='table', mode='w', complevel=1)
	logmessage(returnMessage)
	return returnMessage

##########################
# Redo the delete functions to accommodate multiple values. 
# For pandas it doesn't make any difference whether its one value or multiple

##########################

def sequenceDel(column,value):
	content = []
	if column == 'route_id':
		# drop it from sequence DB too.
		sDb = tinyDBopen(sequenceDBfile)
		sItem = Query()
		sDb.remove(sItem['route_id'] == value)
		sDb.close();

		message = 'Removed entries if any for route_id: '+value +' in sequenceDB.'
		logmessage(message)
		content.append(message)

	if column == 'stop_id':
		# drop the stop from sequence DB too.
		sDb = tinyDBopen(sequenceDBfile)
		sItem = Query()
		changesFlag = False
		rows = sDb.all()

		# do this this only if sequenceDBfile is not empty
		if len(rows):
			for row in rows:
				# do zapping only if the stop is present in that sequence
				if value in row['0']:
					row['0'][:] = ( x for x in row['0'] if x != value )
					changesFlag = True
					message = 'Zapped stop_id: ' + value + ' from sequence DB for route: '+ row['route_id'] + ' direction: 0'
					logmessage(message)
					content.append(message)
				if value in row['1']:
					row['1'][:] = ( x for x in row['1'] if x != value )
					changesFlag = True
					message = 'Zapped stop_id: ' + value + ' from sequence DB for route: '+ row['route_id'] + ' direction: 1'
					logmessage(message)
					content.append(message)
			
			# rows loop over, now run write_back command only if there have been changes.
			if changesFlag:
				sDb.write_back(rows)
		
		sDb.close();

	if column == 'shape_id':
		sDb = tinyDBopen(sequenceDBfile)
		sItem = Query()
		changesFlag = False
		rows = sDb.all()

		# do this this only if sequenceDBfile is not empty
		if len(rows):
			somethingEditedFlag = False
			routesAffected = []
			for row in rows:
				if row.get('shape0','') == value:
					row.pop('shape0',None)
					routesAffected.append(row.get('route_id'))
					somethingEditedFlag = True
				if row.get('shape1','') == value:
					row.pop('shape1s',None)
					routesAffected.append(row.get('route_id'))
					somethingEditedFlag = True
			if somethingEditedFlag:
				sDb.write_back(rows)
				message = 'Zapped shape_id: {} in Sequence DB for route(s): {}'\
					.format(value,','.join(routesAffected) )
				logmessage(message)
				content.append(message)
		sDb.close();

	return '<br>'.join(content)

