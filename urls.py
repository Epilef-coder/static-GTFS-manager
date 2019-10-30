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
        (r"/API/app/config", AppConfig),
        (r"/API/app/stats", Appstats),
        (r"/API/app/database/blank",AppDatabaseBlank),
        (r"/API/app/database/gtfs/import",AppDatabaseGTFSImport),
        # TODO: REMOVE (r"/API/allStops", allStops),
        # TODO: REMOVE (r"/API/allStopsKeyed", allStopsKeyed),
        # TODO: REMOVE  (r"/API/routes", routes),
        # TODO: REMOVE (r"/API/fareAttributes", fareAttributes),
        # TODO: REMOVE (r"/API/fareRulesPivoted", fareRulesPivoted),
        # TODO: REMOVE (r"/API/agency", agency),
        # TODO: REMOVE (r"/API/calendar", calendar),
        # TODO: REMOVE (r"/API/sequence", sequence),
        # TODO: REMOVE (r"/API/trips", trips),
        # TODO: REMOVE (r"/API/stopTimes", stopTimes),
        # TODO: REMOVE (r"/API/routeIdList", routeIdList),
        # TODO: REMOVE (r"/API/tripIdList", tripIdList),
        # TODO: REMOVE (r"/API/serviceIds", serviceIds),

        (r"/API/commitExport", commitExport),
        (r"/API/pastCommits", pastCommits),
        # TODO: REMOVE (r"/API/gtfsImportZip", gtfsImportZip),
        # TODO: REMOVE (r"/API/XMLUpload", XMLUpload),
        # TODO: REMOVE (r"/API/XMLDiagnose", XMLDiagnose),
        # TODO: REMOVE (r"/API/stations", stations),
        # TODO: REMOVE (r"/API/fareChartUpload", fareChartUpload),
        # TODO: REMOVE (r"/API/xml2GTFS", xml2GTFS),
        # TODO: REMOVE e(r"/API/gtfsBlankSlate", gtfsBlankSlate),
        # TODO: REMOVE (r"/API/translations", translations),
        # TODO: REMOVE (r"/API/shapesList", shapesList),
        # TODO: REMOVE (r"/API/allShapesList", allShapesList),
        # TODO: REMOVE (r"/API/shape", shape),
        # TODO: Replace(r"/API/listAll", listAll),
        # TODO: Replace(r"/API/zoneIdList", zoneIdList),
        # TODO: Replace(r"/API/diagnoseID", diagnoseID),
        # TODO: Replace(r"/API/deleteByKey", deleteByKey),
        # TODO: Replace(r"/API/replaceID", replaceID),
        # TODO: Replace(r"/API/hydGTFS", hydGTFS),
        # TODO: RMOVE (r"/API/frequencies", frequencies),
        # TODO: REMOVE (r"/API/tableReadSave", tableReadSave),
        # TODO: REMOVE (r"/API/tableColumn", tableColumn),
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
        (r"/API/gtfs/trips/list/tripswithstoptimes/(.*)", gtfstripslisttripswithstoptimes),
        (r"/API/gtfs/trips/route/(.*)", gtfstripsbyroute),
        (r"/API/gtfs/trips/(.*)", gtfstrips),
        (r"/API/gtfs/stoptimes", gtfsstoptimes),
        (r"/API/gtfs/stoptimes/(.*)", gtfsstoptimes), # Get stoptimes by trip_id
        (r"/API/gtfs/shape", gtfsshape),
        (r"/API/gtfs/shape/list/id", gtfsshapelistids),
        (r"/API/gtfs/shape/list/all", allShapesList),
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
        # Allow access to the exportfolder.
        (r"/export/(.*)", tornado.web.StaticFileHandler, {"path": exportFolder}),
        # Pass it to e default staticfilehandler.
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": STATIC_ROOT, "default_filename": "index.html"})
    ]