// keeps track of objects that can be dragged with the mouse
// or that can occlude other objects from being dragged with mouse

// DragObjects.objects is array of draggable objects or occluding objects
// if object.draggable=true, then object is draggable otherwise it occludes
// if object.constrain_to_parent=true, then object can only be moved to 
// points on its parent

// includes possible orthographic overlay scene
// assumption is that the orthographic camera is pointing from z direction
// and that objects in orthographic overlay scene are in front of 
// regular perspective scene

'use strict';

var DragObjects = function (renderer, camera, container, controls, cameraOrtho) {

    THREE.Object3D.call( this );

    this.objects=[];
    this.objectsOrtho=[];
    
    this.plane = new THREE.Mesh( new THREE.PlaneGeometry( 2000, 2000, 8, 8 ), 
				 new THREE.MeshBasicMaterial( { opacity: 0.25, 
								transparent: true, wireframe: true } ) );
    this.plane.visible = false;

    this.add( this.plane );

    this.SELECTED=null;
    this.INTERSECTED=null;
    this.orthoCameraUsed=false;
    this.mouse = new THREE.Vector2();
    this.offset = new THREE.Vector3();
    this.projector = new THREE.Projector();


    // Register a bunch of event listeners for mouse actions.
    renderer.domElement.addEventListener( 'mousemove', onDocumentMouseMove.bind(null, renderer, camera, this, container, controls, cameraOrtho), false );
    renderer.domElement.addEventListener( 'mousedown', onDocumentMouseDown.bind(null, renderer, camera, this, container, controls, cameraOrtho), false );
    renderer.domElement.addEventListener( 'mouseup', onDocumentMouseUp.bind(null, renderer, camera, this, container, controls, cameraOrtho), false );


}

DragObjects.prototype = Object.create( THREE.Object3D.prototype );



function cursorPositionInCanvas(canvas, event) {
    var x, y;
    
    var canoffset = $(canvas).offset();
    x = event.clientX + document.documentElement.scrollLeft - Math.floor(canoffset.left);
    y = event.clientY + document.documentElement.scrollTop - Math.floor(canoffset.top) + 1;
    
    return [x,y];
}

function onDocumentMouseMove(renderer, camera, drag, container, controls, cameraOrtho, event ) {

    event.preventDefault();
    
    drag.mouse.x = (cursorPositionInCanvas( renderer.domElement, event )[0]) / $(renderer.domElement).width() * 2 - 1;
    drag.mouse.y = - (cursorPositionInCanvas( renderer.domElement, event )[1])/ $(renderer.domElement).height() * 2 + 1;
    
    //console.log(drag.mouse.x + ", "+ drag.mouse.y);


    var vector = new THREE.Vector3( drag.mouse.x, drag.mouse.y, 0.5 );
    drag.projector.unprojectVector( vector, camera );
    // Now get a ray going from the camera into the scene; below we'll check if this
    // ray intersects with anything in dragobjects[], which is an array of points.
    var raycaster = new THREE.Raycaster( camera.position, vector.sub( camera.position ).normalize() );
    

    // if have an orthographic camera, also use a pickingRay
    var raycasterOrtho, vectorOrtho;
    if(cameraOrtho !== undefined) {
	vectorOrtho = new THREE.Vector3(drag.mouse.x, drag.mouse.y, 0.5 );
	raycasterOrtho = drag.projector.pickingRay(vectorOrtho, cameraOrtho);
    }

    if ( drag.SELECTED) {
	
	var theparent = drag.SELECTED.parent;
	
	// if SELECTED is constrained to parent
	// move SELECTED to closest intersection of Ray with parent
	// or don't move SELECTED if no intersection
	// here, we do not compensate for the location on object
	// where it was grabbed, but place the central position of the
	// object along the itersection of the ray with the parent
	if(drag.SELECTED.constrain_to_parent) {
	    // want imprecision for dragging objects along lines
	    raycaster.linePrecision=10; 
	    // if SELECTED was found via orthographic camera
	    // use same camera to intersect parent
	    var intersects;
	    if(drag.orthoCameraUsed) {
		intersects = raycasterOrtho.intersectObject(theparent);
	    }
	    else {
		intersects = raycaster.intersectObject(theparent);
	    }
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
		vectorOrtho.set( drag.mouse.x, drag.mouse.y, 0.5 );
		drag.projector.unprojectVector( vectorOrtho, cameraOrtho );
		vectorOrtho.sub(drag.offset);
		// adjust for possible transformations of parent
		if(theparent) {
		    vectorOrtho.copy(theparent.worldToLocal(vectorOrtho));
		}
		vectorOrtho.z = drag.SELECTED.position.z;
		drag.SELECTED.position.copy(vectorOrtho);
		
	    }
	    else {

		// if selected is not constrained to parent
		// move along the invisible drag.plane
		// offset is vector from location at which grabbed object
		// to the central position of the object
		// adjust for possible transformations of parent
		var intersects = raycaster.intersectObject(drag.plane);
		if(theparent) {
		    drag.SELECTED.position.copy( theparent.worldToLocal(intersects[ 0 ].point.sub(drag.offset)));
		}
		else {
		    drag.SELECTED.position.copy(intersects[ 0 ].point.sub(drag.offset));
		}
	    }
	}
	
	drag.SELECTED.dispatchEvent( { type: 'moved' } );
	return;
	
    }

    // if nothing selected then first try intersection
    // with orthographic camera, if exists, else use projective camera
    var intersects=null;
    if(cameraOrtho !== undefined) {
	intersects = raycasterOrtho.intersectObjects( drag.objectsOrtho );
	if(intersects.length > 0){
	    drag.orthoCameraUsed=true;
	}
	else {
	    intersects=null;
	}
    }
    if(intersects === null) {
	intersects = raycaster.intersectObjects( drag.objects );
	drag.orthoCameraUsed=false;
	
    }
    
    if ( intersects.length > 0  && intersects[ 0 ].object.draggable) {

	if ( drag.INTERSECTED != intersects[ 0 ].object ) {
	    
	    if ( drag.INTERSECTED ) {
		drag.INTERSECTED.material.color.setHex( drag.INTERSECTED.currentHex );
	    }
	    
	    drag.INTERSECTED = intersects[ 0 ].object;
	    drag.INTERSECTED.currentHex = drag.INTERSECTED.material.color.getHex();

	    // reduce each color by 1.5 to show intersected
	    var oldHex = drag.INTERSECTED.currentHex;
	    var newHex = Math.ceil((oldHex % 256)/1.5);
	    oldHex -= oldHex % 256;
	    newHex += Math.ceil((oldHex % (256*256))/(1.5*256))*256;
	    oldHex -= oldHex % (256*256);
	    newHex += Math.ceil((oldHex % (256*256*256))/(1.5*256*256))*256*256;
	    drag.INTERSECTED.material.color.setHex(newHex);
	    
	    if(!drag.orthoCameraUsed && !drag.INTERSECTED.constrain_to_parent) {
		// set drag plane to go through INTERSECTED and
		// be parallel to camera
		// (might not be parallel to camera if position (0,0,0) is not 
		//  in center of screen)
		drag.plane.position.set(0,0,0);
		drag.plane.lookAt( camera.position );
		
		// if drag.INTERSECTED has parent, need to adjust position
		// for possible rotations and translations of parent
		vector.copy(drag.INTERSECTED.position);
		if(drag.INTERSECTED.parent) {
		    drag.plane.position.copy(drag.INTERSECTED.parent.localToWorld(vector));
		}
		else {
		    drag.plane.position.copy(vector);
		}
		
		
	    }
	}    
	container.style.cursor = 'pointer';
    }	  
    
    else {
	
	if ( drag.INTERSECTED ) drag.INTERSECTED.material.color.setHex( drag.INTERSECTED.currentHex );
	
	drag.INTERSECTED = null;
	
	container.style.cursor = 'auto';
	
    }
    
}

function onDocumentMouseDown( renderer, camera, drag, container, controls, cameraOrtho, event ) {
    
    event.preventDefault();
    
    // These two lines transform the mouse's 2D screen coordinates to a vector in our 
    // 3D space.  Setting z = 0.5 before unprojecting seems to be a standard kludge
    // with unknown source; even mrdoob says he's not sure about it:
    // http://stackoverflow.com/questions/11036106/three-js-projector-and-ray-objects 
    var vector = new THREE.Vector3( drag.mouse.x, drag.mouse.y, 0.5 );
    drag.projector.unprojectVector( vector, camera );
    // Now get a ray going from the camera through the mouse cursor. Below we'll check if this
    // ray intersects with any objects.
    var raycaster = new THREE.Raycaster( camera.position, vector.sub( camera.position ).normalize() );
    

    // if have an orthographic camera, also use a pickingRay
    var raycasterOrtho, vectorOrtho;
    if(cameraOrtho !== undefined) {
	vectorOrtho = new THREE.Vector3(drag.mouse.x, drag.mouse.y, 0.5 );
	raycasterOrtho = drag.projector.pickingRay(vectorOrtho, cameraOrtho);
    }


    // first try intersection intersecting using orthographic camera ray
    // if it exists.  If it doesn't exist or didn't intersect and object
    // use projective camera ray
    var intersects=null;
    if(cameraOrtho !== undefined) {
	intersects = raycasterOrtho.intersectObjects( drag.objectsOrtho );
	if(intersects.length > 0){
	    drag.orthoCameraUsed=true;
	}
	else {
	    intersects=null;
	}
    }
    if(intersects === null) {
	intersects = raycaster.intersectObjects( drag.objects );
	drag.orthoCameraUsed=false;

    }


    if ( intersects.length > 0 && intersects[0].object.draggable) {
	
	controls.enabled = false;
	
	drag.SELECTED = intersects[ 0 ].object;
	
	// record offset as difference between point at which
	// grabbed object (intersection) and the actual position
	// of object 
	// offset is used to adjust position of objects when not
	// constrained to parent so that have same position relative
	// to mouse pointer
	// (for objects contrained to parent, center position of
	// object is placed at intersection with parent independent
	// of offset)
	
	drag.offset.copy(intersects[0].point);
	vector.copy(drag.SELECTED.position);

	if(drag.SELECTED.parent) {
	    drag.offset.sub(drag.SELECTED.parent.localToWorld(vector));
	}
	else {
	    drag.offset.sub(vector);
	}
	
	container.style.cursor = 'move';
	
    }
    
}

function onDocumentMouseUp( renderer, camera, drag, container, controls, cameraOrtho, event ) {
    
    event.preventDefault();
    controls.enabled = true;
    
    if ( drag.INTERSECTED ) {
	
	if(!drag.orthoCameraUsed && !drag.INTERSECTED.constrain_to_parent) {
	    var vector = new THREE.Vector3();
	    vector.copy(drag.INTERSECTED.position);
	    if(drag.INTERSECTED.parent) {
		drag.plane.position.copy( drag.INTERSECTED.parent.localToWorld(vector) );
	    }
	    else {
		drag.plane.position.copy( vector );
	    }
	}
	
	drag.SELECTED = null;
	drag.parent_info = null;

    }
    container.style.cursor = 'auto';
}


