//homepage.js
$(function () {

});

// Buttons:
$("#exportGTFS").on("click", function () {
	exportGTFS();
});

$("#importGTFSbutton").on("click", function () {
	gtfsImportZip();
});

$("#gtfsBlankSlateButton").on("click", function () {
	gtfsBlankSlate();
});

// #########################################
// Initiate bootstrap / jquery components like tabs, accordions
$(document).ready(function () {
	getPythonGTFSstats();
	getPythonPastCommits();

});
// ##############################
// Functions:

function getPythonGTFSstats() {
	let xhr = new XMLHttpRequest();
	//make API call from with this as get parameter name
	xhr.open('GET', `${APIpath}stats`);
	xhr.onload = function () {
		if (xhr.status === 200) { //we have got a Response
			console.log(`Loaded data from Server API/stats .`);
			var data = JSON.parse(xhr.responseText);




			var htmlcontent = '';
			htmlcontent += '<div class="btn-group-vertical">'
			data.files.forEach(function (file) {
				var background = 'btn-primary';
				var foreground = 'badge-light'
				switch (file.type) {
					case 1:
						background = 'btn-primary';
						foreground = 'badge-light'
						break;
					case 2:
						background = 'btn-secondary';
						foreground = 'badge-light'
						break;

					case 3:
						background = 'btn-light';
						foreground = 'badge-dark'
						break;
				}

				htmlcontent += `<button type="button" class="btn ${background} d-flex justify-content-between">
			${file.filename} <span class="badge ${foreground}">${file.rows}</span>
		  </button>`;
			});

			htmlcontent += '</div>';
			console.log(htmlcontent);
			$('#GTFSstats').html(htmlcontent);
		}
		else {
			console.log('Server request to API/stats for all stops failed.  Returned status of ' + xhr.status + ', message: ' + xhr.responseText);
			//$('#GTFSstats').html('<p>Failed to fetch stats. Message: ' + xhr.responseText + '</p>');
			$.toast({
				title: 'GTFS Stats',
				subtitle: 'Fetch failed',
				content: 'Failed to fetch stats. Message: ' + xhr.responseText,
				type: 'error',
				delay: 5000
			});
		}
	};
	xhr.send();
}

function getPythonPastCommits() {
	let xhr = new XMLHttpRequest();
	xhr.open('GET', `${APIpath}pastCommits`);
	xhr.onload = function () {
		if (xhr.status === 200) { //we have got a Response
			console.log(`Loaded data from Server ${APIpath}pastCommits .`);

			var data = JSON.parse(xhr.responseText);
			var content = '<ol class="list-inline">';
			for (i in data.commits) {
				content += '<li>' + data.commits[i] + ' : <a href="export/' + data.commits[i] + '/gtfs.zip">Download gtfs.zip</a></li>';
			}
			content += '</ol>';

			$('#pastCommits').html(content);
		}
		else {
			console.log(`Server request to ${APIpath}pastCommits failed.  Returned status of ` + xhr.status + ', message: ' + xhr.responseText);
			$.toast({
				title: 'Past Commits',
				subtitle: 'Error Loading',
				content: xhr.responseText,
				type: 'error',
				delay: 5000
			});
		}
	};
	xhr.send();
}

function exportGTFS() {
	// lowercase and zap everything that is not a-z, 0-9, - or _  from https://stackoverflow.com/a/4460306/4355695
	var commit = $("#commitName").val().toLowerCase().replace(/[^a-z0-9-_]/g, "");

	$("#commitName").val(commit); // showing the corrected name to user.

	//reject if its blank
	if (!commit.length) {
		$.toast({
			title: 'GTFS Export',
			subtitle: 'No valid name',
			content: 'Please give a valid name for the commit',
			type: 'error',
			delay: 5000
		});
		shakeIt('commitName'); return;
	}
	/*
	var pw = $("#password").val();
	if ( ! pw.length ) { 
		$('#exportGTFSlog').html('<div class="alert alert-danger">Please enter the password.</div>');
		shakeIt('password'); return;
	}
	*/
	$.toast({
		title: 'GTFS Export',
		subtitle: 'Processing',
		content: 'Initated commit.. please wait..<br>If it\'s a large feed then expect it to take around 5 mins.',
		type: 'info',
		delay: 5000
	});

	let xhr = new XMLHttpRequest();
	//make API call from with this as get parameter name
	xhr.open('GET', `${APIpath}commitExport?commit=${commit}`);
	xhr.onload = function () {
		if (xhr.status === 200) { //we have got a Response
			console.log(`Sent commit message to Server API/commitExport .`);
			$.toast({
				title: 'GTFS Export',
				subtitle: 'Finished',
				content: xhr.responseText,
				type: 'success',
				delay: 5000
			});
			getPythonPastCommits();
		}
		else {
			console.log('Server request to API/commitExport for all stops failed.  Returned status of ' + xhr.status + ', message: ' + xhr.responseText);
			$.toast({
				title: 'GTFS Export',
				subtitle: 'Error',
				content: xhr.responseText,
				type: 'error',
				delay: 5000
			});
		}
	};
	xhr.send();
}

function gtfsImportZip() {
	// make POST request to API/gtfsImportZip

	// idiot-proofing: check if the files have been uploaded or not.
	if (document.getElementById('gtfsZipFile').value == '') {
		$.toast({
			title: 'GTFS Import',
			subtitle: 'Warning',
			content: 'Please select a file first!',
			type: 'warning',
			delay: 5000
		});
		shakeIt('gtfsZipFile'); return;
	}

	var pw = $("#password").val();
	if (!pw.length) {
		$('#importGTFSStatus').html('<div class="alert alert-danger">Please enter the password.</div>');
		shakeIt('password'); return;
	}
	$.toast({
		title: 'GTFS Import',
		subtitle: 'Proccessing',
		content: 'Importing GTFS file, please wait..',
		type: 'info',
		delay: 5000
	});

	var formData = new FormData();
	formData.append('gtfsZipFile', $('#gtfsZipFile')[0].files[0]);

	$.ajax({
		url: `${APIpath}app/database/gtfs/import?pw=${pw}`,
		type: 'POST',
		data: formData,
		cache: false,
		processData: false,  // tell jQuery not to process the data
		contentType: false,  // tell jQuery not to set contentType
		success: function (data) {
			console.log(data);
			$.toast({
				title: 'GTFS Import',
				subtitle: 'Success',
				content: 'Successfully imported GTFS feed. See the other pages to explore the data.<br>A backup has been taken of the earlier data just in case.',
				type: 'success',
				delay: 5000
			});
			// housekeeping: run stats and past commits scan again and clear out blank slate status
			getPythonGTFSstats();
			getPythonPastCommits();
		},
		error: function (jqXHR, exception) {
			console.log('app/database/gtfs/import POST request failed.');
			$.toast({
				title: 'GTFS Import',
				subtitle: 'Failed',
				content: 'GTFS Import function failed for some reason.<br>Please try again or <a href="https://github.com/WRI-Cities/static-GTFS-manager/issues">file a bug on github.</a><br>Message from server: ' + jqXHR.responseText,
				type: 'error',
				delay: 5000
			});
		}
	});
}

function gtfsBlankSlate() {
	if (!confirm('Are you sure you want to do this?'))
		return;
	var pw = $("#password").val();
	$.toast({
		title: 'GTFS Blank Slate',
		subtitle: 'Proccessing',
		content: 'Processing, please wait..',
		type: 'info',
		delay: 5000
	});

	$.ajax({
		url: `${APIpath}app/database/blank?pw=${pw}`,
		type: 'GET',
		cache: false,
		processData: false,  // tell jQuery not to process the data
		contentType: false,  // tell jQuery not to set contentType
		success: function (data) {
			console.log(data);
			// housekeeping: run stats again and clear out GTFS import status text
			getPythonGTFSstats();
			$.toast({
				title: 'GTFS Blank Slate',
				subtitle: 'Success',
				content: data,
				type: 'success',
				delay: 5000
			});

		},
		error: function (jqXHR, exception) {
			console.log('API/gtfsBlankSlate GET request failed.');
			$.toast({
				title: 'GTFS Blank Slate',
				subtitle: 'Error',
				content: jqXHR.responseText,
				type: 'error',
				delay: 5000
			});
		}
	});
}