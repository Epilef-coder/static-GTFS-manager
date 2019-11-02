import time, os, datetime
import gc
import json
import zipfile
from collections import OrderedDict

import pandas as pd
from tinydb import TinyDB

from utils.logmessage import logmessage
from settings import uploadFolder, debugMode, requiredFeeds, dbFolder, chunkRules, exportFolder, sequenceDBfile
from utils.tables import findFiles


def importGTFS(zipname):
    start1 = time.time()

    # take backup first
    if not debugMode:
        backupDB() # do when in production, skip when developing / debugging

    # unzip imported zip
    # make a separate folder to unzip in, so that when importing we don't end up picking other .txt files that happen to be in the general uploads folder.
    unzipFolder = uploadFolder + '{:unzip-%H%M%S}/'.format(datetime.datetime.now())
    if not os.path.exists(unzipFolder):
        os.makedirs(unzipFolder)

    fileToUnzip = uploadFolder + zipname
    logmessage('Extracting uploaded zip to {}'.format(unzipFolder))

    # UNZIP a zip file, from https://stackoverflow.com/a/36662770/4355695
    with zipfile.ZipFile( fileToUnzip,"r" ) as zf:
        zf.extractall(unzipFolder)

    # loading names of the unzipped files
    # scan for txt files, non-recursively, only at folder level. from https://stackoverflow.com/a/22208063/4355695
    filenames = [f for f in os.listdir(unzipFolder) if f.lower().endswith('.txt') and os.path.isfile(os.path.join(unzipFolder, f))]
    logmessage('Extracted files: ' + str(list(filenames)) )

    if not len(filenames):
        return False

    # Check if essential files are there or not.
    # ref: https://developers.google.com/transit/gtfs/reference/#feed-files
    # using set and subset. From https://stackoverflow.com/a/16579133/4355695
    # hey we need to be ok with incomplete datasets, the tool's purpose is to complete them!
    if not set(requiredFeeds).issubset(filenames):
        logmessage('Note: We are importing a GTFS feed that does not contain all the required files as per GTFS spec: %s \
                Kindly ensure the necessary files get created before exporting.' % str(list(requiredFeeds)))


    # purge the DB. We're doing this only AFTER the ZIPfile is successfully uploaded and unzipped and tested.
    purgeDB()

    logmessage('Commencing conversion of gtfs feed files into the DB\'s .h5 files')
    for txtfile in filenames:
        tablename = txtfile[:-4]
        # using Pandas to read the csv and write it as .h5 file

        if not chunkRules.get(tablename,None):
            # normal files that don't need chunking
            df = pd.read_csv(unzipFolder + txtfile ,dtype=str, na_values='')
            # na_filter=False to read blank cells as empty strings instead of NaN. from https://stackoverflow.com/a/45194703/4355695
            # reading ALL columns as string, and taking all NA values as blank string

            if not len(df):
                # skip the table if it's empty.
                print('Skipping',tablename,'because its empty')
                continue

            h5File = tablename.lower() + '.h5'
            logmessage('{}: {} rows'.format(h5File, str(len(df)) ) )
            df.to_hdf(dbFolder+h5File, 'df', format='table', mode='w', complevel=1)
            # if there is no chunking rule for this table, then make one .h5 file with the full table.
            del df
            gc.collect()

        else:
            # let the chunking commence
            logmessage('Storing {} in chunks.'.format(tablename))
            chunkSize = chunkRules[tablename].get('chunkSize',200000)
            IDcol = chunkRules[tablename].get('key')

            fileCounter = 0
            lookupJSON = OrderedDict()
            carryOverChunk = pd.DataFrame()

            if tablename == 'shapes':
                chunk_count = 0
                reader = pd.read_csv(unzipFolder + txtfile, chunksize=chunkSize, dtype=str, na_values='')
                for chunk in reader:
                    grouped = chunk.groupby(['shape_id'])
                    chunk_count = chunk_count + 1
                    print("Processing next chunk...", chunk_count)
                    for name, group in grouped:
                        # I use assumption that customer name is in the name of files
                        fileCounter += 1
                        h5File = tablename + '_' + str(fileCounter) + '.h5'  # ex: stop_times_1.h5
                        lookupJSON[name] = h5File
                        if os.path.exists(dbFolder + h5File):
                            group.to_hdf(dbFolder + h5File, 'df', format='table', append=True, mode='a', complevel=1)
                        else:
                            group.to_hdf(dbFolder + h5File, 'df', format='table', mode='w', complevel=1)
            else:
                for chunk in pd.read_csv(unzipFolder + txtfile, chunksize=chunkSize, dtype=str, na_values=''):
                    # see if can use na_filter=False to speed up

                    if not len(chunk):
                        # skip the table if it's empty.
                        # there's probably going to be only one chunk if this is true
                        print('Skipping',tablename,'because its empty')
                        continue

                    # zap the NaNs at chunk level
                    chunk = chunk.fillna('')

                    IDList = chunk[IDcol].unique().tolist()
                    # print('first ID: ' + IDList[0])
                    # print('last ID: ' + IDList[-1])
                    workChunk = chunk[ chunk[IDcol].isin(IDList[:-1]) ]
                    if len(carryOverChunk):
                        workChunk = pd.concat([carryOverChunk, workChunk],ignore_index=True)
                    carryOverChunk = chunk[ chunk[IDcol] == IDList[-1] ]

                    fileCounter += 1
                    h5File = tablename + '_' + str(fileCounter) + '.h5' # ex: stop_times_1.h5
                    logmessage('{}: {} rows'.format(h5File, str(len(workChunk)) ) )
                    workChunk.to_hdf(dbFolder+h5File, 'df', format='table', mode='w', complevel=1)
                    del workChunk
                    gc.collect()

                    # making lookup table
                    for x in IDList[:-1]:
                        if lookupJSON.get(x,None):
                            logmessage('WARNING: {} may not have been sorted properly. Encountered a repeat instance of {}={}'
                                .format(txtfile,IDcol,x))
                        lookupJSON[x] = h5File

                # chunk loop over.
                del chunk

                # Now append the last carry-over chunk in to the last chunkfile
                logmessage('Appending the {} rows of last ID to last chunk {}'
                    .format(str(len(carryOverChunk)),h5File))
                carryOverChunk.to_hdf(dbFolder+h5File, 'df', format='table', append=True, mode='a', complevel=1)
                # need to set append=True to tell it to append. mode='a' is only for file-level.
                # add last ID to lookup
                # TODO: FIX this bug: https://stackoverflow.com/questions/48856584/python-pandas-dataframe-valueerror-trying-to-store-a-string-with-len
                # If a column value is longer len() then the longest value of the first chunk, you cannot append it.
                lookupJSON[ IDList[-1] ] = h5File

                del carryOverChunk
                gc.collect()

            lookupJSONFile = chunkRules[tablename].get('lookup','lookup.json')
            with open(dbFolder + lookupJSONFile, 'w') as outfile:
                json.dump(lookupJSON, outfile, indent=2)
            # storing lookup json
            logmessage('Lookup json: {} created for mapping ID {} to {}_n.h5 chunk files.'.format(lookupJSONFile,IDcol,tablename))


    logmessage('Finished importing GTFS feed. You can remove the feed zip {} and folder {} from {} if you want.'.format(zipname,unzipFolder,uploadFolder))
    return True

def exportGTFS (folder):
    # create commit folder
    if not os.path.exists(folder):
        os.makedirs(folder)
    else:
        returnmessage = 'Folder with same name already exists: ' + folder + '. Please choose a different commit name.'
        return returnmessage

    # let's zip them!
    zf = zipfile.ZipFile(folder + 'gtfs.zip', mode='w')

    # find .h5 files.. non-chunk ones first
    filenames = findFiles(dbFolder, ext='.h5', chunk='n')
    print(filenames)

    for h5File in filenames:
        start1 = time.time()
        tablename = h5File[:-3] # remove last 3 chars, .h5

        try:
            df = pd.read_hdf(dbFolder + h5File).fillna('').astype(str)
        except (KeyError, ValueError) as e:
            df = pd.DataFrame()
            logmessage('Note: {} does not have any data.'.format(h5File))

        if len(df):
            logmessage('Writing ' + tablename + ' to disk and zipping...')
            df.to_csv(folder + tablename + '.txt', index=False, chunksize=1000000)
            del df
            zf.write(folder + tablename + '.txt' , arcname=tablename + '.txt', compress_type=zipfile.ZIP_DEFLATED )
        else:
            del df
            logmessage(tablename + ' is empty so not exporting that.')
        end1 = time.time()
        logmessage('Added {} in {} seconds.'.format(tablename,round(end1-start1,3)))
    gc.collect()

    # Now, process chunk files.

    for tablename in list(chunkRules.keys()):
        start1 = time.time()
        filenames = findFiles(dbFolder, ext='.h5', prefix=tablename)
        if not len(filenames): continue #skip if no files

        print('Processing chunks for {}: {}'.format(tablename,list(filenames)) )

        # first, getting all columns
        columnsList = set()
        for count,h5File in enumerate(filenames):
            try:
                df = pd.read_hdf(dbFolder + h5File,stop=0)
            except (KeyError, ValueError) as e:
                df = pd.DataFrame()
                logmessage('Note: {} does not have any data.'.format(h5File))
            columnsList.update(df.columns.tolist())
            del df
        gc.collect()
        columnsList = list(columnsList)

        # moving the main ID to first position
        # from https://stackoverflow.com/a/1014544/4355695
        IDcol = chunkRules[tablename]['key']
        columnsList.insert(0, columnsList.pop(columnsList.index(IDcol)))
        logmessage('Columns for {}: {}'.format(tablename,list(columnsList)))

        for count,h5File in enumerate(filenames):
            logmessage('Writing {} to csv'.format(h5File))
            try:
                df1 = pd.read_hdf(dbFolder + h5File).fillna('').astype(str)
            except (KeyError, ValueError) as e:
                df1 = pd.DataFrame()
                logmessage('Note: {} does not have any data.'.format(h5File))
            # in case the final columns list has more columns than df1 does, concatenating an empty df with the full columns list.
            # from https://stackoverflow.com/a/30926717/4355695
            columnsetter = pd.DataFrame(columns=columnsList)
            df2 = pd.concat([df1,columnsetter], ignore_index=True, copy=False, sort=False)[columnsList]
            # adding [columnsList] so the ordering of columns is strictly maintained between all chunks

            appendFlag,headerFlag = ('w',True) if count == 0 else ('a',False)
            # so at first loop, we'll create a new one and include column headers.
            # In subsequent loops we'll append and not repeat the column headers.
            df2.to_csv(folder + tablename + '.txt', mode=appendFlag, index=False, header=headerFlag, chunksize=10000)

            del df2
            del df1
            gc.collect()

        mid1 = time.time()
        logmessage('CSV {} created in {} seconds, now zipping'.format(tablename + '.txt',round(mid1-start1,3)))

        zf.write(folder + tablename +'.txt' , arcname=tablename +'.txt', compress_type=zipfile.ZIP_DEFLATED )

        end1 = time.time()
        logmessage('Added {} to zip in {} seconds.'.format(tablename,round(end1-mid1,3)))

        logmessage('Added {} in {} seconds.'.format(tablename,round(end1-start1,3)))

    zf.close()
    gc.collect()
    logmessage('Generated GTFS feed at {}'.format(folder))

    returnmessage = '<p>Success! Generated GTFS feed at <a href="' + folder + 'gtfs.zip' + '">' + folder + 'gtfs.zip<a></b>. Click to download.</p><p>You can validate the feed on <a href="https://gtfsfeedvalidator.transitscreen.com/" target="_blank">GTFS Feed Validator</a> website.</p>'
    return returnmessage


def backupDB():
    backupfolder = exportFolder + '{:%Y-%m-%d-backup-%H%M}/'.format(datetime.datetime.now())
    logmessage('\nbackupDB: Creating backup of DB in {}.'.format(backupfolder))
    exportGTFS(backupfolder)
    logmessage('Backup created.\n')


def purgeDB():
    # purging existing .h5 files in dbFolder
    for filename in os.listdir(dbFolder):
        if filename.endswith('.h5'):
            os.unlink(dbFolder + filename)
    logmessage('Removed .h5 files from ' + dbFolder)

    # purge lookup files of chunked files too
    for filename in os.listdir(dbFolder):
        if filename.endswith('.json'):
            os.unlink(dbFolder + filename)
    logmessage('Removed .json files from ' + dbFolder)

    # also purge sequenceDB
    db2 = TinyDB(sequenceDBfile, sort_keys=True, indent=2)
    db2.purge_tables()  # wipe out the database, clean slate.
    logmessage(sequenceDBfile + ' purged.')
    db2.close()