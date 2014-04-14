(function($) { $(function() {
    // If adding an new questions (i.e., URL ends in "/add/")
    // then prepopulate allowed_sympy_commands with those commands
    // marked as default.
    var pathnamePieces = window.location.pathname.split("/");
    var lastPiece = pathnamePieces[pathnamePieces.length-2]
    if(lastPiece === "add") {
	$.get("/assess/question/default_sympy_commands", function(data) {
	    // Since by the time the ajax request is returned,
	    // admin/js/SelectFilter2.js has changed the multi-select box
	    // into a filter interface with two multi-select boxes,
	    // we need to add the default commands to the "to" filter box
	    // and delete the commands from the "from" filter box
	    for(var i=0; i<data.length; i++) {
		$("#id_allowed_sympy_commands_to").append(
		    '<option value="' +data[i][0] + '">' + data[i][1]
			+ '</option>');
		$("#id_allowed_sympy_commands_from option[value='" 
		  + data[i][0] + "']").remove();
	    }
	});

    }
})})(jQuery || django.jQuery)
