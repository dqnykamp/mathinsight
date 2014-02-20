/**
 * @author WestLangley / http://github.com/WestLangley
 * @author zz85 / http://github.com/zz85
 * @author bhouston / http://exocortex.com
 *
 * Creates an arrow for visualizing directions
 *
 * Parameters:
 *  dir - Vector3
 *  origin - Vector3
 *  length - Number
 *  hex - color in hex value
 *  headLength - Number
 *  headWidth - Number
 *  LineWidth - Number
 */

/* modified to include LineWidth */

'use strict';

var Arrow = function ( dir, origin, length, hex, headLength, headWidth, lineWidth, arrowDetail) {

    // dir is assumed to be normalized
    
    THREE.Object3D.call( this );
    
    if ( hex === undefined ) hex = 0xffff00;
    if ( length === undefined ) length = 1;
    if ( headLength === undefined ) headLength = 0.2 * length;
    if ( headWidth === undefined ) headWidth = 0.2 * headLength;
    if ( lineWidth === undefined ) lineWidth = 1;
    if ( arrowDetail === undefined ) arrowDetail = 5;

    this.position = origin;
    
    var lineGeometry = new THREE.Geometry();
    lineGeometry.vertices.push( new THREE.Vector3( 0, 0, 0 ) );
    lineGeometry.vertices.push( new THREE.Vector3( 0, 1, 0 ) );

    this.line = new THREE.Line( lineGeometry, new THREE.LineBasicMaterial( { color: hex, linewidth: lineWidth } ) );
    this.line.matrixAutoUpdate = false;
    this.add( this.line );
    
    var coneGeometry = new THREE.CylinderGeometry( 0, 0.5, 1, arrowDetail, 1 );
    coneGeometry.applyMatrix( new THREE.Matrix4().makeTranslation( 0, - 0.5, 0 ) );

    this.cone = new THREE.Mesh( coneGeometry, new THREE.MeshBasicMaterial( { color: hex } ) );
    this.cone.matrixAutoUpdate = false;
    this.add( this.cone );
    
    this.setDirection( dir );
    this.setLength( length, headLength, headWidth );
    
};

Arrow.prototype = Object.create( THREE.Object3D.prototype );

Arrow.prototype.setDirection = function () {

    var axis = new THREE.Vector3();
    var radians;
    
    return function ( dir ) {
	
	// dir is assumed to be normalized
	
	if ( dir.y > 0.99999 ) {
	    
	    this.quaternion.set( 0, 0, 0, 1 );
	    
	} else if ( dir.y < - 0.99999 ) {
	    
	    this.quaternion.set( 1, 0, 0, 0 );
	    
	} else {
	    
	    axis.set( dir.z, 0, - dir.x ).normalize();
	    
	    radians = Math.acos( dir.y );
	    
	    this.quaternion.setFromAxisAngle( axis, radians );
	    
	}
	
    };
    
}();

Arrow.prototype.setLength = function ( length, headLength, headWidth ) {
    
    if ( headLength === undefined ) headLength = 0.2 * length;
    if ( headWidth === undefined ) headWidth = 0.2 * headLength;
    
    this.line.scale.set( 1, length-headLength, 1 );
    this.line.updateMatrix();
    
    this.cone.scale.set( headWidth, headLength, headWidth );
    this.cone.position.y = length;
    this.cone.updateMatrix();
    
};

Arrow.prototype.setColor = function ( hex ) {

	this.line.material.color.setHex( hex );
	this.cone.material.color.setHex( hex );

};
