/*
 V15: Dimension chains copied from labelled strings on the original
 14-page PDF. One 3D unit equals 1000 mm. No pixel measurements.
 Names "rear/first" are AXIS SPANS, not room clear dimensions.
 Coordinates for cabin/window outlines are schematic (CAD unavailable).
*/
(function(){
 "use strict";
 const p=(id,title,source,view,desc,chains,focus,zoom)=>({id,title,source,view,desc,chains,focus,zoom});
 const x=(from,seq,z,atY=-.42,expected=null,note='')=>({axis:'x',from,seq,z,at:atY,expected,note});
 const y=(from,seq,z,atX=-.50,expected=null,note='')=>({axis:'y',from,seq,z,at:atX,expected,note});
 const v=(from,seq,atX,atY,expected=null,note='')=>({axis:'z',from,seq,atX,atY,expected,note});
 const presets=[
 p('main','Tổng trục nhà: 18.850 × 6.000','KT06–KT09','all','Chỉ đo khoảng cách giữa các trục; KHÔNG phải kích thước thông thủy từng phòng.',[
 x(0,[7000,4150,7700],.80,-.45,18850),y(0,[6000],.80,-.43,6000)
 ],null,1),
 p('site','Tổng chiều dài khu đất / sân','KT01','site','Ranh đất có cạnh xiên; chuỗi dài 32.950 mm chỉ đo theo phương ghi trên KT01, không quy khu đất thành hình chữ nhật.',[
 x(-1,[1000,18850,3000,10100],.08,-.62,32950),
 x(18.85,[1800,1200],.18,6.42,3000,'Sân/bậc 3.000 mm theo KT01/KT06')
 ],{x:16.2,y:3,z:.8},1),
 p('groundRear','Tầng trệt · chia nhịp bếp 7.000','KT06','ground','Mạch số phía dưới KT06: 1.730 + 1.520 + 3.750 = 7.000 mm.',[
 x(0,[1730,1520,3750],.83,-.55,7000)
 ],{x:3.4,y:2.5,z:.80},2.0),
 p('groundCore','Tầng trệt · chia nhịp thang 4.150','KT06','ground','Chuỗi kích thước theo cạnh dưới KT06: 650 + 1.520 + 1.980 = 4.150 mm; KT12 còn có chuỗi thang khác.',[
 x(7,[650,1520,1980],.83,-.50,4150)
 ],{x:9.08,y:2.8,z:.80},2.25),
 p('groundFront','Tầng trệt · chia nhịp khách 7.700','KT06','ground','Chuỗi KT06 bên dưới khu phòng khách.',[
 x(11.15,[1000,1000,3700,1000,1000],.83,-.55,7700)
 ],{x:15,y:2.7,z:.80},2.1),
 p('groundWidth','Tầng trệt · chuỗi ngang A–B','KT06','ground','Bản vẽ đọc B→A: 1.000 + 1.520 + 2.280 + 900 + 300. Dưới đây đảo chiều A→B để đặt đúng trong 3D.',[
 y(0,[300,900,2280,1520,1000],.83,-.70,6000)
 ],{x:2.5,y:3,z:.80},1.8),
 p('firstRear','Lầu 1 · chia nhịp sau 7.000','KT07','first','Nhịp 1–2: 1.115 + 1.520 + 965 + 1.100 + 800 + 1.500 = 7.000 mm. Đây là các đoạn theo chuỗi kích thước, không phải số đo nội thất.',[
 x(0,[1115,1520,965,1100,800,1500],4.73,-.56,7000)
 ],{x:3.4,y:3,z:4.70},2.2),
 p('firstCore','Lầu 1 · chia lõi thang 4.150','KT07','first','Chuỗi ở cạnh dưới KT07: 1.315 + 1.520 + 1.315 = 4.150 mm.',[
 x(7,[1315,1520,1315],4.73,-.5,4150)
 ],{x:9.1,y:2.6,z:4.70},2.25),
 p('firstFront','Lầu 1 · chia nhịp trước 7.700','KT07','first','KT07: 1.400 + 800 + 1.500 + 1.180 + 1.520 + 1.300 = 7.700 mm. Ban công 1.400 mm là đoạn riêng ngoài trục 4.',[
 x(11.15,[1400,800,1500,1180,1520,1300],4.73,-.55,7700),
 x(18.85,[1400],4.73,6.48,1400,'Ban công ngoài trục 4')
 ],{x:15.45,y:2.6,z:4.70},2.0),
 p('wcRear','WC sau · chiều sâu thể hiện trên KT07','KT07','first','Chiều 1.600 mm thể hiện sát khung WC phía sau. Đây chỉ là một phương kích thước WC theo bản vẽ, chưa phải kích thước phòng thông thủy đã bóc CAD.',[
 y(0,[1600],4.73,5.08,1600)
 ],{x:5.08,y:.85,z:4.70},2.5),
 p('terraceWc','WC tầng sân thượng · chiều sâu','KT08','terrace','KT08 ghi 1.600 mm tại chiều sâu khu WC sau; bề dày tường và thiết bị vệ sinh chưa được đo bóc CAD.',[
 y(0,[1600],8.33,5.08,1600)
 ],{x:5.08,y:.84,z:8.30},2.5),
 p('firstWidth','Lầu 1 · chuỗi ngang A–B','KT07','first','KT07 đọc B→A: 800 + 900 + 2.200 + 900 + 1.200 mm. Đảo chiều khi hiển thị từ A→B.',[
 y(0,[1200,900,2200,900,800],4.73,-.67,6000)
 ],{x:2.5,y:3,z:4.70},1.8),
 p('terraceRear','Tầng sân thượng · nhịp phòng ngủ 3','KT08','terrace','Chuỗi 1–2 trùng bố trí khu phòng ngủ phía sau của KT07.',[
 x(0,[1115,1520,965,1100,800,1500],8.33,-.55,7000)
 ],{x:3.3,y:2.7,z:8.3},2.2),
 p('terraceCore','Tầng sân thượng · chia lõi thang','KT08','terrace','KT08: 1.315 + 1.520 + 1.315 mm theo cạnh dưới.',[
 x(7,[1315,1520,1315],8.33,-.52,4150)
 ],{x:9.08,y:2.7,z:8.3},2.2),
 p('terraceWidth','Sân thượng · ngang và mép nhô','KT08','terrace','Mặt bằng KT08: bề ngang 6.000; sân phía trước nhịp 7.700 và mép ngoài 1.400 mm.',[
 y(0,[1200,900,2200,900,800],8.33,-.50,6000),
 x(11.15,[7700,1400],8.33,-.70,9100)
 ],{x:14.5,y:3,z:8.3},1.65),
 p('roofCore','Mái tum · phân đoạn lõi và phần nhô','KT09','roof','Chuỗi 750 + 200 + 2.250 + 200 + 750 mm tại lõi; đoạn mái vượt trục 3 là 1.100 mm.',[
 x(7,[750,200,2250,200,750],11.74,-.43,4150),
 x(11.15,[1100],11.74,6.35,1100)
 ],{x:9.3,y:3,z:11.7},2.05),
 p('roofWidth','Mái tum · các đoạn ngang A–B','KT09','roof','Chuỗi trên hình đọc B→A: 950 + 200 + 1.300 + 200 + 3.350 mm; đảo chiều để thể hiện A→B.',[
 y(0,[3350,200,1300,200,950],11.74,-.57,6000)
 ],{x:6,y:3,z:11.7},1.7),
 p('stairOutline','KT12 · cầu thang bao và chi tiết','KT12','first','Khuôn thang 4.150 × 2.450 mm. Bề ngang thang từ A lên B: 1.250 + 50 + 950 + 200 = 2.450. Kích thước cabin 1.340 × 850 mm là số GHI trên KT12; vị trí chính xác cabin/hố thang cần CAD.',[
 x(7,[950,2250,950],4.73,6.38,4150),
 y(3.55,[1250,50,950,200],4.73,11.32,2450),
 x(8.55,[1340],4.73,4.16,1340,'Vị trí cabin tại đây chỉ là mô phỏng, chưa phải định vị được xác nhận.')
 ],{x:9.08,y:4.55,z:4.7},2.65),
 p('levelMarks','Cao độ mặt đứng (chỉ tạm theo KT10)','KT10 / KT11','all','Dựa vào KT10: +0.800, +4.700, +8.300, +11.700 m; các khoảng cao 3.900 / 3.600 / 3.400 mm. KT11 có ghi khác, KHÔNG được coi đây là cao độ thi công.',[
 v(.80,[3900,3600,3400],19.10,5.90,10900),
 v(11.7,[1500],9.2,5.90,1500,'Phần nhô trên mái theo mặt đứng KT10')
 ],null,.97)
 ];
 for(const ps of presets){
  for(const c of ps.chains){
   const sum=c.seq.reduce((a,b)=>a+b,0);
   if(c.expected!==null&&sum!==c.expected)throw new Error('Sai chuỗi '+ps.id+': '+sum+' thay vì '+c.expected);
  }
 }
 const group=document.createElement('div');
 group.id='preciseDimensionTable';
 group.innerHTML='<h3>Chuỗi kích thước chi tiết mới — lấy theo KT01, KT06–KT12</h3>'+
 '<p class="dimNote">Các kích thước dưới đây là <b>đoạn chia trên trục bản vẽ</b>, không phải chiều dài thông thủy hoặc kích thước đồ nội thất. Chọn một nhóm trong Thước đo 3D để hiện đường đo đúng vị trí của nhịp. Không suy số đo từ pixel ảnh.</p>'+
 '<div class="measureSummary"></div><div class="measureRows"></div>'+
 '<p class="dimNote"><b>Lưu ý:</b> Cửa, vách WC, thiết bị thang máy và nội thất không có đầy đủ kích thước hoặc tọa độ trong PDF; không đưa số mô phỏng vào danh sách đo xác thực. KT10/KT11 có mâu thuẫn cao độ.</p>';
 function pretty(v){return Math.round(v).toLocaleString('de-DE')+' mm';}
 function createTables(){
  const t=presets.map(ps=>{
   let lines=[];
   for(const c of ps.chains){
    let pos=c.from*1000;
    const label=['x','y','z'][['x','y','z'].indexOf(c.axis)];
    c.seq.forEach((v,i)=>{
     const row={name:'Đoạn '+(i+1),value:v,from:pos,to:pos+v,axis:c.axis,note:c.note};
     lines.push(row);pos+=v;
    });
   }
   const rows=lines.map(row=>{
    let sourceLabel=row.axis==='x'?'Dọc nhà (trục 1–4)':row.axis==='y'?'Ngang nhà (A–B)':'Chiều đứng';
    return '<tr><td>'+row.name+'</td><td class="dim-measure">'+pretty(row.value)+'</td><td>'+sourceLabel+'</td></tr>';
   }).join('');
   return '<details><summary>'+ps.title+' <small>('+ps.source+') • '+lines.length+' đoạn</small></summary>'+
   '<p>'+ps.desc+'</p><table><thead><tr><th>Đoạn chia</th><th>Trên PDF</th><th>Phương đo</th></tr></thead><tbody>'+rows+'</tbody></table></details>';
  });
  group.querySelector('.measureRows').innerHTML=t.join('');
  const segments=presets.reduce((a,p)=>a+p.chains.reduce((b,c)=>b+c.seq.length,0),0);
  group.querySelector('.measureSummary').textContent='Đã đối chiếu '+presets.length+' nhóm, '+segments+' đoạn số đo từ bản gốc; mọi chuỗi được kiểm tra tổng bằng số ghi.';
 }
 function init(){
  if(document.getElementById('measurePreset'))return;
  createTables();
  document.getElementById('kich-thuoc-chi-tiet').prepend(group);
  const holder=document.createElement('div');
  holder.className='measureSelector';
  holder.innerHTML='<label for="measurePreset"><b>Nhóm thước đo 3D</b></label><select id="measurePreset" aria-label="Chọn nhóm kích thước">'+presets.map(ps=>'<option value="'+ps.id+'">'+ps.title+'</option>').join('')+'</select><div id="measureDesc">Chọn nhóm để tự chuyển tới tầng tương ứng, rồi xem số đo ngay trên mô hình.</div><div id="measureWarning">Số đo trên trục là số ghi trực tiếp từ PDF. Các đoạn quá nhỏ được đánh dấu và liệt kê đầy đủ ở bảng.</div>';
  document.getElementById('dimToggle').insertAdjacentElement('afterend',holder);
 }
 // Hosted SVG/Canvas painter uses the exact same 3D camera as the house renderer.
 function draw({ctx,proj,P,selected='main',w,h}){
  const ps=presets.find(p=>p.id===selected)||presets[0];
  const markers=[];
  const LINE='#154f7d',HELP='#5488a8';
  ctx.save();ctx.setLineDash([]);ctx.textAlign='center';
  for(let j=0;j<ps.chains.length;j++){
   const c=ps.chains[j];let current=c.from;
   const toPoint=q=>c.axis==='x'?P(q,c.at,c.z):
     c.axis==='y'?P(c.at,q,c.z):P(c.atX,c.atY,q);
   const guidePoint=q=>c.axis==='x'?P(q,c.at+(c.at<3?.16:-.16),c.z):
     c.axis==='y'?P(c.at+(c.at<9?.2:-.2),q,c.z):P(c.atX+.18,c.atY,q);
   for(let i=0;i<c.seq.length;i++){
    let next=current+c.seq[i]/1000;
    const a=proj(toPoint(current)),b=proj(toPoint(next));
    const ga=proj(guidePoint(current)),gb=proj(guidePoint(next));
    const length=Math.hypot(b.x-a.x,b.y-a.y),nx=(b.y-a.y)/(length||1),ny=-(b.x-a.x)/(length||1);
    ctx.strokeStyle=LINE;ctx.lineWidth=1.65;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();
    ctx.strokeStyle=HELP;ctx.lineWidth=.85;ctx.setLineDash([3,2]);
    ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(ga.x,ga.y);ctx.moveTo(b.x,b.y);ctx.lineTo(gb.x,gb.y);ctx.stroke();ctx.setLineDash([]);
    ctx.strokeStyle=LINE;ctx.lineWidth=1.7;
    for(const q of [a,b]){ctx.beginPath();ctx.moveTo(q.x-nx*4,q.y-ny*4);ctx.lineTo(q.x+nx*4,q.y+ny*4);ctx.stroke();}
    let label=pretty(c.seq[i]).replace(' mm','');
    let cx=(a.x+b.x)/2,cy=(a.y+b.y)/2;
    const stagger=(i%2===0?-17:24)+(j*5);
    cx+=nx*stagger;cy+=ny*stagger;
    const tooShort=length<28;
    if(tooShort){markers.push({n:i+1,value:label,from:current,to:next});label='#'+(i+1);}
    ctx.font='bold 11px -apple-system,system-ui,sans-serif';
    const boxW=Math.max(25,ctx.measureText(label).width+10);
    if(cx>-30&&cx<w+30&&cy>0&&cy<h){
      ctx.fillStyle='rgba(255,255,255,.96)';
      ctx.fillRect(cx-boxW/2,cy-10,boxW,20);
      ctx.strokeStyle='rgba(27,87,129,.7)';ctx.lineWidth=.6;ctx.strokeRect(cx-boxW/2,cy-10,boxW,20);
      ctx.fillStyle=LINE;ctx.fillText(label,cx,cy+4);
    }
    current=next;
   }
  }
  ctx.restore();
  return markers;
 }
 window.HOUSE_DIMENSIONS_V15={presets,init,draw,pretty};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();