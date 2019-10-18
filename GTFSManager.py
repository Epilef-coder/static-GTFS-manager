import tornado.web
import tornado.ioloop
import webbrowser
# import url handlers

from urls import url_patterns

# setting constants
from settings import *

from utils.logmessage import logmessage
from utils.piwiktracking import logUse

print('\n\nstatic GTFS Manager')
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


def make_app():
    return tornado.web.Application(url_patterns)


# for catching Ctrl+C and exiting gracefully. From https://nattster.wordpress.com/2013/06/05/catch-kill-signal-in-python/
def signal_term_handler(signal, frame):
    # to do: Make this work in windows, ra!
    print(
        '\nClosing Program.\nThank you for using static GTFS Manager. Website: https://github.com/WRI-Cities/static-GTFS-manager/\n')
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_term_handler)
    # Start the background task:
    app = make_app()
    portnum = 5000
    while True:  # loop to increment the port number till we find one that isn't occupied
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
    logmessage(
        "\n\nOpen {} in your Web Browser if you don't see it opening automatically in 5 seconds.\n\nNote: If this is through docker, then it's not going to auto-open in browser, don't wait.".format(
            thisURL))
    logUse()
    tornado.ioloop.IOLoop.current().start()
