// #########################################
// Function-variables to be used in tabulator

var GTFSDefinedColumns = ["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang", "agency_phone", "agency_fare_url", "agency_email"];

var footerHTML = DefaultTableFooter;
const saveButton = `<button id='saveAgencyButton' class='btn btn-outline-primary' disabled>Save Agency Changes</button>`;
footerHTML = footerHTML.replace('{SaveButton}', saveButton);
footerHTML = footerHTML.replace('{FastAdd}', '');
//####################
// Tabulator tables

var table = new Tabulator("#agency-table", {
	selectable: 0,
	index: 'agency_id',
	persistenceID:"GTFS_agency", //id string, can only be numbers, letters, hyphens and underscores.
	persistentLayout:true,
	persistenceMode:true,
	movableRows: true,
	history: true,
	addRowPos: "top",
	movableColumns: true,
	layout: "fitColumns",
	ajaxURL: `${APIpath}gtfs/agency`, //ajax URL
	ajaxLoaderLoading: loaderHTML,
	placeholder: "No Data Available",
	footerElement: footerHTML,
	columns: [
		{ rowHandle: true, formatter: "handle", headerSort: false, frozen: true, width: 30, minWidth: 30, download: true },
		{ title: "agency_id", field: "agency_id", editor: "input", headerSort: false, validator: tabulator_UID_leastchars, download: true },
		{ title: "agency_name", field: "agency_name", editor: "input", headerSort: false, download: true },
		{ title: "agency_url", field: "agency_url", editor: "input", headerSort: false, download: true },
		{ title: "agency_timezone", field: "agency_timezone", editor: select2TZEditor, width: 300, headerSort: false, download: true },
		{ title: "agency_lang", field: "agency_lang", editor: select2LanguageEditor, headerSort: false, download: true, visible: false },
		{ title: "agency_phone", field: "agency_phone", editor: "input", headerSort: false, download: true, visible: false },
		{ title: "agency_fare_url", field: "agency_fare_url", editor: "input", headerSort: false, download: true, visible: false },
		{ title: "agency_email", field: "agency_email", editor: "input", headerSort: false, download: true, visible: false }
	],
	ajaxError: function (xhr, textStatus, errorThrown) {
		console.log('GET request to agency failed.  Returned status of: ' + errorThrown);
	},
	dataEdited: function (data) {
		// The dataEdited callback is triggered whenever the table data is changed by the user. Triggers for this include editing any cell in the table, adding a row and deleting a row.
		$('#saveAgencyButton').removeClass().addClass('btn btn-primary');
		$('#saveAgencyButton').prop('disabled', false);
	},
	rowUpdated:function(row){
		// The rowUpdated callback is triggered when a row is updated by the updateRow, updateOrAddRow, updateData or updateOrAddData, functions.
		$('#saveAgencyButton').removeClass().addClass('btn btn-primary');
		$('#saveAgencyButton').prop('disabled', false);
	},
	dataLoaded: function (data) {
		// parse the first row keys if data exists.
		if (data.length > 0) {
			AddExtraColumns(Object.keys(data[0]), GTFSDefinedColumns, table);			
		}
		else {
			console.log("No data so no columns");
		}
		var NumberofRows = data.length + ' row(s)';
		$("#NumberofRows").html(NumberofRows);
	}
});


// Toggles for show hide columns in table.
$('body').on('change', 'input[id^="check"]', function () {
	var column = this.id.replace('check', '');
	if (this.checked) {
		table.showColumn(column);
		table.redraw();
	}
	else {
		table.hideColumn(column);
		table.redraw();
	}
});

$(document).on("click", "#LinkDownloadCSV", function () {
	table.download("csv", "agency.csv");
});

$(document).on("click", "#LinkDownloadJSON", function () {
	table.download("json", "agency.json");
});

$(document).on("click", "#LinkAddColumn", function () {
	addColumntoTable(table);
});

$(document).on("click", "#LinkDeleteColumn", function () {
	RemoveExtraColumns(table, GTFSDefinedColumns, 'table');
});

$(document).on("click", "#DeleteColumnButton", function () {
	DeleteExtraColumns(table);
});
$(document).on("click", "#LinkShowHideColumn", function () {
	ShowHideColumn(table);
});

// ###################
// commands to run on page load
$(document).ready(function () {
	// executes when HTML-Document is loaded and DOM is ready
	$("#agency_timezone").select2({
		placeholder: "Select a timezone",
		allowClear: true,
		theme: 'bootstrap4',
		data: TimeZoneList
	});
	// Set the default timezone from the settings.js file.
	$("#agency_timezone").val(cfg.GTFS.Timezone).trigger("change");

	$("#agency_lang").select2({
		placeholder: "Select a language",
		allowClear: true,
		theme: 'bootstrap4',
		data: LanguageList
	});
	// Set the default timezone from the settings.js file.
	$("#agency_lang").val(cfg.GTFS.Language).trigger("change");

	var DownloadContent = "";
	DownloadLinks.forEach(function (downloadtype) {
		DownloadContent += '<a class="dropdown-item" href="#" id="LinkDownload' + downloadtype + '">Download ' + downloadtype + '</a>';
	});
	$("#DownloadsMenu").html(DownloadContent);
});

// #########################
// Buttons

$('#saveAgencyButton').on('click', function () {
	saveAgency();
});

$('#addAgencyButton').on('click', function () {
	// First validate the form!
	var $form = $('#Form-AddAgency');
	$form.parsley({
		errorClass: 'has-danger',
		successClass: 'has-success',
		classHandler: function (ParsleyField) {
			return ParsleyField.$element.closest('.form-group');
		},
		errorsContainer: function (ParsleyField) {
			return ParsleyField.$element.closest('.form-group');
		},
		errorsWrapper: '<span class="form-text text-danger"></span>',
		errorTemplate: '<span></span>'
	}).validate()
	if ($form.parsley().validate()) {
		// Process adding the value
		addAgency();
	}
});

$("#agency_id").bind("change keyup", function () {
	if (CAPSLOCK) this.value = this.value.toUpperCase();
});


// #########################
// Functions

function saveAgency() {
	var pw = $("#password").val();
	if (!pw) {
		$.toast({
			title: 'Save Route',
			subtitle: 'No password provided.',
			content: 'Please enter the password.',
			type: 'error',
			delay: 5000
		});
		shakeIt('password'); return;
	}
	$.toast({
		title: 'Save Agency',
		subtitle: 'Saving',
		content: 'Sending data to server.. please wait..',
		type: 'info',
		delay: 5000
	});


	var data = table.getData();
	console.log(data);
	console.log('sending to server via POST');
	// sending POST request using native JS. From https://blog.garstasio.com/you-dont-need-jquery/ajax/#posting
	var xhr = new XMLHttpRequest();
	xhr.open('POST', `${APIpath}gtfs/agency?pw=${pw}`);
	xhr.withCredentials = true;
	xhr.setRequestHeader('Content-Type', 'application/json; charset=utf-8');
	xhr.onload = function () {
		if (xhr.status === 200) {
			console.log('Successfully sent data via POST to server API/tableReadSave table=agency, response received: ' + xhr.responseText);
			$.toast({
				title: 'Save Agency',
				subtitle: 'Success',
				content: xhr.responseText,
				type: 'success',
				delay: 5000
			});
			$('#saveAgencyButton').removeClass().addClass('btn btn-outline-primary');
			$('#saveAgencyButton').prop('disabled', true);
			//$('#agencySaveStatus').html('<span class="alert alert-success">Success. Message: ' + xhr.responseText + '</span>');
		} else {
			console.log('Server POST request to API/tableReadSave table=agency failed. Returned status of ' + xhr.status + ', reponse: ' + xhr.responseText);
			$.toast({
				title: 'Save Agency',
				subtitle: 'Failed to save',
				content: xhr.responseText,
				type: 'error',
				delay: 5000
			});
			//$('#agencySaveStatus').html('<span class="alert alert-danger">Failed to save. Message: ' + xhr.responseText+'</span>');
		}
	}
	xhr.send(JSON.stringify(data)); // this is where POST differs from GET : we can send a payload instead of just url arguments.
}

function addAgency() {
	var data = table.getData();
	var agency_id = $('#agency_id').val().toUpperCase().replace(/[^A-Z0-9-_]/g, "");
	var agency_name = $('#agency_name').val();
	var agency_url = $('#agency_url').val();
	var agency_timezone = $('#agency_timezone').select2().val();
	var agency_lang = $('#agency_url').val();
	var agency_phone = $('#agency_phone').val();
	var agency_fare_url = $('#agency_fare_url').val();
	var agency_email = $('#agency_email').val();

	$('#agency_id').val(agency_id);
	if (!agency_id.length) {
		$.toast({
			title: 'Add Agency',
			subtitle: 'Failed to Add',
			content: 'Give a valid id please.',
			type: 'error',
			delay: 5000
		});
		//$('#agencyAddStatus').html('<span class="alert alert-warning">Give a valid id please.</span>');
		return;

	}

	var agency_id_list = data.map(a => a.agency_id);
	var isPresent = agency_id_list.indexOf(agency_id) > -1;
	if (isPresent) {
		//$('#agencyAddStatus').html('<span class="alert alert-danger">' + agency_id + ' is already there.</span>');
		$.toast({
			title: 'Add Agency',
			subtitle: 'Failed to Add',
			content: agency_id + ' is already there.',
			type: 'error',
			delay: 5000
		});
	} else {
		table.addData([{ 'agency_id': agency_id, 'agency_name': agency_name, 'agency_url': agency_url, 'agency_timezone': agency_timezone, 'agency_lang': agency_lang, 'agency_phone': agency_phone, 'agency_fare_url':agency_fare_url, 'agency_email': agency_email }]);
		//$('#agencyAddStatus').html('<span class="alert alert-success">Added agency_id ' + agency_id + '</span>');
		$.toast({
			title: 'Add Agency',
			subtitle: 'Success',
			content: 'Added agency_id ' + agency_id,
			type: 'success',
			delay: 5000
		});
	}
}