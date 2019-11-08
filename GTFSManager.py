import tornado.web
import tornado.ioloop
import webbrowser

from urls import url_patterns

# setting constants
from settings import *

from utils.logmessage import logmessage
from utils.piwiktracking import logUse

print('Static GTFS Manager')
print('Fork it on Github: https://github.com/WRI-Cities/static-GTFS-manager/')
print('Starting up the program, loading dependencies, please wait...\n\n')

# import requests # nope, not needed for now
import signal, sys  # for catching Ctrl+C and exiting gracefully.

thisURL = ''

# for checking imported ZIP against
# to do: don't make this a HARD requirement. Simply logmessage about it.

# create folders if they don't exist
for folder in [uploadFolder, xmlFolder, logFolder, configFolder, dbFolder, exportFolder]:
    if not os.path.exists(folder):
        os.makedirs(folder)

logmessage('Loaded dependencies, starting static GTFS Manager program.')


# def make_app():
#     return tornado.web.Application(url_patterns)

# for catching Ctrl+C and exiting gracefully. From https://nattster.wordpress.com/2013/06/05/catch-kill-signal-in-python/

class MyApplication(tornado.web.Application):
    is_closing = False

    def signal_handler(self, signum, frame):
        print('exiting...')
        self.is_closing = True

    def try_exit(self):
        if self.is_closing:
            # clean up here
            tornado.ioloop.IOLoop.instance().stop()
            print(
                '\nClosing Program.\nThank you for using static GTFS Manager. Website: https://github.com/WRI-Cities/static-GTFS-manager/\n')
            print('exit success')
            sys.exit(0)

application = MyApplication(url_patterns)

if __name__ == "__main__":
    # Start the background task:
    signal.signal(signal.SIGINT, application.signal_handler)
    portnum = 5000
    while True:  # loop to increment the port number till we find one that isn't occupied
        try:
            port = int(os.environ.get("PORT", portnum))
            application.listen(port)
            break
        except OSError:
            portnum += 1
            if portnum > 9999:
                print('Can\'t launch as no port number from 5000 through 9999 is free.')
                sys.exit()

    thisURL = "http://localhost:" + str(port)
    if 'APP' in appconfig:
        if 'Browser' in appconfig['APP']:
            if appconfig['APP']['Browser'] == 'true':
                webbrowser.open(thisURL)
        else:
            webbrowser.open(thisURL)
    else:
        webbrowser.open(thisURL)

    logmessage(
        "\n\nOpen {} in your Web Browser if you don't see it opening automatically in 5 seconds.\n\nNote: If this is through docker, then it's not going to auto-open in browser, don't wait.".format(
            thisURL))
    logUse()
    # Handle Control-C on Windows also
    tornado.ioloop.PeriodicCallback(application.try_exit, 100).start()
    tornado.ioloop.IOLoop.current().start()
