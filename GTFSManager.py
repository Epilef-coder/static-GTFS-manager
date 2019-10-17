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

import webbrowser
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



