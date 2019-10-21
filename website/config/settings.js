const APIpath = 'API/';
const VERSION = 'v3.4.3';

var cfg = {};
// Pure javascript because jquery is not loaded yet.
var xmlhttp = new XMLHttpRequest();
xmlhttp.open('GET', APIpath + 'app/config', true);
xmlhttp.onreadystatechange = function() {
    if (xmlhttp.readyState == 4) {
        if(xmlhttp.status == 200) {
            cfg = JSON.parse(xmlhttp.responseText);            
		 }
		 else {
			 console.log('Error Loading settings...');
			 alert('Error Loading settings, loaded fallback settings!');
			 cfg = {"GOOGLEAPI":"","MAPBOXAPI":"","MapProviders":[{"id":"OpenStreetMap.Mapnik","name":"OpenStreetMap.Mapnik","variant":"","apikey":"","default":true}],"GTFS":{"Timezone":"America/Bogota","Currency":"COP"}, "APP":{WideScreen:false}}
		 }	 
		 
    }
};
xmlhttp.send(null);

// from commonfuncs.js

// this flag tells whether it is mandatory for all UIDs to be in capitals or not.
const CAPSLOCK = false;

// const route_type_options = {0:"0-Tram, Streetcar, Light rail", 1:"1-Subway, Metro", 2:"2-Rail", 3:"3-Bus",4:"4-Ferry", 1100:"1100-Air Service",  };
// //const route_type_lookup = {0:"Tram, Streetcar, Light rail", 1:"Subway, Metro", 2:"Rail", 3:"Bus",4:"Ferry" };
// const route_type_lookup = route_type_options;

// this json holds the different pages. If you want to add/remove/rename a page, do so here.
const menu = {
	"Home": "index.html",
	"GTFS": {
		"Agency": "agency.html",
		"Stops": "stops.html",
		"Routes": "routes.html",
		"Calendar": "calendar.html",
		"Trips, Stop_times": "tripstimings.html",
		"Frequencies": "frequencies.html",
		"Fares": "fares.html",
		"Shapes": "shapes.html",
		"Translations": "translations.html",
		"Feed Info": "feedinfo.html",
		"Validate GTFS": "validate.html"
	},
	"Tools": {
		// to do: bulk action pages, diagnostic pages etc
		"Default Route Sequence": "sequence.html",
		"Rename ID": "renameID.html",
		"Delete ID": "deleteID.html"		
	},
	"Data": {
		//"Import / Export GTFS": "gtfs.html",
		"Import KMRL format": "kmrl.html",
		"Import HMRL format": "hmrl.html",
		"Import Stops CSV": "import-stops.html",
		"Import Stops KML/GeoJson": "import-stops-kml.html",
		"Import Stops Openstreetmap": "import-stops-osm.html"
	},
	"Config": "config.html"
}
// Default timezone used in the application.

// default table footer
var DownloadLinks = ["CSV","JSON"];
const DefaultTableFooter = `<div class="btn-toolbar justify-content-between" role="toolbar" aria-label="Toolbar with button groups">
<div class="btn-toolbar">
<div class="btn-group dropup" role="group" id="SelectionButtons">
		<button id="btnGroupDrop3" type="button" class="btn btn-secondary dropdown-toggle mx-1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" title="Config columns">
			<i class="fas fa-cogs"></i>	
		</button>
		<div class="dropdown-menu" aria-labelledby="btnGroupDrop3" id="SelectConfigMenu">
			<a class="dropdown-item" href="#" id="LinkAddColumn">Add Column</a>
			<a class="dropdown-item" href="#" id="LinkDeleteColumn">Delete Column</a>
			<a class="dropdown-item" href="#" id="LinkShowHideColumn">Show / Hide Column</a>
		</div>
	</div>	
	<div class="btn-group dropup mr-2" role="group" id="DownloadButtons">
		<button id="btnGroupDrop2" type="button" class="btn btn-secondary dropdown-toggle mx-1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" title="Download the content of the table">
			Download
		</button>
		<div class="dropdown-menu" aria-labelledby="btnGroupDrop2" id="DownloadsMenu"></div>
	</div>
	{FastAdd}
</div>
<div class="btn-group"><div id="NumberofRows"></div></div>
<div class="btn-group" role="group" aria-label="Save Button" id="SaveButtonPosition">{SaveButton}</div>
</div>`;


// loader:
const loaderHTML = '<div class="spinner-border text-danger" role="status"><span class="sr-only">Loading...</span></div>';

// from stops.js
const UID_leastchars = 2;
const tabulator_UID_leastchars = "minLength:2";
const UID_maxchars = 20;
const MARKERSLIMIT = 100;

// from tripstimings.js , formerly schedules.js
// const wheelchairOptions = {"":"blank-No info", 1:"1-Yes", 2:"2-No"};
// const wheelchairOptionsFormat = {"":"", 1:"1 (Yes)", 2:"2 (No)"};
// const bikesAllowedOptions = {'':"blank-No info", 1:"1-Yes", 2:"2-No"};
// const bikesAllowedOptionsFormat = {"":"", 1:"1 (Yes)", 2:"2 (No)"};

// from calendar.js:
// const calendar_operationalChoices = {1:"1 - Operating on this day", 0:"0 - Not operating"};
// const calendar_exception_type_choices = {1:"1 - service is LIVE on this date", 2:"2 - Service is DISABLED on this date"};


// Leaflet Map related
