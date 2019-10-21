$(document).on("click", "#ValidateGTFS", function () {
	$('#ValidateModal').modal('show');
	var GoogleTransit = 0;
	var SaveReportvalue = 0;
	if ($('#GoogleTransiteExtension').is(':checked')) {
	    GoogleTransit = 1;
	}
	if ($('#SaveReport').is(':checked')) {
	    SaveReportvalue = 1
	}
	console.log(GoogleTransit);
	console.log(SaveReportvalue);

	let xhr = new XMLHttpRequest();
	//make API call from with this as get parameter name
	xhr.open('GET', `${APIpath}app/gtfs/validate?savereport=${SaveReportvalue}&googletransit=${GoogleTransit}`);
	xhr.onload = function () {
		if (xhr.status === 200) { //we have got a Response
			console.log(`Loaded trips data for the chosen route from Server API/trips .`);
			htmlcontent = xhr.responseText;
			$('#ValidateModalBody').replaceWith(htmlcontent);
		}
		else {
			console.log('Server request to API/trips failed.  Returned status of ' + xhr.status + ', message: ' + xhr.responseText);
			$.toast({
				title: 'Trips',
				subtitle: 'Loading',
				content: 'Could not load trips data from server. Message: ' + xhr.responseText,
				type: 'error',
				delay: 5000
			});
		}
	};
	xhr.send();
});


var table = new Tabulator("#reports-table", {
	selectable: 0,
	movableRows: true,
	history: true,
	addRowPos: "top",
	movableColumns: true,
	layout: "fitColumns",
	ajaxURL: `${APIpath}app/gtfs/validate/reports`, //ajax URL
	ajaxLoaderLoading: loaderHTML,
	placeholder: "No Data Available",
	autoColumns:true,
	ajaxError: function (xhr, textStatus, errorThrown) {
		console.log('GET request to agency failed.  Returned status of: ' + errorThrown);
	},
//	dataEdited: function (data) {
//		// The dataEdited callback is triggered whenever the table data is changed by the user. Triggers for this include editing any cell in the table, adding a row and deleting a row.
//		$('#saveAgencyButton').removeClass().addClass('btn btn-primary');
//		$('#saveAgencyButton').prop('disabled', false);
//	},
//	rowUpdated:function(row){
//		// The rowUpdated callback is triggered when a row is updated by the updateRow, updateOrAddRow, updateData or updateOrAddData, functions.
//		$('#saveAgencyButton').removeClass().addClass('btn btn-primary');
//		$('#saveAgencyButton').prop('disabled', false);
//	},
//	dataLoaded: function (data) {
//		// parse the first row keys if data exists.
//		if (data.length > 0) {
//			AddExtraColumns(Object.keys(data[0]), GTFSDefinedColumns, table);
//		}
//		else {
//			console.log("No data so no columns");
//		}
//		var NumberofRows = data.length + ' row(s)';
//		$("#NumberofRows").html(NumberofRows);
//	}
});
