import json
import shutil
import time

import pandas as pd
import tornado.web

from settings import xmlFolder, uploadFolder
from utils.importexport import csvwriter, diagnoseXMLs, csvunpivot
from utils.krmlxml2gtfs import xml2GTFSConvert
from utils.logmessage import logmessage
from utils.password import decrypt
from utils.piwiktracking import logUse
from utils.upload import uploadaFile


class krmlstations(tornado.web.RequestHandler):
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


class krmlXMLUpload(tornado.web.RequestHandler):
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


class krmlXMLDiagnose(tornado.web.RequestHandler):
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


class krmlfareChartUpload(tornado.web.RequestHandler):
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


class krmlxml2GTFS(tornado.web.RequestHandler):
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