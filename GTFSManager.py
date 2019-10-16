from utils.logmessage import logmessage
from utils.piwiktracking import logUse

print('\n\nstatic GTFS Manager')
print('Fork it on Github: https://github.com/WRI-Cities/static-GTFS-manager/')
print('Starting up the program, loading dependencies, please wait...\n\n')

import tornado.web
import tornado.ioloop

# import url handlers
from urls import url_patterns

# Temp has to be a handler that calls this function.
from utils.password import decrypt
# import all utils from the /utils folder.

import pandas as pd
import webbrowser
import shutil # used in fareChartUpload to fix header if changed
# import requests # nope, not needed for now
import signal, sys # for catching Ctrl+C and exiting gracefully.

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


def make_app():
    return tornado.web.Application(url_patterns)

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



