//###################
// global variables
var operationalChoices = {1:"1 - Operating on this day", 0:"0 - Not operating"};
var service_id_list = [];
var globalIDs = {}; // Contains keys: stop_id_list, route_id_list, trip_id_list, shapeIDsJson, zone_id_list, service_id_list
var globalKey = '';
var globalValue = '';

// for Maintenance Change UID function:
var globalValueFrom = '';
var globalValueTo = '';
var globalTableKeys = [];

// ###################
// commands to run on page load
$(document).ready(function() {
	// executes when HTML-Document is loaded and DOM is ready
	// $( "#tabs2" ).tabs({
	// 	active:0,
	// 	activate: function(event ,ui){
	// 		resetGlobals();
	// 	}
	// });
	//getPythonAgency();
	//getPythonCalendar();
	//getPythonTranslations();
	getPythonAllIDs();  
});

$('#deepActionsButton').on('click', function(){
	deleteByKey();
});

function getPythonAllIDs() {
	// shorter GET request. from https://api.jquery.com/jQuery.get/
	var jqxhr = $.get( `${APIpath}gtfs/delete/listid`, function( data ) {
		globalIDs =  JSON.parse(data) ;
		console.log('/API/gtfs/delete/listid GET request successful. Loaded lists of all ids.');
		populateLists();
	})
	.fail( function() {
		console.log('GET request to /API/gtfs/delete/listid failed.')
	});

}

// #################################
function populateLists() {
	//globalIDs
	//var renameContent = '<option>No Selection</option>';
	// stop2Delete
	var select2items = [];		
	select2items.push({id : '', text: ''});	
	globalIDs['stop_id_list'].forEach(function(row){
		select2items.push({id : row, text: 'stop: ' + row});
	});
	$("#stop2Delete").select2({				
		placeholder: "Pick a stop",
		theme: 'bootstrap4',
		data: select2items
	  });
	$('#stop2Delete').on('select2:select', function (e) {
		var valueSelected = e.params.data.id;
		if( valueSelected == '') { 			
			return;
		}
		let stop_id = valueSelected;
		console.log(stop_id);
		globalKey = 'stop_id';
		globalValue = stop_id;
		diagnoseID(globalKey,globalValue);
	});

	// route2Delete
	var select2items = [];		
	select2items.push({id : '', text: ''});	
	globalIDs['route_id_list'].forEach(function(row){		
		select2items.push({id : row, text: 'route: ' + row});
	});
	$("#route2Delete").select2({				
		placeholder: "Pick a route",
		theme: 'bootstrap4',
		data: select2items
	  });
	$('#route2Delete').on('select2:select', function (e) {
		var valueSelected = e.params.data.id;
		if( valueSelected == '') { 			
			return;
		}
		console.log(valueSelected);
		globalKey = 'route_id';
		globalValue = valueSelected;
		diagnoseID(globalKey,globalValue);
	});
	
	// trip2Delete
	var select2items = [];		 	
	select2items.push({id : '', text: ''});	
	globalIDs['trip_id_list'].forEach(function(row){		
		select2items.push({id : row, text: 'trip: ' + row});
	});
	$("#trip2Delete").select2({				
		placeholder: "Pick a Trip",
		theme: 'bootstrap4',
		data: select2items
	  });
	$('#trip2Delete').on('select2:select', function (e) {
		var valueSelected = e.params.data.id;
		if( valueSelected == '') { 			
			return;
		}
		console.log(valueSelected);
		globalKey = 'trip_id';
		globalValue = valueSelected;
		diagnoseID(globalKey,globalValue);
	});
	
	// shape2Delete
	var select2items = [];		 	
	select2items.push({id : '', text: ''});	
	globalIDs['shapeIDsJson']['all'].forEach(function(row){
		select2items.push({id : row, text: 'shape: ' + row});
			
	});
	$("#shape2Delete").select2({				
		placeholder: "Pick a Shape",
		theme: 'bootstrap4',
		data: select2items
	  });
	$('#shape2Delete').on('select2:select', function (e) {
		var valueSelected = e.params.data.id;
		if( valueSelected == '') { 			
			return;
		}
		console.log(valueSelected);
		globalKey = 'shape_id';
		globalValue = valueSelected;
		diagnoseID(globalKey,globalValue);
	});
	
	// service2Delete
	var select2items = [];		 	
	select2items.push({id : '', text: ''});	
	globalIDs['service_id_list'].forEach(function(row){
		select2items.push({id : row, text: 'service: ' + row});
			
	});
	$("#service2Delete").select2({				
		placeholder: "Pick a Calendar Service",
		theme: 'bootstrap4',
		data: select2items
	  });
	$('#service2Delete').on('select2:select', function (e) {
		var valueSelected = e.params.data.id;
		if( valueSelected == '') { 			
			return;
		}
		console.log(valueSelected);
		globalKey = 'service_id';
		globalValue = valueSelected;
		diagnoseID(globalKey,globalValue);
	});
	

	// zone2Delete
	var select2items = [];		 	
	select2items.push({id : '', text: ''});	
	globalIDs['zone_id_list'].forEach(function(row){
		select2items.push({id : row, text: 'zone: ' + row});
	});
	$("#zone2Delete").select2({				
		placeholder: "Pick a Fare Zone",
		theme: 'bootstrap4',
		data: select2items
	  });
	$('#zone2Delete').on('select2:select', function (e) {
		var valueSelected = e.params.data.id;
		if( valueSelected == '') { 			
			return;
		}
		console.log(valueSelected);
		globalKey = 'zone_id';
		globalValue = valueSelected;
		diagnoseID(globalKey,globalValue);
	});

	// fareID2Delete
	var select2items = [];		 	
	select2items.push({id : '', text: ''});	
	globalIDs['fare_id_list'].forEach(function(row){
		select2items.push({id : row, text: 'fareID: ' + row});
	});
	$("#fareID2Delete").select2({				
		placeholder: "Pick a Fare ID",
		theme: 'bootstrap4',
		data: select2items
	  });
	$('#fareID2Delete').on('select2:select', function (e) {
		var valueSelected = e.params.data.id;
		if( valueSelected == '') { 			
			return;
		}
		console.log(valueSelected);
		globalKey = 'fare_id';
		globalValue = valueSelected;
		diagnoseID(globalKey,globalValue);
	});

	// agency2Delete
	var select2items = [];		 	
	select2items.push({id : '', text: ''});	
	globalIDs['agency_id_list'].forEach(function(row){
		select2items.push({id : row, text: 'agency: ' + row});
	});
	$("#agency2Delete").select2({				
		placeholder: "Pick an Agency ID",
		theme: 'bootstrap4',
		data: select2items
	  });
	$('#agency2Delete').on('select2:select', function (e) {
		var valueSelected = e.params.data.id;
		if( valueSelected == '') { 			
			return;
		}
		console.log(valueSelected);
		globalKey = 'agency_id';
		globalValue = valueSelected;
		diagnoseID(globalKey,globalValue);
	});
	
}

// #################################

function diagnoseID(column,value) {
	$('#dryRunResults').val('Loading...');
	if(value == 'No Selection' || value == '') {
		resetGlobals();
		return;
	}

		// shorter GET request. from https://api.jquery.com/jQuery.get/
	var jqxhr = $.get( `${APIpath}gtfs/delete/diagnose/${column}?value=${value}`, function( returndata ) {
		console.log('diagnoseID API GET request successful.');
		$('#dryRunResults').val(returndata);
	})
	.fail( function() {
		console.log('GET request to API/diagnoseID failed.');
		$('#dryRunResults').val('GET request to API/diagnoseID failed. Please check logs.');
	});
}

function deleteByKey() {

	var consent = $('#deepActionsConfirm').is(':checked');
	if(!consent) {
		$('#deepActionsStatus').html('Check ON the confirmation box first.');
		return;
	}

	// shorter GET request. from https://api.jquery.com/jQuery.get/
	if( ! confirm('Are you sure you want to do this? Press Cancel to go back, take backup export etc.') ) {
		$('#deepActionsStatus').html('Okay, not this time. Make a fresh selection again if you change your mind.');
		globalKey = '';
		globalValue = '';
		return;
	}

	var pw = $("#password").val();
	if ( ! pw ) { 
		$('#deepActionsStatus').html('Please enter the password.');
		shakeIt('password'); return;
	}

	$('#deepActionsStatus').html('Processing.. please wait..');
	
	key = globalKey;
	value = globalValue;
	console.log(key,value);

	if( ! (key.length && value.length ) ) {
		$('#deepActionsStatus').html('All values have not been properly set. Please check and try again.');
		shakeIt('deepActionsButton'); return;
	}
	var jqxhr = $.get( `${APIpath}gtfs/delete/${key}?pw=${pw}&value=${value}`, function( returndata ) {
		console.log('deleteByKey API GET request successful. Message: ' + returndata);
		$('#deepActionsStatus').html('<div class="alert alert-success">' + returndata +'</div>');
		
		// resetting global vars and emptying of dry run textbox so that pressing this button again doesn't send the API request. 
		resetGlobals();

		getPythonAllIDs();
	})
	.fail( function() {
		console.log('GET request to API/deleteByKey failed.');
		$('#deepActionsStatus').html('Error at backend, please debug.');
	});
}

function resetGlobals() {
	globalKey = ''; globalValue = '';
	$('#dryRunResults').val('');

	// clear the consent checkbox
	//$('#deepActionsConfirm').removeAttr('checked');
	document.getElementById("deepActionsConfirm").checked = false;

	// even Change UID:
	var globalValueFrom = '';
	var globalValueTo = '';
	var globalTableKeys = [];
	$('#renameTablesInfo').html('');
	$('#renameStatus').html('');
	/*
	document.getElementById("replaceIDButton").disabled = true;
	document.getElementById("replaceIDButton").className = "btn";
	*/
}