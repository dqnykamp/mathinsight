/**
 * @author WestLangley / http://github.com/WestLangley
 * @author zz85 / http://github.com/zz85
 * @author bhouston / http://exocortex.com
 *
 * Creates an arrow for visualizing directions
 *
 * Parameters:
 *  dir - Vector3
 *  origin - Vector3 (assumed to be normalized)
 *  length - Number
 *  hex - color in hex value
 *  headLength - Number
 *  headWidth - Number
 *  LineWidth - Number
 */

/* modified to include LineWidth */

'use strict';

var Arrow = function ( parameters) {

    // dir is assumed to be normalized
    
    THREE.Object3D.call( this );
    
    if ( parameters === undefined ) parameters = {};

    this.position = parameters.hasOwnProperty("origin") ? 
	parameters["origin"] : new THREE.Vector3(0,0,0);
    
    var hex =  parameters.hasOwnProperty("hex") ?  parameters["hex"] :
	0xffff00;
    this.headLength = parameters.hasOwnProperty("headLength") ?  
	parameters["headLength"] :  0.2*length;
    this.headWidth = parameters.hasOwnProperty("headWidth") ?  
	parameters["headWidth"] :  0.2*this.headLength;
    var lineWidth = parameters.hasOwnProperty("lineWidth") ?  
	parameters["lineWidth"] :  1;
    var arrowDetail = parameters.hasOwnProperty("arrowDetail") ?  
	parameters["arrowDetail"] :  5;

    this.addTail = parameters.hasOwnProperty("addTail") ?  
	parameters["addTail"] :  false;
    this.tailLength = parameters.hasOwnProperty("tailLength") ?  
	parameters["tailLength"] :  0.2*this.headLength;
    this.tailWidth = parameters.hasOwnProperty("tailWidth") ?  
	parameters["tailWidth"] :  0.8*this.headWidth;

    var lineGeometry = new THREE.Geometry();
    lineGeometry.vertices.push( new THREE.Vector3( 0, 0, 0 ) );
    lineGeometry.vertices.push( new THREE.Vector3( 0, 1, 0 ) );

    this.line = new THREE.Line( lineGeometry, new THREE.LineBasicMaterial( { color: hex, linewidth: lineWidth } ) );
    this.line.matrixAutoUpdate = false;
    this.add( this.line );
    
    var coneGeometry = new THREE.CylinderGeometry( 0, 0.5, 1, arrowDetail, 1 );
    //coneGeometry.applyMatrix( new THREE.Matrix4().makeTranslation( 0, - 0.5, 0 ) );

    this.cone = new THREE.Mesh( coneGeometry, new THREE.MeshBasicMaterial( { color: hex } ) );
    this.cone.matrixAutoUpdate = false;
    this.add( this.cone );
    
    if(this.addTail) {
	var tailGeometry = new THREE.CylinderGeometry( 0.5, 0.5, 1, arrowDetail, 1 );
	tailGeometry.applyMatrix( new THREE.Matrix4().makeTranslation( 0, 0.5, 0 ) );
	this.tail = new THREE.Mesh( tailGeometry, new THREE.MeshBasicMaterial( { color: hex } ) );
	this.tail.matrixAutoUpdate = false;
	this.add(this.tail);
    }


    if(parameters.hasOwnProperty("endpoint")) {
	this.setEndpoint( parameters["endpoint"] );
    }
    else {
	var dir = parameters.hasOwnProperty("dir") ? 
     	    parameters["dir"] : new THREE.Vector3(1,0,0);
	var length = parameters.hasOwnProperty("length") ? 
	    parameters["length"] : 1;

	this.setDirection( dir );
	this.setLength( length );
    }


};

Arrow.prototype = Object.create( THREE.Object3D.prototype );

Arrow.prototype.setEndpoint = function () {
    var dir = new THREE.Vector3();
    var length;

    return function (endpoint, headLength, headWidth, tailLength, tailWidth ) {
    
	dir.copy(endpoint).sub(this.position);
	
	length = dir.length();
	dir.normalize();
	
	this.setLength(length);
	this.setDirection(dir);
	
    };
}();


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

Arrow.prototype.setLength = function ( length, headLength, headWidth, tailLength, tailWidth ) {
    
    if ( headLength === undefined ) {
	headLength = this.headLength;
    }
    else {
	this.headLength = headLength;
    }
    if ( headWidth === undefined ) {
	headWidth = this.headWidth;
    }
    else {
	this.headWidth = headWidth;
    }
    if ( tailLength === undefined ) {
	tailLength = this.tailLength;
    }
    else {
	this.tailLength = tailLength;
    }
    if ( tailWidth === undefined ) {
	tailWidth = this.tailWidth;
    }
    else {
	this.tailWidth = tailWidth;
    }
    
    this.line.scale.set( 1, length-headLength, 1 );
    this.line.updateMatrix();
    
    this.cone.scale.set( headWidth, headLength, headWidth );
    this.cone.position.set(0,length-headLength/2,0);
    this.cone.updateMatrix();

    if(this.addTail) {
	this.tail.scale.set( tailWidth, tailLength, tailWidth );
	this.tail.position.set(0,0,0);
	this.tail.updateMatrix();
	
    }
    
};

Arrow.prototype.setColor = function ( hex ) {

	this.line.material.color.setHex( hex );
	this.cone.material.color.setHex( hex );

};


// return an invisible sphere around the arrow tip
// that can be added to a drag.objects and will move the arrow 
// tip to its new location upon being moved

Arrow.prototype.returnDragTipSphere= function() {
    
    if(this.dragTipSphere) {
	return this.dragTipSphere;
    }
    
    var sphereGeometry = new THREE.SphereGeometry( 0.5 );
    this.dragTipSphere = new THREE.Mesh( sphereGeometry, new THREE.MeshBasicMaterial( ) );
    
    this.dragTipSphere.scale.set(this.headLength*2,this.headLength*2,this.headLength*2);
    
    this.dragTipSphere.draggable=true;
    this.dragTipSphere.visible=false;

    // find position of the cone in coordinates of arrow parent
    // update arrow matrix world since this is probably called before render()
    this.updateMatrixWorld();
    this.dragTipSphere.position.copy(this.cone.position);
    this.localToWorld(this.dragTipSphere.position);
    this.dragTipSphere.represents = this.cone;
    

    var dir = new THREE.Vector3();
    var pos = new THREE.Vector3();

    // create local variables so can refer to arrow and sphere
    // inside listener function
    var thearrow = this;
    var dragTipSphere = this.dragTipSphere;

    
    this.dragTipSphere.addEventListener('moved', function(event) {
	
	// Initialize should be set if called before render has
	// been called to update matrix world of parent and arrow
	// to reflect any transformations made to parent of the sphere
	// or the arrow.  Then localToWorld and worldToLocal
	// will function as expected.
	if(event.initialize) {
	    if(dragTipSphere.parent) {
		dragTipSphere.parent.updateMatrixWorld();
	    }
	    if(thearrow.parent) {
		thearrow.parent.updateMatrixWorld();
	    }
	    else {
		thearrow.updateMatrixWorld();
	    }
	}

    	// find position of the sphere in coordinates of arrow parent
	dir.copy(dragTipSphere.position);
	if(dragTipSphere.parent) {
	    dragTipSphere.parent.localToWorld(dir);
	}
	if(thearrow.parent) {
    	    thearrow.parent.worldToLocal(dir);
	}
    	dir.sub(thearrow.position);
    	var length = dir.length();
    	dir.divideScalar(length);
    	length += thearrow.headLength/2.0;
	
    	thearrow.setDirection( dir );
    	thearrow.setLength( length );
	
    });

    // set position of dragTipSphere to position of arrow tip
    // adjusting for transformations of arrow and sphere parent
    this.dragTipSphere.adjustPosition = function() {
	if(dragTipSphere.parent) {
	    dragTipSphere.parent.updateMatrixWorld();
	}
	thearrow.updateMatrixWorld();
	
    	// find position of the cone in coordinates of sphere parent
    	pos.copy(thearrow.cone.position);
    	thearrow.localToWorld(pos);
	if(dragTipSphere.parent) {
	    dragTipSphere.parent.worldToLocal(pos);
	}
	dragTipSphere.position.copy(pos);

    }

    // create listeners to make sure dragTipSphere is aligned
    // with arrow tip after dragTipSphere or arrow is added
    // to some object
    this.addEventListener('added', function(event) {
	dragTipSphere.adjustPosition();
    });
    
    this.dragTipSphere.addEventListener('added', function(event) {
	dragTipSphere.adjustPosition();
    });


    return this.dragTipSphere;
}


// return an invisible sphere around the arrow tail
// that can be added to a drag.objects and will move the arrow tail
// to its new location upon being moved (preserving location of arrow tip)

Arrow.prototype.returnDragTailSphere= function() {
    
    if(this.dragTailSphere) {
	return this.dragTailSphere;
    }
    

    var sphereGeometry = new THREE.SphereGeometry( 0.5 );
    this.dragTailSphere = new THREE.Mesh( sphereGeometry, new THREE.MeshBasicMaterial( ) );
    this.dragTailSphere.scale.set(this.tailWidth*2,this.tailWidth*2,this.tailWidth*2);


    this.dragTailSphere.draggable=true;
    this.dragTailSphere.visible=false;
    this.updateMatrixWorld();
    this.dragTailSphere.position.set(0,0,0);
    this.localToWorld(this.dragTailSphere.position);
    if(this.tail) {
	this.dragTailSphere.represents = this.tail;
    }
    
    // create local variables so can refer to arrow and sphere
    // inside listener function
    var thearrow = this;
    var dragTailSphere = this.dragTailSphere;

    var dir = new THREE.Vector3();
    var pos = new THREE.Vector3();
    this.dragTailSphere.addEventListener('moved', function(event) {
	
	// Since the moved event could be called multiple times in
	// one render cycle (due to many mouse move events)
	// need to update the world matrix of the arrow to reflect
	// any movements of the arrow in the current render cycle
	// (updateMatrixWorld is called automatically by render)
    	thearrow.updateMatrixWorld();
	
	// Initialize should be set if called before render has
	// been called to update matrix world of parent to reflect
	// any transformations made to parent of the sphere.
	// Then localToWorld and worldToLocal will function as expected.
	if(event.initialize) {
	    if(dragTailSphere.parent) {
		dragTailSphere.parent.updateMatrixWorld();
	    }
	    if(thearrow.parent) {
		thearrow.parent.updateMatrixWorld();
	    }
	}

    	// find position of the cone in coordinates of arrow parent
    	dir.copy(thearrow.cone.position);
    	thearrow.localToWorld(dir);
	pos.copy(dragTailSphere.position);
	if(dragTailSphere.parent) {
	    dragTailSphere.parent.localToWorld(pos);
	}
	if(thearrow.parent) {
    	    thearrow.parent.worldToLocal(dir);
	    thearrow.parent.worldToLocal(pos);
	}
    	dir.sub(pos);
	
    	var length = dir.length();
    	dir.divideScalar(length);
    	length += thearrow.headLength/2.0;
		
    	thearrow.position.copy(pos);

    	thearrow.setDirection( dir );
    	thearrow.setLength( length );
		
    });

    
    this.dragTailSphere.adjustPosition = function() {
	if(dragTailSphere.parent) {
	    dragTailSphere.parent.updateMatrixWorld();
	}
	thearrow.updateMatrixWorld();
	
    	// find position of the cone in coordinates of sphere parent
    	pos.set(0,0,0);
    	thearrow.localToWorld(pos);
	if(dragTailSphere.parent) {
	    dragTailSphere.parent.worldToLocal(pos);
	}
	dragTailSphere.position.copy(pos);

    }

    // create listeners to make sure dragTailSphere is aligned
    // with arrow tip after dragTailSphere or arrow is added
    // to some object
    this.addEventListener('added', function(event) {
	dragTailSphere.adjustPosition();
    });
    
    this.dragTailSphere.addEventListener('added', function(event) {
	dragTailSphere.adjustPosition();
    });

    return this.dragTailSphere;
    
}