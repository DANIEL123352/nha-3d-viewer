import * as THREE from './vendor/three.module.js';

const container=document.getElementById('fpContainer');
const stage=document.getElementById('stage');
const orbitHost=document.createElement('div');orbitHost.id='v16OrbitHost';stage.appendChild(orbitHost);
const dimsCanvas=document.createElement('canvas');dimsCanvas.id='v16Dimensions';stage.appendChild(dimsCanvas);
const dimsCtx=dimsCanvas.getContext('2d');
let orbitMode='all',shellClosed=true,showSite=false,revealStairs=false,showDims=false,measurePreset='main';
let classicLook=true; // default: original 3D exploded architectural presentation, not the sealed V16 box.
const EXPLODE_GAP=.73;
let classicLabels=null;

let orbit={az:1.04,alt:.73,dist:31,target:new THREE.Vector3(9.5,6.2,3)};
let roofGroup,siteGroup;
const pointerMap=new Map();

const enter=document.getElementById('fpEnter');
const exit=document.getElementById('fpExit');
const status=document.getElementById('fpStatus');
const spots=document.getElementById('fpSpots');
let renderer=null,scene=null,camera=null,active=false,floor=0;
let walking=null;
let floorGroups=[],shellGroups=[];
const elevations=[.8,4.7,8.3];
const names=['Tầng trệt','Lầu 1','Sân thượng'];
const spotsList={
 living:[0,17.0,2.1,0],kitchen:[0,5.5,4.15,0],hall:[0,9.25,2.1,1.57],
 bed1:[1,4.9,4.35,0],bed2:[1,16.7,2.35,0],
 bed3:[2,4.9,4.35,0],wcRear:[1,4.60,1.00,3.14],
 wcFront:[1,12.35,1.05,3.14],terrace:[2,16.4,3.05,0]
};
let player={x:16.4,z:2.75,y:elevations[0]+1.57,yaw:Math.PI/2,pitch:0};
const keys=new Set();
let move={x:0,z:0,id:null};
let lookId=null,lookX=0,lookY=0,lastTime=performance.now();
const materials=new Map();
function material(color,opacity){
 const key=color+' '+opacity;
 if(!materials.has(key)){
  const m=new THREE.MeshStandardMaterial({color,side:THREE.DoubleSide,roughness:.85,transparent:opacity<.39,opacity:opacity<.39?opacity:1,depthWrite:opacity>=.39,metalness:0});
  materials.set(key,m);
 }
 return materials.get(key);
}
function meshRectangle(group,x1,x2,y1,y2,z1,z2,c=0xf0e9de,a=1){
 const m=new THREE.Mesh(new THREE.BoxGeometry(x2-x1,z2-z1,y2-y1),material(c,a));
 m.position.set((x1+x2)/2,(z1+z2)/2,(y1+y2)/2);group.add(m);return m;
}
function addSourceFaces(group,faces){
 // Render exactly the original home's polygons. The original model's coordinate system
 // is (x length, y width, z elevation); Three uses (x length, y elevation, z width).
 const lineMat=new Map();
 for(const item of faces){
  if(item.line){
   const pts=item.line.map(p=>new THREE.Vector3(p.x,p.z,p.y));
   let c=item.stroke||'#82919f';
   let g=new THREE.BufferGeometry().setFromPoints(pts);
   group.add(new THREE.Line(g,new THREE.LineBasicMaterial({color:c,transparent:true,opacity:.85})));
   continue;
  }
  const v=item.pts;
  if(!v||v.length<3)continue;
  const vertices=[];
  for(let i=1;i<v.length-1;i++)for(const k of [v[0],v[i],v[i+1]])vertices.push(k.x,k.z,k.y);
  const geom=new THREE.BufferGeometry();
  geom.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));
  geom.computeVertexNormals();
  const op=typeof item.alpha==='number'?Math.max(.08,Math.min(1,item.alpha)):1;
  group.add(new THREE.Mesh(geom,material(item.fill||'#dadada',op)));
 }
}

function addRod(group,a,b,radius=.034,color='#668aa0'){
 const delta=b.clone().sub(a),len=delta.length();if(len<.001)return;
 const m=new THREE.Mesh(new THREE.CylinderGeometry(radius,radius,len,7),material(color,1));
 m.position.copy(a).add(b).multiplyScalar(.5);
 m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),delta.normalize());
 group.add(m);
}
function balconyRails(group,idx){
 if(idx===0)return;
 const level=elevations[idx];
 // Independent, thick, watertight railing geometry: no raster/canvas line sorting.
 for(const z of [0,6]){
  addRod(group,new THREE.Vector3(18.85,level+1.06,z),new THREE.Vector3(20.25,level+1.06,z),.047);
  addRod(group,new THREE.Vector3(18.85,level+.53,z),new THREE.Vector3(20.25,level+.53,z),.028);
  for(const x of [18.85,19.55,20.25]){
   addRod(group,new THREE.Vector3(x,level+.05,z),new THREE.Vector3(x,level+1.08,z),.038);
  }
 }
 for(const top of [.54,1.07])addRod(group,new THREE.Vector3(20.25,level+top,.05),new THREE.Vector3(20.25,level+top,5.95),.045);
 for(let i=0;i<=8;i++){
  let z=i*.75;
  addRod(group,new THREE.Vector3(20.25,level+.05,z),new THREE.Vector3(20.25,level+1.08,z),.035);
 }
}
function extraWC(group,idx){
 if(idx<1)return;
 const base=elevations[idx];
 for(const x of (idx===1?[3.82,11.57]:[3.82])){
   // Fixture positions are illustrative only, per KT07/KT08 WC zones.
   meshRectangle(group,x+.16,x+.95,.15,1.06,base+.03,base+.10,0xf2f6f6);
   meshRectangle(group,x+.95,x+.99,.16,1.12,base+.11,base+1.96,0xa7d6e5,.24);
   addRod(group,new THREE.Vector3(x+.52,base+1.90,.24),new THREE.Vector3(x+.52,base+1.92,.58),.020);
   addRod(group,new THREE.Vector3(x+.52,base+1.92,.58),new THREE.Vector3(x+.80,base+1.92,.58),.029);
   meshRectangle(group,x+1.16,x+1.73,.17,.64,base+.68,base+.83,0xf8fafb);
   meshRectangle(group,x+2.12,x+2.59,.38,.90,base+.09,base+.42,0xf6f8f8);
   meshRectangle(group,x+2.13,x+2.61,.82,1.05,base+.36,base+.88,0xf5f8f9);
 }
}
function sourceFloor(i){
 const g=new THREE.Group(),faces=window.houseGeomForFPS(i,revealStairs);
 addSourceFaces(g,faces);balconyRails(g,i);extraWC(g,i);
 return g;
}
function lineOutside(group,a,b,y1,y2,c=0xe2dcd2){
 // fixed floor shell to supply eye-level walls missing from cutaway source.
 const th=.09;
 if(a[0]===b[0])meshRectangle(group,a[0]-th,a[0]+th,Math.min(a[1],b[1]),Math.max(a[1],b[1]),y1,y2,c);
 else meshRectangle(group,Math.min(a[0],b[0]),Math.max(a[0],b[0]),a[1]-th,a[1]+th,y1,y2,c);
}
function addShell(group,idx){
 const base=elevations[idx],top=base+3.20;
 const c=0xe9e5dc;
 // Exact footprint of original house. Walls are representative where drawings lack wall thickness.
 lineOutside(group,[0,0],[0,6],base,top,c);
 lineOutside(group,[0,0],[idx===2?11.15:18.85,0],base,top,c);
 lineOutside(group,[0,6],[idx===2?11.15:18.85,6],base,top,c);
 if(idx!==2)lineOutside(group,[18.85,0],[18.85,6],base,top,c);
 // Leave the middle 1.55-3.5m wide passage open between front/rear and core.
 for(const x of [7,11.15]){
  lineOutside(group,[x,0],[x,1.54],base,top,c);
  lineOutside(group,[x,3.52],[x,6],base,top,c);
  meshRectangle(group,x-.10,x+.10,1.54,3.52,base+2.23,top,c);
 }
 // 3D ceiling exists only while walking; terrace open on front.
 meshRectangle(group,0,idx===2?11.15:18.85,0,6,top,top+.12,0xf8f5ed);
 // Additional shaft walls at stair zone (same KT12 footprint).
 for(const [a,b] of [
 [[7.04,3.56],[7.04,5.93]],
 [[11.10,3.56],[11.10,5.93]],
 [[7.04,5.93],[11.10,5.93]]
 ])lineOutside(group,a,b,base,top,0xd1d5d1);
 // shower and basin WC added by source model; do not duplicate objects.
}
function setup(){
 if(renderer)return true;
 try{
  renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.8));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.15;
 }catch(e){status.textContent='iPhone không hỗ trợ WebGL trong trình xem này. Hãy mở bằng Safari.';return false;}
 scene=new THREE.Scene();scene.background=new THREE.Color('#eaf1f7');
 scene.add(new THREE.HemisphereLight(0xffffff,0xabb9c0,2));
 let sunlight=new THREE.DirectionalLight(0xffffff,1.6);sunlight.position.set(8,15,12);scene.add(sunlight);
 for(let i=0;i<3;i++){
  const g=new THREE.Group();scene.add(g);floorGroups.push(g);
  const faceData=window.houseGeomForFPS(i,revealStairs);
  addSourceFaces(g,faceData);balconyRails(g,i);extraWC(g,i);
  const sh=new THREE.Group();scene.add(sh);shellGroups.push(sh);addShell(sh,i);
 }
 // Original KT09 roof geometry, not a second design.
 roofGroup=new THREE.Group();scene.add(roofGroup);
 if(window.houseGeomForRoof)addSourceFaces(roofGroup,window.houseGeomForRoof());
 siteGroup=new THREE.Group();scene.add(siteGroup);
 meshRectangle(siteGroup,21.85,31.95,-.2,6.3,-.27,-.13,0xa6c4ac);
 meshRectangle(siteGroup,-1,0,0,6,-.27,-.13,0xc1cfc1);
 camera=new THREE.PerspectiveCamera(57,1,.045,130);
 orbitHost.appendChild(renderer.domElement);
 renderer.domElement.style.touchAction='none';
 const resetSize=()=>{if(!renderer)return;
  const target=active?container:orbitHost;
  const w=Math.max(240,target.clientWidth),h=Math.max(240,target.clientHeight);
  renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();
  if(!active){
   const dpr=Math.min(window.devicePixelRatio||1,2);
   dimsCanvas.width=Math.round(w*dpr);dimsCanvas.height=Math.round(h*dpr);
   dimsCanvas.style.width=w+'px';dimsCanvas.style.height=h+'px';
  }
 };
 window.v16Resize=resetSize;
 new ResizeObserver(resetSize).observe(stage);
 new ResizeObserver(resetSize).observe(container);resetSize();
 renderer.domElement.addEventListener('pointerdown',e=>{
  lookId=e.pointerId;lookX=e.clientX;lookY=e.clientY;
  pointerMap.set(e.pointerId,{x:e.clientX,y:e.clientY});
  renderer.domElement.setPointerCapture(e.pointerId);e.preventDefault();
 });
 renderer.domElement.addEventListener('pointermove',e=>{
  if(!pointerMap.has(e.pointerId))return;
  const prev=pointerMap.get(e.pointerId);
  pointerMap.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(pointerMap.size===2 && !active){
    const points=[...pointerMap.values()];
    const dist=Math.hypot(points[0].x-points[1].x,points[0].y-points[1].y);
    if(window.v16Pinch>0)orbit.dist=Math.max(6,Math.min(90,orbit.dist*window.v16Pinch/dist));
    window.v16Pinch=dist;e.preventDefault();return;
  }
  if(lookId!==e.pointerId)return;
  if(active){
   player.yaw-=(e.clientX-prev.x)*.0055;
   player.pitch=Math.max(-1.15,Math.min(1.15,player.pitch-(e.clientY-prev.y)*.005));
  }else{
   orbit.az-=(e.clientX-prev.x)*.008;
   orbit.alt=Math.max(.10,Math.min(1.48,orbit.alt+(e.clientY-prev.y)*.008));
  }
  lookX=e.clientX;lookY=e.clientY;e.preventDefault();
 });
 for(const event of ['pointerup','pointercancel'])
  renderer.domElement.addEventListener(event,e=>{pointerMap.delete(e.pointerId);lookId=null;window.v16Pinch=0});
 renderer.domElement.addEventListener('wheel',e=>{if(!active)orbit.dist=Math.max(6,Math.min(90,orbit.dist+e.deltaY*.026));e.preventDefault()},{passive:false});
 window.addEventListener('keydown',e=>{if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space'].includes(e.code))e.preventDefault();keys.add(e.code);});
 window.addEventListener('keyup',e=>keys.delete(e.code));
 const joystick=document.getElementById('fpJoystick'),knob=document.getElementById('fpKnob');
 function stick(e){
  const rect=joystick.getBoundingClientRect(),dx=e.clientX-(rect.left+rect.width/2),dz=e.clientY-(rect.top+rect.height/2),lim=rect.width*.30;
  const scale=Math.min(1,lim/(Math.hypot(dx,dz)||1));move.x=dx*scale/lim;move.z=dz*scale/lim;
  knob.style.transform='translate('+(move.x*lim)+'px,'+(move.z*lim)+'px)';
 }
 joystick.addEventListener('pointerdown',e=>{move.id=e.pointerId;joystick.setPointerCapture(e.pointerId);stick(e);e.preventDefault()});
 joystick.addEventListener('pointermove',e=>{if(e.pointerId===move.id){stick(e);e.preventDefault()}});
 function stop(e){if(e.pointerId!==move.id)return;move={x:0,z:0,id:null};knob.style.transform='translate(0,0)';}
 joystick.addEventListener('pointerup',stop);joystick.addEventListener('pointercancel',stop);
 status.textContent='V16 · 3D thống nhất, WebGL';
 requestAnimationFrame(frame);
 return true;
}
function validPosition(x,z){
 if(x<.40||x>18.42||z<.38||z>5.62)return false;
 // prevent walking through the solid stair core that stays enclosed by shell
 if(x>7.18&&x<11.01&&z>3.40&&z<5.9)return false;
 return true;
}
function frame(now){
 const dt=Math.min(.055,(now-lastTime)/1000);lastTime=now;
 if(renderer){
   if(active){
     let forward=-move.z,strafe=move.x;
     if(keys.has('KeyW')||keys.has('ArrowUp'))forward++;
     if(keys.has('KeyS')||keys.has('ArrowDown'))forward--;
     if(keys.has('KeyA'))strafe--;
     if(keys.has('KeyD'))strafe++;
     if(keys.has('ArrowLeft'))player.yaw+=dt*1.1;
     if(keys.has('ArrowRight'))player.yaw-=dt*1.1;
     const mag=Math.max(1,Math.hypot(forward,strafe)),speed=2.2;
     const dx=(-Math.cos(player.yaw)*forward+Math.sin(player.yaw)*strafe)/mag*dt*speed;
     const dz=(Math.sin(player.yaw)*forward+Math.cos(player.yaw)*strafe)/mag*dt*speed;
     if(validPosition(player.x+dx,player.z))player.x+=dx;
     if(validPosition(player.x,player.z+dz))player.z+=dz;
     camera.position.set(player.x,player.y,player.z);
     camera.lookAt(player.x-Math.cos(player.yaw)*Math.cos(player.pitch),player.y+Math.sin(player.pitch),
                   player.z+Math.sin(player.yaw)*Math.cos(player.pitch));
   }else{
     const cp=Math.cos(orbit.alt),sp=Math.sin(orbit.alt);
     camera.position.set(orbit.target.x+orbit.dist*cp*Math.cos(orbit.az),
                         orbit.target.y+orbit.dist*sp,
                         orbit.target.z+orbit.dist*cp*Math.sin(orbit.az));
     camera.lookAt(orbit.target);
   }
   renderer.render(scene,camera);
   if(!active){drawV16Dimensions();positionClassicLabels();}
 }
 requestAnimationFrame(frame);
}
function setFloor(idx){
 floor=Math.max(0,Math.min(2,idx));
 player.y=elevations[floor]+1.58;
 floorGroups.forEach((g,i)=>g.visible=i===floor);
 shellGroups.forEach((g,i)=>g.visible=i===floor);
 roofGroup.visible=false;siteGroup.visible=false;
 status.textContent='Cùng mô hình cũ · '+names[floor]+' · Vuốt để nhìn quanh';
 document.querySelectorAll('#fpToolbar [data-level]').forEach(el=>el.style.background=Number(el.dataset.level)===floor?'#d0e7f5':'#ffffffec');
}
function spot(name){
 const p=spotsList[name];if(!p)return;
 setFloor(p[0]);player.x=p[1];player.z=p[2];player.yaw=p[3];player.pitch=-.18;
 document.querySelectorAll('#fpSpots [data-spot]').forEach(b=>b.style.background=b.dataset.spot===name?'#cae4f4':'#fff');
}
function show(){
 floorGroups.forEach(g=>g.position.y=0);roofGroup.position.y=0;
 if(!window.houseGeomForFPS){status.textContent='Dữ liệu mô hình gốc chưa sẵn sàng';return;}
 if(!setup())return;
 active=true;document.body.classList.add('fp-active');spots.style.display='flex';
 container.prepend(renderer.domElement);
 camera.fov=77;camera.updateProjectionMatrix();
 setFloor(floor);spot(floor===0?'living':floor===1?'bed2':'terrace');
 updateClassicStyle();window.v16Resize();
}
function hide(){
 active=false;document.body.classList.remove('fp-active');spots.style.display='none';
 orbitHost.appendChild(renderer.domElement);camera.fov=57;camera.updateProjectionMatrix();
 setOrbitMode(orbitMode);updateClassicStyle();window.v16Resize();
}
enter.addEventListener('click',show);exit.addEventListener('click',hide);
document.querySelectorAll('#fpToolbar [data-level]').forEach(b=>b.addEventListener('click',()=>setFloor(Number(b.dataset.level))));
document.querySelectorAll('#fpSpots [data-spot]').forEach(b=>b.addEventListener('click',()=>spot(b.dataset.spot)));


function drawV16Dimensions(){
 const w=dimsCanvas.clientWidth,h=dimsCanvas.clientHeight;
 if(!w||!h)return;
 const dpr=dimsCanvas.width/w;dimsCtx.setTransform(dpr,0,0,dpr,0,0);
 dimsCtx.clearRect(0,0,w,h);
 if(!showDims||!window.HOUSE_DIMENSIONS_V15)return;
 const project=p=>{
  let offset=0;
  if(classicLook && (orbitMode==='all'||orbitMode==='site') && measurePreset!=='levelMarks'){
    const sourceY=p.z;
    if(sourceY>=elevations[2]-.28 && sourceY<11.50)offset=2*EXPLODE_GAP;
    else if(sourceY>=elevations[1]-.28 && sourceY<elevations[2]-.28)offset=EXPLODE_GAP;
    else if(sourceY>=11.50)offset=3*EXPLODE_GAP;
  }
  const v=new THREE.Vector3(p.x,p.z+offset,p.y).project(camera);
  return {x:(v.x+1)*w/2,y:(1-v.y)*h/2};
 };
 window.HOUSE_DIMENSIONS_V15.draw({ctx:dimsCtx,proj:project,
   P:(x,y,z)=>({x,y,z}),selected:measurePreset,w,h});
}

function createClassicLabels(){
 const wrapper=document.createElement('div');wrapper.id='v17ClassicLabels';
 const items=[
  ['BẾP / BÀN ĂN',0,3.0,2.7,.48],['PHÒNG KHÁCH',0,15.6,2.65,.48],
  ['PHÒNG NGỦ 1',1,2.55,3.4,.62],['PHÒNG NGỦ 2',1,15.95,2.9,.62],
  ['PHÒNG NGỦ 3',2,2.65,3.4,.62],['SÂN THƯỢNG',2,15.6,2.8,.55],
  ['THANG MÁY',1,9.15,4.37,2.70],['MÁI TUM',3,8.8,4.05,11.94]
 ];
 for(const [label,floorNum,x,z,h] of items){
  const el=document.createElement('div');el.className='v17Label';el.textContent=label;
  wrapper.appendChild(el);
 }
 stage.appendChild(wrapper);classicLabels={wrapper,items};
}
function positionClassicLabels(){
 if(!classicLabels || !camera || !renderer)return;
 const enabled=classicLook && !active;
 const wrapper=classicLabels.wrapper;
 wrapper.style.display=enabled?'block':'none';
 if(!enabled)return;
 const rec=orbitHost.getBoundingClientRect();
 if(!rec.width||!rec.height)return;
 const occupied=[];
 [...wrapper.children].forEach((el,index)=>{
  const [label,floorNum,x,z,h]=classicLabels.items[index];
  const show=floorNum===3?(orbitMode==='all'||orbitMode==='site'||orbitMode==='roof'):
    (orbitMode==='all'||orbitMode==='site'||orbitMode==='roof'||orbitMode===['ground','first','terrace'][floorNum]);
  if(!show){el.style.display='none';return;}
  let height=floorNum===3?h+(orbitMode==='all'||orbitMode==='site'?3*EXPLODE_GAP:0):
    elevations[floorNum]+h+((orbitMode==='all'||orbitMode==='site')?floorNum*EXPLODE_GAP:0);
  const pos=new THREE.Vector3(x,height,z).project(camera);
  let sx=(pos.x+1)*rec.width/2,sy=(1-pos.y)*rec.height/2;
  if(pos.z>1 || sx<12||sx>rec.width-12||sy<45||sy>rec.height-22){el.style.display='none';return;}
  const width=label.length*7.1+15;
  if(occupied.some(q=>Math.abs(q.x-sx)<(q.w+width)/2+7 && Math.abs(q.y-sy)<27)){
   el.style.display='none';return;
  }
  occupied.push({x:sx,y:sy,w:width});
  el.style.display='block';
  el.style.left=Math.round(sx)+'px';el.style.top=Math.round(sy)+'px';
 });
}
function updateClassicStyle(){
 const exploded=classicLook && !active && (orbitMode==='all'||orbitMode==='site');
 floorGroups.forEach((g,i)=>{g.position.y=exploded?i*EXPLODE_GAP:0;});
 roofGroup.position.y=exploded?3*EXPLODE_GAP:0;
 // Presentation view uses the older architectural cutaway, but every bar is still a real WebGL mesh.
 // FPS always restores real floor elevations and the enclosure walls.
 shellGroups.forEach((g,i)=>{
  if(active){g.position.y=0;g.visible=i===floor;return;}
  g.position.y=0;
  g.visible=!classicLook && shellClosed && (orbitMode==='all'||orbitMode==='site'||orbitMode==='roof');
 });
 const title=document.getElementById('floorLabel');
 if(title && orbitMode==='all' && !active)title.textContent=classicLook?'Toàn nhà · 3 tầng tách lớp':'Toàn nhà · 3D khối kín';
 const btn=document.getElementById('v17StyleToggle');
 if(btn){btn.textContent=classicLook?'Kiểu 3D cũ ✓':'Kiểu nhà kín ✓';
   btn.classList.toggle('toggle-on',classicLook);}
 const shellButton=document.getElementById('v16ShellToggle');
 if(shellButton){shellButton.style.display=classicLook?'none':'';}
 const badge=document.getElementById('v16Badge');
 if(badge)badge.textContent=(classicLook?'3D CŨ · WEBGL':'3D KHỐI KÍN')+' · '+
  (orbitMode==='all'?'Toàn bộ':orbitMode==='site'?'Sân đất':orbitMode==='roof'?'Mái tum':orbitMode);
 positionClassicLabels();
}
function setOrbitMode(md){
 orbitMode=md;
 const title=document.getElementById('floorLabel');
 if(title)title.textContent=md==='all'?(classicLook?'Toàn nhà · 3 tầng tách lớp':'Toàn nhà · 3D khối kín'):md==='site'?'Khu đất · Mô phỏng ranh đất':md==='roof'?'Mái tum · KT09':md==='ground'?'Tầng trệt · KT06':md==='first'?'Lầu 1 · KT07':'Sân thượng · KT08';
 floorGroups.forEach((g,i)=>g.visible=md==='all'||md==='site'||md==='roof'||md===['ground','first','terrace'][i]);
 shellGroups.forEach((g,i)=>g.visible=shellClosed && (md==='all'||md==='site'||md==='roof'));
 roofGroup.visible=md==='all'||md==='site'||md==='roof';
 siteGroup.visible=showSite||md==='site';
 const target=md==='site'?[16.2,4,3]:md==='roof'?[8.6,9,3]:md==='all'?[9.5,6.2,3]:
    [9.4,elevations[['ground','first','terrace'].indexOf(md)]+1.3,3];
 orbit.target.set(...target);
 if(md==='site')orbit.dist=49;
 else if(md==='roof')orbit.dist=26;
 else if(md==='all')orbit.dist=31;
 else orbit.dist=23;
 updateClassicStyle();
 if(document.getElementById('v16Badge'))document.getElementById('v16Badge').textContent=
    (classicLook?'3D CŨ · WEBGL · ':'3D KHỐI KÍN · ')+(md==='all'?'Toàn bộ':md==='site'?'Sân đất':md==='roof'?'Mái tum':md);
}
function refreshV16FloorGeometry(){
 for(let i=0;i<3;i++){
  const old=floorGroups[i],fresh=new THREE.Group();
  addSourceFaces(fresh,window.houseGeomForFPS(i,revealStairs));
  balconyRails(fresh,i);extraWC(fresh,i);
  scene.add(fresh);floorGroups[i]=fresh;
  old.traverse(o=>{if(o.geometry)o.geometry.dispose()});
  scene.remove(old);
 }
 setOrbitMode(orbitMode);updateClassicStyle();
}
function bindOrbitControls(){
 document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{if(!active)setOrbitMode(b.dataset.mode)}));
 const link=(id,fn)=>document.getElementById(id)?.addEventListener('click',fn);
 link('reset',()=>{orbit.az=1.04;orbit.alt=.73;orbit.dist=31;setOrbitMode('all')});
 link('turnLeft',()=>orbit.az-=Math.PI/6);
 link('turnRight',()=>orbit.az+=Math.PI/6);
 link('zoomIn',()=>orbit.dist=Math.max(6,orbit.dist*.84));
 link('zoomOut',()=>orbit.dist=Math.min(90,orbit.dist*1.19));
 link('siteToggle',()=>{showSite=!showSite;siteGroup.visible=showSite||orbitMode==='site'});
 link('furnitureToggle',()=>{queueMicrotask(()=>{refreshV16FloorGeometry()})});
 link('stairVisualToggle',()=>{revealStairs=!revealStairs;queueMicrotask(refreshV16FloorGeometry)});
 link('dimToggle',()=>queueMicrotask(()=>{showDims=document.getElementById('dimToggle').textContent.includes('Bật')}));
 document.getElementById('measurePreset')?.addEventListener('change',()=>queueMicrotask(()=>{
  measurePreset=document.getElementById('measurePreset').value;
  showDims=true;
  if(measurePreset==='levelMarks' && classicLook)classicLook=false;

  const ps=window.HOUSE_DIMENSIONS_V15?.presets.find(x=>x.id===measurePreset);
  if(!ps)return;
  setOrbitMode(ps.view);
  shellClosed=false;shellGroups.forEach(g=>g.visible=false);
  if(ps.focus)orbit.target.set(ps.focus.x,ps.focus.z,ps.focus.y);
  orbit.dist=Math.max(5.5,30/(ps.zoom||1));updateClassicStyle();
 }));
 const slider=document.getElementById('angleRange');
 if(slider)slider.addEventListener('input',()=>{orbit.az=Number(slider.value)*Math.PI/180});
 // Explicit layer control; all rails remain physical meshes even with outer wall cutaway.
 const button=document.createElement('button');button.type='button';button.id='v16ShellToggle';
 button.textContent='Vỏ nhà: Kín';button.classList.add('toggle-on');
 button.addEventListener('click',()=>{
   shellClosed=!shellClosed;button.classList.toggle('toggle-on',shellClosed);
   button.textContent='Vỏ nhà: '+(shellClosed?'Kín':'Cắt lớp');
   shellGroups.forEach((g,i)=>g.visible=shellClosed&&(orbitMode==='all'||orbitMode==='site'||orbitMode==='roof'));
 });
 document.getElementById('scriptControls')?.appendChild(button);
 const toggle=document.createElement('button');toggle.type='button';toggle.id='v17StyleToggle';
 toggle.className='toggle-on';
 toggle.textContent='Kiểu 3D cũ ✓';
 toggle.title='Chuyển qua lại giữa phối cảnh cũ tách tầng và phối cảnh nhà kín. Các tính năng V16 được giữ nguyên.';
 toggle.addEventListener('click',()=>{
   classicLook=!classicLook;
   updateClassicStyle();
   if(classicLook && orbitMode==='all')orbit.dist=29;
 });
 // Show switch prominently before the enclosing-wall button.
 button.insertAdjacentElement('beforebegin',toggle);

 const badge=document.createElement('span');badge.id='v16Badge';
 badge.textContent='3D KHỐI KÍN · Toàn bộ';
 document.getElementById('scriptControls')?.appendChild(badge);
}

// One true scene, no canvas painter in normal use. Original V15 stays as no-WebGL fallback.
if(setup()){
 hide();
 bindOrbitControls();
 createClassicLabels();
 document.body.classList.add('v16-ready');
 setOrbitMode('all');
 orbit.az=.85;orbit.alt=.72;orbit.dist=30;updateClassicStyle();
}
