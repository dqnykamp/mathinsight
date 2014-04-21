// create a vector field of arrows

// code is unfinished, as it needs to determine correct normalization
// for length of vectors so that they look reasonable without overlapping
// Will need some way to adjust this length as well, in case particular
// use needs a different normalization

'use strict';

var VectorField = function ( F, params) {

    if (params === undefined){var params = {};}
    
    if (params.minx  === undefined) {params.minx = -1;}
    if (params.maxx  === undefined) {params.maxx = 1;}
    if (params.dx  === undefined) {params.dx = 1;}
    if (params.miny  === undefined) {params.miny = -1;}
    if (params.maxy  === undefined) {params.maxy = 1;}
    if (params.dy  === undefined) {params.dy = 1;}
    if (params.minz  === undefined) {params.minz = -1;}
    if (params.maxz  === undefined) {params.maxz = 1;}
    if (params.dz  === undefined) {params.dz = 1;}
    if (params.lambertMaterial === undefined) {params.lambertMaterial=false;}
    if (params.color === undefined) {params.color=0x999999;}

    var axesSize;
    if (params.axesParams === undefined) {
	axesSize = 1;
    }
    else {
	axesSize = params.axesParams.size instanceof THREE.Vector3 ? Math.max(params.axesParams.size.x, params.axesParams.size.y, params.axesParams.size.z) : params.axesParams.size;
	console.log(axesSize);
    }
    
    THREE.Object3D.call( this );
    
    var miniSphereGeometry = new THREE.SphereGeometry( 0.1 );
    if(params.lambertMaterial) {
	var miniSphereMaterial = new THREE.MeshLambertMaterial( { color: params.color, ambient: params.color } );
    }
    else {
	var miniSphereMaterial = new THREE.MeshBasicMaterial( { color: params.color } );
    }
    var miniSphere = new THREE.Mesh( miniSphereGeometry, miniSphereMaterial);
    
    for(var x=params.minx; x<=params.maxx; x+=params.dx) {
	for(var y=params.miny; y<=params.maxy; y+=params.dy) {
	    for(var z=params.minz; z<=params.maxz; z+=params.dz) {
		var Fvec = F(x,y,z);
		var Fmag = Math.sqrt(Fvec.x*Fvec.x+Fvec.y*Fvec.y+Fvec.z*Fvec.z);
		var Fdir = Fvec.clone();
		if(Fmag > 0) Fdir.normalize();
		var Forigin = new THREE.Vector3(x,y,z);
		var Fcolor = 0x999999;
		if(Fmag > 0) {
		    // todo: calculate normalization for vector field
		    // Fmag/5 works just for sample vector field

		    var arrowProps = {
			dir: Fdir,
			origin: Forigin,
			length: Fmag/axesSize,
			color: Fcolor,
			headLength: Math.min(0.4, 0.99*Fmag/axesSize),
			headWidth: 0.2,
			lineWidth: 3,			
			lambertMaterial:params.lambertMaterial,
		    }
		    //TODO: previously 'arrowProps' was:
		    //Fdir, Forigin, Fmag/5, Fcolor, Math.min(0.4,0.99*Fmag/5), 0.2, 3,10
		    this.add(new Arrow(arrowProps));
		}
		else {
		    var object = miniSphere.clone();
		    object.position.copy(Forigin);
		    this.add(object);
		}
		//dz = Math.max(2, 1/axesSize, Math.sqrt(Fvec.z*Fvec.z)/axesSize);
	    }
	    //dy = Math.max(2, 1/axesSize, Math.sqrt(Fvec.y*Fvec.y)/axesSize);
	}
	//dx = Math.max(2, 1/axesSize, Math.sqrt(Fvec.x*Fvec.x)/axesSize);
    }
};

VectorField.prototype = Object.create( THREE.Object3D.prototype );


