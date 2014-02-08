

function cursorPositionInCanvas(canvas, event) {
    var x, y;
    
    canoffset = $(canvas).offset();
    x = event.clientX + document.documentElement.scrollLeft - Math.floor(canoffset.left);
    y = event.clientY + document.documentElement.scrollTop - Math.floor(canoffset.top) + 1;
    
    return [x,y];
}

function onDocumentMouseMove(renderer, camera, drag, container, controls, event ) {

    event.preventDefault();
    
    drag.mouse.x = (cursorPositionInCanvas( renderer.domElement, event )[0]) / $(renderer.domElement).width() * 2 - 1;
    drag.mouse.y = - (cursorPositionInCanvas( renderer.domElement, event )[1])/ $(renderer.domElement).height() * 2 + 1;
    
    //console.log(drag.mouse.x + ", "+ drag.mouse.y);


    var vector = new THREE.Vector3( drag.mouse.x, drag.mouse.y, 0.5 );
    drag.projector.unprojectVector( vector, camera );
    // Now get a ray going from the camera into the scene; below we'll check if this
    // ray intersects with anything in dragobjects[], which is an array of points.
    var raycaster = new THREE.Raycaster( camera.position, vector.sub( camera.position ).normalize() );
    
    if ( drag.SELECTED) {
	
	var theparent = drag.SELECTED.parent;
	
	// haven't implemented how to move if no parent
	if(drag.SELECTED.constrain_to_parent) {
	    var intersects = raycaster.intersectObject(theparent);
	    if (intersects.length > 0) {
		// need to adjust from word coordinates
		// to the coordinates local to the parent
		// this adjusts for rotations and translations
		// of parent and its parents
		drag.SELECTED.position.copy( theparent.worldToLocal(intersects[ 0 ].point));
	    }
	}
	else {
	    var intersects = raycaster.intersectObject(drag.plane);
	    if(theparent) {
		drag.SELECTED.position.copy( theparent.worldToLocal(intersects[ 0 ].point.sub(drag.offset)));
	    }
	    else {
		drag.SELECTED.position.copy(intersects[ 0 ].point.sub(drag.offset));
	    }
	}
	
	drag.SELECTED.dispatchEvent( { type: 'moved' } );
	return;
	
    }
    
    
    var intersects = raycaster.intersectObjects( drag.objects );
    if ( intersects.length > 0  && intersects[ 0 ].object.draggable) {

	if ( drag.INTERSECTED != intersects[ 0 ].object ) {
	    
	    if ( drag.INTERSECTED ) {
		drag.INTERSECTED.material.color.setHex( drag.INTERSECTED.currentHex );
	    }
	    
	    drag.INTERSECTED = intersects[ 0 ].object;
	    drag.INTERSECTED.currentHex = drag.INTERSECTED.material.color.getHex();
	    //drag.INTERSECTED.material.color.setHex(drag.INTERSECTED.currentHex/2);
	    
	    if(! drag.INTERSECTED.constrain_to_parent) {
		drag.plane.position.set(0,0,0);
		drag.plane.lookAt( camera.position );
		
		// if drag.INTERSECTED has parent, need to adjust position
		// for possible rotations and translations of parent
		vector = new THREE.Vector3();
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

function onDocumentMouseDown( renderer, camera, drag, container, controls, event ) {
    
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
    
    // Check what the ray intersects with.
    var intersects = raycaster.intersectObjects( drag.objects );
    
    if ( intersects.length > 0 && intersects[0].object.draggable) {
	
	controls.enabled = false;
	
	drag.SELECTED = intersects[ 0 ].object;
	
	
	
	var intersects = raycaster.intersectObject( drag.plane );
	
	drag.offset.copy( intersects[ 0 ].point ).sub( drag.plane.position );
	
	//console.log("("+offset.x+", "+offset.y+", "+offset.z+")");
	
	
	container.style.cursor = 'move';
	
    }
    
}

function onDocumentMouseUp( renderer, camera, drag, container, controls, event ) {
    
    event.preventDefault();
    controls.enabled = true;
    
    if ( drag.INTERSECTED ) {
	
	vector = new THREE.Vector3();
	vector.copy(drag.INTERSECTED.position);
	if(drag.INTERSECTED.parent) {
	    drag.plane.position.copy( drag.INTERSECTED.parent.localToWorld(vector) );
	}
	else {
	    drag.plane.position.copy( vector );
	}
	
	drag.SELECTED = null;
    }
    container.style.cursor = 'auto';
}


function registerDragListeners(renderer, camera, drag, container, controls) {

    // Register a bunch of event listeners for mouse actions.
    renderer.domElement.addEventListener( 'mousemove', onDocumentMouseMove.bind(null, renderer, camera, drag, container, controls), false );
    renderer.domElement.addEventListener( 'mousedown', onDocumentMouseDown.bind(null, renderer, camera, drag, container, controls), false );
    renderer.domElement.addEventListener( 'mouseup', onDocumentMouseUp.bind(null, renderer, camera, drag, container, controls), false );

}


DragObjects = function () {

    THREE.Object3D.call( this );

    this.objects=[];
    
    this.plane = new THREE.Mesh( new THREE.PlaneGeometry( 2000, 2000, 8, 8 ), 
				 new THREE.MeshBasicMaterial( { color: 0xffffff, opacity: 0.25, 
								transparent: true, wireframe: true } ) );
    this.plane.visible = !true;

    this.add( this.plane );

    this.SELECTED=null;
    this.INTERSECTED=null;
    this.mouse = new THREE.Vector2();
    this.offset = new THREE.Vector3();
    this.projector = new THREE.Projector();

}

DragObjects.prototype = Object.create( THREE.Object3D.prototype );
