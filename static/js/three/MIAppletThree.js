var MIAppletThree = function(container_id, width, height) {
    this.container = document.getElementById(container_id);
    this.width=width;
    this.height=height;
    
    this.namedObjects={};
    
}
    

MIAppletThree.prototype.getValue = function(name) {
    
    var object = this.namedObjects.hasOwnProperty(name) ? 
	this.namedObjects[name] : null;
    if(object===null) {
	return null;
    }
    // return value if getValue method exists
    return object.getValue && object.getValue();
}

MIAppletThree.prototype.getObject = function(name) {
	
    return this.namedObjects.hasOwnProperty(name) ? 
	this.namedObjects[name] : null;
}
    
MIAppletThree.prototype.setValue = function(name, value) {
	
    var object = this.namedObjects.hasOwnProperty(name) ? 
	this.namedObjects[name] : null;
    if(object===null) {
	return null;
    }
    // return value if getValue method exists
    return object.setValue && object.setValue(value, {recursive:false});
}
    
MIAppletThree.prototype.setPosition = function(name, pos) {
    var object = this.namedObjects.hasOwnProperty(name) ? 
	this.namedObjects[name] : null;
    if(object===null) {
	return null;
    }
    // return value if getValue method exists
    return object.setPosition && object.setPosition(pos, {recursive:false});
}
    
MIAppletThree.prototype.registerObjectUpdateListener = function(name, listener) {
    var object = this.namedObjects.hasOwnProperty(name) ? 
	this.namedObjects[name] : null;
    if(object===null) {
	return null;
    }
    object.addEventListener('updated', listener);
}		      
