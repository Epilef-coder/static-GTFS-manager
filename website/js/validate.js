var trashIcon = function (cell, formatterParams, onRendered) { //plain text value
	return "<i class='fas fa-trash-alt'></i>";
};
var viewIcon = function (cell, formatterParams, onRendered) { //plain text value
	return "<i class='fas fa-eye'></i>";
};

var downloadIcon = function (cell, formatterParams, onRendered) { //plain text value
	return "<i class='fas fa-download'></i>";
};


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
	columns:[
	    {formatter:"rowSelection", titleFormatter:"rowSelection",width:50, headerSort:false, cellClick:function(e, cell){
            cell.getRow().toggleSelect();
          }},
        {title:"id", field:"id", visible:false, editor:false},
        {title:"filename", field:"filename", visible:true, editor:false},
        {
            formatter: viewIcon, align: "center", title: "View", headerSort: false, tooltip: "View this report", width:100,cellClick: function (e, cell) {
                var row = cell.getRow();
                selectedrow = row.getData();
                console.log(selectedrow.id);
                window.open(`${APIpath}app/gtfs/validate/report/${selectedrow.id}`, selectedrow.id,"height=600,width=600,modal=yes,alwaysRaised=yes");
            }
	    },
	    {
            formatter: downloadIcon, align: "center", title: "Download", headerSort: false, tooltip: "Download this report", width:150,cellClick: function (e, cell) {
                var row = cell.getRow();
                selectedrow = row.getData();
                downloadreport(selectedrow.id);
            }
	    },
        {
            formatter: trashIcon, align: "center", title: "Delete", headerSort: false, tooltip: "Delete this report", width:100,cellClick: function (e, cell) {
                var row = cell.getRow();
                selectedrow = row.getData();
                deletereport(selectedrow.id);
                cell.getRow().delete();
            }
	    }
    ],
	ajaxError: function (xhr, textStatus, errorThrown) {
		console.log('GET request to API/app/gtfs/validate/reports failed.  Returned status of: ' + errorThrown);
	},
	ajaxResponse:function(url, params, response){
        //url - the URL of the request
        //params - the parameters passed with the request
        //response - the JSON object returned in the body of the response.
        return response.files; //return the tableData property of a response json object
    }
});

function downloadreport(reportid) {
    console.log('download');
    $.ajax({
        url: `${APIpath}app/gtfs/validate/report/${reportid}`,
        success: download.bind(true, "text/html", `${reportid}.html`)
    });
}

function deletereport(reportid) {
    var pw = $("#password").val();
        if (!pw) {
            $.toast({
                title: 'Delete report',
                subtitle: 'No password provided.',
                content: 'Please enter the password.',
                type: 'error',
                delay: 5000
            });
            shakeIt('password'); return;
        }
    $.get( `${APIpath}app/gtfs/validate/report/remove/${reportid}?pw=${pw}`, function() {
      $.toast({
                title: 'Delete report',
                subtitle: 'Success.',
                content: 'Remove report.',
                type: 'success',
                delay: 5000
            });
    });

}