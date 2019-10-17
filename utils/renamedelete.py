import json
import os

import pandas as pd
from tinydb import Query

from settings import configFolder, debugMode, chunkRules, sequenceDBfile, dbFolder
from utils.calendar import CombineServiceIDFromCalenderFiles
from utils.logmessage import logmessage
from utils.shapes import allShapesListFunc
from utils.tables import readColumnDB, tinyDBopen, findFiles, findChunk, readTableDB, readChunkTableDB


def GetAllIds ():
    zoneCollector = set()

    # stops
    stop_id_list = readColumnDB('stops', 'stop_id')

    # also collect zone_ids
    zoneCollector.update(readColumnDB('stops', 'zone_id'))

    # routes
    route_id_list = readColumnDB('routes', 'route_id')

    # trips
    trip_id_list = readColumnDB('trips', 'trip_id')

    # fare zone ids
    zoneCollector.update(readColumnDB('fare_rules', 'origin_id'))
    zoneCollector.update(readColumnDB('fare_rules', 'destination_id'))

    # zones collected; transfer all collected zones to zone_id_list
    zone_id_list = list(zoneCollector)

    # fare_ids
    # solves https://github.com/WRI-Cities/static-GTFS-manager/issues/36
    fare_id_list = readColumnDB('fare_attributes', 'fare_id')

    # agency_ids
    # solves https://github.com/WRI-Cities/static-GTFS-manager/issues/42
    agency_id_list = readColumnDB('agency', 'agency_id')

    # next are repetitions of other functions
    # shapes
    shapeIDsJson = allShapesListFunc()

    # service ids
    service_id_list = CombineServiceIDFromCalenderFiles()

    # wrapping it all together
    returnJson = {'stop_id_list': stop_id_list, 'route_id_list': route_id_list, 'trip_id_list': trip_id_list,
                  'zone_id_list': zone_id_list, 'shapeIDsJson': shapeIDsJson, 'service_id_list': service_id_list,
                  'fare_id_list': fare_id_list, 'agency_id_list': agency_id_list}

    return returnJson


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
            .format(column,h5File) )
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