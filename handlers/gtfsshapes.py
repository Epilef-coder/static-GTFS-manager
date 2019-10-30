import pandas as pd
import tornado.web
import tornado.ioloop
import gc # garbage collector, from https://stackoverflow.com/a/1316793/4355695
import time
import json

from settings import uploadFolder
from utils.logmessage import logmessage
from utils.password import decrypt
from utils.shapes import allShapesListFunc, geoJson2shape
from utils.tables import readTableDB, readColumnDB, replaceTableDB
from utils.upload import uploadaFile


class shapesList(tornado.web.RequestHandler):
    def get(self):
        # API/shapesList?route=${route_id}
        start = time.time()
        logmessage('\nshapesList GET call')
        route_id = self.get_argument('route','')
        if not len(route_id):
            self.set_status(400)
            self.write("Error: invalid route.")
            return

        shapeIDsJson = {}
        df = readTableDB('trips', key='route_id', value=route_id)

        # since shape_id is an optional column, handle gracefully if column not present.
        if 'shape_id' not in df.columns:
            shapeIDsJson = { '0':[], '1':[] }
            self.write(json.dumps(shapeIDsJson))
            del df
            gc.collect()
            return

        # get shape_id's used by that route and direction. Gets rid of blanks and NaNs, gets unique list and outputs as list.
        shapeIDsJson['0'] = df[ (df.direction_id == '0') ].shape_id.replace('', pd.np.nan).dropna().unique().tolist()
        shapeIDsJson['1'] = df[ (df.direction_id == '1') ].shape_id.replace('', pd.np.nan).dropna().unique().tolist()

        self.write(json.dumps(shapeIDsJson))
        del df
        gc.collect()
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("shapesList GET call took {} seconds.".format(round(end-start,2)))


class shape(tornado.web.RequestHandler):
    def post(self):
        # ${APIpath}shape?pw=${pw}&route=${route_id}&id=${shape_id}&reverseFlag=${reverseFlag}
        start = time.time()
        logmessage('\nshape POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        route_id = self.get_argument('route', default='')
        shapePrefix = self.get_argument('id', default='')
        reverseFlag = self.get_argument('reverseFlag', default=False) == 'true'
        logmessage(route_id)
        logmessage(shapePrefix)
        logmessage(reverseFlag)

        if not ( len(route_id) and len(shapePrefix) ):
            self.set_status(400)
            self.write("Error: Invalid route or shape id prefix.")
            return

        shapeArray = False

        geoJson0 = uploadaFile( self.request.files['uploadShape0'][0] )
        logmessage(geoJson0)
        if reverseFlag:
            geoJson1 = uploadaFile( self.request.files['uploadShape1'][0] )
            logmessage(geoJson1)
            shapeArray = geoJson2shape(shapePrefix, shapefile=(uploadFolder+geoJson0), shapefileRev=(uploadFolder+geoJson1) )
        else:
            shapeArray = geoJson2shape(shapePrefix, shapefile=(uploadFolder+geoJson0), shapefileRev=None)

        if not shapeArray:
            self.set_status(400)
            self.write("Error: One or more geojson files is faulty. Please ensure it's a proper line.")
            return

        shape0 = str(shapePrefix) + '_0'
        shape1 = str(shapePrefix) + '_1'
        shapeArray0 = [ x for x in  shapeArray if x['shape_id'] == shape0 ]
        shapeArray1 = [ x for x in  shapeArray if x['shape_id'] == shape1 ]

        replaceTableDB('shapes', shapeArray0, key='shape_id', value=shape0)
        replaceTableDB('shapes', shapeArray1, key='shape_id', value=shape1)


        self.write('Saved ' + shape0 + ', ' + shape1 + ' to shapes table in DB.')
        end = time.time()
        logmessage("shape POST call took {} seconds.".format(round(end-start,2)))

    def get(self):
        # API/shape?shape=${shape_id}
        start = time.time()
        logmessage('\nshape GET call')
        shape_id = self.get_argument('shape', default='')
        print(shape_id)

        if not len(shape_id):
            self.set_status(400)
            self.write("Error: invalid shape.")
            return

        shapeDf = readTableDB('shapes', key='shape_id', value=shape_id)

        if not len(shapeDf):
            self.set_status(400)
            self.write("Error: Given shape_id is not present in shapes table in DB.")
            return

        # need to sort this array before returning it. See https://github.com/WRI-Cities/static-GTFS-manager/issues/22
        shapeDf.shape_pt_sequence = shapeDf.shape_pt_sequence.astype(int)
        # type-cast the column as int before sorting!

        sortedShapeJson = shapeDf.sort_values('shape_pt_sequence').to_json(orient='records', force_ascii=False)
        # sort ref: http://pandas.pydata.org/pandas-docs/version/0.19/generated/pandas.DataFrame.sort.html
        self.write(sortedShapeJson)

        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("shape GET call took {} seconds.".format(round(end-start,2)))


class gtfsshape(tornado.web.RequestHandler):
    def get(self, shape_id=None):
        # /API/gtfs/shape/{shape_id}
        if shape_id:
            start = time.time()
            print(shape_id)
            logmessage('\n/API/gtfs/shape/{} GET call'.format(shape_id))

            shapeDf = readTableDB('shapes', key='shape_id', value=shape_id)

            if not len(shapeDf):
                self.set_status(400)
                self.write("Error: Given shape_id is not present in shapes table in DB.")
                return

            # need to sort this array before returning it. See https://github.com/WRI-Cities/static-GTFS-manager/issues/22
            shapeDf.shape_pt_sequence = shapeDf.shape_pt_sequence.astype(int)
            # type-cast the column as int before sorting!

            sortedShapeJson = shapeDf.sort_values('shape_pt_sequence').to_json(orient='records', force_ascii=False)
            # sort ref: http://pandas.pydata.org/pandas-docs/version/0.19/generated/pandas.DataFrame.sort.html
            self.write(sortedShapeJson)

            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("/API/gtfs/shape/{} GET call took {} seconds.".format(shape_id,round(end-start, 2)))

    def post(self, shape_id=None):
        if shape_id:
            # ${APIpath}shape?pw=${pw}&route=${route_id}&id=${shape_id}&reverseFlag=${reverseFlag}
            start = time.time()
            logmessage('\nshape POST call')
            pw = self.get_argument('pw', default='')
            if not decrypt(pw):
                    self.set_status(400)
                    self.write("Error: invalid password.")
                    return
            logmessage(shape_id)

            if not (len(shape_id)):
                    self.set_status(400)
                    self.write("Error: Invalid route or shape id prefix.")
                    return

            data = json.loads(self.request.body.decode('UTF-8'))

            replaceTableDB('shapes', data, key='shape_id', value=shape_id)

            self.write('Saved to shapes table in DB.')

            end = time.time()
            logmessage("shape POST call took {} seconds.".format(round(end-start, 2)))


class gtfsshapelistids(tornado.web.RequestHandler):
    def get(self):
        # /API/gtfs/shape/list/id
        start = time.time()
        logmessage('\n/API/gtfs/shape/list/id GET call')
        listCollector = set()
        listCollector.update(readColumnDB('shapes', 'shape_id'))
        # to do: find out why this function is only looking at stops table
        List = list(listCollector)
        List.sort()
        self.write(json.dumps(List))
        end = time.time()
        logmessage("\n/API/gtfs/shape/list/id GET call took {} seconds.".format(round(end - start, 2)))


class allShapesList(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        logmessage('\nallShapesList GET call')
        shapeIDsJson = allShapesListFunc()
        self.write(json.dumps(shapeIDsJson))
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("allShapesList GET call took {} seconds.".format(round(end-start,2)))


class gtfsshapeslistbyroute(tornado.web.RequestHandler):
    #/API/gtfs/shape/list/route/{route_id}
    def get(self, route_id=None):
        if route_id:
            start = time.time()
            logmessage('\n/API/gtfs/shape/list/route/{} GET call'.format(route_id))
            if not len(route_id):
                self.set_status(400)
                self.write("Error: invalid route.")
                return

            shapeIDsJson = {}
            df = readTableDB('trips', key='route_id', value=route_id)

            # since shape_id is an optional column, handle gracefully if column not present.
            if 'shape_id' not in df.columns:
                shapeIDsJson = { '0':[], '1':[] }
                self.write(json.dumps(shapeIDsJson))
                del df
                gc.collect()
                return

            # get shape_id's used by that route and direction. Gets rid of blanks and NaNs, gets unique list and outputs as list.
            shapeIDsJson['0'] = df[ (df.direction_id == '0') ].shape_id.replace('', pd.np.nan).dropna().unique().tolist()
            shapeIDsJson['1'] = df[ (df.direction_id == '1') ].shape_id.replace('', pd.np.nan).dropna().unique().tolist()

            self.write(json.dumps(shapeIDsJson))
            del df
            gc.collect()
            # time check, from https://stackoverflow.com/a/24878413/4355695
            end = time.time()
            logmessage("API/gtfs/shape/list/route/{} GET call took {} seconds.".format(route_id,round(end-start,2)))



