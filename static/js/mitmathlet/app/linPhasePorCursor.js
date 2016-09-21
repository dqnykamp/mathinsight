define("app/linPhasePorCursor",["require","underscore","utils","tool","graph","checkbox","hslider","vslider","text","button","curve","line","diamond","polygon","cross","arrow","rectangle"],function(require){"use strict";var _=require("underscore"),U=require("utils"),Tool=require("tool"),Graph=require("graph"),Checkbox=require("checkbox"),HSlider=require("hslider"),VSlider=require("vslider"),Text=require("text"),Button=require("button"),Curve=require("curve"),Line=require("line"),Diamond=require("diamond"),Polygon=require("polygon"),Cross=require("cross"),Arrow=require("arrow"),Rectangle=require("rectangle"),tool,sGraph,detGraph,portraitGraph,thetaSlider,sSlider,trSlider,detSlider,xReadoutText,yReadoutText,eigenval1Text,eigenval2Text,zoneText,diffEqText,matrixLabel,aText,bText,cText,dText,clearBtn,cyanArea,greenArea,yellowArea,parabolaCurve,horizontalLine,verticalLine,sGraphCross,detGraphCross,middleRectangle,bottomLine,topLine,preDrawnCurves=[],fixedPreDrawnArrows=[],movingPreDrawnArrows=
[],preDrawnLines=[],userCurves=[],userArrows=[],userDiamonds=[],initCurvePoints=[],initLinePoints=[new Point2D(1,1),new Point2D(-1,1),new Point2D(-1,-1),new Point2D(1,-1)],initArrowPoints=[new Point2D(1,1),new Point2D(-1,1),new Point2D(-1,-1),new Point2D(1,-1)],arrowTipPoints=[],thetaMin=0,thetaMax=180,sMin=-4,sMax=4,trMin=-4,trMax=4,detMin=-4,detMax=4,theta=0,thetaRad=0,s=1,det=1,tr=1,a=.5,b=1.5,c=-0.5,d=.5,eigen,omega,detPrev=det,trPrev=tr,xPara=[],yPara=[],CLOSE=.05,fitInc=0,radius=2,lastAddedIsArrow,curveClass={cyan:"curve-cyan",green:"curve-green",red:"curve-red",yellow:"curve-yellow"},diamondClass={cyan:"diamond-cyan",green:"diamond-green",red:"diamond-red",yellow:"diamond-yellow"},textClass={cyan:"text-cyan",green:"text-green",red:"text-red",yellow:"text-yellow"},textClassCenter={cyan:"text-cyan-center",green:"text-green-center",red:"text-red-center",yellow:"text-yellow-center"},state={a:a,b:b,c:c,d:d};initializeTool();function getState(){return JSON.stringify(state)}function setState
(stateStr){state=JSON.parse(stateStr),updateStateFromOutside()}function getGrade(){return JSON.stringify(state)}window.linPhasePorCursor={getState:getState,setState:setState,getGrade:getGrade};function updateStateFromOutside(){a=state.a,b=state.b,c=state.c,d=state.d}function updateStateFromInside(){state.a=a,state.b=b,state.c=c,state.d=d}function initializeTool(){try{U.testForFeatures(!1,!1,!1,!0)}catch(err){window.alert(err.toString()+" The tool is disabled.")}U.enableHelpLink("help-text","help-link"),initTool()}function initTool(){var toolContainer=document.getElementById("daimp-tool-container");tool=new Tool(toolContainer),initCurvePoints=getInitCurvePoints(),sGraph=new Graph(80,35,160,160),sGraph.setPlottingBounds(thetaMin,thetaMax,sMin,sMax),tool.add(sGraph),sGraph.addEventListener("mousedown",sGraphMouseHandler),sGraph.addEventListener("mousedrag",sGraphMouseHandler),detGraph=new Graph(sGraph.x,sGraph.y+sGraph.height+142,160,160),detGraph.setPlottingBounds(trMin,trMax,detMin,detMax
),detGraph.hasReadout=!0,tool.add(detGraph),detGraph.addEventListener("mousedown",detGraphMouseHandler),detGraph.addEventListener("mousedrag",detGraphMouseHandler),portraitGraph=new Graph(sGraph.x+sGraph.width+130,sGraph.y,400,400),portraitGraph.setPlottingBounds(-4,4,-4,4),portraitGraph.setXAxis(0),portraitGraph.setXText("x"),portraitGraph.setYAxis(0),portraitGraph.setYText("y"),tool.add(portraitGraph),portraitGraph.addEventListener("mousedown",portraitGraphMouseDown),portraitGraph.addEventListener("mousedrag",portraitGraphMouseDrag),portraitGraph.addEventListener("mouseover",graphShowReadouts),portraitGraph.addEventListener("mousemove",graphShowReadouts),portraitGraph.addEventListener("mouseout",graphHideReadouts),thetaSlider=new HSlider(sGraph.x,sGraph.y+sGraph.height+40,sGraph.width,50),thetaSlider.setPlottingBounds(thetaMin,thetaMax),thetaSlider.setText(U.STR.theta),thetaSlider.setShortTicks(22.5),thetaSlider.setLongTicks(45),thetaSlider.setValue(theta,0,"normal-text",!0),thetaSlider
.setLabels([{x:0,str:"0"},{x:90,str:U.STR.pi+"/2"},{x:180,str:U.STR.pi}]),tool.add(thetaSlider),thetaSlider.addEventListener("mousedown",thetaSliderHandler),thetaSlider.addEventListener("mousedrag",thetaSliderHandler),sSlider=new VSlider(sGraph.x-30,sGraph.y,20,sGraph.height),sSlider.setPlottingBounds(sMin,sMax),sSlider.setText("s"),sSlider.setShortTicks(1),sSlider.setLongTicks(2),sSlider.setValue(s,2),sSlider.setAutomaticLabels(2,0,!1),tool.add(sSlider),sSlider.addEventListener("mousedown",sSliderHandler),sSlider.addEventListener("mousedrag",sSliderHandler),sSlider.addEventListener("mouseup",sSliderHandler),trSlider=new HSlider(detGraph.x,detGraph.y+detGraph.height+40,detGraph.width,50),trSlider.setPlottingBounds(trMin,trMax),trSlider.setText("tr"),trSlider.setShortTicks(1),trSlider.setLongTicks(2),trSlider.setValue(tr,2),trSlider.setAutomaticLabels(2,0,!1),tool.add(trSlider),trSlider.addEventListener("mousedown",detTrSliderHandler),trSlider.addEventListener("mousedrag",detTrSliderHandler
),detSlider=new VSlider(detGraph.x-30,detGraph.y,20,detGraph.height),detSlider.setPlottingBounds(detMin,detMax),detSlider.setText("det"),detSlider.setShortTicks(1),detSlider.setLongTicks(2),detSlider.setValue(det,2),detSlider.setAutomaticLabels(2,0,!1),tool.add(detSlider),detSlider.addEventListener("mousedown",detTrSliderHandler),detSlider.addEventListener("mousedrag",detTrSliderHandler),xReadoutText=new Text(portraitGraph.x,portraitGraph.y+portraitGraph.height+20),xReadoutText.addText("x = ","normal-text"),tool.add(xReadoutText),yReadoutText=new Text(xReadoutText.x,xReadoutText.y+20),yReadoutText.addText("y = ","normal-text"),tool.add(yReadoutText),zoneText=new Text(portraitGraph.x+portraitGraph.width/2,portraitGraph.y+portraitGraph.height+20),zoneText.addText("","centered-text"),tool.add(zoneText),clearBtn=new Button(portraitGraph.x+portraitGraph.width-70,portraitGraph.y+portraitGraph.height+25,70,20),clearBtn.addText("Clear"),tool.add(clearBtn),clearBtn.addEventListener("mousedown",buttonMouseDown
),diffEqText=new Text(zoneText.x,zoneText.y+20),diffEqText.addText("u' = A u","centered-text"),tool.add(diffEqText),matrixLabel=new Text(portraitGraph.x,portraitGraph.y+portraitGraph.height+100),matrixLabel.addText("A = ","normal-text"),tool.add(matrixLabel),aText=new Text(matrixLabel.x+45,matrixLabel.y-10),aText.addText("a","normal-text"),tool.add(aText),bText=new Text(aText.x+60,aText.y),bText.addText("b","normal-text"),tool.add(bText),cText=new Text(aText.x,aText.y+20),cText.addText("c","normal-text"),tool.add(cText),dText=new Text(bText.x,bText.y+20),dText.addText("d","normal-text"),tool.add(dText),addLeftBracket(matrixLabel.x+32,matrixLabel.y-30,50,"mat-a-bracket"),addRightBracket(matrixLabel.x+150,matrixLabel.y-30,50,"mat-a-bracket"),eigenval1Text=new Text(bText.x+166,bText.y),eigenval1Text.addText(U.STR.lambda,"normal-text"),eigenval1Text.addSubScript("1","normal-text"),eigenval1Text.addText(" = ","normal-text"),tool.add(eigenval1Text),eigenval2Text=new Text(dText.x+166,dText.y),
eigenval2Text.addText(U.STR.lambda,"normal-text"),eigenval2Text.addSubScript("2","normal-text"),eigenval2Text.addText(" = ","normal-text"),tool.add(eigenval2Text),portraitGraph.setCrosshairs(!0,!0),eigen=getEigen(),addPreDrawnCurves(),setPreDrawnCurves(),addFixedPreDrawnArrows(),setFixedPreDrawnArrows(),eigen.eigen1.y===0&&(addPreDrawnLines(),setPreDrawnLines(),addMovingPreDrawnArrows(),setMovingPreDrawnArrows()),updateText(),middleRectangle=new Rectangle(sGraph,-1,-1,182,2,"middle-rectangle","bottom-left"),middleRectangle.clipPath=U.createClipPath(sGraph.node,-2,0,sGraph.width+4,sGraph.height),middleRectangle.rectangle.setAttribute("clip-path","url(#"+middleRectangle.clipPath+")"),bottomLine=new Line(sGraph,0,0,180,0,"bottom-top-line"),topLine=new Line(sGraph,0,0,180,0,"bottom-top-line"),sGraphCross=new Cross(sGraph,theta,s,6,1,"s-graph-cross"),updateSGraph();var len=161;xPara=new Array(len),yPara=new Array(len);var i=0,x=trMin,xInc=.05;while(i<len)xPara[i]=x,yPara[i]=parabola(x),x+=xInc
,i++;cyanArea=new Polygon(detGraph,[trMin,0,trMax,0,trMax,detMin,trMin,detMin],"diamond-cyan"),xPara.push(trMax),xPara.push(trMin),yPara.push(0),yPara.push(0),greenArea=new Polygon(detGraph,xPara,yPara,"diamond-green"),xPara.pop(),xPara.pop(),yPara.pop(),yPara.pop(),xPara.push(trMax),xPara.push(trMin),yPara.push(detMax),yPara.push(detMax),yellowArea=new Polygon(detGraph,xPara,yPara,"diamond-yellow"),xPara.pop(),xPara.pop(),yPara.pop(),yPara.pop(),parabolaCurve=new Curve(detGraph,xPara,yPara,"curve-red"),horizontalLine=new Line(detGraph,trMin,0,trMax,0,"curve-red-thick"),verticalLine=new Line(detGraph,0,0,0,detMax,"curve-red"),detGraphCross=new Cross(detGraph,tr,det,6,1,"det-graph-cross"),tool.finalize()}function parabola(x){return x*x/4}function addLeftBracket(x,y,h,cssClass){var l1,l2,l3;l1=U.createLine(tool.svg,x,y,x,y+h,cssClass),l2=U.createLine(tool.svg,x,y,x+6,y,cssClass),l3=U.createLine(tool.svg,x,y+h,x+6,y+h,cssClass)}function addRightBracket(x,y,h,cssClass){var l1,l2,l3;l1=U.createLine
(tool.svg,x,y,x,y+h,cssClass),l2=U.createLine(tool.svg,x,y,x-6,y,cssClass),l3=U.createLine(tool.svg,x,y+h,x-6,y+h,cssClass)}function dxdt(x,y){return a*x+b*y}function dydt(x,y){return c*x+d*y}function buttonMouseDown(){clearPreDrawnShapes(),clearUserShapes()}function thetaSliderHandler(){theta=thetaSlider.value,thetaRad=U.degToRad(theta),initCurvePoints=getInitCurvePoints(),updateSGraph(),calculateMatrix(),detTrSliderHandler()}function sSliderHandler(){s=sSlider.value,updateSGraph(),calculateMatrix(),detTrSliderHandler()}function detTrSliderHandler(){var dT,dD,slope;tr=trSlider.value,det=detSlider.value,nearRedBoundary()&&(dT=tr-trPrev,dD=det-detPrev,nearHorizontalAxis()?fitInc>1&&dD!==0&&(slope=dT/dD,tr=getTrIntWithHorizontalAxis(slope,tr,det),det=0):nearParabola()?(dT!==0&&(slope=dD/dT,tr=getTrIntWithParabola(slope,tr,det)),det=tr*tr/4):nearVerticalAxis()&&fitInc>1&&dT!==0&&(slope=dD/dT,det=getDetIntWithVerticalAxis(slope,tr,det),tr=0),trSlider.setValue(tr),detSlider.setValue(det),fitInc=0
),updateSGraph(),calculateMatrix(),detGraphCross.setXY(tr,det),eigen=getEigen(),trPrev=tr,detPrev=det,clearUserShapes();if(matrixIsZero(a,b,c,d)){buttonMouseDown(),updateText();return}preDrawnCurves.length===0?addPreDrawnCurves():setPreDrawnCurves(),fixedPreDrawnArrows.length===0?(addFixedPreDrawnArrows(),setFixedPreDrawnArrows()):setFixedPreDrawnArrows(),eigen.eigen1.y===0?(preDrawnLines.length===0?(addPreDrawnLines(),setPreDrawnLines()):setPreDrawnLines(),movingPreDrawnArrows.length===0?(addMovingPreDrawnArrows(),setMovingPreDrawnArrows()):setMovingPreDrawnArrows()):(clearShapes(preDrawnLines,"line"),clearShapes(movingPreDrawnArrows,"arrow")),updateText()}function sGraphMouseHandler(mpos){theta=mpos.x,s=mpos.y,thetaSlider.setValue(theta),sSlider.setValue(s),thetaRad=U.degToRad(theta),initCurvePoints=getInitCurvePoints(),updateSGraph(),calculateMatrix(),detTrSliderHandler()}function detGraphMouseHandler(mpos){tr=mpos.x,det=mpos.y,trSlider.setValue(tr),detSlider.setValue(det),updateSGraph
(),calculateMatrix(),detTrSliderHandler(),graphHideReadouts()}function portraitGraphMouseDown(mpos){addUserShape(mpos),setUserShape(mpos),graphShowReadouts(mpos)}function portraitGraphMouseDrag(mpos){setUserShape(mpos),graphShowReadouts(mpos)}function graphHideReadouts(mpos){xReadoutText.setText(0,"x ="),yReadoutText.setText(0,"y =")}function graphShowReadouts(mpos){xReadoutText.setText(0,"x = "+U.floatToString(mpos.x,2)),yReadoutText.setText(0,"y = "+U.floatToString(mpos.y,2))}function calculateMatrix(){var k,l,m1,m2,cos=Math.cos(thetaRad),sin=Math.sin(thetaRad);k=s*s+tr*tr/4-det,l=k>0?Math.sqrt(k):0,m1=new Matrix2D(tr/2,l+s,l-s,tr/2),m2=new Matrix2D(cos,-sin,sin,cos),m2.mult(m1),m2.mult(new Matrix2D(cos,sin,-sin,cos)),a=m2.a11,b=m2.a12,c=m2.a21,d=m2.a22}function updateSGraph(){var omega=det-tr*tr/4;omega>=0?(omega=Math.sqrt(omega),middleRectangle.setRectangle(-1,-omega,182,2*omega),bottomLine.setXY(0,-omega,180,-omega),topLine.setXY(0,omega,180,omega),middleRectangle.setVisibility(!0)
,bottomLine.setVisibility(!0),topLine.setVisibility(!0),s=s<=0?Math.min(s,-omega):Math.max(s,omega)):(middleRectangle.setVisibility(!1),bottomLine.setVisibility(!1),topLine.setVisibility(!1)),sGraphCross.setXY(theta,s),sSlider.setValue(s)}function updateText(){aText.setText(0,U.floatToString(a,2)),bText.setText(0,U.floatToString(b,2)),cText.setText(0,U.floatToString(c,2)),dText.setText(0,U.floatToString(d,2)),zoneText.setText(0,eigen.zone),zoneText.setClass(0,textClassCenter[eigen.color]),eigenval1Text.setClass(0,textClass[eigen.color]),eigenval1Text.setClass(1,textClass[eigen.color]),eigenval1Text.setClass(2,textClass[eigen.color]),eigenval1Text.setText(2," = "+eigen.eigen1.toComplexString(),textClass[eigen.color]),eigenval2Text.setClass(0,textClass[eigen.color]),eigenval2Text.setClass(1,textClass[eigen.color]),eigenval2Text.setClass(2,textClass[eigen.color]),eigenval2Text.setText(2," = "+eigen.eigen2.toComplexString(),textClass[eigen.color])}function inAllowedBounds(pt){var xMin=2*portraitGraph
.xMin,xMax=2*portraitGraph.xMax,yMin=2*portraitGraph.yMin,yMax=2*portraitGraph.yMax;return pt.x<=xMax&&pt.x>=xMin&&pt.y<=yMax&&pt.y>=yMin}function getTrIntWithParabola(slope,tr0,det0){var disc=4*(slope*slope+det0-slope*tr0),tr1,tr2,d1,d2;return disc>=0?(tr1=2*slope-Math.sqrt(disc),tr2=2*slope+Math.sqrt(disc)):(tr1=0,tr2=0),d1=Math.abs(tr1-tr0),d2=Math.abs(tr2-tr0),d1<=d2?tr1:tr2}function getTrIntWithHorizontalAxis(slope,tr0,det0){return tr0-slope*det0}function getDetIntWithVerticalAxis(slope,tr0,det0){return det0-slope*tr0}function nearRedBoundary(){return nearParabola()||nearHorizontalAxis()||nearVerticalAxis()}function nearParabola(){var parab=tr*tr/4;return Math.abs(det-parab)<CLOSE}function nearHorizontalAxis(){return Math.abs(det)<CLOSE}function nearVerticalAxis(){return Math.abs(tr)<CLOSE&&det>=0}function addPreDrawnCurves(){preDrawnCurves.length===0&&_.each(initCurvePoints,function(pt){addSolutionCurve(pt,preDrawnCurves)})}function addFixedPreDrawnArrows(){_.each(initCurvePoints,
function(pt){addSolutionArrow(pt,fixedPreDrawnArrows)})}function addMovingPreDrawnArrows(){var arrow,i;for(i=0;i<4;i++)arrow=new Arrow(portraitGraph,initArrowPoints[i].x,initArrowPoints[i].y,arrowTipPoints[i].x,arrowTipPoints[i].y,diamondClass[eigen.color]),arrow.setHead(3,6),arrow.alwaysShowHead=!0,movingPreDrawnArrows.push(arrow)}function addPreDrawnLines(){_.each(initLinePoints,function(pt){addSolutionLine(pt,preDrawnLines)})}function addUserShape(pt){addSolutionCurve(pt,userCurves),regionIsDiamond(pt)?(addSolutionDiamond(pt,userDiamonds),lastAddedIsArrow=!1):(addSolutionArrow(pt,userArrows),lastAddedIsArrow=!0)}function setPreDrawnCurves(){_.each(initCurvePoints,function(pt,ind){setSolutionCurve(pt,preDrawnCurves,2*ind)})}function setFixedPreDrawnArrows(){_.each(initCurvePoints,function(pt,ind){setSolutionArrow(pt,fixedPreDrawnArrows,ind),crossOnCenter()&&(s>0&&(ind===0||ind===2)||s<0&&(ind===1||ind===3))?fixedPreDrawnArrows[ind].setVisibility(!1):fixedPreDrawnArrows[ind].setVisibility
(!0)})}function setMovingPreDrawnArrows(){var i;for(i=0;i<4;i++)movingPreDrawnArrows[i].setXY(initArrowPoints[i].x,initArrowPoints[i].y,arrowTipPoints[i].x,arrowTipPoints[i].y),movingPreDrawnArrows[i].setClass(diamondClass[eigen.color]),crossOnCenter()||crossOnParabola()?movingPreDrawnArrows[i].setVisibility(!1):movingPreDrawnArrows[i].setVisibility(!0)}function setPreDrawnLines(){var lambda1=eigen.eigen1.x,lambda2=eigen.eigen2.x,slope1,slope2,r=3,xa1,ya1,xa2,ya2,epsilon=1e-5;initLinePoints.length=0,Math.abs(lambda1-d)>=epsilon?slope1=c/(lambda1-d):b!==0?slope1=(lambda1-a)/b:slope1=1e3,Math.abs(lambda2-d)>=epsilon?slope2=c/(lambda2-d):b!==0?slope2=(lambda2-a)/b:slope2=1e3,initLinePoints=[new Point2D(4,4*slope1),new Point2D(-4,-4*slope1),new Point2D(4,4*slope2),new Point2D(-4,-4*slope2)],_.each(initLinePoints,function(pt,ind){setSolutionLine(pt,preDrawnLines,ind),crossOnCenter()||crossOnParabola()?preDrawnLines[ind].setVisibility(!1):preDrawnLines[ind].setVisibility(!0)}),xa1=r/Math.sqrt
(1+slope1*slope1),ya1=slope1*xa1,xa2=r/Math.sqrt(1+slope2*slope2),ya2=slope2*xa2,crossOnParabola()?(arrowTipPoints=[new Point2D(xa1,ya1),new Point2D(-xa1,-ya1),new Point2D(xa1,ya1),new Point2D(-xa1,-ya1)],tr<0?initArrowPoints=[new Point2D(5,5*slope1),new Point2D(-5,-5*slope1),new Point2D(5,5*slope2),new Point2D(-5,-5*slope2)]:initArrowPoints=[new Point2D(0,0),new Point2D(0,0),new Point2D(0,0),new Point2D(0,0)]):(arrowTipPoints=[new Point2D(xa1,ya1),new Point2D(-xa1,-ya1),new Point2D(xa2,ya2),new Point2D(-xa2,-ya2)],eigen.color==="red"||eigen.color==="cyan"?initArrowPoints=[new Point2D(5,5*slope1),new Point2D(-5,-5*slope1),new Point2D(0,0),new Point2D(0,0)]:eigen.color==="green"&&(tr<0?initArrowPoints=[new Point2D(5,5*slope1),new Point2D(-5,-5*slope1),new Point2D(5,5*slope2),new Point2D(-5,-5*slope2)]:initArrowPoints=[new Point2D(0,0),new Point2D(0,0),new Point2D(0,0),new Point2D(0,0)]))}function setUserShape(pt){var isDiamond=regionIsDiamond(pt),arrow,diamond;setSolutionCurve(pt,userCurves
,userCurves.length-2),lastAddedIsArrow?isDiamond?(removeSolutionArrow(),addSolutionDiamond(pt,userDiamonds),setSolutionDiamond(pt,userDiamonds,userDiamonds.length-1),lastAddedIsArrow=!1):setSolutionArrow(pt,userArrows,userArrows.length-1):isDiamond?setSolutionDiamond(pt,userDiamonds,userDiamonds.length-1):(removeSolutionDiamond(),addSolutionArrow(pt,userArrows),setSolutionArrow(pt,userArrows,userArrows.length-1),lastAddedIsArrow=!0)}function clearPreDrawnShapes(pt){clearShapes(preDrawnCurves,"curve"),clearShapes(preDrawnLines,"line"),clearShapes(fixedPreDrawnArrows,"arrow"),clearShapes(movingPreDrawnArrows,"arrow")}function clearUserShapes(pt){clearShapes(userCurves,"curve"),clearShapes(userArrows,"arrow"),clearShapes(userDiamonds,"diamonds")}function addSolutionCurve(pt,curveGroup){var points;points=getSolutionPoints(pt,.05,500),curveGroup.push(new Curve(portraitGraph,points,curveClass[eigen.color])),points=getSolutionPoints(pt,-0.05,500),curveGroup.push(new Curve(portraitGraph,points,
curveClass[eigen.color]))}function addSolutionLine(pt,lineGroup){lineGroup.push(new Line(portraitGraph,0,0,pt.x,pt.y,curveClass[eigen.color]))}function addSolutionArrow(pt,arrowGroup){var nextPt=getSolutionPoints(pt,.02,5),arrow=new Arrow(portraitGraph,pt.x,pt.y,nextPt[2],nextPt[3],diamondClass[eigen.color]);arrow.setHead(3,6),arrow.alwaysShowHead=!0,arrowGroup.push(arrow)}function addSolutionDiamond(pt,diamondGroup){var diamond=new Diamond(portraitGraph,pt.x,pt.y,3,diamondClass[eigen.color]);diamondGroup.push(diamond)}function setSolutionCurve(pt,curveGroup,curveIndex){var points;points=getSolutionPoints(pt,.05,500),curveGroup[curveIndex].setPoints(points),curveGroup[curveIndex].setClass(curveClass[eigen.color]),points=getSolutionPoints(pt,-0.05,500),curveGroup[curveIndex+1].setPoints(points),curveGroup[curveIndex+1].setClass(curveClass[eigen.color])}function setSolutionLine(pt,lineGroup,lineIndex){lineGroup[lineIndex].setXY(0,0,pt.x,pt.y),lineGroup[lineIndex].setClass(curveClass[eigen
.color])}function setSolutionArrow(pt,arrowGroup,arrowIndex){var nextPt=getSolutionPoints(pt,.02,5),deltaX=nextPt[2]-pt.x,deltaY=nextPt[3]-pt.y,slope;deltaX!==0&&(slope=deltaY/deltaX),arrowGroup[arrowIndex].setXY(pt.x,pt.y,nextPt[2],nextPt[3]),arrowGroup[arrowIndex].setClass(diamondClass[eigen.color])}function setSolutionDiamond(pt,diamondGroup,diamondIndex){diamondGroup[diamondIndex].setXY(pt.x,pt.y),diamondGroup[diamondIndex].setClass(diamondClass[eigen.color])}function removeSolutionArrow(){var arrow=userArrows[userArrows.length-1];arrow.line.parentNode.removeChild(arrow.line),arrow.head.parentNode.removeChild(arrow.head),userArrows.pop()}function removeSolutionDiamond(){var diamond=userDiamonds[userDiamonds.length-1];diamond.point.parentNode.removeChild(diamond.point),userDiamonds.pop()}function clearShapes(shapeGroup,shapeType){_.each(shapeGroup,function(shape){shapeType==="curve"?shape.polyline.parentNode.removeChild(shape.polyline):shapeType==="line"?shape.line.parentNode.removeChild
(shape.line):shapeType==="arrow"?(shape.line.parentNode.removeChild(shape.line),shape.head.parentNode.removeChild(shape.head)):shape.point.parentNode.removeChild(shape.point)}),shapeGroup.length=0}function getSolutionPoints(pt0,step,nbrSteps){var pt1,pt2,points=[],i=0;pt1=pt0;while(i<nbrSteps&&inAllowedBounds(pt1))pt2=U.rk4(pt1,step,dxdt,dydt),points.push(pt1.x),points.push(pt1.y),pt1=pt2,i++;return points}function getInitCurvePoints(){var x=radius*Math.cos(thetaRad),y=radius*Math.sin(thetaRad);return[new Point2D(x,y),new Point2D(-y,x),new Point2D(-x,-y),new Point2D(y,-x)]}function Point2D(x,y){this.x=x,this.y=y}function Vector2D(x,y){this.x=x,this.y=y,this.decimalDigits=2,this.toString=function(){var xStr=U.floatToString(this.x,this.decimalDigits),yStr=U.floatToString(this.y,this.decimalDigits);return"( "+xStr+" , "+yStr+" )"},this.toComplexString=function(){var x=roundToZeroWhenSmall(this.x),y=roundToZeroWhenSmall(this.y),xAbsStr=U.floatToString(Math.abs(x),this.decimalDigits),yAbsStr=
U.floatToString(Math.abs(y),this.decimalDigits),yStr=yAbsStr+" i",minusStr=" "+U.STR.minus+" ",plusStr=" "+U.STR.plus+" ";return x>0?y<0?xAbsStr+minusStr+yStr:y===0?xAbsStr:xAbsStr+plusStr+yStr:x===0?y<0?U.STR.minus+yStr:y===0?xAbsStr:yStr:y<0?U.STR.minus+xAbsStr+minusStr+yStr:y===0?U.STR.minus+xAbsStr:U.STR.minus+xAbsStr+plusStr+yStr}}function roundToZeroWhenSmall(val){var small=.01;return Math.abs(val)<.01?0:val}function getEigen(){var disc,r,s,result;return disc=tr*tr-4*det,r=tr/2,s=disc/4,result={},s>0?(det<0?(result.color="cyan",result.zone="saddle"):det===0?(result.color="red",result.zone="degenerate"):(result.color="green",tr<0?result.zone="nodal sink":result.zone="nodal source"),result.eigen1=new Vector2D(r-Math.sqrt(s),0),result.eigen2=new Vector2D(r+Math.sqrt(s),0)):s===0?(result.color="red",tr<0?result.zone="defective nodal sink":tr===0?result.zone="degenerate":result.zone="defective nodal source",result.eigen1=new Vector2D(r,0),result.eigen2=new Vector2D(r,0)):(tr<0?(result.
color="yellow",result.zone="spiral sink"):tr===0?(result.color="red",result.zone="center"):(result.color="yellow",result.zone="spiral source"),result.eigen1=new Vector2D(r,-Math.sqrt(-s)),result.eigen2=new Vector2D(r,Math.sqrt(-s))),result}function trace(a11,a12,a21,a22){return a11+a22}function determinant(a11,a12,a21,a22){return a11*a22-a12*a21}function matrixIsZero(a11,a12,a21,a22){return a11===0&a12===0&&a21===0&&a22===0}function regionIsDiamond(pt){return s>0&&(theta===0||theta===180)&&pt.y===0||matrixIsZero(a,b,c,d)||pt.x===0&&pt.y===0}function crossOnCenter(){return tr===0&&det===0}function crossOnParabola(){return det===tr*tr/4}function Matrix2D(a11,a12,a21,a22){this.a11=a11,this.a12=a12,this.a21=a21,this.a22=a22,this.mult=function(m){var b11=this.a11*m.a11+this.a12*m.a21,b12=this.a11*m.a12+this.a12*m.a22,b21=this.a21*m.a11+this.a22*m.a21,b22=this.a21*m.a12+this.a22*m.a22;this.a11=b11,this.a12=b12,this.a21=b21,this.a22=b22}}});