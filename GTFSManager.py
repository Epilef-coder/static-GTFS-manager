print('\n\nstatic GTFS Manager')
print('Fork it on Github: https://github.com/WRI-Cities/static-GTFS-manager/')
print('Starting up the program, loading dependencies, please wait...\n\n')

import tornado.web
import tornado.ioloop
import json
import os
import time, datetime
# import url handlers
from handlers.config import APIKeys
from handlers.gtfsagency import *
from handlers.gtfsroutes import *
from handlers.gtfsfares import *
from handlers.gtfsshapes import *
from handlers.gtfsstops import *
from handlers.gtfstrips import *
from handlers.gtfsstoptimes import *
from handlers.importexport import *
from handlers.appstats import *


# import all utils from the /utils folder.
import utils

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

import csv
import io # used in hyd csv import
import requests, platform # used to log user stats

# setting constants
from settings import *
root = os.path.dirname(__file__) # needed for tornado

thisURL = ''


# for checking imported ZIP against
# to do: don't make this a HARD requirement. Simply logmessage about it.



# create folders if they don't exist
for folder in [uploadFolder, xmlFolder, logFolder, configFolder, dbFolder, exportFolder]:
    if not os.path.exists(folder):
        os.makedirs(folder)


# importing GTFSserverfunctions.py, embedding it inline to avoid re-declarations etc
exec(open(os.path.join(root,"GTFSserverfunctions.py"), encoding='utf8').read())
exec(open(os.path.join(root,"xml2GTFSfunction.py"), encoding='utf8').read())
exec(open(os.path.join(root,"hydCSV2GTFS.py"), encoding='utf8').read())

logmessage('Loaded dependencies, starting static GTFS Manager program.')

'''
# Tornado API functions template:
class APIHandler(tornado.web.RequestHandler):
    def get(self):
        #get the Argument that User had passed as name in the get request
        userInput=self.get_argument('name')
        welcomeString=sayHello(userInput)
        #return this as JSON
        self.write(json.dumps(welcomeString))

    def post(self):
        user = self.get_argument("username")
        passwd = self.get_argument("password")
        time.sleep(10)
        self.write("Your username is %s and password is %s" % (user, passwd))
'''


class sequence(tornado.web.RequestHandler):
    def get(self):
        # API/sequence?route=${route_id}
        start = time.time()
        logmessage('\nsequence GET call')
        route_id = self.get_argument('route',default='')

        if not len(route_id):
            self.set_status(400)
            self.write("Error: invalid route.")
            return

        #to do: first check in sequence db. If not found there, then for first time, scan trips and stop_times to load sequence. And store that sequence in sequence db so that next time we fetch from there.

        sequence = sequenceReadDB(sequenceDBfile, route_id)
        # read sequence db and return sequence array. If not found in db, return false.

        message = '<span class="alert alert-success">Loaded default sequence for this route from DB.</span>'

        if not sequence:
            logmessage('sequence not found in sequence DB file, so extracting from gtfs tables instead.')
            # Picking the first trip instance for each direction of the route.
            sequence = extractSequencefromGTFS(route_id)

            if sequence == [ [], [] ] :
                message = '<span class="alert alert-info">This seems to be a new route. Please create a sequence below and save to DB.</span>'
            else:
                message = '<span class="alert alert-warning">Loaded a computed sequence from existing trips. Please finalize and save to DB.</span>'

            # we have computed a sequence from the first existing trip's entry in trips and stop_times tables for that route (one sequence for each direction)
            # Passing it along. Let the user finalize it and consensually save it.

        # so either way, we now have a sequence array.

        returnJson = { 'data':sequence, 'message':message }
        self.write(json.dumps(returnJson))
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("sequence GET call took {} seconds.".format(round(end-start,2)))

    #using same API endpoint, post request for saving.
    def post(self):
        # ${APIpath}sequence?pw=${pw}&route=${selected_route_id}&shape0=${chosenShape0}&shape1=${chosenShape1}
        start = time.time()
        logmessage('\nsequence POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        route_id = self.get_argument('route', default='')
        shape0 = self.get_argument('shape0', default='')
        shape1 = self.get_argument('shape1', default='')

        if not len(route_id):
            self.set_status(400)
            self.write("Error: invalid route.")
            return

        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads( self.request.body.decode('UTF-8') )

        '''
        This is what the data would look like: [
            ['ALVA','PNCU','CPPY','ATTK','MUTT','KLMT','CCUV','PDPM','EDAP','CGPP','PARV','JLSD','KALR','LSSE','MGRD'],
            ['MACE','MGRD','LSSE','KALR','JLSD','PARV','CGPP','EDAP','PDPM','CCUV','KLMT','MUTT','ATTK','CPPY','PNCU','ALVA']
        ];
        '''
        # to do: the shape string can be empty. Or one of the shapes might be there and the other might be an empty string. Handle it gracefully.
        # related to https://github.com/WRI-Cities/static-GTFS-manager/issues/35
        # and : https://github.com/WRI-Cities/static-GTFS-manager/issues/38
        shapes = [shape0, shape1]

        if sequenceSaveDB(sequenceDBfile, route_id, data, shapes):
            self.write('saved sequence to sequence db file.')
        else:
            self.set_status(400)
            self.write("Error, could not save to sequence db for some reason.")
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("API/sequence POST call took {} seconds.".format(round(end-start,2)))


class calendar(tornado.web.RequestHandler):
    def get(self):
        # API/calendar?current=y
        start = time.time() # time check
        logmessage('\ncalendar GET call')
        current = self.get_argument('current',default='')

        if current.lower() == 'y':
            calendarJson = calendarCurrent().to_json(orient='records', force_ascii=False)
        else:
            calendarJson = readTableDB('calendar').to_json(orient='records', force_ascii=False)
        self.write(calendarJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("calendar GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        # API/calendar?pw=${pw}
        start = time.time() # time check
        logmessage('\ncalendar POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        calendarData = json.loads( self.request.body.decode('UTF-8') )

        #csvwriter(calendarData,'calendar.txt')
        replaceTableDB('calendar', calendarData)

        self.write('Saved Calendar data to DB.')
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("calendar POST call took {} seconds.".format(round(end-start,2)))


class serviceIds(tornado.web.RequestHandler):
    def get(self):
        # API/serviceIds
        start = time.time() # time check
        logmessage('\nserviceIds GET call')
        service_id_list = serviceIdsFunc()
        self.write(json.dumps(service_id_list))
        end = time.time()
        logmessage("serviceIds GET call took {} seconds.".format(round(end-start,2)))


class XMLUpload(tornado.web.RequestHandler):
    def post(self):
        # `${APIpath}XMLUpload?pw=${pw}&depot=${depot}`,
        start = time.time()
        logmessage('\nXMLUpload GET call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return

        # pass form file objects to uploadaFile funciton, get filenames in return
        weekdayXML = uploadaFile( self.request.files['weekdayXML'][0] )
        sundayXML = uploadaFile( self.request.files['sundayXML'][0] )

        depot = self.get_argument('depot', default='')
        if( depot == 'None' or depot == ''):
            depot = None

        diagnoseData = diagnoseXMLs(weekdayXML, sundayXML, depot)
        # function diagnoseXMLs returns dict having keys: report, weekdaySchedules, sundaySchedules

        if diagnoseData is False:
            self.set_status(400)
            self.write("Error: invalid xml(s).")
            return

        returnJson = {'weekdayXML':weekdayXML, 'sundayXML':sundayXML }
        returnJson.update(diagnoseData)

        self.write(json.dumps(returnJson))
        end = time.time()
        logmessage("XMLUpload POST call took {} seconds.".format(round(end-start,2)))
        logUse('XMLUpload')

class XMLDiagnose(tornado.web.RequestHandler):
    def get(self):
        # `${APIpath}XMLDiagnose?weekdayXML=${weekdayXML}&sundayXML=${sundayXML}&depot=${depot}`
        start = time.time()
        logmessage('\nXMLDiagnose GET call')
        weekdayXML = self.get_argument('weekdayXML', default='')
        sundayXML = self.get_argument('sundayXML', default='')

        if not ( len(weekdayXML) and len(sundayXML) ):
            self.set_status(400)
            self.write("Error: invalid xml(s).")
            return

        depot = self.get_argument('depot', default='')
        if( depot == 'None' or depot == ''):
            depot = None

        diagnoseData = diagnoseXMLs(weekdayXML, sundayXML, depot)
        # function diagnoseXMLs returns dict having keys: report, weekdaySchedules, sundaySchedules

        if diagnoseData is False:
            self.set_status(400)
            self.write("Error: invalid xml(s), diagnoseData function failed.")
            return

        returnJson = {'weekdayXML':weekdayXML, 'sundayXML':sundayXML }
        returnJson.update(diagnoseData)

        self.write(json.dumps(returnJson))
        end = time.time()
        logmessage("XMLDiagnose GET call took {} seconds.".format(round(end-start,2)))
        logUse('XMLDiagnose')


class stations(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        logmessage('\nstations GET call')
        stationsArray = pd.read_csv(xmlFolder + "stations.csv", na_filter=False).to_dict('records')
        self.write(json.dumps(stationsArray))
        end = time.time()
        logmessage("stations GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        start = time.time()
        logmessage('\nstations POST call')
        stationsArray = pd.read_csv(xmlFolder + "stations.csv", na_filter=False).to_dict('records')

        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return

        data = json.loads( self.request.body.decode('UTF-8') )

        if stationsArray == data :
            self.write('No changes to save.')
        else:
            csvwriter(data, xmlFolder + 'stations.csv')
            self.write('Saved changes to stations.csv.')

        end = time.time()
        logmessage("stations POST call took {} seconds.".format(round(end-start,2)))


class fareChartUpload(tornado.web.RequestHandler):
    def post(self):
        # `${APIpath}fareChartUpload?pw=${pw}`,
        start = time.time()
        logmessage('\nfareChartUpload POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return

        # pass form file objects to uploadaFile funciton, get filenames in return
        fareChart = uploadaFile( self.request.files['fareChart'][0] )

        # idiot-proofing : What if the only column header in the file 'Stations' is named to something else?
        # We can do a quick replace of first word before (,) in first line
        # from https://stackoverflow.com/a/14947384/4355695
        targetfile = uploadFolder + fareChart
        from_file = open(targetfile, encoding='utf8')
        line = from_file.readline()
        lineArray = line.split(',')
        if lineArray[0] != 'Stations':
            logmessage('Fixing header on ' + fareChart + ' so the unpivot doesn\'t error out.')
            lineArray[0] = 'Stations'
            line = ','.join(lineArray)
            to_file = open(targetfile,mode="w",encoding='utf8')
            to_file.write(line)
            shutil.copyfileobj(from_file, to_file)
            to_file.close()
        from_file.close()

        try:
            fares_array = csvunpivot(uploadFolder + fareChart, ['Stations'], 'destination_id', 'fare_id', ['fare_id','Stations','destination_id']).to_dict('records')

        except:
            self.set_status(400)
            self.write("Error: invalid file.")
            return

        fare_id_set = set()
        fare_id_set.update([ row['fare_id'] for row in fares_array ])

        # this set is having a null value, NaN as well.
        # need to lose the NaN man
        # from https://stackoverflow.com/a/37148508/4355695
        faresList = [x for x in fare_id_set if x==x]
        faresList.sort()

        logmessage(faresList)

        report = 'Loaded Fares Chart successfully.'

        returnJson = {'report':report, 'faresList':faresList }

        self.write(json.dumps(returnJson))
        end = time.time()
        logmessage("fareChartUpload POST call took {} seconds.".format(round(end-start,2)))
        logUse('fareChartUpload')

class xml2GTFS(tornado.web.RequestHandler):
    def post(self):
        # `${APIpath}xml2GTFS?pw=${pw}`
        start = time.time()
        logmessage('\nxml2GTFS POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        configdata = json.loads( self.request.body.decode('UTF-8') )
        logmessage(configdata)
        # and so it begins! Ack lets pass it to a function.
        returnMessage = xml2GTFSConvert(configdata)

        if not len(returnMessage):
            self.set_status(400)
            returnMessage = 'Import was unsuccessful, please debug on python side.'

        self.write(returnMessage)
        end = time.time()
        logmessage("xml2GTFS POST call took {} seconds.".format(round(end-start,2)))
        logUse('xml2GTFS')

class gtfsBlankSlate(tornado.web.RequestHandler):
    def get(self):
        # API/gtfsBlankSlate?pw=${pw}
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

class translations(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        logmessage('\ntranslations GET call')
        translationsJson = readTableDB('translations').to_json(orient='records', force_ascii=False)
        self.write(translationsJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("translations GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        # API/translations?pw=${pw}
        start = time.time() # time check
        logmessage('\ntranslations POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        translationsData = json.loads( self.request.body.decode('UTF-8') )

        replaceTableDB('translations', translationsData)

        self.write('Saved Translations data to DB.')
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("translations POST call took {} seconds.".format(round(end-start,2)))


class listAll(tornado.web.RequestHandler):
    def get(self):
        # ${APIpath}listAll
        # a Master API call for fetching all id's!
        start = time.time()
        logmessage('\nlistAll GET call')

        zoneCollector = set()

        # stops
        stop_id_list = readColumnDB('stops','stop_id')

        # also collect zone_ids
        zoneCollector.update( readColumnDB('stops','zone_id') )

        # routes
        route_id_list = readColumnDB('routes','route_id')

        # trips
        trip_id_list = readColumnDB('trips','trip_id')

        # fare zone ids
        zoneCollector.update( readColumnDB('fare_rules','origin_id') )
        zoneCollector.update( readColumnDB('fare_rules','destination_id') )

        # zones collected; transfer all collected zones to zone_id_list
        zone_id_list = list(zoneCollector)

        # fare_ids
        # solves https://github.com/WRI-Cities/static-GTFS-manager/issues/36
        fare_id_list = readColumnDB('fare_attributes','fare_id')

        # agency_ids
        # solves https://github.com/WRI-Cities/static-GTFS-manager/issues/42
        agency_id_list = readColumnDB('agency','agency_id')

        # next are repetitions of other functions
        # shapes
        shapeIDsJson = allShapesListFunc()

        # service ids
        service_id_list = serviceIdsFunc()

        # wrapping it all together
        returnJson = { 'stop_id_list':stop_id_list, 'route_id_list':route_id_list, 'trip_id_list':trip_id_list, 'zone_id_list':zone_id_list, 'shapeIDsJson':shapeIDsJson, 'service_id_list': service_id_list, 'fare_id_list':fare_id_list, 'agency_id_list':agency_id_list }
        self.write(json.dumps(returnJson))
        end = time.time()
        logmessage("listAll GET call took {} seconds.".format(round(end-start,2)))


class zoneIdList(tornado.web.RequestHandler):
    def get(self):
        # ${APIpath}zoneIdList
        start = time.time()
        logmessage('\nzoneIdList GET call')

        zoneCollector = set()
        zoneCollector.update( readColumnDB('stops','zone_id') )
        # to do: find out why this function is only looking at stops table

        zoneList = list(zoneCollector)
        zoneList.sort()
        self.write(json.dumps(zoneList))
        end = time.time()
        logmessage("zoneIdList GET call took {} seconds.".format(round(end-start,2)))


class diagnoseID(tornado.web.RequestHandler):
    def get(self):
        # ${APIpath}diagnoseID?column=column&value=value
        start = time.time()
        logmessage('\ndiagnoseID GET call')
        column = self.get_argument('column', default='')
        value = self.get_argument('value', default='')

        if not ( len(column) and len(value) ):
            self.set_status(400)
            self.write("Error: invalid parameters.")
            return
        returnMessage = diagnoseIDfunc(column,value)
        self.write(returnMessage)

        end = time.time()
        logmessage("diagnoseID GET call took {} seconds.".format(round(end-start,2)))


class deleteByKey(tornado.web.RequestHandler):
    def get(self):
        # ${APIpath}deleteByKey?pw=pw&key=key&value=value&tables=table1,table2
        start = time.time()
        logmessage('\ndeleteByKey GET call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return

        column = self.get_argument('key', default='')
        value = self.get_argument('value', default='')
        if not ( len(column) and len(value) ):
            logmessage("API/deleteByKey : Error: invalid parameters.")
            self.set_status(400)
            self.write("Error: invalid parameters.")
            return

        returnMessage = deleteID(column,value)
        self.write(returnMessage)

        end = time.time()
        logmessage("deleteByKey GET call took {} seconds.".format(round(end-start,2)))


class replaceID(tornado.web.RequestHandler):
    def get(self):
        # ${APIpath}replaceID?pw=pw&key=key&valueFrom=valueFrom&valueTo=valueTo
        start = time.time()
        logmessage('\nreplaceID POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return

        key = self.get_argument('key',default='')
        valueFrom = self.get_argument('valueFrom', default='')
        valueTo = self.get_argument('valueTo', default='')
        # tableKeys = json.loads( self.request.body.decode('UTF-8') )
        # tablekeys: [ {'table':'stops','key':'stop_id'},{...}]

        if not ( len(valueFrom) and len(valueTo) and len(key) ):
            self.set_status(400)
            self.write("Error: Invalid parameters.")
            return

        # main function:
        returnMessage = replaceIDfunc(key,valueFrom,valueTo)

        self.write(returnMessage)

        end = time.time()
        logmessage("replaceID POST call took {} seconds.".format(round(end-start,2)))


class hydGTFS(tornado.web.RequestHandler):
    def post(self):
        start = time.time()
        logmessage('\nhydGTFS POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return

        files = self.request.files
        #print(files)

        # Getting POST form input data, from https://stackoverflow.com/a/32418838/4355695
        #formdata = self.request.body_arguments() # that didn't work
        payload = json.loads( self.get_body_argument("payload", default=None, strip=False) )
        #print(payload)

        returnJson = hydGTFSfunc(files, payload)

        #returnMessage = {'status':'Feature Under Construction!'}
        self.write(returnJson)

        end = time.time()
        logmessage("hydGTFS POST call took {} seconds.".format(round(end-start,2)))

class frequencies(tornado.web.RequestHandler):
    def get(self):
        # ${APIpath}frequencies
        start = time.time()
        logmessage('\nfrequencies GET call')

        freqJson = readTableDB('frequencies').to_json(orient='records', force_ascii=False)
        self.write(freqJson)
        end = time.time()
        logmessage("frequences GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        # ${APIpath}frequencies
        start = time.time()
        logmessage('\nfrequencies POST call')
        pw=self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads( self.request.body.decode('UTF-8') )

        if replaceTableDB('frequencies', data): #replaceTableDB(tablename, data)
            self.write('Saved frequencies data to DB.')
        else:
            self.set_status(400)
            self.write("Error: Could not save to DB.")
        end = time.time()
        logmessage("frequencies POST call took {} seconds.".format(round(end-start,2)))

class tableReadSave(tornado.web.RequestHandler):
    def get(self):
        # ${APIpath}tableReadSave?table=table&key=key&value=value
        start = time.time()

        table=self.get_argument('table',default='')
        logmessage('\ntableReadSave GET call for table={}'.format(table))

        if not table:
            self.set_status(400)
            self.write("Error: invalid table.")
            return

        key=self.get_argument('key',default=None)
        value=self.get_argument('value',default=None)
        if key and value:
            dataJson = readTableDB(table, key=key, value=value).to_json(orient='records', force_ascii=False)
        else:
            dataJson = readTableDB(table).to_json(orient='records', force_ascii=False)

        self.write(dataJson)
        end = time.time()
        logUse('{}_read'.format(table))
        logmessage("tableReadSave GET call for table={} took {} seconds.".format(table,round(end-start,2)))

    def post(self):
        # ${APIpath}tableReadSave?pw=pw&table=table&key=key&value=value
        start = time.time()
        pw=self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return

        table=self.get_argument('table',default='')
        if not table:
            self.set_status(400)
            self.write("Error: invalid table.")
            return

        logmessage('\ntableReadSave POST call for table={}'.format(table))

        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads( self.request.body.decode('UTF-8') )

        key = self.get_argument('key',default=None)
        value = self.get_argument('value',default=None)
        if key and value:
            status = replaceTableDB(table, data, key, value)
        else:
            status = replaceTableDB(table, data)

        if status:
            self.write('Saved {} data to DB.'.format(table) )
        else:
            self.set_status(400)
            self.write("Error: Could not save to DB.")
        end = time.time()
        logUse('{}_write'.format(table))
        logmessage("tableReadSave POST call for table={} took {} seconds.".format(table,round(end-start,2)))

class tableColumn(tornado.web.RequestHandler):
    def get(self):
        # API/tableColumn?table=table&column=column&key=key&value=value
        start = time.time()
        logmessage('\nrouteIdList GET call')

        table=self.get_argument('table',default='')
        column=self.get_argument('column',default='')
        logmessage('\ntableColumn GET call for table={}, column={}'.format(table,column))

        if (not table) or (not column) :
            self.set_status(400)
            self.write("Error: invalid table or column given.")
            return

        key=self.get_argument('key',default=None)
        value=self.get_argument('value',default=None)

        if key and value:
            returnList = readColumnDB(table, column, key=key, value=value)
        else:
            returnList = readColumnDB(table, column)

        returnList.sort()
        self.write(json.dumps(returnList))
        end = time.time()
        logUse('{}_column'.format(table))
        logmessage("tableColumn GET call took {} seconds.".format(round(end-start,2)))


def make_app():
    return tornado.web.Application([
        #(r"/API/data", APIHandler),
        (r"/API/allStops", allStops),
        (r"/API/allStopsKeyed", allStopsKeyed),
        (r"/API/routes", routes),
        (r"/API/fareAttributes", fareAttributes),
        (r"/API/fareRulesPivoted", fareRulesPivoted),
        (r"/API/fareRules", fareRules),
        (r"/API/agency", agency),
        (r"/API/calendar", calendar),
        (r"/API/sequence", sequence),
        (r"/API/trips", trips),
        (r"/API/stopTimes", stopTimes),
        (r"/API/routeIdList", routeIdList),
        (r"/API/tripIdList", tripIdList),
        (r"/API/serviceIds", serviceIds),
        (r"/API/stats", stats),
        (r"/API/commitExport", commitExport),
        (r"/API/pastCommits", pastCommits),
        (r"/API/gtfsImportZip", gtfsImportZip),
        (r"/API/XMLUpload", XMLUpload),
        (r"/API/XMLDiagnose", XMLDiagnose),
        (r"/API/stations", stations),
        (r"/API/fareChartUpload", fareChartUpload),
        (r"/API/xml2GTFS", xml2GTFS),
        (r"/API/gtfsBlankSlate", gtfsBlankSlate),
        (r"/API/translations", translations),
        (r"/API/shapesList", shapesList),
        (r"/API/allShapesList", allShapesList),
        (r"/API/shape", shape),
        (r"/API/listAll", listAll),
        (r"/API/zoneIdList", zoneIdList),
        (r"/API/diagnoseID", diagnoseID),
        (r"/API/deleteByKey", deleteByKey),
        (r"/API/replaceID", replaceID),
        (r"/API/hydGTFS", hydGTFS),
        (r"/API/frequencies", frequencies),
        (r"/API/tableReadSave", tableReadSave),
        (r"/API/tableColumn", tableColumn),
        (r"/API/Config/ApiKeys", APIKeys),
        (r"/API/gtfs/shapes", gtfsshape),
        #(r"/API/idList", idList),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": root, "default_filename": "index.html"})
    ])

# for catching Ctrl+C and exiting gracefully. From https://nattster.wordpress.com/2013/06/05/catch-kill-signal-in-python/
def signal_term_handler(signal, frame):
    # to do: Make this work in windows, ra!
    print('\nClosing Program.\nThank you for using static GTFS Manager. Website: https://github.com/WRI-Cities/static-GTFS-manager/\n')
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_term_handler)
    app = make_app()
    portnum = 5000
    while True: # loop to increment the port number till we find one that isn't occupied
        try:
            port = int(os.environ.get("PORT", portnum))
            app.listen(port)
            break
        except OSError:
            portnum += 1
            if portnum > 9999:
                print('Can\'t launch as no port number from 5000 through 9999 is free.')
                sys.exit()

    thisURL = "http://localhost:" + str(port)
    webbrowser.open(thisURL)
    logmessage("\n\nOpen {} in your Web Browser if you don't see it opening automatically in 5 seconds.\n\nNote: If this is through docker, then it's not going to auto-open in browser, don't wait.".format(thisURL))
    logUse()
    tornado.ioloop.IOLoop.current().start()



