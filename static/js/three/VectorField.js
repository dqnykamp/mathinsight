
VectorField = function ( F, minx, maxx, dx, miny, maxy, dy, minz, maxz, dz) {

    THREE.Object3D.call( this );
    
    var miniSphereGeometry = new THREE.SphereGeometry( 0.1 );
    var miniSphereMaterial = new THREE.MeshBasicMaterial( { color: 0x999999 } );
    var miniSphere = new THREE.Mesh( miniSphereGeometry, miniSphereMaterial);
    
    for(var x=minx; x<=maxx; x+=dx) {
	for(var y=miny; y<=maxy; y+=dy) {
	    for(var z=minz; z<=maxz; z+=dz) {
		var Fvec = F(x,y,z);
		var Fmag = Math.sqrt(Fvec.x*Fvec.x+Fvec.y*Fvec.y+Fvec.z*Fvec.z);
		var Fdir = Fvec.clone();
		if(Fmag > 0) Fdir.normalize();
		var Forigin = new THREE.Vector3(x,y,z);
		var Fcolor = 0x999999;
		if(Fmag > 0) {
		    // todo: calculate normalization for vector field
		    // Fmag/5 works just for sample vector field
		    this.add(new Arrow(Fdir, Forigin, Fmag/5, Fcolor, Math.min(0.4,0.99*Fmag/5), 0.2, 3,10));
		}
		else {
		    var object = miniSphere.clone();
		    object.position.copy(Forigin);
		    this.add(object);
		}
		
	    }
	}
    }
    
    
};

VectorField.prototype = Object.create( THREE.Object3D.prototype );

