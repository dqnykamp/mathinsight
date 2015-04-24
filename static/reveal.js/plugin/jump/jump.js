/*
reveal.js-jump-plugin
by Paul Jähne
https://github.com/SethosII/reveal.js-jump-plugin
Licensed under GNU Lesser General Public License

Modified by Duane Nykamp
*/

'use strict';

var jumpToSlide = "";

function keyHandle(event) {
    var isSpecialKey = event.shiftKey || event.ctrlKey || event.altKey || event.metaKey;
    var isNumberKey = event.which >= 48 && event.which <= 57;
    var isDashKey = event.which === 45;

    if (isNumberKey || isDashKey && !isSpecialKey) {
	jumpToSlide += String.fromCharCode(event.charCode);
    } else {
	var isEnterKey = event.which === 13;
	var isJumpToSlideEmpty = jumpToSlide === "";

	if (isEnterKey && !isJumpToSlideEmpty) {
	    // horizontal and vertical slides as well as fragment
	    // are separated by a dash
	    jumpToSlide = jumpToSlide.split("-");

	    var indexh, indexv, indexf;

	    indexh= jumpToSlide[0]-1;

	    if(jumpToSlide.length > 1) {
		indexv = jumpToSlide[1]-1;
	    }
	    if(jumpToSlide.length > 2) {
		indexf = jumpToSlide[2]-1;
	    }

	    Reveal.slide(indexh, indexv, indexf);

	}
	// Reset jumpToSlide variable
	jumpToSlide = "";
    }
}

document.onkeypress = keyHandle;
