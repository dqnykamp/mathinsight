'use strict';

// This file contains options for standard 3D axes, box 3D axes, and 2D axes.
// Standard and box axes are accessed through Axes, 2D is accessed through Axes2D

/**
* This is the standard Axes function, which shows standard 3D Axes by default,
* and/or 3D box axes if specified by showBoxAxes.
*
* Parameters:
* size: A number (or THREE.Vector3()) representing positive size x, y, and z, will ultimately be formed into a THREE.Vector3(), default is THREE.Vector3(1, 1, 1)
* negSize: A number (or THREE.Vector3()) representing negative size x, y, and z, will ultimately be formed into a THREE.Vector3(), , default is THREE.Vector3(-1, -1, -1)
* label: overall axis label, default is ''
* labelx: label for x axis, default is 'x'
* labely: label for y axis, default is 'y'
* labelz: label for z axis, default is 'z'
* showLabels: boolean determining visibility of x, y, and z labels, default is true
* color: a color in hex
* showStandardAxes: a boolean determining standard axis visibility, default is true
* showBoxAxes: a boolean determining box axis visibility, default is false
* labelFontSize: Font size for labels, default is 120
* labelScale: scale of font for labels, default is 2
* labelColor: the color of the text for the labels in hex string, default is '#000000'
* showAxisTicks: a boolean determining whether ticks will be displayed on each axis, default is false
* axisTick: a number specifying the tick increment, default is proportional to axis size
* axisTickSize: a number specifying the tick size, default is 0.25
* axisTickIncrement: a number specifying the spacing between ticks, default is 1
* showAxisTickLabels: a boolean determining whether tick labels will be displayed on each axis, default is false
*/


var Axes = function (params) {

	if (params === undefined){var params = {};}
	
	if (!isNaN(params)){//i.e. if params is a number, convert it to object format
		var incomingSize = params;
		params = {};
		params.size = incomingSize;
	}
	
	if (params.size === undefined) {
		params.size = new THREE.Vector3(1,1,1);
    }
    else if(!(params.size instanceof THREE.Vector3)) {
		params.size = new THREE.Vector3(params.size, params.size, params.size);
    }
	
    if (params.negSize === undefined) {
		params.negSize = params.size.clone().negate();
    }
    else if (!(params.negSize instanceof THREE.Vector3)) {
		params.negSize = new THREE.Vector3(params.negSize,params.negSize,params.negSize);
    }
	
	if (params.label  === undefined) {params.label = '';}
	if (params.labelx === undefined) {params.labelx = 'x';}
	if (params.labely === undefined) {params.labely = 'y';}
	if (params.labelz === undefined) {params.labelz = 'z';}
	if (params.showLabels === undefined){params.showLabels = true;}
	if (params.color === undefined){params.color = 0x000000;}
	if (params.showBoxAxes === undefined) {params.showBoxAxes = false;}
	if (params.showStandardAxes === undefined) {params.showStandardAxes = true;}
	if (params.labelFontSize === undefined) {params.labelFontSize = 120;}
	if (params.labelScale === undefined) {params.labelScale = 2;}
	if (params.labelColor === undefined) {params.labelColor = '#000000';}
	if (params.axisTickSize === undefined) {params.axisTickSize = 0.25;}
	if (params.axisTickIncrement === undefined) {params.axisTickIncrement = 1;}
	if (params.showAxisTickLabels === undefined) {params.showAxisTickLabels = false;}

	
	//Overall geometry, containing all vectors for standard and/or box axes
	var geometry = new THREE.Geometry();
    
	if (params.showBoxAxes === true){
	
	geometry.vertices.push(
		
		//Axes Box--lines grouped by dimension spanned--"top"
		new THREE.Vector3(0, params.size.y, params.size.z), new THREE.Vector3( params.size.x, params.size.y, params.size.z ),
		new THREE.Vector3(0, params.size.y, params.size.z), new THREE.Vector3( params.negSize.x, params.size.y, params.size.z ),
		
		new THREE.Vector3(0, params.size.y, params.negSize.z), new THREE.Vector3( params.size.x, params.size.y, params.negSize.z ),
		new THREE.Vector3(0, params.size.y, params.negSize.z), new THREE.Vector3( params.negSize.x, params.size.y, params.negSize.z ),
		
		new THREE.Vector3(params.size.x, params.size.y, 0), new THREE.Vector3( params.size.x, params.size.y, params.size.z ),
		new THREE.Vector3(params.size.x, params.size.y, 0), new THREE.Vector3( params.size.x, params.size.y, params.negSize.z ),
		
		new THREE.Vector3(params.negSize.x, params.size.y, 0), new THREE.Vector3( params.negSize.x, params.size.y, params.size.z),
		new THREE.Vector3(params.negSize.x, params.size.y, 0), new THREE.Vector3( params.negSize.x, params.size.y, params.negSize.z),
		
		
		//Axes Box--lines grouped by dimension spanned--"bottom"
		new THREE.Vector3(0, params.negSize.y, params.size.z), new THREE.Vector3( params.size.x, params.negSize.y, params.size.z ),
		new THREE.Vector3(0, params.negSize.y, params.size.z), new THREE.Vector3( params.negSize.x, params.negSize.y, params.size.z ),
		
		new THREE.Vector3(0, params.negSize.y, params.negSize.z), new THREE.Vector3( params.size.x, params.negSize.y, params.negSize.z ),
		new THREE.Vector3(0, params.negSize.y, params.negSize.z), new THREE.Vector3( params.negSize.x, params.negSize.y, params.negSize.z ),
		
		new THREE.Vector3(params.size.x, params.negSize.y, 0), new THREE.Vector3( params.size.x, params.negSize.y, params.size.z ),
		new THREE.Vector3(params.size.x, params.negSize.y, 0), new THREE.Vector3( params.size.x, params.negSize.y, params.negSize.z ),
		
		new THREE.Vector3(params.negSize.x, params.negSize.y, 0), new THREE.Vector3( params.negSize.x, params.negSize.y, params.size.z),
		new THREE.Vector3(params.negSize.x, params.negSize.y, 0), new THREE.Vector3( params.negSize.x, params.negSize.y, params.negSize.z),
		
		//Axes Box--lines grouped by dimension spanned--"right"
		new THREE.Vector3(params.size.x, 0, params.size.z), new THREE.Vector3( params.size.x, params.size.y, params.size.z ),
		new THREE.Vector3(params.size.x, 0, params.size.z), new THREE.Vector3( params.size.x, params.negSize.y, params.size.z ),
		                             
		new THREE.Vector3(params.size.x, 0, params.negSize.z), new THREE.Vector3( params.size.x, params.size.y, params.negSize.z ),
		new THREE.Vector3(params.size.x, 0, params.negSize.z), new THREE.Vector3( params.size.x, params.negSize.y, params.negSize.z ),
		
		//Axes Box--lines grouped by dimension spanned--"left"
		new THREE.Vector3(params.negSize.x, 0, params.size.z), new THREE.Vector3( params.negSize.x, params.size.y, params.size.z ),
		new THREE.Vector3(params.negSize.x, 0, params.size.z), new THREE.Vector3( params.negSize.x, params.negSize.y, params.size.z ),
		
		new THREE.Vector3(params.negSize.x, 0, params.negSize.z), new THREE.Vector3( params.negSize.x, params.size.y, params.negSize.z ),
		new THREE.Vector3(params.negSize.x, 0, params.negSize.z), new THREE.Vector3( params.negSize.x, params.negSize.y, params.negSize.z )	
		);
	
	}
	
	
	if (params.showAxisTicks){
		for (var i = params.negSize.x; i < params.size.x; i+=params.axisTickIncrement){
		geometry.vertices.push(new THREE.Vector3(i, -params.axisTickSize, 0), new THREE.Vector3(i, params.axisTickSize, 0));
		}
		for (var i = params.negSize.y; i < params.size.y; i+=params.axisTickIncrement){
		geometry.vertices.push(new THREE.Vector3(-params.axisTickSize, i, 0), new THREE.Vector3(params.axisTickSize, i, 0));	
		}
		for (var i = params.negSize.z; i < params.size.z; i+=params.axisTickIncrement){
		geometry.vertices.push(new THREE.Vector3(0, -params.axisTickSize, i), new THREE.Vector3(0, params.axisTickSize, i));	
		}
	}
	
	
	
	if (params.showStandardAxes === true) {
	
		geometry.vertices.push(
			new THREE.Vector3(), new THREE.Vector3( params.size.x, 0, 0 ),
			new THREE.Vector3(), new THREE.Vector3( 0, params.size.y, 0 ),
			new THREE.Vector3(), new THREE.Vector3( 0, 0, params.size.z ),
			new THREE.Vector3(), new THREE.Vector3( params.negSize.x, 0, 0 ),
			new THREE.Vector3(), new THREE.Vector3( 0, params.negSize.y, 0 ),
			new THREE.Vector3(), new THREE.Vector3( 0, 0, params.negSize.z )
		);
	}
	
	var material = new THREE.LineBasicMaterial( { color: params.color, linewidth: 5 } );
    
	THREE.Line.call( this, geometry, material, THREE.LinePieces );
	
	if (params.showAxisTickLabels){
		for (var i = params.negSize.x; i < params.size.x; i+=params.axisTickIncrement){
			if (i != 0){
				var sprite = new TextLabel( i.toString(),   { fontSize: params.labelFontSize, scale: params.labelScale, textColor: params.labelColor, fontWeight: ""} );
				sprite.position.set(i, params.axisTickSize*2, 0);
				this.add( sprite );
			}
		}
		
		for (var i = params.negSize.y; i < params.size.y; i+=params.axisTickIncrement){
			if (i !=0){
				var sprite = new TextLabel( i.toString(),   { fontSize: params.labelFontSize, scale: params.labelScale, textColor: params.labelColor, fontWeight: ""} );
				sprite.position.set(params.axisTickSize*2, i, 0);
				this.add( sprite );
			}
		}
		
		for (var i = params.negSize.z; i < params.size.z; i+=params.axisTickIncrement){
			if (i != 0){
				var sprite = new TextLabel( i.toString(),   { fontSize: params.labelFontSize, scale: params.labelScale, textColor: params.labelColor, fontWeight: ""} );
				sprite.position.set(0, params.axisTickSize*2, i);
				this.add( sprite );
			}
		}
	}
	
	if (params.showLabels) {
	
		var spritex = new TextLabel( params.labelx,   { fontSize: params.labelFontSize, scale: params.labelScale, textColor: params.labelColor} );
		spritex.position.set(params.size.x*1.1, 0, 0);
		this.add( spritex );
		
		var spritey = new TextLabel( params.labely,   { fontSize: params.labelFontSize, scale: params.labelScale, textColor: params.labelColor} );
		spritey.position.set(0, params.size.y*1.1, 0);
		this.add( spritey );
		
		var spritez = new TextLabel( params.labelz,   { fontSize: params.labelFontSize, scale: params.labelScale, textColor: params.labelColor} );
		spritez.position.set(0, 0, params.size.z*1.1);
		this.add( spritez );
		
		var spriteOverallLabel = new TextLabel( params.label,   { fontSize: params.labelFontSize, scale: params.labelScale, textColor: params.labelColor} );
		spriteOverallLabel.position.set(params.size.x*1.1, params.size.y*1.1, params.size.z*1.1);
		this.add( spriteOverallLabel );
    }
	
};

Axes.prototype = Object.create( THREE.Line.prototype );


// two-dimensional axes
var Axes2D = function (params) {

    if (params === undefined){var params = {};}
	
    if (!isNaN(params)){//i.e. if params is a number, convert it to object format
	var incomingSize = params;
	params = {};
	params.size = incomingSize;
    }
	
    if (params.size === undefined) {
	params.size = new THREE.Vector2(1,1);
    }
    else if(!(params.size instanceof THREE.Vector2)) {
	params.size = new THREE.Vector2(params.size, params.size);
    }
	
    if (params.negSize === undefined) {
	params.negSize = params.size.clone().negate();
    }
    else if (!(params.negSize instanceof THREE.Vector2)) {
	params.negSize = new THREE.Vector3(params.negSize,params.negSize);
    }
	
    if (params.label  === undefined) {params.label = '';}
    if (params.labelx === undefined) {params.labelx = 'x';}
    if (params.labely === undefined) {params.labely = 'y';}
    if (params.showLabels === undefined){params.showLabels = true;}
    if (params.color === undefined){params.color = 0x000000;}
    if (params.labelFontSize === undefined) {params.labelFontSize = 120;}
    if (params.labelScale === undefined) {params.labelScale = 2;}
    if (params.labelColor === undefined) {params.labelColor = '#000000';}

    var geometry = new THREE.Geometry();
    
    geometry.vertices.push(
	new THREE.Vector3(), new THREE.Vector3( params.size.x, 0, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, params.size.y, 0 ),
	new THREE.Vector3(), new THREE.Vector3( params.negSize.x, 0, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, params.negSize.y, 0 )
    );
    
    var material = new THREE.LineBasicMaterial( { color: params.color, linewidth: 5 } );
    
    THREE.Line.call( this, geometry, material, THREE.LinePieces );
    
    if (params.showLabels) {
	
	var spritex = new TextLabel( params.labelx,   { fontSize: params.labelFontSize, scale: params.labelScale, textColor: params.labelColor} );
	spritex.position.set(params.size.x*1.05, 0, 0);
	this.add( spritex );
	
	var spritey = new TextLabel( params.labely,   { fontSize: params.labelFontSize, scale: params.labelScale, textColor: params.labelColor} );
	spritey.position.set(0, params.size.y*1.05, 0);
	this.add( spritey );
	
    }
};

Axes2D.prototype = Object.create( THREE.Line.prototype );







