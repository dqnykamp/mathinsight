/* based on AxisHelper */

/**
 * @author sroucheray / http://sroucheray.org/
 * @author mrdoob / http://mrdoob.com/
 */

Axes = function ( size, labels ) {
    
    size = size || 1;
    labels = labels || true;

    var geometry = new THREE.Geometry();
    
    geometry.vertices.push(
	new THREE.Vector3(), new THREE.Vector3( size, 0, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, size, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, 0, size ),
	new THREE.Vector3(), new THREE.Vector3( -size, 0, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, -size, 0 ),
	new THREE.Vector3(), new THREE.Vector3( 0, 0, -size )
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
	var spritex = AxesMakeTextSprite( "x",   { fontsize: 120} );
	spritex.position.set(5.5, 0.2, 0);
	this.add( spritex );
	
	var spritey = AxesMakeTextSprite( "y",   { fontsize: 120} );
	spritey.position.set(0, 5.5, 0);
	this.add( spritey );
	
	var spritez = AxesMakeTextSprite( "z",   { fontsize: 120} );
	spritez.position.set(0, 0.2, 5.5);
	this.add( spritez );
    }
};

Axes.prototype = Object.create( THREE.Line.prototype );


function AxesMakeTextSprite( message, parameters )
{
    if ( parameters === undefined ) parameters = {};
    
    var fontface = parameters.hasOwnProperty("fontface") ? 
	parameters["fontface"] : "Arial";
    
    var fontsize = parameters.hasOwnProperty("fontsize") ? 
	parameters["fontsize"] : 172;
    
    var canvas = document.createElement('canvas');
    var context = canvas.getContext('2d');
    context.font = "Bold " + fontsize + "px " + fontface;
    
    // get size data (height depends only on font size)
    var metrics = context.measureText( message );
    var textWidth = metrics.width;
    
    
    // text color
    context.fillStyle = "rgba(0, 0, 0, 1.0)";

    context.fillText( message, 0, fontsize);
    
    // canvas contents will be used for a texture
    var texture = new THREE.Texture(canvas) 
    texture.needsUpdate = true;

    var spriteMaterial = new THREE.SpriteMaterial( 
	{ map: texture, useScreenCoordinates: false} );
    var sprite = new THREE.Sprite( spriteMaterial );
    //sprite.scale.set(10,10,10.0);
    return sprite;	
}
