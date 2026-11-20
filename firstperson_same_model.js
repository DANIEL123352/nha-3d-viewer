import * as THREE from './vendor/three.module.js';

const container=document.getElementById('fpContainer');
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
  const m=new THREE.MeshStandardMaterial({color,side:THREE.DoubleSide,roughness:.85,transparent:opacity<.99,opacity,depthWrite:opacity>=.99,metalness:0});
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
  const faceData=window.houseGeomForFPS(i);
  addSourceFaces(g,faceData);
  const sh=new THREE.Group();scene.add(sh);shellGroups.push(sh);addShell(sh,i);
 }
 camera=new THREE.PerspectiveCamera(77,1,.045,90);
 container.prepend(renderer.domElement);
 renderer.domElement.style.touchAction='none';
 const resetSize=()=>{if(!renderer)return;const w=container.clientWidth,h=container.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();};
 new ResizeObserver(resetSize).observe(container);resetSize();
 renderer.domElement.addEventListener('pointerdown',e=>{
  lookId=e.pointerId;lookX=e.clientX;lookY=e.clientY;
  renderer.domElement.setPointerCapture(e.pointerId);e.preventDefault();
 });
 renderer.domElement.addEventListener('pointermove',e=>{
  if(lookId!==e.pointerId)return;
  player.yaw-=(e.clientX-lookX)*.0055;
  player.pitch=Math.max(-1.15,Math.min(1.15,player.pitch+(e.clientY-lookY)*.005));
  lookX=e.clientX;lookY=e.clientY;e.preventDefault();
 });
 for(const event of ['pointerup','pointercancel'])renderer.domElement.addEventListener(event,()=>lookId=null);
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
 status.textContent='Đang xem chính mô hình 3D cũ';
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
 if(active&&renderer){
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
  camera.lookAt(player.x-Math.cos(player.yaw)*Math.cos(player.pitch),player.y+Math.sin(player.pitch),player.z+Math.sin(player.yaw)*Math.cos(player.pitch));
  renderer.render(scene,camera);
 }
 requestAnimationFrame(frame);
}
function setFloor(idx){
 floor=Math.max(0,Math.min(2,idx));
 player.y=elevations[floor]+1.58;
 floorGroups.forEach((g,i)=>g.visible=i===floor);
 shellGroups.forEach((g,i)=>g.visible=i===floor);
 status.textContent='Cùng mô hình cũ · '+names[floor]+' · Vuốt để nhìn quanh';
 document.querySelectorAll('#fpToolbar [data-level]').forEach(el=>el.style.background=Number(el.dataset.level)===floor?'#d0e7f5':'#ffffffec');
}
function spot(name){
 const p=spotsList[name];if(!p)return;
 setFloor(p[0]);player.x=p[1];player.z=p[2];player.yaw=p[3];player.pitch=-.18;
 document.querySelectorAll('#fpSpots [data-spot]').forEach(b=>b.style.background=b.dataset.spot===name?'#cae4f4':'#fff');
}
function show(){
 if(!window.houseGeomForFPS){status.textContent='Dữ liệu mô hình gốc chưa sẵn sàng';return;}
 active=true;document.body.classList.add('fp-active');spots.style.display='flex';
 if(!setup()){active=false;return;}
 setFloor(floor);spot(floor===0?'living':floor===1?'bed2':'terrace');
}
function hide(){active=false;document.body.classList.remove('fp-active');spots.style.display='none';}
enter.addEventListener('click',show);exit.addEventListener('click',hide);
document.querySelectorAll('#fpToolbar [data-level]').forEach(b=>b.addEventListener('click',()=>setFloor(Number(b.dataset.level))));
document.querySelectorAll('#fpSpots [data-spot]').forEach(b=>b.addEventListener('click',()=>spot(b.dataset.spot)));
