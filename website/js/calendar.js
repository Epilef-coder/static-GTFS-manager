//###################
// global variables
var service_id_list = [];

// note: constants moved to config/settings.js
// #########################################
// Function-variables to be used in tabulator
var GTFSDefinedColumnsCalendar = ["service_id","monday","tuesday","wednesday","thursday","friday","saturday","sunday","start_date","end_date"];
var GTFSDefinedColumnsDates = ["service_id","date","exception_type"];

const calendar_operationalChoices = {1:"1 - Operating on this day", 0:"0 - Not operating"};

var FastAddCalendar = `
<div class="btn-group dropup mr-2" role="group" id="FastAddGroup">
    <button id="btnGroupFastAdd" type="button" class="btn btn-secondary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" title="Fast add a calendar service">
      Fast Add
    </button>
    <div class="dropdown-menu" aria-labelledby="btnGroupFastAdd">
      <a class="dropdown-item" href="#" id="AddServiceFullweek" data-toggle="popover" data-trigger="hover" data-placement="top" data-html="false" data-content="Add a full week service">Full week</a>
	  <a class="dropdown-item" href="#" id="AddServiceWorkweek" data-toggle="popover" data-trigger="hover" data-placement="top" data-html="false" data-content="Add a work week service">Work week</a>
	  <a class="dropdown-item" href="#" id="AddServiceWeekend" data-toggle="popover" data-trigger="hover" data-placement="top" data-html="false" data-content="Add a weekend service">Weekend</a>
	  <a class="dropdown-item" href="#" id="AddServiceSaterday" data-toggle="popover" data-trigger="hover" data-placement="top" data-html="false" data-content="Add a Saterday only service">Saterday Only</a>
	  <a class="dropdown-item" href="#" id="AddServiceSunday" data-toggle="popover" data-trigger="hover" data-placement="top" data-html="false" data-content="Add a Sunday only service">Sunday Only</a>
    </div>
</div>`;

var footerHTML = DefaultTableFooter;
const saveButtoncalendarDates = "<button id='saveCalendarDatesButton' class='btn btn-outline-primary' disabled>Save Calendar_Dates Changes</button>"
footerHTMLcalendarDates = footerHTML.replace('{SaveButton}', saveButtoncalendarDates);
footerHTMLcalendarDates = footerHTMLcalendarDates.replace('{FastAdd}','');
footerHTMLcalendarDates = footerHTMLcalendarDates.replace('NumberofRows','NumberofRowsCalendarDates');

const saveButtoncalendar = '<button id="saveCalendarButton" class="btn btn-outline-primary" disabled>Save Calendar Changes</button>';
footerHTMLcalendar = footerHTML.replace('{SaveButton}', saveButtoncalendar);
footerHTMLcalendar = footerHTMLcalendar.replace('{FastAdd}',FastAddCalendar);
footerHTMLcalendar = footerHTMLcalendar.replace('{NumberofRows}',FastAddCalendar);
// To workaround double footer menu's in onepage.
// Menu id
footerHTMLcalendar = footerHTMLcalendar.replace('btnGroupDrop1','btnGroupDrop1Calendar');
footerHTMLcalendar = footerHTMLcalendar.replace('btnGroupDrop2','btnGroupDrop2Calendar');
// Menu insertings ID's
footerHTMLcalendar = footerHTMLcalendar.replace('SelectColumnsMenu','SelectColumnsMenuCalendar');
footerHTMLcalendar = footerHTMLcalendar.replace('DownloadsMenu','DownloadsMenuCalendar');
footerHTMLcalendar = footerHTMLcalendar.replace('NumberofRows','NumberofRowsService');

// Menu insertings ID's
footerHTMLcalendar = footerHTMLcalendar.replace('LinkAddColumn','LinkAddColumnCalendar');
footerHTMLcalendar = footerHTMLcalendar.replace('LinkDeleteColumn','LinkDeleteColumnCalendar');
footerHTMLcalendar = footerHTMLcalendar.replace('LinkShowHideColumn','LinkShowHideColumnCalendar');


//####################
// Tabulator tables
var service = new Tabulator("#calendar-table", {
	selectable:0,
	index: 'service_id',
	movableRows: true,
	history:true,
	addRowPos: "top",
	height:400,
	movableColumns: true,
	layout: "fitColumns", //fit columns to width of table (optional)
	ajaxURL: `${APIpath}gtfs/calendar`, //ajax URL
	ajaxLoaderLoading: loaderHTML,
	footerElement: footerHTMLcalendar,
	columns:[
		{rowHandle:true, formatter:"handle", headerSort:false, frozen:true, width:30, minWidth:30 },
		{title:"service_id", field:"service_id", frozen:true, headerFilter:"input", headerFilterPlaceholder:"filter by id",validator:"unique" },
		{title:"monday", field:"monday", editor:"select", editorParams:{values:calendar_operationalChoices}, headerSort:false },
		{title:"tuesday", field:"tuesday", editor:"select", editorParams:{values:calendar_operationalChoices}, headerSort:false },
		{title:"wednesday", field:"wednesday", editor:"select", editorParams:{values:calendar_operationalChoices}, headerSort:false },
		{title:"thursday", field:"thursday", editor:"select", editorParams:{values:calendar_operationalChoices}, headerSort:false },
		{title:"friday", field:"friday", editor:"select", editorParams:{values:calendar_operationalChoices}, headerSort:false },
		{title:"saturday", field:"saturday", editor:"select", editorParams:{values:calendar_operationalChoices}, headerSort:false },
		{title:"sunday", field:"sunday", editor:"select", editorParams:{values:calendar_operationalChoices}, headerSort:false },
		{title:"start_date", field:"start_date", editor:"input", headerFilter:"input", headerFilterPlaceholder:"yyyymmdd" },
		{title:"end_date", field:"end_date", editor:"input", headerFilter:"input", headerFilterPlaceholder:"yyyymmdd" }		
	],
	ajaxError:function(xhr, textStatus, errorThrown){
		console.log('GET request to calendar failed.  Returned status of: ' + errorThrown);
	},
	dataEdited:function(data){
		$('#saveCalendarButton').removeClass().addClass('btn btn-primary');
		$('#saveCalendarButton').prop('disabled', false);
	},
	rowUpdated:function(row){
		// The rowUpdated callback is triggered when a row is updated by the updateRow, updateOrAddRow, updateData or updateOrAddData, functions.
		$('#saveCalendarButton').removeClass().addClass('btn btn-primary');
		$('#saveCalendarButton').prop('disabled', false);	
	},	
	dataLoaded:function(data){
		// parse the first row keys if data exists.
		if (data.length > 0) {
			AddExtraColumns(Object.keys(data[0]), GTFSDefinedColumnsCalendar, service);
		}
		else {
			console.log("No data so no columns");
		}
		var NumberofRows = data.length + ' rows';
		$("#NumberofRowsService").html(NumberofRows);
	}
});

var calendarDates = new Tabulator("#calendar-dates-table", {
	selectable:0,
	index: 'service_id',
	movableRows: true,
	history:true,
	addRowPos: "top",
	height:400,
	movableColumns: true,
	layout:"fitDataFill",
	footerElement: footerHTMLcalendarDates,
	ajaxURL: `${APIpath}gtfs/calendar_dates`, //ajax URL
	ajaxLoaderLoading: loaderHTML,
	columns:[
		{rowHandle:true, formatter:"handle", headerSort:false, frozen:true, width:30, minWidth:30 },
		{title:"service_id", field:"service_id", frozen:true, headerFilter:"input", headerFilterPlaceholder:"filter by id", validator:tabulator_UID_leastchars },
		{title:"date", field:"date", editor:"input", headerFilter:"input", headerFilterPlaceholder:"yyyymmdd", width: 150 },
		{title:"exception_type", field:"exception_type", editor:"select", editorParams:{ values: {1:"1 - Operating on this day", 0:"0 - Not operating"}}, headerFilter:"input", headerTooltip: "indicates whether service is available on the date specified in the date field."  }
	],
	ajaxError:function(xhr, textStatus, errorThrown){
		console.log('GET request to calendar_dates failed.  Returned status of: ' + errorThrown);
	},
	dataEdited:function(data){
		$('#saveCalendarDatesButton').removeClass().addClass('btn btn-primary');
		$('#saveCalendarDatesButton').prop('disabled', false);
	},
	rowUpdated:function(row){
		// The rowUpdated callback is triggered when a row is updated by the updateRow, updateOrAddRow, updateData or updateOrAddData, functions.
		$('#saveCalendarDatesButton').removeClass().addClass('btn btn-primary');
		$('#saveCalendarDatesButton').prop('disabled', false);
	},	
	dataLoaded:function(data){
		// parse the first row keys if data exists.
		if (data.length > 0) {
			AddExtraColumns(Object.keys(data[0]), GTFSDefinedColumnsDates, calendarDates);
		}
		else {
			console.log("No data so no columns");
		}
		var NumberofRows = data.length + ' rows';
		$("#NumberofRowsCalendarDates").html(NumberofRows);
	}
});

// ###################
// commands to run on page load
$(document).ready(function() {
	// executes when HTML-Document is loaded and DOM is ready
	// Hide columns logic:	
	var DownloadContent = "";
	DownloadLinks.forEach(function(downloadtype) {
		DownloadContent += '<a class="dropdown-item" href="#" id="LinkDownload'+downloadtype+'">Download '+downloadtype+'</a>';		                
	});
	$("#DownloadsMenu").html(DownloadContent);
	var DownloadContent = "";
	DownloadLinks.forEach(function(downloadtype) {
		DownloadContent += '<a class="dropdown-item" href="#" id="LinkDownloadCalendar'+downloadtype+'">Download '+downloadtype+'</a>';		                
	});
	$("#DownloadsMenuCalendar").html(DownloadContent);
});

// Toggles for show hide columns in stop table.

$(document).on("click", "#LinkAddColumnCalendar", function () {
	addColumntoTable(service);
});

$(document).on("click", "#LinkDeleteColumnCalendar", function () {
	RemoveExtraColumns(service, GTFSDefinedColumnsCalendar, 'service');
});

$(document).on("click", "#LinkShowHideColumnCalendar", function () {
	ShowHideColumn(service, 'service');
});

$(document).on("click", "#DeleteColumnButton", function () {
	SelectTableForDeleteExtraColumns();
});

$(document).on("click", "#LinkAddColumn", function () {
	addColumntoTable(calendarDates);
});

$(document).on("click", "#LinkDeleteColumn", function () {
	RemoveExtraColumns(calendarDates, GTFSDefinedColumnsDates, 'calendarDates');
});

$(document).on("click", "#LinkShowHideColumn", function () {
	ShowHideColumn(calendarDates,'calendar_dates');
});

$('body').on('change', 'input[id^="check"]', function() {
	var column = this.id.replace('check','');
	if (this.value == 'calendar_dates' ){
		if(this.checked) {		
			calendarDates.showColumn(column);
			calendarDates.redraw();
		}
		else {		
			calendarDates.hideColumn(column);
			calendarDates.redraw();		
		}
	}
	else {
		if(this.checked) {		
			service.showColumn(column);
			service.redraw();
		}
		else {		
			service.hideColumn(column);
			service.redraw();
		
		}
	}
});

$(document).on("click","#LinkDownloadCSV", function () {
	calendarDates.download("csv", "calendar_dates.csv");
});

$(document).on("click","#LinkDownloadJSON", function () {
	calendarDates.download("json", "calendar_dates.json");
});

$(document).on("click","#LinkDownloadCalendarCSV", function () {
	service.download("csv", "calendar.csv");
});

$(document).on("click","#LinkDownloadCalendarJSON", function () {
	service.download("json", "calendar.json");
});

// Quick Adds:

$("#AddServiceFullweek").on("click", function(){	
	var filteredEvents = service.getData().filter(function(service){
		return service.service_id == 'FULLWEEK';
	});
	if (filteredEvents.length == 0) {
		// Gernerate a start and enddate
		var rightNow = new Date();
		ydm = rightNow.toISOString().slice(0, 10).replace(/-/g, '');
		rightNowPlus1Year = rightNow.setFullYear(rightNow.getFullYear() + 1);
		ydmplusone = rightNow.toISOString().slice(0, 10).replace(/-/g, '');
		service.addRow([{ 'service_id': 'FULLWEEK', 'monday': 1, tuesday: 1, wednesday: 1, thursday: 1, friday: 1, saturday: 1, sunday: 1, start_date: ydm, end_date: ydmplusone }]);
	}
	else {
		$.toast({
			title: 'Fast Add',
			subtitle: 'Full Week',
			content: 'There is already a service with the service_id FULLWEEK',
			type: 'error',
			delay: 3000
		});
	}	
});

$("#AddServiceWorkweek").on("click", function(){
	var filteredEvents = service.getData().filter(function(service){
		return service.service_id == 'WORKWEEK';
	});
	if (filteredEvents.length == 0) {
		var rightNow = new Date();
		ydm = rightNow.toISOString().slice(0, 10).replace(/-/g, '');
		rightNowPlus1Year = rightNow.setFullYear(rightNow.getFullYear() + 1);
		ydmplusone = rightNow.toISOString().slice(0, 10).replace(/-/g, '');
		service.addRow([{ 'service_id': 'WORKWEEK', 'monday': 1, tuesday: 1, wednesday: 1, thursday: 1, friday: 1, saturday: 0, sunday: 0, start_date: ydm, end_date: ydmplusone }]);
	}
	else {
		$.toast({
			title: 'Fast Add',
			subtitle: 'Work Week',
			content: 'There is already a service with the service_id WORKWEEK',
			type: 'error',
			delay: 3000
		});
	}	
});

$("#AddServiceWeekend").on("click", function(){
	var filteredEvents = service.getData().filter(function(service){
		return service.service_id == 'WEEKEND';
	});
	if (filteredEvents.length == 0) {
		var rightNow = new Date();
		ydm = rightNow.toISOString().slice(0, 10).replace(/-/g, '');
		rightNowPlus1Year = rightNow.setFullYear(rightNow.getFullYear() + 1);
		ydmplusone = rightNow.toISOString().slice(0, 10).replace(/-/g, '');
		service.addRow([{ 'service_id': 'WEEKEND', 'monday': 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0, saturday: 1, sunday: 1, start_date: ydm, end_date: ydmplusone }]);
	}
	else {
		$.toast({
			title: 'Fast Add',
			subtitle: 'Weekend',
			content: 'There is already a service with the service_id WEEKEND',
			type: 'error',
			delay: 3000
		});
	}	
});

$("#AddServiceSaterday").on("click", function(){
	var filteredEvents = service.getData().filter(function(service){
		return service.service_id == 'SATERDAY';
	});
	if (filteredEvents.length == 0) {
		var rightNow = new Date();
		ydm = rightNow.toISOString().slice(0, 10).replace(/-/g, '');
		rightNowPlus1Year = rightNow.setFullYear(rightNow.getFullYear() + 1);
		ydmplusone = rightNow.toISOString().slice(0, 10).replace(/-/g, '');
		service.addRow([{ 'service_id': 'SATERDAY', 'monday': 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0, saturday: 1, sunday: 0, start_date: ydm, end_date: ydmplusone }]);
	}
	else {
		$.toast({
			title: 'Fast Add',
			subtitle: 'Saterday',
			content: 'There is already a service with the service_id SATERDAY',
			type: 'error',
			delay: 3000
		});
	}	
});

$("#AddServiceSunday").on("click", function(){
	var filteredEvents = service.getData().filter(function(service){
		return service.service_id == 'SUNDAY';
	});
	if (filteredEvents.length == 0) {
		var rightNow = new Date();
		ydm = rightNow.toISOString().slice(0, 10).replace(/-/g, '');
		rightNowPlus1Year = rightNow.setFullYear(rightNow.getFullYear() + 1);
		ydmplusone = rightNow.toISOString().slice(0, 10).replace(/-/g, '');
		service.addRow([{ 'service_id': 'SUNDAY', 'monday': 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0, saturday: 0, sunday: 1, start_date: ydm, end_date: ydmplusone }]);
	}
	else {
		$.toast({
			title: 'Fast Add',
			subtitle: 'Sunday',
			content: 'There is already a service with the service_id SUNDAY',
			type: 'error',
			delay: 3000
		});
	}	
});


// #########################
// Buttons

$("#saveCalendarButton").on("click", function(){
	saveCalendar();
});

$("#calendar2add").bind("change keyup", function(){
	if(CAPSLOCK) this.value=this.value.toUpperCase();
});


$('#addCalendarButton').on('click', function(){
	addCalendar(service, $("#calendar2add").val(),'service');
});

// ############################
// 23.10.18: Calendar_dates:

$('#addCalendarDatesButton').on('click', function(){
	addCalendar(calendarDates, $("#calendarDates2add").val(),'');
});

// #########################
// Functions

function saveCalendar() {	
	$.toast({
		title: 'Save Calendar',
		subtitle: 'Sending data',
		content: 'Sending data, please wait...',
		type: 'info',
		delay: 1000
	});
	var data = service.getData();
	
	var pw = $("#password").val();
	if ( ! pw ) { 		
		$.toast({
			title: 'Save Calendar',
			subtitle: 'No password provided.',
			content: 'Please enter the password.',
			type: 'error',
			delay: 5000
		});
		shakeIt('password'); return;
	}
	console.log('sending calendar data to server via POST');
	// sending POST request using native JS. From https://blog.garstasio.com/you-dont-need-jquery/ajax/#posting
	var xhr = new XMLHttpRequest();
	xhr.open('POST', `${APIpath}gtfs/calendar?pw=${pw}`);
	xhr.withCredentials = true;
	xhr.setRequestHeader('Content-Type', 'application/json; charset=utf-8');
	xhr.onload = function () {
		if (xhr.status === 200) {
			console.log('<span class="alert alert-success">Successfully sent data via POST to server /API/gtfs/calendar, response received: ' + xhr.responseText + '</span>');
			$.toast({
				title: 'Save Calendar',
				subtitle: 'Success',
				content: xhr.responseText,
				type: 'success',
				delay: 5000
			});
			
		} else {
			console.log('Server POST request to API/gtfs/calendar failed. Returned status of ' + xhr.status + ', reponse: ' + xhr.responseText );
			$.toast({
				title: 'Save Calendar',
				subtitle: 'Error',
				content: xhr.responseText,
				type: 'error',
				delay: 5000
			});			
		}
	}
	xhr.send(JSON.stringify(data)); // this is where POST differs from GET : we can send a payload instead of just url arguments.
}

function addCalendar(tablename, inputvalue, table) {
	var data = tablename.getData();
	var service_id = inputvalue.replace(/[ `,]/g, "");
	
	if(! service_id.length) {
		$.toast({
			title: 'Add Calendar or Service',
			subtitle: 'Error',
			content: 'Give a valid id please.',
			type: 'error',
			delay: 5000
		});			
		return;
	}
	
	var service_id_list = data.map(a => a.service_id);
	var isPresent = service_id_list.indexOf(service_id) > -1;
	if(table=="service" && isPresent) {
		// 17.4.19 made the unique-only condition only for calendar table and not calendar-dates.
		$.toast({
			title: 'Add Calendar',
			subtitle: 'Error',
			content: 'Sorry, ' + service_id + ' is already taken. Please try another value.',
			type: 'error',
			delay: 5000
		});			
	} else {		
			tablename.addRow([{ 'service_id': service_id }]);		
	}
}

$("#saveCalendarDatesButton").on("click", function(){
	$.toast({
		title: 'Save Calendar dates',
		subtitle: 'Sending data',
		content: 'Sending data, please wait...',
		type: 'info',
		delay: 1000
	});	
	var data = calendarDates.getData();
	
	var pw = $("#password").val();
	if ( ! pw ) { 
		$.toast({
			title: 'Save Calendar',
			subtitle: 'No password provided.',
			content: 'Please enter the password.',
			type: 'error',
			delay: 5000
		});
		shakeIt('password'); return;
	}

	console.log('sending calendarDates data to server via POST');
	// sending POST request using native JS. From https://blog.garstasio.com/you-dont-need-jquery/ajax/#posting
	var xhr = new XMLHttpRequest();
	xhr.open('POST', `${APIpath}gtfs/calendar_dates?pw=${pw}`);
	xhr.withCredentials = true;
	xhr.setRequestHeader('Content-Type', 'application/json; charset=utf-8');
	xhr.onload = function () {
		if (xhr.status === 200) {
			console.log('<span class="alert alert-success">Successfully sent data via POST to server /API/gtfs/calendar_dates, response received: ' + xhr.responseText + '</span>');
			$.toast({
				title: 'Save Calendar dates',
				subtitle: 'Success',
				content: xhr.responseText,
				type: 'success',
				delay: 5000
			});
		} else {
			console.log('Server POST request to API/gtfs/calendar_dates failed. Returned status of ' + xhr.status + ', reponse: ' + xhr.responseText );
			$.toast({
				title: 'Save Calendar dates',
				subtitle: 'Error',
				content: xhr.responseText,
				type: 'error',
				delay: 5000
			});			
		}
	}
	xhr.send(JSON.stringify(data)); // this is where POST differs from GET : we can send a payload instead of just url arguments.
	
});