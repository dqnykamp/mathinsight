function web(){var $='',X=' top: -1000px;',vb='" for "gwt:onLoadErrorFn"',tb='" for "gwt:onPropertyErrorFn"',eb='");',wb='#',Ib='&',gc='.cache.js',yb='/',Eb='//',Zb='9F61182EE8EE5387FE55A1F0E81CA8BD',fc=':',$b=':1',_b=':2',ac=':3',bc=':4',cc=':5',dc=':6',ec=':7',nb='::',Z='<!doctype html>',_='<html><head><\/head><body><\/body><\/html>',qb='=',xb='?',sb='Bad handler "',Y='CSS1Compat',cb='Chrome',bb='DOMContentLoaded',S='DUMMY',Lb='Unexpected exception in locale detection, using default: ',Kb='_',Jb='__gwt_Locale',Yb='ar',Db='base',Bb='baseUrl',N='begin',T='body',M='bootstrap',Ab='clear.cache.gif',pb='content',Gb='default',ic='end',db='eval("',Tb='gecko',Ub='gecko1_8',O='gwt.codesvr.web=',P='gwt.codesvr=',ub='gwt:onLoadErrorFn',rb='gwt:onPropertyErrorFn',ob='gwt:property',jb='head',Qb='ie10',Sb='ie8',Rb='ie9',U='iframe',zb='img',gb='javascript',V='javascript:""',hc='loadExternalRefs',Fb='locale',Hb='locale=',kb='meta',ib='moduleRequested',hb='moduleStartup',Pb='msie',lb='name',W='position:absolute; width:0; height:0; border:none; left: -1000px;',Ob='safari',fb='script',Wb='selectingPermutation',R='startup',ab='undefined',Vb='unknown',Mb='user.agent',Q='web',Xb='web.devmode.js',Cb='web.nocache.js',mb='web::',Nb='webkit';var q=window;var r=document;t(M,N);function s(){var a=q.location.search;return a.indexOf(O)!=-1||a.indexOf(P)!=-1}
function t(a,b){if(q.__gwtStatsEvent){q.__gwtStatsEvent({moduleName:Q,sessionId:q.__gwtStatsSessionId,subSystem:R,evtGroup:a,millis:(new Date).getTime(),type:b})}}
web.__sendStats=t;web.__moduleName=Q;web.__errFn=null;web.__moduleBase=S;web.__softPermutationId=0;web.__computePropValue=null;web.__getPropMap=null;web.__gwtInstallCode=function(){};web.__gwtStartLoadingFragment=function(){return null};var u=function(){return false};var v=function(){return null};__propertyErrorFunction=null;var w=q.__gwt_activeModules=q.__gwt_activeModules||{};w[Q]={moduleName:Q};var A;function B(){D();return A}
function C(){D();return A.getElementsByTagName(T)[0]}
function D(){if(A){return}var a=r.createElement(U);a.src=V;a.id=Q;a.style.cssText=W+X;a.tabIndex=-1;r.body.appendChild(a);A=a.contentDocument;if(!A){A=a.contentWindow.document}A.open();var b=document.compatMode==Y?Z:$;A.write(b+_);A.close()}
function F(k){function l(a){function b(){if(typeof r.readyState==ab){return typeof r.body!=ab&&r.body!=null}return /loaded|complete/.test(r.readyState)}
var c=b();if(c){a();return}function d(){if(!c){c=true;a();if(r.removeEventListener){r.removeEventListener(bb,d,false)}if(e){clearInterval(e)}}}
if(r.addEventListener){r.addEventListener(bb,d,false)}var e=setInterval(function(){if(b()){d()}},50)}
function m(c){function d(a,b){a.removeChild(b)}
var e=C();var f=B();var g;if(navigator.userAgent.indexOf(cb)>-1&&window.JSON){var h=f.createDocumentFragment();h.appendChild(f.createTextNode(db));for(var i=0;i<c.length;i++){var j=window.JSON.stringify(c[i]);h.appendChild(f.createTextNode(j.substring(1,j.length-1)))}h.appendChild(f.createTextNode(eb));g=f.createElement(fb);g.language=gb;g.appendChild(h);e.appendChild(g);d(e,g)}else{for(var i=0;i<c.length;i++){g=f.createElement(fb);g.language=gb;g.text=c[i];e.appendChild(g);d(e,g)}}}
web.onScriptDownloaded=function(a){l(function(){m(a)})};t(hb,ib);var n=r.createElement(fb);n.src=k;r.getElementsByTagName(jb)[0].appendChild(n)}
web.__startLoadingFragment=function(a){return I(a)};web.__installRunAsyncCode=function(a){var b=C();var c=B().createElement(fb);c.language=gb;c.text=a;b.appendChild(c);b.removeChild(c)};function G(){var c={};var d;var e;var f=r.getElementsByTagName(kb);for(var g=0,h=f.length;g<h;++g){var i=f[g],j=i.getAttribute(lb),k;if(j){j=j.replace(mb,$);if(j.indexOf(nb)>=0){continue}if(j==ob){k=i.getAttribute(pb);if(k){var l,m=k.indexOf(qb);if(m>=0){j=k.substring(0,m);l=k.substring(m+1)}else{j=k;l=$}c[j]=l}}else if(j==rb){k=i.getAttribute(pb);if(k){try{d=eval(k)}catch(a){alert(sb+k+tb)}}}else if(j==ub){k=i.getAttribute(pb);if(k){try{e=eval(k)}catch(a){alert(sb+k+vb)}}}}}v=function(a){var b=c[a];return b==null?null:b};__propertyErrorFunction=d;web.__errFn=e}
function H(){function e(a){var b=a.lastIndexOf(wb);if(b==-1){b=a.length}var c=a.indexOf(xb);if(c==-1){c=a.length}var d=a.lastIndexOf(yb,Math.min(c,b));return d>=0?a.substring(0,d+1):$}
function f(a){if(a.match(/^\w+:\/\//)){}else{var b=r.createElement(zb);b.src=a+Ab;a=e(b.src)}return a}
function g(){var a=v(Bb);if(a!=null){return a}return $}
function h(){var a=r.getElementsByTagName(fb);for(var b=0;b<a.length;++b){if(a[b].src.indexOf(Cb)!=-1){return e(a[b].src)}}return $}
function i(){var a=r.getElementsByTagName(Db);if(a.length>0){return a[a.length-1].href}return $}
function j(){var a=r.location;return a.href==a.protocol+Eb+a.host+a.pathname+a.search+a.hash}
var k=g();if(k==$){k=h()}if(k==$){k=i()}if(k==$&&j()){k=e(r.location.href)}k=f(k);return k}
function I(a){if(a.match(/^\//)){return a}if(a.match(/^[a-zA-Z]+:\/\//)){return a}return web.__moduleBase+a}
function J(){var i=[];var j;function k(a,b){var c=i;for(var d=0,e=a.length-1;d<e;++d){c=c[a[d]]||(c[a[d]]=[])}c[a[e]]=b}
var l=[];var m=[];function n(a){var b=m[a](),c=l[a];if(b in c){return b}var d=[];for(var e in c){d[c[e]]=e}if(__propertyErrorFunc){__propertyErrorFunc(a,d,b)}throw null}
m[Fb]=function(){var b=null;var c=Gb;try{if(!b){var d=location.search;var e=d.indexOf(Hb);if(e>=0){var f=d.substring(e+7);var g=d.indexOf(Ib,e);if(g<0){g=d.length}b=d.substring(e+7,g)}}if(!b){b=v(Fb)}if(!b){b=q[Jb]}if(b){c=b}while(b&&!u(Fb,b)){var h=b.lastIndexOf(Kb);if(h<0){b=null;break}b=b.substring(0,h)}}catch(a){alert(Lb+a)}q[Jb]=c;return b||Gb};l[Fb]={ar:0,'default':1};m[Mb]=function(){var b=navigator.userAgent.toLowerCase();var c=function(a){return parseInt(a[1])*1000+parseInt(a[2])};if(function(){return b.indexOf(Nb)!=-1}())return Ob;if(function(){return b.indexOf(Pb)!=-1&&r.documentMode>=10}())return Qb;if(function(){return b.indexOf(Pb)!=-1&&r.documentMode>=9}())return Rb;if(function(){return b.indexOf(Pb)!=-1&&r.documentMode>=8}())return Sb;if(function(){return b.indexOf(Tb)!=-1}())return Ub;return Vb};l[Mb]={gecko1_8:0,ie10:1,ie8:2,ie9:3,safari:4};u=function(a,b){return b in l[a]};web.__getPropMap=function(){var a={};for(var b in l){if(l.hasOwnProperty(b)){a[b]=n(b)}}return a};web.__computePropValue=n;q.__gwt_activeModules[Q].bindings=web.__getPropMap;t(M,Wb);if(s()){return I(Xb)}var o;try{k([Yb,Ub],Zb);k([Yb,Qb],Zb+$b);k([Yb,Rb],Zb+_b);k([Yb,Ob],Zb+ac);k([Gb,Ub],Zb+bc);k([Gb,Qb],Zb+cc);k([Gb,Rb],Zb+dc);k([Gb,Ob],Zb+ec);o=i[n(Fb)][n(Mb)];var p=o.indexOf(fc);if(p!=-1){j=parseInt(o.substring(p+1),10);o=o.substring(0,p)}}catch(a){}web.__softPermutationId=j;return I(o+gc)}
function K(){if(!q.__gwt_stylesLoaded){q.__gwt_stylesLoaded={}}t(hc,N);t(hc,ic)}
G();web.__moduleBase=H();w[Q].moduleBase=web.__moduleBase;var L=J();K();t(M,ic);F(L);return true}
web.succeeded=web();