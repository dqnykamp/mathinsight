function web3d(){var Y='',V=' top: -1000px;',tb='" for "gwt:onLoadErrorFn"',rb='" for "gwt:onPropertyErrorFn"',cb='");',ub='#',Ub='.cache.js',wb='/',Cb='//',Pb='536C49FADF1D8E06A74107A2135C17F0',Tb=':',Qb=':1',Rb=':2',Sb=':3',lb='::',X='<!doctype html>',Z='<html><head><\/head><body><\/body><\/html>',ob='=',vb='?',qb='Bad handler "',W='CSS1Compat',ab='Chrome',_='DOMContentLoaded',Q='DUMMY',Bb='base',zb='baseUrl',L='begin',R='body',K='bootstrap',yb='clear.cache.gif',nb='content',Wb='end',bb='eval("',Kb='gecko',Lb='gecko1_8',M='gwt.codesvr.web3d=',N='gwt.codesvr=',sb='gwt:onLoadErrorFn',pb='gwt:onPropertyErrorFn',mb='gwt:property',hb='head',Hb='ie10',Jb='ie8',Ib='ie9',S='iframe',xb='img',eb='javascript',T='javascript:""',Vb='loadExternalRefs',ib='meta',gb='moduleRequested',fb='moduleStartup',Gb='msie',jb='name',U='position:absolute; width:0; height:0; border:none; left: -1000px;',Fb='safari',db='script',Nb='selectingPermutation',P='startup',$='undefined',Mb='unknown',Db='user.agent',O='web3d',Ob='web3d.devmode.js',Ab='web3d.nocache.js',kb='web3d::',Eb='webkit';var o=window;var p=document;r(K,L);function q(){var a=o.location.search;return a.indexOf(M)!=-1||a.indexOf(N)!=-1}
function r(a,b){if(o.__gwtStatsEvent){o.__gwtStatsEvent({moduleName:O,sessionId:o.__gwtStatsSessionId,subSystem:P,evtGroup:a,millis:(new Date).getTime(),type:b})}}
web3d.__sendStats=r;web3d.__moduleName=O;web3d.__errFn=null;web3d.__moduleBase=Q;web3d.__softPermutationId=0;web3d.__computePropValue=null;web3d.__getPropMap=null;web3d.__gwtInstallCode=function(){};web3d.__gwtStartLoadingFragment=function(){return null};var s=function(){return false};var t=function(){return null};__propertyErrorFunction=null;var u=o.__gwt_activeModules=o.__gwt_activeModules||{};u[O]={moduleName:O};var v;function w(){B();return v}
function A(){B();return v.getElementsByTagName(R)[0]}
function B(){if(v){return}var a=p.createElement(S);a.src=T;a.id=O;a.style.cssText=U+V;a.tabIndex=-1;p.body.appendChild(a);v=a.contentDocument;if(!v){v=a.contentWindow.document}v.open();var b=document.compatMode==W?X:Y;v.write(b+Z);v.close()}
function C(k){function l(a){function b(){if(typeof p.readyState==$){return typeof p.body!=$&&p.body!=null}return /loaded|complete/.test(p.readyState)}
var c=b();if(c){a();return}function d(){if(!c){c=true;a();if(p.removeEventListener){p.removeEventListener(_,d,false)}if(e){clearInterval(e)}}}
if(p.addEventListener){p.addEventListener(_,d,false)}var e=setInterval(function(){if(b()){d()}},50)}
function m(c){function d(a,b){a.removeChild(b)}
var e=A();var f=w();var g;if(navigator.userAgent.indexOf(ab)>-1&&window.JSON){var h=f.createDocumentFragment();h.appendChild(f.createTextNode(bb));for(var i=0;i<c.length;i++){var j=window.JSON.stringify(c[i]);h.appendChild(f.createTextNode(j.substring(1,j.length-1)))}h.appendChild(f.createTextNode(cb));g=f.createElement(db);g.language=eb;g.appendChild(h);e.appendChild(g);d(e,g)}else{for(var i=0;i<c.length;i++){g=f.createElement(db);g.language=eb;g.text=c[i];e.appendChild(g);d(e,g)}}}
web3d.onScriptDownloaded=function(a){l(function(){m(a)})};r(fb,gb);var n=p.createElement(db);n.src=k;p.getElementsByTagName(hb)[0].appendChild(n)}
web3d.__startLoadingFragment=function(a){return G(a)};web3d.__installRunAsyncCode=function(a){var b=A();var c=w().createElement(db);c.language=eb;c.text=a;b.appendChild(c);b.removeChild(c)};function D(){var c={};var d;var e;var f=p.getElementsByTagName(ib);for(var g=0,h=f.length;g<h;++g){var i=f[g],j=i.getAttribute(jb),k;if(j){j=j.replace(kb,Y);if(j.indexOf(lb)>=0){continue}if(j==mb){k=i.getAttribute(nb);if(k){var l,m=k.indexOf(ob);if(m>=0){j=k.substring(0,m);l=k.substring(m+1)}else{j=k;l=Y}c[j]=l}}else if(j==pb){k=i.getAttribute(nb);if(k){try{d=eval(k)}catch(a){alert(qb+k+rb)}}}else if(j==sb){k=i.getAttribute(nb);if(k){try{e=eval(k)}catch(a){alert(qb+k+tb)}}}}}t=function(a){var b=c[a];return b==null?null:b};__propertyErrorFunction=d;web3d.__errFn=e}
function F(){function e(a){var b=a.lastIndexOf(ub);if(b==-1){b=a.length}var c=a.indexOf(vb);if(c==-1){c=a.length}var d=a.lastIndexOf(wb,Math.min(c,b));return d>=0?a.substring(0,d+1):Y}
function f(a){if(a.match(/^\w+:\/\//)){}else{var b=p.createElement(xb);b.src=a+yb;a=e(b.src)}return a}
function g(){var a=t(zb);if(a!=null){return a}return Y}
function h(){var a=p.getElementsByTagName(db);for(var b=0;b<a.length;++b){if(a[b].src.indexOf(Ab)!=-1){return e(a[b].src)}}return Y}
function i(){var a=p.getElementsByTagName(Bb);if(a.length>0){return a[a.length-1].href}return Y}
function j(){var a=p.location;return a.href==a.protocol+Cb+a.host+a.pathname+a.search+a.hash}
var k=g();if(k==Y){k=h()}if(k==Y){k=i()}if(k==Y&&j()){k=e(p.location.href)}k=f(k);return k}
function G(a){if(a.match(/^\//)){return a}if(a.match(/^[a-zA-Z]+:\/\//)){return a}return web3d.__moduleBase+a}
function H(){var f=[];var g;function h(a,b){var c=f;for(var d=0,e=a.length-1;d<e;++d){c=c[a[d]]||(c[a[d]]=[])}c[a[e]]=b}
var i=[];var j=[];function k(a){var b=j[a](),c=i[a];if(b in c){return b}var d=[];for(var e in c){d[c[e]]=e}if(__propertyErrorFunc){__propertyErrorFunc(a,d,b)}throw null}
j[Db]=function(){var b=navigator.userAgent.toLowerCase();var c=function(a){return parseInt(a[1])*1000+parseInt(a[2])};if(function(){return b.indexOf(Eb)!=-1}())return Fb;if(function(){return b.indexOf(Gb)!=-1&&p.documentMode>=10}())return Hb;if(function(){return b.indexOf(Gb)!=-1&&p.documentMode>=9}())return Ib;if(function(){return b.indexOf(Gb)!=-1&&p.documentMode>=8}())return Jb;if(function(){return b.indexOf(Kb)!=-1}())return Lb;return Mb};i[Db]={gecko1_8:0,ie10:1,ie8:2,ie9:3,safari:4};s=function(a,b){return b in i[a]};web3d.__getPropMap=function(){var a={};for(var b in i){if(i.hasOwnProperty(b)){a[b]=k(b)}}return a};web3d.__computePropValue=k;o.__gwt_activeModules[O].bindings=web3d.__getPropMap;r(K,Nb);if(q()){return G(Ob)}var l;try{h([Lb],Pb);h([Hb],Pb+Qb);h([Ib],Pb+Rb);h([Fb],Pb+Sb);l=f[k(Db)];var m=l.indexOf(Tb);if(m!=-1){g=parseInt(l.substring(m+1),10);l=l.substring(0,m)}}catch(a){}web3d.__softPermutationId=g;return G(l+Ub)}
function I(){if(!o.__gwt_stylesLoaded){o.__gwt_stylesLoaded={}}r(Vb,L);r(Vb,Wb)}
D();web3d.__moduleBase=F();u[O].moduleBase=web3d.__moduleBase;var J=H();I();r(K,Wb);C(J);return true}
web3d.succeeded=web3d();