"use strict";(function(global){if(global.DataView)return;if(!global.ArrayBuffer)fail("ArrayBuffer not supported");if(!Object.defineProperties)fail("This module requires ECMAScript 5");var nativele=new Int8Array(new Int32Array([1]).buffer)[0]===1;var temp=new Uint8Array(8);global.DataView=function DataView(buffer,offset,length){if(!(buffer instanceof ArrayBuffer))fail("Bad ArrayBuffer");offset=offset||0;length=length||buffer.byteLength-offset;if(offset<0||length<0||offset+length>buffer.byteLength)fail("Illegal offset and/or length");Object.defineProperties(this,{buffer:{value:buffer,enumerable:false,writable:false,configurable:false},byteOffset:{value:offset,enumerable:false,writable:false,configurable:false},byteLength:{value:length,enumerable:false,writable:false,configurable:false},_bytes:{value:new Uint8Array(buffer,offset,length),enumerable:false,writable:false,configurable:false}})};global.DataView.prototype={constructor:DataView,getInt8:function getInt8(offset){return get(this,Int8Array,1,offset)},getUint8:function getUint8(offset){return get(this,Uint8Array,1,offset)},getInt16:function getInt16(offset,le){return get(this,Int16Array,2,offset,le)},getUint16:function getUint16(offset,le){return get(this,Uint16Array,2,offset,le)},getInt32:function getInt32(offset,le){return get(this,Int32Array,4,offset,le)},getUint32:function getUint32(offset,le){return get(this,Uint32Array,4,offset,le)},getFloat32:function getFloat32(offset,le){return get(this,Float32Array,4,offset,le)},getFloat64:function getFloat32(offset,le){return get(this,Float64Array,8,offset,le)},setInt8:function setInt8(offset,value){set(this,Int8Array,1,offset,value)},setUint8:function setUint8(offset,value){set(this,Uint8Array,1,offset,value)},setInt16:function setInt16(offset,value,le){set(this,Int16Array,2,offset,value,le)},setUint16:function setUint16(offset,value,le){set(this,Uint16Array,2,offset,value,le)},setInt32:function setInt32(offset,value,le){set(this,Int32Array,4,offset,value,le)},setUint32:function setUint32(offset,value,le){set(this,Uint32Array,4,offset,value,le)},setFloat32:function setFloat32(offset,value,le){set(this,Float32Array,4,offset,value,le)},setFloat64:function setFloat64(offset,value,le){set(this,Float64Array,8,offset,value,le)}};function get(view,type,size,offset,le){if(offset===undefined)fail("Missing required offset argument");if(offset<0||offset+size>view.byteLength)fail("Invalid index: "+offset);if(size===1||!!le===nativele){if((view.byteOffset+offset)%size===0)return new type(view.buffer,view.byteOffset+offset,1)[0];else{for(var i=0;i<size;i++)temp[i]=view._bytes[offset+i];return new type(temp.buffer)[0]}}else{for(var i=0;i<size;i++)temp[size-i-1]=view._bytes[offset+i];return new type(temp.buffer)[0]}}function set(view,type,size,offset,value,le){if(offset===undefined)fail("Missing required offset argument");if(value===undefined)fail("Missing required value argument");if(offset<0||offset+size>view.byteLength)fail("Invalid index: "+offset);if(size===1||!!le===nativele){if((view.byteOffset+offset)%size===0){new type(view.buffer,view.byteOffset+offset,1)[0]=value}else{new type(temp.buffer)[0]=value;for(var i=0;i<size;i++)view._bytes[i+offset]=temp[i]}}else{new type(temp.buffer)[0]=value;for(var i=0;i<size;i++)view._bytes[offset+i]=temp[size-1-i]}}function fail(msg){throw new Error(msg)}})(this);