# import url handlers
from handlers.config import APIKeys
from handlers.gtfsagency import *
from handlers.gtfscalendar import calendar
from handlers.gtfsfrequencies import frequencies
from handlers.gtfsroutes import *
from handlers.gtfsfares import *
from handlers.gtfsshapes import *
from handlers.gtfsstops import *
from handlers.gtfstrips import *
from handlers.gtfsstoptimes import *
from handlers.importexport import *
from handlers.appstats import *
from utils.tables import tableReadSave, tableColumn

url_patterns = [
        #(r"/API/data", APIHandler),
        (r"/API/allStops", allStops),
        (r"/API/allStopsKeyed", allStopsKeyed),
        (r"/API/routes", routes),
        (r"/API/fareAttributes", fareAttributes),
        (r"/API/fareRulesPivoted", fareRulesPivoted),
        (r"/API/fareRules", fareRules),
        (r"/API/agency", agency),
        (r"/API/calendar", calendar),
        # TODO: Replace(r"/API/sequence", sequence),
        (r"/API/trips", trips),
        (r"/API/stopTimes", stopTimes),
        (r"/API/routeIdList", routeIdList),
        (r"/API/tripIdList", tripIdList),
        # TODO: Replace(r"/API/serviceIds", serviceIds),
        (r"/API/stats", stats),
        (r"/API/commitExport", commitExport),
        (r"/API/pastCommits", pastCommits),
        (r"/API/gtfsImportZip", gtfsImportZip),
        # TODO: Replace(r"/API/XMLUpload", XMLUpload),
        # TODO: Replace(r"/API/XMLDiagnose", XMLDiagnose),
        # TODO: Replace(r"/API/stations", stations),
        # TODO: Replace(r"/API/fareChartUpload", fareChartUpload),
        # TODO: Replace(r"/API/xml2GTFS", xml2GTFS),
        # TODO: Replace(r"/API/gtfsBlankSlate", gtfsBlankSlate),
        # TODO: Replace(r"/API/translations", translations),
        (r"/API/shapesList", shapesList),
        (r"/API/allShapesList", allShapesList),
        (r"/API/shape", shape),
        # TODO: Replace(r"/API/listAll", listAll),
        # TODO: Replace(r"/API/zoneIdList", zoneIdList),
        # TODO: Replace(r"/API/diagnoseID", diagnoseID),
        # TODO: Replace(r"/API/deleteByKey", deleteByKey),
        # TODO: Replace(r"/API/replaceID", replaceID),
        # TODO: Replace(r"/API/hydGTFS", hydGTFS),
        (r"/API/frequencies", frequencies),
        (r"/API/tableReadSave", tableReadSave),
        (r"/API/tableColumn", tableColumn),
        (r"/API/Config/ApiKeys", APIKeys),
        (r"/API/gtfs/shapes", gtfsshape),
        # New API Calls
        (r"/API/gtfs/agency", gtfsagency),
        (r"/API/gtfs/agency/list/id", gtfsagencylistids),
        (r"/API/gtfs/agency/list/idname", gtfsagencylistidnames),
        (r"/API/gtfs/agency/(.*)", gtfsagency),
        (r"/API/gtfs/stop", gtfsstops),
        (r"/API/gtfs/stop/list/id", gtfsstopslistids),
        (r"/API/gtfs/stop/list/idname", gtfsstoplistidnames),
        (r"/API/gtfs/stop/(.*)", gtfsstops),
        (r"/API/gtfs/route", gtfsroutes),
        (r"/API/gtfs/route/list/id", gtfsrouteslistids),
        (r"/API/gtfs/route/list/idname", gtfsrouteslistidnames),
        (r"/API/gtfs/route/(.*)", gtfsroutes),
        #(r"/API/idList", idList),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": root, "default_filename": "index.html"})
    ]

# Try to make a api
# /api/gtfs/agency (Get all agencies)
# /api/gtfs/agency/list/id get list of agency_id's
# /api/gtfs/agency/list/idname get list of agency_id's and name's
# /api/gtfs/agency/{agency_id} Get agency by agency_id

# All gtfs based here /API/gtfs/*
# All app code api here /API/app/* (stats)
# All app import here /API/app/import/*
# All app export here /API/app/export/*
# All hrml specific code: /API/hrml/*
# All krml specific code: /API/krml/*
