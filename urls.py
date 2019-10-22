# import url handlers

from handlers.app import AppDatabaseBlank, AppDatabaseGTFSImport, AppConfig, Appstats
from handlers.gtfsagency import *
from handlers.gtfscalendar import calendar, gtfscalendarlistids, gtfscalendarcurrent,gtfscalendar
from handlers.gtfscalendardates import gtfscalendardateslistids,gtfscalendardates
from handlers.gtfsfeedinfo import gtfsfeedinfo
from handlers.gtfstranslations import gtfstranlations
from handlers.gtfsfrequencies import gtfsfrequencies, gtfsfrequencieslistids
from handlers.gtfsroutes import *
from handlers.gtfsfarerules import gtfsfarerules, gtfsfareruleslistids, fareRulesPivoted
from handlers.gtfsfareattributes import gtfsfareattributes, gtfsfareattributeslistids
from handlers.gtfsshapes import gtfsshape, gtfsshapelistids, gtfsshapeslistbyroute, shape, allShapesList
from handlers.gtfsstops import *
from handlers.gtfstrips import *
from handlers.gtfsstoptimes import *
from handlers.hrml import hrmlhydGTFS
from handlers.importexport import commitExport, pastCommits
from handlers.krml import krmlstations, krmlXMLUpload, krmlXMLDiagnose, krmlfareChartUpload, krmlxml2GTFS
from handlers.renamedelete import gtfsrenamelistAllids, gtfsdeletelistAllids, gtfsReplaceID, gtfsdeletediag, \
        gtfsdeleteByKey
from handlers.sequence import defaultsequence, defaultsequencebyroute
from handlers.validate import googlevalidate, pastreportsgtfsvalidate, getreportsgtfsvalidate, deletereportsgtfsvalidate
from settings import STATIC_ROOT, exportFolder
from utils.tables import tableReadSave, tableColumn

url_patterns = [
        #(r"/API/data", APIHandler),
        (r"/API/app/config", AppConfig),
        (r"/API/app/stats", Appstats),
        (r"/API/app/database/blank",AppDatabaseBlank),
        (r"/API/app/database/gtfs/import",AppDatabaseGTFSImport),
        (r"/API/allStops", allStops),
        (r"/API/allStopsKeyed", allStopsKeyed),
        (r"/API/routes", routes),
        #(r"/API/fareAttributes", fareAttributes),
        #(r"/API/fareRulesPivoted", fareRulesPivoted),
        (r"/API/agency", agency),
        (r"/API/calendar", calendar),
        # TODO: Replace(r"/API/sequence", sequence),
        # (r"/API/trips", trips),
        (r"/API/stopTimes", stopTimes),
        (r"/API/routeIdList", routeIdList),
        (r"/API/tripIdList", tripIdList),
        # TODO: Replace(r"/API/serviceIds", serviceIds),

        (r"/API/commitExport", commitExport),
        (r"/API/pastCommits", pastCommits),
        #(r"/API/gtfsImportZip", gtfsImportZip),
        # TODO: Replace(r"/API/XMLUpload", XMLUpload),
        # TODO: Replace(r"/API/XMLDiagnose", XMLDiagnose),
        # TODO: Replace(r"/API/stations", stations),
        # TODO: Replace(r"/API/fareChartUpload", fareChartUpload),
        # TODO: Replace(r"/API/xml2GTFS", xml2GTFS),
        # TODO: Replace(r"/API/gtfsBlankSlate", gtfsBlankSlate),
        # TODO: Replace(r"/API/translations", translations),
        #TODO: REMOVE (r"/API/shapesList", shapesList),
        (r"/API/allShapesList", allShapesList),
        (r"/API/shape", shape),
        # TODO: Replace(r"/API/listAll", listAll),
        # TODO: Replace(r"/API/zoneIdList", zoneIdList),
        # TODO: Replace(r"/API/diagnoseID", diagnoseID),
        # TODO: Replace(r"/API/deleteByKey", deleteByKey),
        # TODO: Replace(r"/API/replaceID", replaceID),
        # TODO: Replace(r"/API/hydGTFS", hydGTFS),
        # TODO: RMOVE (r"/API/frequencies", frequencies),
        (r"/API/tableReadSave", tableReadSave),
        (r"/API/tableColumn", tableColumn),
        (r"/API/gtfs/shapes", gtfsshape),
        # New API Calls
        (r"/API/gtfs/agency", gtfsagency),
        (r"/API/gtfs/agency/list/id", gtfsagencylistids),
        (r"/API/gtfs/agency/list/idname", gtfsagencylistidnames),
        (r"/API/gtfs/agency/(.*)", gtfsagency),
        (r"/API/gtfs/stop", gtfsstops),
        (r"/API/gtfs/stop/list/id", gtfsstopslistids),
        (r"/API/gtfs/stop/list/idname", gtfsstoplistidnames),
        (r"/API/gtfs/stop/list/zoneid", gtfsstoplistzoneid),
        (r"/API/gtfs/stop/(.*)", gtfsstops),
        (r"/API/gtfs/route", gtfsroutes),
        (r"/API/gtfs/route/list/id", gtfsrouteslistids),
        (r"/API/gtfs/route/list/idname", gtfsrouteslistidnames),
        (r"/API/gtfs/route/(.*)", gtfsroutes),
        (r"/API/gtfs/calendar", gtfscalendar),
        (r"/API/gtfs/calendar/list/id", gtfscalendarlistids),
        (r"/API/gtfs/calendar/current", gtfscalendarcurrent),
        (r"/API/gtfs/calendar/(.*)", gtfscalendar),
        (r"/API/gtfs/calendar_dates", gtfscalendardates),
        (r"/API/gtfs/calendar_dates/list/id", gtfscalendardateslistids),
        (r"/API/gtfs/calendar_dates/(.*)", gtfscalendardates),
        (r"/API/gtfs/trips", gtfstrips),
        (r"/API/gtfs/trips/list/id", gtfstripslistids),
        (r"/API/gtfs/trips/route/(.*)", gtfstripsbyroute),
        (r"/API/gtfs/trips/(.*)", gtfstrips),
        (r"/API/gtfs/stoptimes", gtfsstoptimes),
        (r"/API/gtfs/stoptimes/(.*)", gtfsstoptimes), # Get stoptimes by trip_id
        (r"/API/gtfs/shape", gtfsshape),
        (r"/API/gtfs/shape/list/id", gtfsshapelistids),
        (r"/API/gtfs/shape/list/route/(.*)", gtfsshapeslistbyroute),
        (r"/API/gtfs/shape/(.*)", gtfsshape),
        (r"/API/defaultsequence/route/(.*)", defaultsequencebyroute),  # Custom defaultsequence api's
        (r"/API/defaultsequence/(.*)", defaultsequence),  # Custom defaultsequence api's
        (r"/API/gtfs/frequencies", gtfsfrequencies),
        (r"/API/gtfs/frequencies/list/id", gtfsfrequencieslistids),
        (r"/API/gtfs/frequencies/(.*)", gtfsfrequencies),
        (r"/API/gtfs/farerules", gtfsfarerules),
        (r"/API/gtfs/farerules/list/id", gtfsfareruleslistids),
        (r"/API/gtfs/farerules/pivoted", fareRulesPivoted),
        (r"/API/gtfs/farerules/(.*)", gtfsfarerules),
        (r"/API/gtfs/fareattributes", gtfsfareattributes),
        (r"/API/gtfs/fareattributes/list/id", gtfsfareattributeslistids),
        (r"/API/gtfs/fareattributes/(.*)", gtfsfareattributes),
        (r"/API/gtfs/translations", gtfstranlations),
        (r"/API/gtfs/translations/(.*)", gtfstranlations),
        (r"/API/gtfs/feedinfo", gtfsfeedinfo),
        (r"/API/gtfs/rename/listid", gtfsrenamelistAllids),
        (r"/API/gtfs/rename/(.*)", gtfsReplaceID),
        (r"/API/gtfs/delete/listid", gtfsdeletelistAllids),
        (r"/API/gtfs/delete/diagnose/(.*)", gtfsdeletediag),
        (r"/API/gtfs/delete/(.*)", gtfsdeleteByKey),
        (r"/API/app/database/krml/import/stations", krmlstations),
        (r"/API/app/database/krml/import/xml", krmlXMLUpload),
        (r"/API/app/database/krml/import/diagnose", krmlXMLDiagnose),
        (r"/API/app/database/krml/import/farechart", krmlfareChartUpload),
        (r"/API/app/database/krml/import", krmlxml2GTFS),
        (r"/API/app/database/hrml/import", hrmlhydGTFS),
        (r"/API/app/gtfs/validate", googlevalidate),
        (r"/API/app/gtfs/validate/reports", pastreportsgtfsvalidate),
        (r"/API/app/gtfs/validate/report/remove/(.*)", deletereportsgtfsvalidate),
        (r"/API/app/gtfs/validate/report/(.*)", getreportsgtfsvalidate),

        #(r"/API/idList", idList),
        (r"/export/(.*)", tornado.web.StaticFileHandler, {"path": exportFolder}),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": STATIC_ROOT, "default_filename": "index.html"})
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
