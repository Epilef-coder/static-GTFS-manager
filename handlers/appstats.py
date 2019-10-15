import tornado.web
import tornado.ioloop
import pandas as pd # Replace import with function
import time

from settings import *
from utils.logmessage import logmessage
from utils.tables import readTableDB,findFiles
from utils.piwiktracking import logUse

class stats(tornado.web.RequestHandler):
    def get(self):
        # API/stats
        start = time.time()
        logmessage('\nstats GET call')
        stats = GTFSstats()

        self.write(json.dumps(stats))
        end = time.time()
        logmessage("stats GET call took {} seconds.".format(round(end - start, 2)))
        logUse('stats')


def GTFSstats():
    '''
    Gives current stats of the GTFS tables held in DB
    Enlists:
        - agency name(s).
        - mandatory GTFS tables
        - optional GTFS tables
        - extra tables present in feed but not part of traditional GTFS spec (only mentioned if present)

    - List number of entries in each
    - Pad to have tabular like view
    - Format numbers to have thousands separators
    - If there are excess agencies, mention only first two and then put number of remaining
    '''
    content = '';

    agencyDF = readTableDB('agency')
    if len(agencyDF):
        agencyList = agencyDF.agency_name.tolist()
        if len(agencyList) > 2: agencyList[:] = agencyList[:2] + ['and {} more'.format(len(agencyList) - 2)]
        # if there are excess agencies, mention only first two and then put number of remaining

        content += 'Agency: {}<br>'.format(', '.join(agencyList))
    else:
        content += 'Agency: none found.<br>'

    filenames = findFiles(dbFolder, ext='.h5', prefix=None, chunk='all')

    coveredFiles = []

    # first, run through the main GTFS files in proper order
    content += '<br>1. Main tables: (*)<br>'
    for feed in requiredFeeds:
        tablename = feed[:-4]  # remove .txt
        count = 0

        if tablename not in chunkRules.keys():
            # normal tables
            if os.path.exists(dbFolder + tablename + '.h5'):
                hdf = pd.HDFStore(dbFolder + tablename + '.h5')
                try:
                    count = hdf.get_storer('df').nrows
                # gets number of rows, without reading the entire file into memory. From https://stackoverflow.com/a/26466301/4355695
                except (KeyError, ValueError) as e:
                    logmessage('Note: {} does not have any data.'.format(tablename + '.h5'))
                hdf.close()
                # have to close this opened file, else will conflict with pd.read_csv later on
                coveredFiles.append(tablename + '.h5')
            message = '{}: {:,} entries'.format(tablename.ljust(20), count)
            # {:,} : does number formattting. from https://stackoverflow.com/q/16670125/4355695
            # .ljust(20): pads spaces to string so that total len=20. from https://stackoverflow.com/a/5676676/4355695
            logmessage(message)
            content += message + '<br>'

        else:
            # chunked files
            chunks = findFiles(dbFolder, ext='.h5', prefix=tablename, chunk='y')
            if chunks:
                for h5File in chunks:
                    hdf = pd.HDFStore(dbFolder + h5File)
                    try:
                        count += hdf.get_storer('df').nrows
                    except (KeyError, ValueError) as e:
                        logmessage('Note: {} does not have any data.'.format(h5File))
                    hdf.close()
                    coveredFiles.append(h5File)
            message = '{}: {:,} entries'.format(tablename.ljust(20), count)
            logmessage(message)
            content += message + '<br>'

    # requiredFeeds loop over

    # next, cover optional tables in GTFS spec
    content += '<br>2. Additional tables: (#)<br>'
    for feed in optionalFeeds:
        tablename = feed[:-4]  # remove .txt
        count = 0

        if tablename not in chunkRules.keys():
            # normal tables
            if os.path.exists(dbFolder + tablename + '.h5'):
                hdf = pd.HDFStore(dbFolder + tablename + '.h5')
                try:
                    count = hdf.get_storer('df').nrows
                except (KeyError, ValueError) as e:
                    logmessage('Note: {} does not have any data.'.format(tablename + '.h5'))
                hdf.close()
                coveredFiles.append(tablename + '.h5')
            message = '{}: {:,} entries'.format(tablename.ljust(20), count)
            logmessage(message)
            content += message + '<br>'

        else:
            # chunked files
            chunks = findFiles(dbFolder, ext='.h5', prefix=tablename, chunk='y')
            if chunks:
                for h5File in chunks:
                    hdf = pd.HDFStore(dbFolder + h5File)
                    try:
                        count += hdf.get_storer('df').nrows
                    except (KeyError, ValueError) as e:
                        logmessage('Note: {} does not have any data.'.format(h5File))
                    hdf.close()
                    coveredFiles.append(h5File)
            message = '{}: {:,} entries'.format(tablename.ljust(20), count)
            logmessage(message)
            content += message + '<br>'

    # optionalFeeds loop over

    # now we cover the files that are present in the feed but not part of the GTFS spec
    remainingFiles = set(filenames) - set(coveredFiles)
    if (remainingFiles): content += '<br>3. Other tables: (^)<br>'
    for h5File in remainingFiles:
        hdf = pd.HDFStore(dbFolder + h5File)
        try:
            count = hdf.get_storer('df').nrows
        except (KeyError, ValueError) as e:
            logmessage('Note: {} does not have any data.'.format(h5File))
            count = 0
        hdf.close()
        message = '{}: {:,} entries'.format(h5File[:-3].ljust(20), count)
        logmessage(message)
        content += message + '<br>'

    # Footnotes
    content += '<br>----<br>*: required part of GTFS spec, needed to make valid GTFS'
    content += '<br>#: part of GTFS spec but not compulsory'
    if (remainingFiles): content += '<br>^: not part of traditional GTFS spec, used by operator for additional purposes'

    return content

# end of GTFSstats function
