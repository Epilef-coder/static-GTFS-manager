import json
from collections import OrderedDict
from math import radians, sin, cos, atan2, sqrt

from settings import sequenceDBfile
from utils.logmessage import logmessage
from utils.tables import readColumnDB, tinyDBopen

def allShapesListFunc():
    shapeIDsJson = {}

    shapeIDsJson['all'] = readColumnDB('shapes','shape_id')

    db = tinyDBopen(sequenceDBfile)
    allSequences = db.all()
    db.close()

    shapeIDsJson['saved'] = { x['route_id']:[ x.get('shape0', ''), x.get('shape1','') ]  for x in allSequences }

    return shapeIDsJson


def geoJson2shape(route_id, shapefile, shapefileRev=None):
    with open(shapefile, encoding='utf8') as f:
        # loading geojson, from https://gis.stackexchange.com/a/73771/44746
        data = json.load(f)
    logmessage('Loaded',shapefile)

    output_array = []
    try:
        coordinates = data['features'][0]['geometry']['coordinates']
    except:
        logmessage('Invalid geojson file ' + shapefile)
        return False

    prevlat = coordinates[0][1]
    prevlon = coordinates[0][0]
    dist_traveled = 0
    i = 0
    for item in coordinates:
        newrow = OrderedDict()
        newrow['shape_id'] = route_id + '_0'
        newrow['shape_pt_lat'] = item[1]
        newrow['shape_pt_lon'] = item[0]
        calcdist = lat_long_dist(prevlat,prevlon,item[1],item[0])
        dist_traveled = dist_traveled + calcdist
        newrow['shape_dist_traveled'] = dist_traveled
        i = i + 1
        newrow['shape_pt_sequence'] = i
        output_array.append(newrow.copy())
        prevlat = item[1]
        prevlon = item[0]

    # Reverse trip now.. either same shapefile in reverse or a different shapefile
    if( shapefileRev ):
        with open(shapefileRev, encoding='utf8') as g:
            data2 = json.load(g)
        logmessage('Loaded',shapefileRev)
        try:
            coordinates = data2['features'][0]['geometry']['coordinates']
        except:
            logmessage('Invalid geojson file ' + shapefileRev)
            return False
    else:
        coordinates.reverse()

    prevlat = coordinates[0][1]
    prevlon = coordinates[0][0]
    dist_traveled = 0
    i = 0
    for item in coordinates:
        newrow = OrderedDict()
        newrow['shape_id'] = route_id + '_1'
        newrow['shape_pt_lat'] = item[1]
        newrow['shape_pt_lon'] = item[0]
        calcdist = lat_long_dist(prevlat,prevlon,item[1],item[0])
        dist_traveled = float(format( dist_traveled + calcdist , '.2f' ))
        newrow['shape_dist_traveled'] = dist_traveled
        i = i + 1
        newrow['shape_pt_sequence'] = i
        output_array.append(newrow.copy())
        prevlat = item[1]
        prevlon = item[0]

    return output_array


def lat_long_dist(lat1,lon1,lat2,lon2):
    # function for calculating ground distance between two lat-long locations
    R = 6373.0 # approximate radius of earth in km.

    lat1 = radians( float(lat1) )
    lon1 = radians( float(lon1) )
    lat2 = radians( float(lat2) )
    lon2 = radians( float(lon2) )

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = float(format( R * c , '.2f' )) #rounding. From https://stackoverflow.com/a/28142318/4355695
    return distance