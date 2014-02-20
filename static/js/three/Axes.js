/* based on AxisHelper */

/**
 * @author sroucheray / http://sroucheray.org/
 * @author mrdoob / http://mrdoob.com/
 */

// will need to add a "boxed" axes type where have a box around
// the whole region, possibly with actual values of the coordinates
// labeled

'use strict';

// three-dimensional axes
var Axes = function ( size, neg_size, labels ) {
    
    if(size ===undefined) {
	size = new THREE.Vector3(1,1,1);
    }
    else if(!(size instanceof THREE.Vector3)) {
	size = new THREE.Vector3(size,size,size);
    }
    if(neg_size===undefined) {
	neg_size = size.clone().negate();
    }
    else if(!(neg_size instanceof THREE.Vector3)) {
	neg_size = new THREE.Vector3(neg_size,neg_size,neg_size);
    }
    

    labels = labels || true;

    var geometry = new THREE.Geometry();
    
    geometry.vertices.push(
	new THREE.Vector3(), new THREE.Vector3( size.x, 0, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, size.y, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, 0, size.z ),
	new THREE.Vector3(), new THREE.Vector3( neg_size.x, 0, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, neg_size.y, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, 0, neg_size.z )
    );
    
    geometry.colors.push(
	new THREE.Color( 0x000000 ), new THREE.Color( 0x000000 ),
	new THREE.Color( 0x000000 ), new THREE.Color( 0x000000 ),
	new THREE.Color( 0x000000 ), new THREE.Color( 0x000000 ),
	new THREE.Color( 0x000000 ), new THREE.Color( 0x000000 ),
	new THREE.Color( 0x000000 ), new THREE.Color( 0x000000 ),
	new THREE.Color( 0x000000 ), new THREE.Color( 0x000000 )
    );

    var material = new THREE.LineBasicMaterial( { vertexColors: THREE.VertexColors, linewidth: 5 } );
    
    THREE.Line.call( this, geometry, material, THREE.LinePieces );

    if(labels) {
	var spritex = new TextLabel( "x",   { fontsize: 120} );
	spritex.position.set(size.x*1.1, 0, 0);
	this.add( spritex );
	
	var spritey = new TextLabel( "y",   { fontsize: 120} );
	spritey.position.set(0, size.y*1.1, 0);
	this.add( spritey );
	
	var spritez = new TextLabel( "z",   { fontsize: 120} );
	spritez.position.set(0, 0, size.z*1.1);
	this.add( spritez );
    }
};

Axes.prototype = Object.create( THREE.Line.prototype );

// two-dimensional axes
var Axes2D = function ( size, neg_size, labels ) {
    
    if(size ===undefined) {
	size = new THREE.Vector2(1,1);
    }
    else if(!(size instanceof THREE.Vector2)) {
	size = new THREE.Vector2(size,size);
    }
    if(neg_size===undefined) {
	neg_size = size.clone().negate();
    }
    else if(!(neg_size instanceof THREE.Vector2)) {
	neg_size = new THREE.Vector2(neg_size,neg_size);
    }
    

    labels = labels || true;

    var geometry = new THREE.Geometry();
    
    geometry.vertices.push(
	new THREE.Vector3(), new THREE.Vector3( size.x, 0, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, size.y, 0 ),
	new THREE.Vector3(), new THREE.Vector3( neg_size.x, 0, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, neg_size.y, 0 )
    );
    
    geometry.colors.push(
	new THREE.Color( 0x000000 ), new THREE.Color( 0x000000 ),
	new THREE.Color( 0x000000 ), new THREE.Color( 0x000000 ),
	new THREE.Color( 0x000000 ), new THREE.Color( 0x000000 ),
	new THREE.Color( 0x000000 ), new THREE.Color( 0x000000 )
    );

    var material = new THREE.LineBasicMaterial( { vertexColors: THREE.VertexColors, linewidth: 5 } );
    
    THREE.Line.call( this, geometry, material, THREE.LinePieces );

    if(labels) {
	var spritex = new TextLabel( "x",   { fontsize: 120} );
	spritex.position.set(size.x*1.1, 0, 0);
	this.add( spritex );
	
	var spritey = new TextLabel( "y",   { fontsize: 120} );
	spritey.position.set(0, size.y*1.1, 0);
	this.add( spritey );
	
    }
};

Axes2D.prototype = Object.create( THREE.Line.prototype );

