import time

import tornado.web
from tinydb import TinyDB, Query
from utils.logmessage import logmessage
from utils.password import decrypt

from settings import *

import pandas as pd
import numpy as np
import gc  # garbage collector, from https://stackoverflow.com/a/1316793/4355695
import os, json

from utils.piwiktracking import logUse


def readTableDB(tablename, key=None, value=None):
    '''
	main function for reading a table or part of it from the DB
	read-only
	note: this does not handle non-primary keys for chunked tables. - let's change that!
	'''

    # if tablename is a blank string, return empty array.
    if not len(tablename):
        return pd.DataFrame()

    if tablename not in chunkRules.keys():
        # not a chunked file
        h5Files = [tablename + '.h5']

    else:
        # if it's a chunked file
        if key == chunkRules[tablename].get('key'):
            h5File = findChunk(value, tablename)
            if not h5File:
                logmessage('readTableDB: No {} chunk found for key={}'.format(tablename, value))
                h5Files = []
            else:
                h5Files = [h5File]
        else:
            h5Files = findFiles(dbFolder, ext='.h5', prefix=tablename, chunk='y')

    # so now we have array/list h5Files having one or more .h5 files to be read.

    collectDF = pd.DataFrame()
    for h5File in h5Files:

        # check if file exists.
        if not os.path.exists(dbFolder + h5File):
            continue

        try:
            df = pd.read_hdf(dbFolder + h5File).fillna('').astype(str)
        # typecasting as str, keeping NA values blank ''
        except (KeyError, ValueError) as e:
            df = pd.DataFrame()
            logmessage('Note: {} does not have any data.'.format(h5File))

        if (key and value):
            logmessage('readTableDB: table:{}, column:{}, value:"{}"'.format(tablename, key, value))
            # check if this column is present or not
            if key not in df.columns:
                logmessage('readTableDB: Error: column {} not found in {}. Skipping it.'.format(key, h5File))
                continue
            df.query('{} == "{}"'.format(key, value), inplace=True)
        # note: in case the column (key) has a space, see https://github.com/pandas-dev/pandas/issues/6508. Let's avoid spaces in column headers please!
        # dilemma: what if the value is a number instead of a string? let's see that happens!
        # -> solved by typecasting everything as str by default
        collectDF = collectDF.append(df.copy(), ignore_index=True, sort=False)
        del df

    logmessage('readTableDB: Loaded {}, {} records'.format(tablename, len(collectDF)))
    return collectDF


def replaceTableDB(tablename, data, key=None, value=None):
    # new Data
    xdf = pd.DataFrame(data).fillna('').astype(str)
    # type-casting everything as string only, it's safer. See https://github.com/WRI-Cities/static-GTFS-manager/issues/82

    if value is not None:
        value = str(value)

    # fork out if it's stop_times or other chunked table

    if tablename in chunkRules.keys():
        # we do NOT want to come here from the replaceID() function. That should be handled separately.
        # Here, do only if it's coming from the actual data editing side.
        if value is None or key != chunkRules[tablename]['key']:
            # NOPE, not happening! for chunked table, value HAS to be a valid id.
            logmessage('Invalid key-value pair for chunked table', tablename, ':', key, '=', value)
            del xdf
            gc.collect()
            return False
        chunkyStatus = replaceChunkyTableDB(xdf, value, tablename)

        del xdf
        gc.collect()
        return chunkyStatus

    # fork over, now back to regular

    h5File = tablename + '.h5'

    # if file doesn't exist (ie, brand new data), make a new .h5 with the data and scram
    if not os.path.exists(dbFolder + h5File):
        xdf.to_hdf(dbFolder + h5File, 'df', format='table', mode='w', complevel=1)
        logmessage('DB file for {} not found so created with the new data.'.format(tablename))

    # else proceed if file exists

    elif ((key is not None) and (value is not None)):
        # remove entries matching the key and value
        try:
            df = pd.read_hdf(dbFolder + h5File).fillna('').astype(str)
            oldLen = len(df[df[key] == str(value)])
            df.query(key + ' != "' + str(value) + '"', inplace=True)
        except (KeyError, ValueError) as e:
            df = pd.DataFrame()
            logmessage('Note: {} does not have any data.'.format(h5File))
            oldLen = 0

        df3 = pd.concat([df, xdf], ignore_index=True)
        df3.to_hdf(dbFolder + h5File, 'df', format='table', mode='w', complevel=1)

        logmessage('Replaced {} entries for {}={} with {} new entries in {}.' \
                   .format(oldLen, key, str(value), str(len(xdf)), tablename))
        del df3
        del df

    else:
        # directly replace whatever's there with new data.
        xdf.to_hdf(dbFolder + h5File, 'df', format='table', mode='w', complevel=1)
        logmessage('Replaced {} with new data, {} entries inserted.'.format(tablename, str(len(data))))

    del xdf
    gc.collect()
    return True


def sequenceSaveDB(sequenceDBfile, route_id, data, shapes=None):
    '''
	save onward and return stops sequence for a route
	'''
    dataToUpsert = {'route_id': route_id, '0': data[0], '1': data[1]}
    if shapes:
        if len(shapes[0]):
            dataToUpsert.update({'shape0': shapes[0]})
        if len(shapes[1]):
            dataToUpsert.update({'shape1': shapes[1]})
    # add shapes names to sequence DB only if they are valid shape names, not if they are blank strings.
    # solves part of https://github.com/WRI-Cities/static-GTFS-manager/issues/38

    db = tinyDBopen(sequenceDBfile)
    Item = Query()
    status = True
    try:
        db.upsert(dataToUpsert, Item['route_id'] == route_id)
    except:
        status = False
    db.close()
    return status


def sequenceReadDB(sequenceDBfile, route_id):
    db = tinyDBopen(sequenceDBfile)

    Item = Query()
    '''
	check = db.contains(Item['route_id'] == route_id)
	if not check:
		db.close()
		return False
	'''
    sequenceItem = db.search(Item['route_id'] == route_id)
    db.close()

    if sequenceItem == []:
        return False

    sequenceArray = [sequenceItem[0]['0'], sequenceItem[0]['1']]
    logmessage('Got the sequence from sequence db file.')
    return sequenceArray


def tinyDBopen(filename):
    # made for the event when db file is corrupted. using this instead of default db open statement will reset the file if corrupted.
    try:
        db = TinyDB(filename, sort_keys=True, indent=2)
    except JSONDecodeError:
        logmessage('tinyDBopen: DB file {} has invalid json. Making a backup copy and creating a new blank one.'.format(
            filename))
        shutil.copy(filename, filename + '_backup')  # copy file. from http://www.techbeamers.com/python-copy-file/

    except FileNotFoundError:
        logmessage('tinyDBopen: {} not found so creating.'.format(filename))
        open(filename, 'w').close()  # make a blank file. from https://stackoverflow.com/a/12654798/4355695
        db = TinyDB(filename, sort_keys=True, indent=2)

    return db


def replaceChunkyTableDB(xdf, value, tablename='stop_times'):
    chunkFile = findChunk(value, tablename)
    key = chunkRules[tablename]['key']
    lookupJSONFile = chunkRules[tablename]['lookup']

    if chunkFile:
        logmessage('Editing ' + chunkFile)
        try:
            df = pd.read_hdf(dbFolder + chunkFile).fillna('').astype(str)
        except (KeyError, ValueError) as e:
            df = pd.DataFrame()
            logmessage('Note: {} does not have any data.'.format(chunkFile))
        initLen = len(df)

        df = df[df[key] != str(value)]
        # df.query('trip_id != "' + str(trip_id) + '"', inplace=True)
        reducedLen = len(df)

        if reducedLen == initLen:
            logmessage('Warning: id {} was supposed to be in {} but no entries there. \
			Cross-check later. Proceeding with insering new data for now.'.format(value, chunkFile))
        else:
            logmessage('{} older entries for id {} removed.'.format(str(initLen - reducedLen), value))


    else:
        # if the trip wasn't previously existing, take the smallest chunk and add in there.
        chunkFile = smallestChunk(tablename)
        try:
            df = pd.read_hdf(dbFolder + chunkFile).fillna('').astype(str)
        except (KeyError, ValueError) as e:
            df = pd.DataFrame()
            logmessage('Note: {} does not have any data.'.format(chunkFile))
        except FileNotFoundError as e:
            df = pd.DataFrame()
            logmessage('Note: {} does not exist yet, so we will likely create it.'.format(chunkFile))

    # next 3 lines to be done in either case
    # newdf = pd.concat([df,xdf],ignore_index=True)
    newdf = df.append(xdf, ignore_index=True, sort=False)
    logmessage('{} new entries for id {} added. Now writing to {}.'.format(str(len(xdf)), value, chunkFile))
    newdf.to_hdf(dbFolder + chunkFile, 'df', format='table', mode='w', complevel=1)

    # add entry for new trip in stop_times_lookup.json
    with open(dbFolder + lookupJSONFile) as f:
        table_lookup = json.load(f)

    # adding a new key in the json.
    table_lookup[value] = chunkFile

    with open(dbFolder + lookupJSONFile, 'w') as outfile:
        json.dump(table_lookup, outfile, indent=2)

    # for cross-checking
    logmessage('Making new.csv and test.csv in {} for cross-checking.'.format(uploadFolder))
    xdf.to_csv(uploadFolder + 'new.csv', index_label='sr')
    newdf.to_csv(uploadFolder + 'test.csv', index_label='sr')

    # clean up after job done
    del newdf
    del df
    gc.collect()
    return True


def findChunk(value, tablename="stop_times"):
    lookupJSONFile = chunkRules[tablename]['lookup']
    print('lookup for {}: {}'.format(tablename, lookupJSONFile))

    try:
        with open(dbFolder + lookupJSONFile) as f:
            table_lookup = json.load(f)
    except FileNotFoundError:
        logmessage(dbFolder + lookupJSONFile, 'not found so creating it as empty json.')
        with open(dbFolder + lookupJSONFile, 'a') as f:
            f.write('{}')
        table_lookup = {}

    chunkFile = table_lookup.get(value, None)
    print('Found chunk for id {}: {}'.format(value, chunkFile))
    return chunkFile


def smallestChunk(prefix, maxSizeMB=configRules.get('MAX_CHUNK_SIZE', 1)):
    '''
	Find the smallest chunk of a chunked table, by size, as the place to put a new set of records in.
	This helps to balance the sizes out over time.
	In case ALL the chunks are too heavy (set some limit), then christen the next chunk.
	'''
    # filenames = [f for f in os.listdir(dbFolder) if f.lower().endswith('.h5') and ( f.lower().startswith(prefix) ) and os.path.isfile(os.path.join(dbFolder, f))]
    filenames = findFiles(dbFolder, prefix=prefix, chunk='y')

    if not len(filenames):
        # no chunks present, return tablename_1
        return prefix + '_1.h5'

    # chunkFile = sorted(filenames, key=lambda filename: os.path.getsize(os.path.join(dbFolder, filename)))[0]
    # sort the list of files by size and pick first one. From https://stackoverflow.com/a/44215088/4355695
    sizeList = [os.path.getsize(os.path.join(dbFolder, filename)) / (2 ** 20) for filename in filenames]
    # get sizes in MB
    if min(sizeList) < maxSizeMB:
        chunkFile = filenames[sizeList.index(min(sizeList))]
    else:
        nextChunkNum = len(filenames) + 1
        chunkFile = '{}_{}.h5'.format(prefix, nextChunkNum)
        logmessage('smallestChunk: All chunks for {} too big, lets create a new one, {}'.format(prefix, chunkFile))
    return chunkFile


def findFiles(folder, ext='.h5', prefix=None, chunk='all'):
    # chunk : 'all','n' for not chunked,'y' for chunked
    filenames = [f for f in os.listdir(folder)
                 if f.lower().endswith(ext)
                 and (checkPrefix(f, prefix))
                 and (chunkFilter(f, chunk))
                 and os.path.isfile(os.path.join(folder, f))]
    return filenames


def checkPrefix(f, prefix):
    if not prefix: return True
    return f.lower().startswith(prefix)


def chunkFilter(f, chunk):
    '''
	Tells you if the given file is to be taken or not depending on whether you want all, chunked-only or not-chunked-only
	'''
    if chunk == 'all': return True
    chunkList = list(chunkRules.keys())
    if any([f.startswith(x) for x in chunkList]) and chunk == 'y': return True
    if (not any([f.startswith(x) for x in chunkList])) and chunk == 'n': return True
    return False


def readChunkTableDB(tablename, key, value):
    '''
	function to collect data from all the chunks of a chunked table when the key is not the primary key
	'''
    collectDF = pd.DataFrame()
    if (key is None) or (value is None):
        # very nice! take a blank table, go!
        logmessage('readChunkTableDB: Sorry, cannot extract data from table {} with key={} and value={}' \
                   .format(tablename, key, value))
        return pd.DataFrame()

    collect = []
    chunksHaving = []
    for i, h5File in enumerate(findFiles(dbFolder, ext='.h5', prefix=tablename, chunk='y')):
        try:
            df = pd.read_hdf(dbFolder + h5File).fillna('').astype(str) \
                .query('{}=="{}"'.format(key, value))
        except (KeyError, ValueError) as e:
            df = pd.DataFrame()
            logmessage('Note: {} does not have any data.'.format(h5File))
        if len(df):
            collect.append(df.copy())
            chunksHaving.append(h5File)
        del df

    if len(collect):
        collectDF = pd.concat(collect, ignore_index=True)
        logmessage('readChunkTableDB: Collected {} rows from table {} for {}={}' \
                   .format(len(collectDF), tablename, key, value), \
                   '\nChunks having entries:', chunksHaving)
        return collectDF
    else:
        logmessage('readChunkTableDB: No rows found in chunked table {} for {}={}' \
                   .format(tablename, key, value))
        return pd.DataFrame()


def readColumnsDB(tablename, columns):
    # This function will allow you to read multiple columns from a file. You have to input a array into the columsn parameter
    # TODO: Fix the chunking part
    returnList = []
    # check if chunking:
    if tablename not in chunkRules.keys():
        # Not chunking
        df = readTableDB(tablename)
        if len(df):
            returnList = df[columns]
            # if column in df.columns:
            #     returnList = df[column].replace('', np.nan).dropna().unique().tolist()
            # else:
            #     logmessage('readColumnDB: Hey, the column {} doesn\'t exist in the table {} for {}={}' \
            #                .format(column, tablename, key, value))
        del df

    else:
        # Yes chunking
        # to do:
        # if the column seeked is the same as the primary key of the chunk, then just get that list from the json.
        # but if the column is something else, then load that chunk and get the column.

        if column == chunkRules[tablename]['key']:
            lookupJSONFile = chunkRules[tablename]['lookup']
            # check if file exists.
            if not os.path.exists(dbFolder + lookupJSONFile):
                print('readColumnDB: HEY! {} does\'t exist! Returning [].'.format(lookupJSONFile))
            else:
                with open(dbFolder + lookupJSONFile) as f:
                    table_lookup = json.load(f)
                returnList = list(table_lookup.keys())
        # so now we have the ids list taken from the lookup json itself, no need to open .h5 files.

        else:
            if key == chunkRules[tablename]['key']:
                df = readTableDB(tablename)
            else:
                if debugMode: logmessage(
                    'readColumnDB: Note: reading a chunked table {} by non-primary key {}. May take time.' \
                        .format(tablename, key))
                df = readChunkTableDB(tablename)

            if column in df.columns:
                # in a chunked file, give the values as-is, don't do any unique'ing business.
                returnList = df[column].tolist()
            else:
                logmessage('readColumnDB: Hey, the column {} doesn\'t exist in the chunked table {} for {}={}' \
                           .format(column, tablename, key, value))
            del df

    gc.collect()
    return returnList


def readColumnDB(tablename, column, key=None, value=None):
    # This function will read only one column of a file.
    returnList = []
    # check if chunking:
    if tablename not in chunkRules.keys():
        # Not chunking
        df = readTableDB(tablename, key, value)
        if len(df):
            if column in df.columns:
                returnList = df[column].replace('', np.nan).dropna().unique().tolist()
            else:
                logmessage('readColumnDB: Hey, the column {} doesn\'t exist in the table {} for {}={}' \
                           .format(column, tablename, key, value))
        del df

    else:
        # Yes chunking
        # to do:
        # if the column seeked is the same as the primary key of the chunk, then just get that list from the json.
        # but if the column is something else, then load that chunk and get the column.

        if column == chunkRules[tablename]['key']:
            lookupJSONFile = chunkRules[tablename]['lookup']
            # check if file exists.
            if not os.path.exists(dbFolder + lookupJSONFile):
                print('readColumnDB: HEY! {} does\'t exist! Returning [].'.format(lookupJSONFile))
            else:
                with open(dbFolder + lookupJSONFile) as f:
                    table_lookup = json.load(f)
                returnList = list(table_lookup.keys())
        # so now we have the ids list taken from the lookup json itself, no need to open .h5 files.

        else:
            if key == chunkRules[tablename]['key']:
                df = readTableDB(tablename, key=key, value=value)
            else:
                if debugMode: logmessage(
                    'readColumnDB: Note: reading a chunked table {} by non-primary key {}. May take time.' \
                        .format(tablename, key))
                df = readChunkTableDB(tablename, key=key, value=value)

            if column in df.columns:
                # in a chunked file, give the values as-is, don't do any unique'ing business.
                returnList = df[column].tolist()
            else:
                logmessage('readColumnDB: Hey, the column {} doesn\'t exist in the chunked table {} for {}={}' \
                           .format(column, tablename, key, value))
            del df

    gc.collect()
    return returnList


class tableReadSave(tornado.web.RequestHandler):
    def get(self):
        # ${APIpath}tableReadSave?table=table&key=key&value=value
        start = time.time()

        table = self.get_argument('table', default='')
        logmessage('\ntableReadSave GET call for table={}'.format(table))

        if not table:
            self.set_status(400)
            self.write("Error: invalid table.")
            return

        key = self.get_argument('key', default=None)
        value = self.get_argument('value', default=None)
        if key and value:
            dataJson = readTableDB(table, key=key, value=value).to_json(orient='records', force_ascii=False)
        else:
            dataJson = readTableDB(table).to_json(orient='records', force_ascii=False)

        self.write(dataJson)
        end = time.time()
        logUse('{}_read'.format(table))
        logmessage("tableReadSave GET call for table={} took {} seconds.".format(table, round(end - start, 2)))

    def post(self):
        # ${APIpath}tableReadSave?pw=pw&table=table&key=key&value=value
        start = time.time()
        pw = self.get_argument('pw', default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return

        table = self.get_argument('table', default='')
        if not table:
            self.set_status(400)
            self.write("Error: invalid table.")
            return

        logmessage('\ntableReadSave POST call for table={}'.format(table))

        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads(self.request.body.decode('UTF-8'))

        key = self.get_argument('key', default=None)
        value = self.get_argument('value', default=None)
        if key and value:
            status = replaceTableDB(table, data, key, value)
        else:
            status = replaceTableDB(table, data)

        if status:
            self.write('Saved {} data to DB.'.format(table))
        else:
            self.set_status(400)
            self.write("Error: Could not save to DB.")
        end = time.time()
        logUse('{}_write'.format(table))
        logmessage("tableReadSave POST call for table={} took {} seconds.".format(table, round(end - start, 2)))


class tableColumn(tornado.web.RequestHandler):
    def get(self):
        # API/tableColumn?table=table&column=column&key=key&value=value
        start = time.time()
        logmessage('\nrouteIdList GET call')

        table = self.get_argument('table', default='')
        column = self.get_argument('column', default='')
        logmessage('\ntableColumn GET call for table={}, column={}'.format(table, column))

        if (not table) or (not column):
            self.set_status(400)
            self.write("Error: invalid table or column given.")
            return

        key = self.get_argument('key', default=None)
        value = self.get_argument('value', default=None)

        if key and value:
            returnList = readColumnDB(table, column, key=key, value=value)
        else:
            returnList = readColumnDB(table, column)

        returnList.sort()
        self.write(json.dumps(returnList))
        end = time.time()
        logUse('{}_column'.format(table))
        logmessage("tableColumn GET call took {} seconds.".format(round(end - start, 2)))
