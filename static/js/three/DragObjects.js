// keeps track of objects that can be dragged with the mouse
// or that can occlude other objects from being dragged with mouse

// DragObjects.objects is array of draggable objects or occluding objects
// if object.draggable=true, then object is draggable otherwise it occludes
// if object.constrain_to_parent=true, then object can only be moved to 
// points on its parent

// can have two cameras so that can includes an orthographic overlay scene
// assumption is that the orthographic camera is pointing from z direction
// and that objects in orthographic overlay scene are in front of 
// regular perspective scene



'use strict';

var DragObjects = function (renderer, camera, parameters) {

    THREE.Object3D.call( this );

    this.renderer = renderer;
    this.container = this.renderer.domElement.parentNode;
    this.camera = camera;
    if(this.camera instanceof THREE.OrthographicCamera) {
	this.cameraIsOrtho = true;
    }
    else {
	this.cameraIsOrtho = false;
    }

    if ( parameters === undefined ) parameters = {};

    this.camera2 = parameters.hasOwnProperty("camera2") ? 
	parameters["camera2"] : null;
    if(this.camera2) {
	if(this.camera2 instanceof THREE.OrthographicCamera) {
	    this.camera2IsOrtho = true;
	}
	else {
	    this.camera2IsOrtho = false;
	}
    }

    this.controls = parameters.hasOwnProperty("controls") ? 
	parameters["controls"] : null;

    // top camera is camera used to check intersections first
    // default is to make topCamera be orthoGraphic camera, if exists,
    this.topCamera = parameters.hasOwnProperty("topCamera") ? 
	parameters["topCamera"] : null;
    if(this.topCamera === null) {
	this.topCamera=1;
	if(this.camera2IsOrtho && !this.cameraIsOrtho) {
	    this.topCamera = 2;
	}
    }
    
    this.linePrecision = parameters.hasOwnProperty("linePrecision") ? 
	parameters["linePrecision"] : null;
    this.parentLinePrecision = parameters.hasOwnProperty("parentLinePrecision") ? 
	parameters["parentLinePrecision"] : null;

    
    this.objects=[];
    this.objects2=[];
    
    this.plane = new THREE.Mesh( new THREE.PlaneGeometry( 2000, 2000, 8, 8 ), 
				 new THREE.MeshBasicMaterial( { opacity: 0.25, 
								transparent: true, wireframe: true } ) );
    this.plane.visible = false;

    this.add( this.plane );

    this.SELECTED=null;
    this.INTERSECTED=null;
    this.POTENTIALHIGHLIGHT=null;
    this.cameraUsed=null;
    this.mouse = new THREE.Vector2();
    this.offset = new THREE.Vector3();
    this.projector = new THREE.Projector();
    this.vector = new THREE.Vector3();
    this.vector2 = new THREE.Vector3();
    this.orthoCameraUsed = false;
    
    // Register a bunch of event listeners for mouse actions.
    renderer.domElement.addEventListener( 'mousemove', onDocumentMouseMove.bind(null, this), false );
    renderer.domElement.addEventListener( 'mousedown', onDocumentMouseDown.bind(null, this), false );
    renderer.domElement.addEventListener( 'mouseup', onDocumentMouseUp.bind(null, this), false );


}

DragObjects.prototype = Object.create( THREE.Object3D.prototype );



function cursorPositionInCanvas(canvas, event) {
    var x, y;
    
    var canoffset = $(canvas).offset();
    x = event.clientX + document.documentElement.scrollLeft - Math.floor(canoffset.left);
    y = event.clientY + document.documentElement.scrollTop - Math.floor(canoffset.top) + 1;
    
    return [x,y];
}

function onDocumentMouseMove(drag, event ) {

    event.preventDefault();
    
    drag.mouse.x = (cursorPositionInCanvas( drag.renderer.domElement, event )[0]) / $(drag.renderer.domElement).width() * 2 - 1;
    drag.mouse.y = - (cursorPositionInCanvas( drag.renderer.domElement, event )[1])/ $(drag.renderer.domElement).height() * 2 + 1;
    
    //console.log(drag.mouse.x + ", "+ drag.mouse.y);


    drag.vector.set( drag.mouse.x, drag.mouse.y, 0.5 );
    // Now get a ray going from the camera into the scene; below we'll check if this
    // ray intersects with anything in dragobjects[], which is an array of points.
    var raycaster;
    if(drag.cameraIsOrtho) {
	// for orthographic camera, using picking Ray
	raycaster = drag.projector.pickingRay(drag.vector, drag.camera);
    }
    else {
	drag.projector.unprojectVector( drag.vector, drag.camera );
	raycaster = new THREE.Raycaster( drag.camera.position, drag.vector.sub( drag.camera.position ).normalize() );
    }
    
    if(drag.linePrecision !== null) {
	raycaster.linePrecision=drag.linePrecision;
    }



    // if have second camera, repeat
    var raycaster2;
    if(drag.camera2) {
	drag.vector2.set( drag.mouse.x, drag.mouse.y, 0.5 );
	if(drag.camera2IsOrtho) {
	    // for orthographic camera, using picking Ray
	    raycaster2 = drag.projector.pickingRay(drag.vector2, drag.camera2);
	}
	else {
	    drag.projector.unprojectVector( drag.vector2, drag.camera2 );
	    raycaster2 = new THREE.Raycaster( drag.camera2.position, drag.vector2.sub( drag.camera2.position ).normalize() );
	}
	if(drag.linePrecision !== null) {
	    raycaster2.linePrecision=drag.linePrecision;
	}
    }


    if ( drag.SELECTED) {
	
	var theparent = drag.SELECTED.parent;
	
	// determine which raycaster used to obtain SELECTED
	var raycasterUsed, cameraUsed;
	if(drag.cameraUsed===2) {
	    raycasterUsed = raycaster2;
	    drag.orthoCameraUsed = drag.camera2IsOrtho;
	    cameraUsed = drag.camera2;
	}
	else {
	    raycasterUsed = raycaster;
	    drag.orthoCameraUsed = drag.cameraIsOrtho;
	    cameraUsed = drag.camera;
	}

	// if SELECTED is constrained to parent
	// move SELECTED to closest intersection of Ray with parent
	// or don't move SELECTED if no intersection.
	// Modify Ray to go through center of SELECTED 
	// rather than mouse pointer.  
	// In this way, SELECTED will have the same relationship
	// to mouse pointer as it is moved along its parent

	if(drag.SELECTED.constrain_to_parent) {
	    // want imprecision for dragging objects along lines
	    if(drag.parentLinePrecision !== null) {
		raycasterUsed.linePrecision=drag.parentLinePrecision;
	    }
	    else {
		raycasterUsed.linePrecision=10; 
	    }

	    if(drag.orthoCameraUsed) {
		drag.vector.copy(raycasterUsed.ray.origin).sub(drag.offset);
		raycasterUsed.set(drag.vector, raycasterUsed.ray.direction);

	    }
	    else {

		// To modify ray to go through the point where the center
		// of SELECTED will be, intersect ray through drag plane,
		// adjust by offset calculated on mouse down
		// then modify ray to go through this offset point
		var intersects = raycasterUsed.intersectObject(drag.plane);
		drag.vector.copy(intersects[ 0 ].point).sub(drag.offset);
		drag.vector.sub( drag.camera.position ).normalize()
		raycasterUsed.set( drag.camera.position, drag.vector);

	    }
	    // now intersect parent with this new ray
	    var intersects=raycasterUsed.intersectObject(theparent);;

	    if (intersects.length > 0) {
		// need to adjust from world coordinates
		// to the coordinates local to the parent
		// this adjusts for rotations and translations
		// of parent and its parents
		drag.SELECTED.position.copy( theparent.worldToLocal(intersects[ 0 ].point));
		// record information about location of parent 
		// on which SELECTED is now positioned
		drag.parent_info = intersects[0];
	    }
	    
	    // if no intersection with parent, then don't move SELECTED
	    // and leave drag.parent_info at previous state

	}
	else {
	    
	    // for unconstrained object using orthographic camera
	    // position at mouse point
	    // offset is vector from location at which grabbed object
	    // to the central position of the object
	    if(drag.orthoCameraUsed) {
		drag.vector.set( drag.mouse.x, drag.mouse.y, 0.5 );
		drag.projector.unprojectVector( drag.vector, cameraUsed );
		drag.vector.sub(drag.offset);
		// adjust for possible transformations of parent
		if(theparent) {
		    theparent.worldToLocal(drag.vector);
		}
		drag.vector.z = drag.SELECTED.position.z;
		drag.SELECTED.position.copy(drag.vector);
		
	    }
	    else {

		// if selected is not constrained to parent
		// move along the invisible drag.plane
		// offset is vector from central position of the object
		// to location where original ray intersected drag plane
		var intersects = raycasterUsed.intersectObject(drag.plane);
		drag.SELECTED.position.copy(intersects[ 0 ].point.sub(drag.offset));
		
		// adjust for any transformations of parent
		if(theparent) {
		    theparent.worldToLocal(drag.SELECTED.position);
		}
	    }
	}
	
	drag.SELECTED.dispatchEvent( { type: 'moved' } );
	return;
	
    }

    // if nothing selected then first try intersection with topCamera.
    // if second camera exist, use that next
    var intersects=null;
    if(drag.topCamera===2) {
	intersects = raycaster2.intersectObjects( drag.objects2 );
	if(intersects.length > 0){
	    drag.cameraUsed=2;
	}
	else {
	    intersects = raycaster.intersectObjects( drag.objects );
	    drag.cameraUsed=1;
	}
    }
    else {
	intersects = raycaster.intersectObjects( drag.objects );
	if(intersects.length > 0){
	    drag.cameraUsed=1;
	}
	else if (raycaster2) {
	    intersects = raycaster2.intersectObjects( drag.objects2 );
	    drag.cameraUsed=2;
	}
    }

    if(drag.cameraUsed === 2) {
	drag.orthoCameraUsed = drag.camera2IsOrtho;
    }
    else {
	drag.orthoCameraUsed = drag.cameraIsOrtho;
    }
    
    if ( intersects.length > 0  && (intersects[ 0 ].object.draggable ||
				    intersects[ 0 ].object.highlightOnHover ||
				    intersects[ 0 ].object.highlightOnClick)) {

	
	if ( drag.INTERSECTED != intersects[ 0 ].object ) {

	    // if previously had a different INTERSECTED
	    // restore appearance of former INTERSECTED
	    if ( drag.INTERSECTED && !drag.INTERSECTED.highlightOnClick) {
		highlightObject(drag.INTERSECTED, false);
	    }

	    // set INTERSECTED to new object
	    drag.INTERSECTED = intersects[ 0 ].object;
	    
	    if(drag.INTERSECTED.draggable || drag.INTERSECTED.highlightOnHover) {
		highlightObject(drag.INTERSECTED);
	    }

	    if(drag.INTERSECTED.draggable) {
		// set drag plane to go through INTERSECTED and
		// be parallel to camera
		// (might not be parallel to camera if position (0,0,0) is not 
		//  in center of screen)
		drag.plane.position.set(0,0,0);
		var theCamera;
		if(drag.cameraUsed===2) {
		    theCamera=drag.camera2;
		}
		else {
		    theCamera=drag.camera;
		}
		drag.plane.lookAt( theCamera.position );
		
		// if drag.INTERSECTED has parent, need to adjust position
		// for possible rotations and translations of parent
		drag.vector.copy(drag.INTERSECTED.position);
		if(drag.INTERSECTED.parent) {
		    drag.plane.position.copy(drag.INTERSECTED.parent.localToWorld(drag.vector));
		}
		else {
		    drag.plane.position.copy(drag.vector);
		}
	    }	    
	}
	if(drag.INTERSECTED.draggable || drag.INTERSECTED.highlightOnClick) {
		drag.container.style.cursor = 'pointer';
	}
	else {
	    drag.container.style.cursor = 'auto';
	}
    }	  
    
    else {
	
	
	// if previously had a INTERSECTED object
	// restore appearance of former INTERSECTED
	if ( drag.INTERSECTED && !drag.INTERSECTED.highlightOnClick) {
	    highlightObject(drag.INTERSECTED, false);
	}	

	drag.INTERSECTED = null;
	
	drag.container.style.cursor = 'auto';
	
    }
    
}

function onDocumentMouseDown( drag, event ) {
    
    event.preventDefault();
    
    // Transform the mouse's 2D screen coordinates to a vector in our 
    // 3D space.  Setting z = 0.5 before unprojecting seems to be a standard kludge
    // with unknown source; even mrdoob says he's not sure about it:
    // http://stackoverflow.com/questions/11036106/three-js-projector-and-ray-objects 

    drag.vector.set( drag.mouse.x, drag.mouse.y, 0.5 );
    // Now get a ray going from the camera into the scene; below we'll check if this
    // ray intersects with anything in dragobjects[], which is an array of points.
    var raycaster;
    if(drag.cameraIsOrtho) {
	// for orthographic camera, using picking Ray
	raycaster = drag.projector.pickingRay(drag.vector, drag.camera);
    }
    else {
	drag.projector.unprojectVector( drag.vector, drag.camera );
	raycaster = new THREE.Raycaster( drag.camera.position, drag.vector.sub( drag.camera.position ).normalize() );
    }
    
    if(drag.linePrecision !== null) {
	raycaster.linePrecision=drag.linePrecision;
    }

    // if have second camera, repeat
    var raycaster2;
    if(drag.camera2) {
	drag.vector2.set( drag.mouse.x, drag.mouse.y, 0.5 );
	if(drag.camera2IsOrtho) {
	    // for orthographic camera, using picking Ray
	    raycaster2 = drag.projector.pickingRay(drag.vector2, drag.camera2);
	}
	else {
	    drag.projector.unprojectVector( drag.vector2, drag.camera2 );
	    raycaster2 = new THREE.Raycaster( drag.camera2.position, drag.vector2.sub( drag.camera2.position ).normalize() );
	}
	if(drag.linePrecision !== null) {
	    raycaster2.linePrecision=drag.linePrecision;
	}
    }


    // first try intersection with topCamera.
    // if second camera exist, use that next
    var intersects=null;
    var raycasterUsed;
    if(drag.topCamera===2) {
	intersects = raycaster2.intersectObjects( drag.objects2 );
	if(intersects.length > 0){
	    drag.cameraUsed=2;
	    raycasterUsed = raycaster2;
	}
	else {
	    intersects = raycaster.intersectObjects( drag.objects );
	    drag.cameraUsed=1;
	    raycasterUsed = raycaster;
	}
    }
    else {
	intersects = raycaster.intersectObjects( drag.objects );
	if(intersects.length > 0){
	    drag.cameraUsed=1;
	    raycasterUsed = raycaster;
	}
	else if (raycaster2) {
	    intersects = raycaster2.intersectObjects( drag.objects2 );
	    drag.cameraUsed=2;
	    raycasterUsed = raycaster2;
	}

    }

    if(drag.cameraUsed === 2) {
	drag.orthoCameraUsed = drag.camera2IsOrtho;
    }
    else {
	drag.orthoCameraUsed = drag.cameraIsOrtho;
    }


    if ( intersects.length > 0) {

	// if have draggable object, then select the object
	// and mark offsets for new positions after mouse move
	if(intersects[0].object.draggable) {
	    
	    if(drag.controls) {
		drag.controls.enabled = false;
	    }

	    drag.SELECTED = intersects[ 0 ].object;
	    
	    if(drag.orthoCameraUsed) {
		// for orthographic camera, offset is vector from
		// actual position of object to intersection point
		drag.offset.copy(intersects[0].point);
		drag.vector.copy(drag.SELECTED.position);

		// adjust for any transformations of parent
		if(drag.SELECTED.parent) {
		    drag.SELECTED.parent.localToWorld(drag.vector);
		}
		drag.offset.sub(drag.vector);

		// for orthographic camera, ignore z direction
		drag.offset.z=0;
	    }
	    else {

		// Record offset as difference between point where ray intersects 
		// the drag plane and the actual position of object.
		// Offset is used to adjust position of objects 
		// so that have same position relative to mouse pointer.
		// Particularly important for spatially extended objects.
		
		var intersectsPlane = raycasterUsed.intersectObject( drag.plane );
		
		drag.offset.copy(intersectsPlane[0].point);
		drag.vector.copy(drag.SELECTED.position);
		
		// adjust for any transformations of parent
		if(drag.SELECTED.parent) {
		    drag.SELECTED.parent.localToWorld(drag.vector);
		}
		drag.offset.sub(drag.vector);

	    }
	    drag.container.style.cursor = 'move';
	}

	// if highlight on click, then mark as an object 
	// to potentially highlight if still intersect object
	// on mouse up
	else if (intersects[0].object.highlightOnClick) {
	    drag.POTENTIALHIGHLIGHT = intersects[0].object;
	}
    }
    
}

function onDocumentMouseUp( drag, event ) {
    
    event.preventDefault();
    if(drag.controls) {
	drag.controls.enabled = true;
    }
    
    if ( drag.INTERSECTED ) {
	
	if(!drag.orthoCameraUsed) {
	    drag.vector.copy(drag.INTERSECTED.position);
	    if(drag.INTERSECTED.parent) {
		drag.INTERSECTED.parent.localToWorld(drag.vector);
	    }
	    drag.plane.position.copy( drag.vector );
	}

	drag.SELECTED = null;
	drag.parent_info = null;

    }
    drag.container.style.cursor = 'auto';
    
    // if click on an object that was flagged as highlightOnClick
    // check if mouse is still over that object,
    // in which case toggle the highlight
    if(drag.POTENTIALHIGHLIGHT) {
	if( drag.POTENTIALHIGHLIGHT === drag.INTERSECTED) {
	    toggleHighlightObject(drag.POTENTIALHIGHLIGHT);
	}
	drag.POTENTIALHIGHLIGHT = null;
    }

}


function toggleHighlightObject(object) {
    if(object.highlighted) {
	highlightObject(object,false);
	object.highlighted=false
    }
    else {
	highlightObject(object);
	object.highlighted=true;
    }
}

// highlight object, or turn off highlight if activate is false
function highlightObject(object, activate) {
    
    if(activate || activate===undefined) {

	// if object has a highlight function, 
	// call that to turn on hightighting
	if (object.highlight) {
	    object.highlight();
	}
	// else change color of object or object it represents
	else {
	    // save color of object or object it represents
	    if(object.represents) {
		object.currentHex = object.represents.material.color.getHex();
	    }
	    else {
		object.currentHex = object.material.color.getHex();
	    }

	    // reduce each color by 1.5 to show intersected
	    var oldHex = object.currentHex;
	    var newHex = Math.ceil((oldHex % 256)/1.5);
	    oldHex -= oldHex % 256;
	    newHex += Math.ceil((oldHex % (256*256))/(1.5*256))*256;
	    oldHex -= oldHex % (256*256);
	    newHex += Math.ceil((oldHex % (256*256*256))/(1.5*256*256))*256*256;
	    // change color of object or object it represents
	    if(object.represents) {
		object.represents.material.color.setHex(newHex);
	    }
	    else {
		object.material.color.setHex(newHex);
	    }
	}
    }
    // turn off highlighting is activate is false
    else {
	// if object has a highlight function, 
	// call that to turn off highlighting
	if(object.highlight) {
	    object.highlight(false);
	}
	// else if object represents another object
	// restore color to that object
	else if(object.represents) {
	    object.represents.material.color.setHex( object.currentHex );
	}
	// else restore color to object
	else {
	    object.material.color.setHex( object.currentHex );
	}

    }
}