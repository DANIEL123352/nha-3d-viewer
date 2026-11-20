#!/usr/bin/env python3
"""KT06/KT07/KT08/KT09 based detailed interactive BIM-style concept.
Designed from PDF axis geometry, NOT imported from the previous V16 model.
World coordinates X=rear->front, Y=from top of drawing to bottom, Z=elevation, meters.
Detailed fixtures/finishes are illustrative and NOT dimensional survey data.
"""
from pathlib import Path
import math, json, collections, os
import numpy as np
import trimesh
import ezdxf
from trimesh.visual.texture import TextureVisuals
from trimesh.visual.material import PBRMaterial

OUT=Path(os.environ.get('V18_OUT','/mnt/data/NHA_V18_CAD_CHI_TIET'));OUT.mkdir(parents=True,exist_ok=True)
TONE={
'plaster':'#e9e7e1','white':'#f6f4f0','stone':'#d4d0c8','tile':'#e3dfd7','marble':'#eeeae2',
'wood':'#b79673','walnut':'#876c58','woodlight':'#d2b69a','groove':'#635a50','coal':'#343941',
'metal':'#697782','brass':'#a89165','glass':'#9bbfd0','curtain':'#dddcd6',
'cream':'#e4d8c7','fabric':'#b7b1a8','sofa':'#b7b5ae','rug':'#d0c8bb','bedlinen':'#e2e3dd',
'olive':'#779177','leaf':'#6b8768','soil':'#92785c','water':'#8fafbf',
'chrome':'#aeb7bd','porcelain':'#f7f8f7','mirror':'#bccbd1','tv':'#262c34',
'solar':'#42596d','concrete':'#bfc2c1','warm':'#e9cda5', 'pavement':'#c5c2bb',
}

TONE.update({
 'darkmarble':'#626064','greymarble':'#92908e','lightmarble':'#f2ede4','smokestone':'#45484a',
 'gold':'#d1af70','bronze':'#5f5249','taupegrey':'#8e8781','graphite':'#272b2f',
 'lightoak':'#dcc7aa','softtaupe':'#aca69b','warmled':'#ffe6ac',
 'smokeglass':'#899a9e','clearglass':'#c8dedf'
})

def rgba(hexstr,opacity=255):
 c=hexstr.lstrip('#');return tuple(int(c[i:i+2],16) for i in (0,2,4))+(opacity,)
SC=trimesh.Scene();parts=[];counts=collections.Counter();layer_faces=collections.Counter();MATS={}
def mat(color,alpha=1):
 key=(color,alpha)
 if key not in MATS:
  MATS[key]=PBRMaterial(name='mat_'+str(len(MATS)),baseColorFactor=np.array(rgba(TONE.get(color,color),round(alpha*255)),dtype=np.uint8),
        metallicFactor=.04 if color not in ('glass','chrome','metal') else .25,
        roughnessFactor=.14 if color=='mirror' else .24 if color in ('glass','chrome') else .45 if color in ('marble','porcelain','tile') else .76,
        alphaMode='BLEND' if alpha<.99 else 'OPAQUE',doubleSided=True)
 return MATS[key]

def add_mesh(name, floor,cat, mesh,color,alpha=1,reference='ILLUSTRATIVE'):
 # preserve true per-object node name for web viewer layer/category filtering
 mesh.visual=TextureVisuals(uv=np.zeros((len(mesh.vertices),2)),material=mat(color,alpha))
 node=f'F{floor}__{cat}__{name}'
 SC.add_geometry(mesh,geom_name=node,node_name=node)
 parts.append({'node':node,'floor':floor,'category':cat,'reference':reference,'color':color})
 counts[cat]+=1
 return mesh

def box(name,f,c,x0,x1,y0,y1,z0,z1,col,alpha=1,reference='ILLUSTRATIVE'):
 assert x1>x0 and y1>y0 and z1>z0,(name,x0,x1,y0,y1,z0,z1)
 mesh=trimesh.creation.box(extents=[x1-x0,y1-y0,z1-z0]); mesh.apply_translation([(x1+x0)/2,(y1+y0)/2,(z1+z0)/2]);
 return add_mesh(name,f,c,mesh,col,alpha,reference)

def ellip(name,f,c,x,y,z,sx,sy,sz,col,alpha=1):
 mesh=trimesh.creation.icosphere(subdivisions=2,radius=1.0);mesh.apply_scale([sx,sy,sz]);mesh.apply_translation([x,y,z]);return add_mesh(name,f,c,mesh,col,alpha)

def cyl(name,f,c,x,y,z,r,h,col,sections=20):
 mesh=trimesh.creation.cylinder(radius=r,height=h,sections=sections);mesh.apply_translation([x,y,z+h/2]);return add_mesh(name,f,c,mesh,col)

def bar(name,f,c,point1,point2,r,col):
 p=np.array(point1,dtype=float);q=np.array(point2,dtype=float);d=q-p;length=np.linalg.norm(d)
 if length<1e-6:return
 mesh=trimesh.creation.cylinder(radius=r,height=length,sections=9)
 rot=trimesh.geometry.align_vectors([0,0,1],d)
 mesh.apply_transform(rot);mesh.apply_translation((p+q)/2)
 return add_mesh(name,f,c,mesh,col)

def plaque(name,f,c,x0,x1,y0,y1,z,col,th=.025):return box(name,f,c,x0,x1,y0,y1,z,z+th,col)

# Physical anchors from the PDF, in metres, NOT back-calculated from raster pixels.
X=[0,7.0,11.15,18.85];WIDTH=6
L=[.8,4.7,8.3,11.7]
MEAS={'axis_A_B_mm':6000,'axis_1_4_mm':18850,'spans_1_2_2_3_3_4_mm':[7000,4150,7700],
 'balcony_mm':1400,'roof_overhang_from_axis3_mm':1100,'stair_footprint_mm':[4150,2450],
 'lift_car_reference_mm':[1340,850], 'ground_level_m':.8,'first_level_m':4.7,'terrace_level_m':8.3,
 'roof_level_m_kt10':11.7,'conflict_kt11':'upper levels +11.9/+15.0 contradict KT10; do not use for construction.'}
# Layout PDF directly supports: KT06 kitchen behind stairs, living in front; KT07 rear/front bedrooms and 2 WC; KT08 rear bedroom+WC and front open terrace.
# The document does not state joinery material, product dimensions or finish; all are styled illustrative.

def wallx(f,name,x,ya,yb,z0,z1,th=.17,cat='WALL'):
 return box(name,f,cat,x-th/2,x+th/2,ya,yb,z0,z1,'plaster',reference='PDF_ZONE_APPROXIMATE')
def wally(f,name,y,xa,xb,z0,z1,th=.17,cat='WALL'):
 return box(name,f,cat,xa,xb,y-th/2,y+th/2,z0,z1,'plaster',reference='PDF_ZONE_APPROXIMATE')

def floor_base(f):
 z=L[f]
 plaque('architectural_floor_slab',f,'SLAB',0,18.85,0,6,z-.22,'concrete',.22)
 plaque('floor_finish_rear',f,'FINISH',.11,6.90,.11,5.90,z+.014,'tile',.018)
 plaque('floor_finish_hall',f,'FINISH',7.03,11.10,2.40,5.89,z+.014,'marble',.018)
 plaque('floor_finish_front',f,'FINISH',11.20,18.74,.11,5.89,z+.014,'tile',.018)
 # hidden floor centerline zones (not dimensioned objects)
 for x in [0,7.0,11.15,18.85]:
  box(f'column_{x}',f,'STRUCTURE',max(0,x-.16),min(18.85,x+.16),.01,.30,z,z+3.15,'concrete',reference='POSITION_APPROXIMATE') if 0<x<18.85 else None
 # external far wall and rear enclosure
 wally(f,'north_boundary_wall',0,0,18.85,z+.01,z+3.12,cat='SHELL') if f<2 else wally(f,'north_wall_over_rear_bed',0,0,11.15,z,z+3.05,cat='SHELL')
 wallx(f,'rear_wall',0,0,6,z,z+3.12,cat='SHELL')
 # front lateral walls are intentionally cutaway in axonometric mode; full shells are separate.
 # Near wall is constructed as glass/structural segments with cutaway category.
 for a,b in [(0,1.04),(1.78,3.9),(4.82,7),(7,11.15),(11.15,13.2),(14.15,17.55),(18.25,18.85)]:
  if f==2 and a>=11.15: continue
  wally(f,'south_wall_'+str(a),6,a,b,z,z+3.12,cat='SHELL_NEAR')
 if f<2:
  # wide floor-to-ceiling front doors, grounded to main opening per KT06
  wallx(f,'front_pier_left',18.85,0,.82,z,z+3.08,cat='SHELL')
  wallx(f,'front_pier_right',18.85,5.18,6,z,z+3.08,cat='SHELL')
  box('front_lintel',f,'SHELL',18.77,18.85,.82,5.18,z+2.82,z+3.12,'plaster')
  box('front_sliding_glazing',f,'GLASS',18.78,18.81,.84,5.16,z+.08,z+2.75,'glass',.25)
  for yy in [2.25,3.65]:
   bar(f'front_mullion_{yy}',f,'FRAME',(18.80,yy,z+.10),(18.80,yy,z+2.75),.022,'coal')
  for zz in [z+.10,z+2.76]:bar(f'front_track_{zz}',f,'FRAME',(18.81,.82,zz),(18.81,5.18,zz),.022,'coal')
 # Other rear side glass windows with sill and bronze frames
 for xx in [1.4,4.9]:
  if f==0 or (f>0 and xx<5.4):
   box(f'window_glass_{xx}',f,'GLASS',xx-.54,xx+.54,-.005,.028,z+1.10,z+2.5,'glass',.24)
   for off in [-.55,.55]:bar(f'window_jamb_{xx}_{off}',f,'FRAME',(xx+off,0,z+1.08),(xx+off,0,z+2.52),.024,'coal')
   bar(f'window_sill_{xx}',f,'FRAME',(xx-.55,0,z+1.09),(xx+.55,0,z+1.09),.02,'coal')
 # window treatments cloth gathered vertical fins near window
 for x0 in ([2.3,4.4] if f==0 else [1.3,4.35]):
  for k in range(12):
   dx=.043*k
   box(f'curtain_fold_{x0}_{k}',f,'CURTAIN',x0+dx,x0+dx+.018,.18,.28,z+.38,z+2.76,'curtain',.72)


def door_frame(f,name,x,y,z,width=.88,h=2.34,orientation='y'):
 # Frame just outside doorway; frame & glazing/wood door leaf indicated not architectural shopdrawing.
 if orientation=='y':
  for yy in [y-.04,y+width+.04]:
   bar(name+f'_jamb_{yy}',f,'DOOR',(x,yy,z),(x,yy,z+h),.03,'walnut')
  bar(name+'_lintel',f,'DOOR',(x,y-.05,z+h),(x,y+width+.05,z+h),.035,'walnut')
  box(name+'_leaf',f,'DOOR',x-.04,x+.025,y+.05,y+width-.04,z,z+h-.07,'woodlight',.85)
  bar(name+'_handle',f,'HANDLE',(x-.05,y+width*.68,z+1.02),(x-.05,y+width*.68,z+1.22),.012,'brass')
 else:
  for xx in [x-.04,x+width+.04]:bar(name+f'_jamb_{xx}',f,'DOOR',(xx,y,z),(xx,y,z+h),.03,'walnut')
  bar(name+'_lintel',f,'DOOR',(x-.05,y,z+h),(x+width+.05,y,z+h),.035,'walnut')
  box(name+'_leaf',f,'DOOR',x+.06,x+width-.04,y-.04,y+.02,z,z+h-.07,'woodlight',.9)
  bar(name+'_handle',f,'HANDLE',(x+width*.65,y-.05,z+1.04),(x+width*.65,y-.05,z+1.23),.012,'brass')


def stair_core(f):
 b=L[f]
 # Lift+stair plan in KT06/KT07/KT08 lies at the north side of central span,
 # with circulation zone toward Y=2.45..6. Geometry is visibly detailed but railing/treads product sizes modeled.
 plaque('stairs_landing_ground',f,'STAIR',7.05,11.05,.16,2.41,b+.055,'wood',.115)
 # Two flights 11+11 individual steps in tight U. These DO NOT assert tread count without stair schedule.
 for k in range(10):
  x=7.12+k*.195
  box(f'stair_riser_A_{k}',f,'STAIR',x,x+.186,.20,.93,b+.05+k*.166,b+.20+k*.166,'woodlight')
  x=10.88-k*.195
  box(f'stair_riser_B_{k}',f,'STAIR',x-.186,x,1.48,2.27,b+1.76+k*.144,b+1.90+k*.144,'woodlight')
 # landing and handrails, robust physical cylinders
 plaque('turning_landing',f,'STAIR',9.10,10.95,.80,1.68,b+1.67,'woodlight',.16)
 for side_y in [.16,.97,1.48,2.27]:
  bar(f'run_hand_rail_{side_y}',f,'STAIR_RAIL',(7.15,side_y,b+.94),(10.9,side_y,b+2.42),.032,'brass')
  for k in range(5):
   xx=7.3+k*.71;hh=.98+k*.25
   bar(f'handrail_post_{side_y}_{k}',f,'STAIR_RAIL',(xx,side_y,b+.14+k*.25),(xx,side_y,b+.88+k*.25),.022,'coal')
 # Shaft in the middle with metal elevator doors (not true manufacturer 3D dimensions).
 box('lift_shaft_back',f,'LIFT',8.45,8.55,.92,2.14,b,b+3.15,'concrete')
 box('lift_shaft_left',f,'LIFT',8.45,9.93,.86,.95,b,b+3.13,'plaster')
 box('lift_door_left',f,'LIFT',8.58,9.22,.955,.98,b+.12,b+2.32,'metal')
 box('lift_door_right',f,'LIFT',9.23,9.86,.955,.98,b+.12,b+2.32,'chrome')
 bar('lift_door_seam',f,'LIFT',(9.225,.952,b+.18),(9.225,.952,b+2.32),.012,'coal')
 box('lift_marble_surround_top',f,'LIFT',8.36,10.05,.90,1.01,b+2.35,b+2.49,'marble')
 box('lift_control_panel',f,'LIFT',10.03,10.09,1.03,1.20,b+1.07,b+1.68,'coal')
 for zz in [1.22,1.37,1.51]:cyl('lift_control_button_'+str(zz),f,'LIFT',10.10,1.11,b+zz,.025,.028,'chrome')
 # wall around stair zone, not obstruct full circulation to front
 wally(f,'stair_north_core_wall',.12,7.02,11.12,b,b+2.88,cat='CORE')
 for xx in [7.03,11.13]:
  wallx(f,'stair_core_return_'+str(xx),xx,0,2.42,b,b+2.85,cat='CORE')
 for xa,xb in [(7,8.15),(10.05,11.15)]: wally(f,'core_front_piece_'+str(xa),2.45,xa,xb,b,b+2.8,cat='CORE')
 box('core_transom',f,'CORE',8.15,10.05,2.38,2.48,b+2.38,b+2.76,'plaster')


def railings(f,base,x0,x1,balcony=True):
 for Y in [0,6]:
  for Z in [.50,1.03]:bar(f'handrail_yp_{Y}_{Z}',f,'RAILING',(x0,Y,base+Z),(x1,Y,base+Z),.028,'coal')
  for x in np.linspace(x0,x1,max(3,int((x1-x0)/.65)+1)):
   bar(f'rail_vert_{Y}_{x:.2f}',f,'RAILING',(x,Y,base+.06),(x,Y,base+1.03),.017,'metal')
 for Z in [.50,1.03]:bar(f'balcony_front_horizontal_{Z}',f,'RAILING',(x1,0,base+Z),(x1,6,base+Z),.032,'coal')
 for Y in np.linspace(0,6,10):bar(f'balcony_front_vertical_{Y:.1f}',f,'RAILING',(x1,Y,base+.05),(x1,Y,base+1.03),.02,'metal')
 for Y in [0,6]:
  box(f'glass_balustrade_{Y}',f,'RAILING_GLASS',x0+.04,x1-.04,Y-.025,Y+.025,base+.15,base+.95,'glass',.20)

# Fixtures, tiles and interior are DESIGN visualization only.
def art(name,f,x,y,z):
 box(name+'_frame',f,'DECOR',x-.36,x+.36,y-.015,y+.015,z,z+.75,'brass')
 box(name+'_canvas',f,'DECOR',x-.32,x+.32,y-.019,y+.019,z+.04,z+.71,'cream')
 for k in range(4):
  box(f'{name}_line_{k}',f,'DECOR',x-.22+k*.11,x-.18+k*.11,y-.022,y-.020,z+.18,z+.47,'warm')

def plant(name,f,x,y,z,scale=1):
 box(name+'_pot',f,'PLANT',x-.16*scale,x+.16*scale,y-.16*scale,y+.16*scale,z,z+.36*scale,'stone')
 cyl(name+'_earth',f,'PLANT',x,y,z+.32*scale,.13*scale,.05*scale,'soil')
 for i in range(8):
  t=2*math.pi*i/8
  sx=x+.13*scale*math.cos(t);sy=y+.13*scale*math.sin(t)
  bar(f'{name}_stem_{i}',f,'PLANT',(x,y,z+.30*scale),(sx,sy,z+.86*scale),.016*scale,'wood')
  ellip(f'{name}_leaf_{i}',f,'PLANT',sx,sy,z+.80*scale,.13*scale,.08*scale,.26*scale,'leaf')

def spotlight(f,name,x,y,z):
 cyl(name+'_holder',f,'LIGHT',x,y,z-.065,.065,.10,'coal')
 cyl(name+'_warm',f,'LIGHT',x,y,z-.085,.043,.018,'warm')

def kitchen():
 f=0;b=L[f]
 # Document KT06: cabinets along top wall in rear room x 0..7, Y close to 0.
 box('lower_cabinets',f,'CABINET',.36,6.5,.20,.78,b,b+.82,'woodlight')
 plaque('countertop_quartz',f,'COUNTER',.28,6.60,.15,.89,b+.82,'marble',.055)
 box('backsplash',f,'FINISH',.29,6.6,.09,.13,b+.9,b+1.57,'marble')
 for i in range(9):
  xx=.4+i*.67
  if xx+0.63>6.51:break
  box(f'kitchen_lower_door_{i}',f,'CABINET',xx,xx+.62,.78,.805,b+.10,b+.72,'white')
  bar(f'kitchen_lower_handle_{i}',f,'HANDLE',(xx+.47,.827,b+.56),(xx+.57,.827,b+.56),.009,'brass')
 # wall units (open gap) and slim LED under-light strip
 for i in range(7):
  xx=.43+i*.85
  box(f'kitchen_upper_cupboard_{i}',f,'CABINET',xx,xx+.81,.16,.52,b+1.55,b+2.52,'white')
  box(f'kitchen_upper_decor_strip_{i}',f,'CABINET',xx+.75,xx+.78,.52,.535,b+1.65,b+2.39,'wood')
 box('under_cabinet_LED',f,'LIGHT',.44,6.28,.53,.56,b+1.56,b+1.60,'warm')
 # double sink + faucet
 for x0 in [1.28,1.76]:
  box('sink_bowl_'+str(x0),f,'KITCHEN_FIXTURE',x0,x0+.36,.35,.65,b+.80,b+.86,'metal')
 bar('sink_spout_riser',f,'KITCHEN_FIXTURE',(1.65,.32,b+.92),(1.65,.32,b+1.22),.014,'chrome')
 bar('sink_spout_curve',f,'KITCHEN_FIXTURE',(1.65,.32,b+1.22),(1.80,.46,b+1.23),.013,'chrome')
 # stove hob circle burners
 box('cooktop',f,'KITCHEN_FIXTURE',3.53,4.61,.25,.78,b+.88,b+.904,'coal')
 for cx,cy in [(3.78,.42),(4.33,.42),(3.78,.66),(4.33,.66)]:
  cyl(f'hob_burner_{cx}_{cy}',f,'KITCHEN_FIXTURE',cx,cy,b+.905,.09,.008,'metal')
 box('chimney_hood',f,'KITCHEN_FIXTURE',3.72,4.42,.3,.65,b+2.2,b+2.41,'metal')
 # integrated fridge at far corner
 box('fridge_panel',f,'CABINET',5.75,6.52,.80,1.51,b,b+2.45,'white')
 box('fridge_middle_line',f,'CABINET',6.48,6.51,.85,1.48,b+1.1,b+1.12,'metal')
 bar('fridge_handle',f,'HANDLE',(6.48,1.23,b+1.45),(6.48,1.23,b+2.15),.012,'chrome')
 # island and 6 chair table in open kitchen (finishes assumed)
 box('dining_table_top',f,'DINING',2.16,4.42,2.48,3.73,b+.71,b+.78,'marble')
 for x in [2.37,4.24]:
  for yy in [2.66,3.56]: cyl('dining_table_leg_'+str((x,yy)),f,'DINING',x,yy,b,.055,.73,'walnut')
 for i in range(6):
  x=2.40+(i%3)*.77;y=1.86 if i<3 else 4.07
  # square seat + curved-up back cushions
  box(f'chair_base_{i}',f,'CHAIR',x-.26,x+.26,y-.23,y+.23,b+.39,b+.49,'wood')
  box(f'chair_back_{i}',f,'CHAIR',x-.26,x+.26,y+(.15 if i<3 else -.22),y+(.22 if i<3 else -.15),b+.48,b+.94,'cream')
  for dx in [-.20,.20]:bar(f'chair_leg_{i}_{dx}',f,'CHAIR',(x+dx,y-.14,b),(x+dx,y-.14,b+.46),.024,'walnut')
 for i,xx in enumerate([2.70,3.28,3.86]):
  bar('pendant_cord_'+str(i),f,'LIGHT',(xx,3.0,b+3.05),(xx,3.0,b+2.10),.009,'coal')
  cyl('pendant_shade_'+str(i),f,'LIGHT',xx,3,b+2.03,.15,.10,'warm')
 plant('kitchen_corner_green',f,6.35,5.15,b,1.20)
 art('kitchen_wall_art',f,1.0,5.88,b+1.3)

def living():
 f=0;b=L[f]
 # open plan lounge as in KT06 front x11.15..18.85, reference photo uses detailed visual styling.
 plaque('rug_stone_textured',f,'RUG',13.04,17.23,1.11,4.68,b+.032,'rug',.03)
 # 3-seat couch along far wall
 box('sofa_wood_plinth',f,'SOFA',14.22,17.36,.89,1.73,b+.11,b+.31,'walnut')
 box('sofa_seat',f,'SOFA',14.08,17.43,.83,1.95,b+.29,b+.63,'sofa')
 box('sofa_back',f,'SOFA',14.12,17.4,.66,.99,b+.31,b+1.06,'fabric')
 for i in range(3):
  x=14.66+i*1.03
  ellip(f'couch_cushion_{i}',f,'SOFA',x,1.57,b+.64,.43,.34,.16,'cream')
 for i,x in enumerate([14.12,17.29]):
  ellip('sofa_pillow_'+str(i),f,'SOFA',x,1.18,b+.79,.33,.12,.38,'warm')
 # Two lounge chairs with curved back
 for i,(x,y) in enumerate([(13.52,3.46),(17.24,3.53)]):
  cyl(f'armchair_base_{i}',f,'SOFA',x,y,b+.10,.41,.36,'wood')
  ellip(f'armchair_seat_{i}',f,'SOFA',x,y,b+.49,.46,.42,.17,'cream')
  ellip(f'armchair_back_{i}',f,'SOFA',x,y+.35,b+.78,.47,.19,.46,'sofa')
 # circular coffee table, sculpted brass base
 cyl('coffee_round_base',f,'COFFEE',15.5,3.28,b+.08,.23,.26,'walnut')
 cyl('coffee_stone_top',f,'COFFEE',15.5,3.28,b+.37,.69,.07,'marble')
 cyl('coffee_ceramic_vase',f,'DECOR',15.45,3.22,b+.44,.065,.19,'white')
 # media wall has repeated timber flutes and integrated cabinets
 box('tv_media_feature',f,'MEDIA',12.1,17.76,5.74,5.87,b,b+2.67,'walnut')
 for i in range(40):
  x=12.15+i*.135
  box(f'media_wood_flute_{i}',f,'MEDIA',x,x+.022,5.86,5.895,b+.15,b+2.63,'groove')
 box('tv_screen',f,'MEDIA',14.05,16.47,5.67,5.72,b+1.15,b+2.44,'tv')
 box('tv_lower_cabinet',f,'MEDIA',13.2,17.3,5.18,5.73,b+.05,b+.53,'cream')
 for i in range(6):
  box('tv_drawer_front_'+str(i),f,'MEDIA',13.27+i*.66,13.89+i*.66,5.74,5.758,b+.15,b+.42,'white')
 plant('living_olive_tree',f,17.82,4.72,b,1.75)
 spotlight(f,'living_ambient_light',16.6,2.7,b+3.02)


def upholstered_bed(f,name,x0,x1,y0,y1,b,rotated=False):
 # pillow edge near x0; headboard; approximate lengths based on common furniture (NOT KT dimension)
 box(name+'_bed_plinth',f,'BED',x0,x1,y0,y1,b+.1,b+.36,'walnut')
 box(name+'_mattress',f,'BED',x0+.08,x1-.08,y0+.06,y1-.06,b+.37,b+.58,'bedlinen')
 box(name+'_duvet',f,'BED',x0+.48,x1-.08,y0+.10,y1-.10,b+.59,b+.73,'cream')
 box(name+'_duvet_fold',f,'BED',x0+.50,x0+.65,y0+.08,y1-.08,b+.73,b+.77,'fabric')
 for i in range(2):
  y=y0+.38+(i*.70)
  ellip(name+'_pillow_'+str(i),f,'BED',x0+.29,y,b+.64,.26,.29,.11,'white')
 box(name+'_headboard',f,'BED',x0-.13,x0+.11,y0-.12,y1+.12,b+.14,b+1.26,'walnut')
 for j in range(9):
  y=y0+j*(y1-y0)/9
  box(name+'_headboard_rib_'+str(j),f,'BED',x0-.145,x0-.125,y,y+.045,b+.28,b+1.20,'woodlight')
 for i,yy in enumerate([y0-.28,y1+.06]):
  box(name+'_bedside_'+str(i),f,'BED',x0+.07,x0+.54,yy,yy+.20,b+.05,b+.57,'woodlight')
  cyl(name+'_lamp_base_'+str(i),f,'LIGHT',x0+.31,yy+.12,b+.58,.085,.15,'brass')
  cyl(name+'_lamp_shade_'+str(i),f,'LIGHT',x0+.31,yy+.12,b+.75,.115,.25,'warm')
 plaque(name+'_carpet',f,'RUG',x0-.35,x1+.35,y0-.3,y1+.3,b+.023,'rug',.013)

def closet(f,name,x0,x1,y0,y1,b):
 box(name+'_wardrobe',f,'WARDROBE',x0,x1,y0,y1,b,b+2.6,'woodlight')
 cnt=max(2,round((x1-x0)/.55))
 for i in range(cnt):
  xa=x0+(x1-x0)*i/cnt;xb=x0+(x1-x0)*(i+1)/cnt
  box(name+f'_door_{i}',f,'WARDROBE',xa+.018,xb-.018,y1-.02,y1+.015,b+.09,b+2.47,'white')
  bar(name+f'_handle_{i}',f,'HANDLE',(xb-.12,y1+.04,b+1.14),(xb-.12,y1+.04,b+1.55),.010,'brass')
 for i in range(8):
  xx=x0+i*(x1-x0)/8
  box(name+f'_top_slats_{i}',f,'WARDROBE',xx,xx+.018,y0,y1,b+2.54,b+2.59,'walnut')

def bath(f,name,x0,x1,b):
 # actually per KT07 and KT08 located near the south side Y 4.4..6 and rear/front X zones.
 y0=4.42;y1=5.93
 plaque(name+'_wet_floor',f,'BATH',x0,x1,y0,y1,b+.042,'marble',.022)
 wally(f,name+'_partition',y0,x0,x1,b,b+2.66,th=.10,cat='BATH_WALL')
 wallx(f,name+'_end_wall',x0,y0,y1,b,b+2.65,th=.11,cat='BATH_WALL')
 wallx(f,name+'_end_wall_other',x1,y0,y1,b,b+2.65,th=.11,cat='BATH_WALL')
 # opening between x0+1.3 and +2.08 on one wall (partition not completely covering door)
 # shower partition transparent and low tray
 plaque(name+'_shower_tray',f,'BATH',x0+.15,x0+1.02,4.55,5.83,b+.065,'porcelain',.09)
 box(name+'_shower_glass',f,'GLASS',x0+1.02,x0+1.045,4.55,5.78,b+.16,b+2.02,'glass',.22)
 for yy in [4.53,5.76]:bar(name+'_shower_glass_frame_'+str(yy),f,'FRAME',(x0+1.02,yy,b+.13),(x0+1.02,yy,b+2.12),.018,'coal')
 bar(name+'_shower_pipe',f,'BATH_FITTING',(x0+.34,5.8,b+.7),(x0+.34,5.8,b+2.17),.021,'chrome')
 bar(name+'_shower_arm',f,'BATH_FITTING',(x0+.34,5.8,b+2.11),(x0+.73,5.8,b+2.11),.021,'chrome')
 cyl(name+'_shower_head',f,'BATH_FITTING',x0+.73,5.80,b+2.06,.13,.035,'chrome')
 # vanity basin and mirror, facing room
 box(name+'_vanity',f,'BATH',x0+1.14,x0+2.09,5.25,5.80,b+.05,b+.79,'walnut')
 plaque(name+'_basin',f,'BATH_FITTING',x0+1.29,x0+1.99,5.31,5.72,b+.80,'porcelain',.13)
 box(name+'_mirror',f,'MIRROR',x0+1.20,x0+2.02,5.90,5.925,b+1.22,b+2.31,'mirror',.77)
 bar(name+'_faucet',f,'BATH_FITTING',(x0+1.67,5.33,b+.96),(x0+1.67,5.33,b+1.20),.015,'chrome')
 # toilet, tank and pedestal rounded items
 x=x0+2.60
 box(name+'_wc_base',f,'BATH_FITTING',x-.19,x+.19,4.92,5.63,b+.06,b+.40,'porcelain')
 ellip(name+'_wc_bowl',f,'BATH_FITTING',x,5.19,b+.41,.29,.37,.10,'porcelain')
 box(name+'_wc_tank',f,'BATH_FITTING',x-.30,x+.30,5.49,5.71,b+.40,b+1.06,'porcelain')
 cyl(name+'_wc_button',f,'BATH_FITTING',x,5.59,b+1.065,.035,.007,'chrome')
 # tile joints indicate detail, no actual tiled measurement
 for z in np.arange(b+.4,b+2.35,.34):
  bar(name+'_tile_grout_'+str(round(z,2)),f,'BATH',(x0,5.94,z),(x1,5.94,z),.004,'stone')

def bedrooms():
 # f1 rear 2 bedrooms, both toilets per KT07. f2 rear bedroom, WC and open front terrace per KT08.
 for f in [1,2]:
  b=L[f]
  upholstered_bed(f,'rear_bed',.55,2.65,1.35,3.04,b)
  closet(f,'rear_wardrobe',3.0,6.46,.18,.70,b)
  bath(f,'rear_wc',3.25,6.87,b)
  plant(f'rear_plant_f{f}',f,1.2,4.65,b,1.03)
  art(f'rear_art_f{f}',f,3.65,5.70,b+1.33)
  for i,xx in enumerate(np.linspace(1,5,5)):
   spotlight(f,'rear_spot_'+str(i),xx,3.25,b+3.07)
  # rear floor-to-ceiling decorative curtain across one side window
  for j in range(15):
   x=.30+j*.065
   box(f'rear_window_curtain_{j}',f,'CURTAIN',x,x+.025,.25,.33,b+.12,b+2.66,'curtain',.65)
  if f==1:
   upholstered_bed(f,'front_bed',13.28,15.4,.89,2.74,b)
   closet(f,'front_closet',11.45,12.18,.30,3.05,b)
   bath(f,'front_wc',11.25,14.60,b)
   box('reading_console',f,'FURNITURE',16.82,18.02,4.15,4.73,b+.12,b+.79,'walnut')
   ellip('bedroom_armchair',f,'FURNITURE',17.24,1.28,b+.54,.48,.49,.41,'cream')
   plant('bedroom_plant',f,18.1,5.35,b,1.04)
   art('front_bedroom_wall_art',f,16.95,5.83,b+1.55)
  else:
   # front is uncovered terrace, NOT front bedroom (KT08).
   plaque('terrace_deck',f,'TERRACE',11.18,20.25,.11,5.88,b+.025,'pavement',.04)
   plaque('terrace_boundary',f,'TERRACE',18.85,20.25,0,6,b-.20,'concrete',.19)
   railings(f,b,11.15,20.25)
   for i,xx in enumerate([12.0,17.8,19.25]):
    plant('terrace_planter_'+str(i),f,xx,5.33,b,1.18)
   box('terrace_dining_table_top',f,'OUTDOOR',14.70,16.25,1.60,2.52,b+.68,b+.76,'woodlight')
   for x in [14.9,16.03]:
    for yy in [1.83,2.34]:bar('outdoor_table_leg_'+str((x,yy)),f,'OUTDOOR',(x,yy,b),(x,yy,b+.68),.045,'coal')
   for i,(xx,yy) in enumerate([(14.75,1.15),(15.55,1.15),(14.75,2.85),(15.55,2.85)]):
    ellip('outdoor_chair_seat_'+str(i),f,'OUTDOOR',xx,yy,b+.48,.31,.3,.10,'cream')
    for dx in [-.20,.20]:bar(f'outdoor_chair_leg_{i}_{dx}',f,'OUTDOOR',(xx+dx,yy,b),(xx+dx,yy,b+.44),.023,'coal')
   box('terrace_sofa_base',f,'OUTDOOR',17.0,18.78,3.65,4.57,b+.12,b+.45,'wood')
   for i in range(3):ellip('terrace_sofa_cushion_'+str(i),f,'OUTDOOR',17.3+i*.52,4.02,b+.57,.31,.35,.13,'cream')
   # drainage channels (schematic)
   for xx in [11.4,17.8]:box('terrace_drain_'+str(xx),f,'TERRACE',xx,xx+.46,5.70,5.75,b+.05,b+.055,'metal')


def finish_upper_shell(f):
 b=L[f]
 # Partitions per PDF separating WC from rear/front bedrooms near south boundary
 # bathroom partitions are in bath(), extra door frames only.
 for x in [7,11.15]:
  wallx(f,'hall_core_pier_'+str(x),x,2.48,3.58,b,b+2.98,cat='CORE')
  wallx(f,'hall_core_corner_'+str(x),x,5.72,6,b,b+2.98,cat='CORE')
  door_frame(f,'hall_door_'+str(x),x,3.76,b,width=.92)
 if f==1:
  # front room has a small extra arch to balcony as in KT07
  door_frame(f,'front_balcony_entry',18.85,3.42,b,width=1.12)
 else:
  door_frame(f,'terrace_access',11.15,3.54,b,width=1.7)


def roof():
 # Roof only rear room and central core, 1.1m beyond axis 3 as shown in KT09.
 z=L[3]
 plaque('roof_cover_rear',3,'ROOF',0,7,0,6,z,'concrete',.22)
 plaque('roof_cover_stair_left',3,'ROOF',7,12.25,0,2.60,z,'concrete',.22)
 plaque('roof_cover_stair_right',3,'ROOF',7,12.25,5.48,6,z,'concrete',.22)
 plaque('roof_cover_stair_back',3,'ROOF',7,8.10,2.60,5.48,z,'concrete',.22)
 plaque('roof_cover_stair_front',3,'ROOF',10.20,12.25,2.60,5.48,z,'concrete',.22)
 # staircase access enclosure on roof
 for x in [8.1,10.2]:box('rooftop_access_wall_'+str(x),3,'ROOF_ACCESS',x-.11,x+.11,2.65,5.45,z,z+1.52,'plaster')
 box('rooftop_access_lintel',3,'ROOF_ACCESS',8.10,10.2,5.32,5.46,z+1.32,z+1.52,'plaster')
 box('rooftop_access_door',3,'ROOF_ACCESS',8.55,9.68,5.30,5.36,z,z+1.33,'woodlight')
 for yy in [0,6]:
  bar('roof_parapet_'+str(yy),3,'ROOF_RAIL',(0,yy,z+.76),(12.25,yy,z+.76),.03,'coal')
 # bồn nước: stainless steel cylindrical water tank, not manufacturer technical dimension.
 cyl('water_tank_body',3,'WATER_TANK',3.38,3.78,z+.28,.46,.9,'chrome',sections=28)
 for a in [.1,.35,.6,.85]:cyl('water_tank_rib_'+str(a),3,'WATER_TANK',3.38,3.78,z+.28+a,.468,.023,'metal')
 for xx in [2.92,3.84]:box('tank_base_'+str(xx),3,'ROOF_EQUIPMENT',xx,xx+.13,3.32,4.21,z,z+.27,'coal')
 # NNLMT, pitched collector using individual rods and frame
 box('solar_frame',3,'SOLAR',4.53,5.82,3.11,4.09,z+.17,z+.29,'metal')
 plaque('solar_panel',3,'SOLAR',4.60,5.73,3.19,4.03,z+.31,'solar',.045)
 for xx in np.linspace(4.64,5.67,8):bar(f'solar_tubes_{xx:.2f}',3,'SOLAR',(xx,3.26,z+.37),(xx,3.96,z+.37),.032,'chrome')



# V20 procedural original textures (no third-party copyrighted image assets).
# Materials are illustrative, not specified by the construction PDF.
from PIL import Image, ImageFilter
import numpy as np
TEX_DIR=OUT/'textures';TEX_DIR.mkdir(exist_ok=True)
TEX_MAP={}
TEX_TILING={
 'wood':(1.75,1.15), 'walnut':(1.4,.90),'woodlight':(1.7,1.2),
 'groove':(1.5,1.1), 'tile':(1.05,1.05),'stone':(1.20,1.20),
 'marble':(.80,.80),'pavement':(.98,.98),'concrete':(.95,.95),
 'plaster':(1.10,1.10),'white':(1,1),'cream':(.70,.70),'fabric':(1.3,1.3),
 'sofa':(1.2,1.2),'bedlinen':(1,1),'rug':(.58,.58),'curtain':(.65,.65),
}
TEX_TILING.update({'darkmarble':(.48,.52),'greymarble':(.55,.50),
 'lightmarble':(.64,.63),'smokestone':(.80,.76),'taupegrey':(.67,.67),
 'lightoak':(1.7,1.2),'softtaupe':(.9,.9)})
TEXTURED=set(TEX_TILING)
def make_texture(name,seed=11):
    rng=np.random.default_rng(seed+sum(ord(a) for a in name))
    H=W=512
    xx,yy=np.meshgrid(np.linspace(0,1,W),np.linspace(0,1,H))
    fine=rng.normal(0,1,(H,W))
    large=np.asarray(Image.fromarray(np.uint8(np.clip(128+fine*42,0,255))).resize((64,64)).resize((W,H),Image.Resampling.BICUBIC),float)/255-0.5
    big=rng.normal(0,1,(16,16))
    medium=np.asarray(Image.fromarray(np.uint8(np.clip(128+big*28,0,255))).resize((W,H),Image.Resampling.BICUBIC),float)/255-.5
    palette={
       'wood':(165,128,95), 'woodlight':(205,173,132),'walnut':(109,78,59),'groove':(93,67,52),
       'tile':(213,208,194),'stone':(205,201,191),'marble':(233,227,218),'pavement':(188,181,164),
       'plaster':(222,217,208),'white':(232,229,223),'cream':(225,209,184),'fabric':(160,153,141),
       'sofa':(173,166,154),'bedlinen':(231,227,216),'rug':(183,169,150),'curtain':(217,214,206),
       'concrete':(178,180,175),
       'darkmarble':(92,91,95),'greymarble':(155,150,147),
       'lightmarble':(235,228,215),'smokestone':(69,72,73),
       'taupegrey':(142,135,131),'lightoak':(216,194,164),'softtaupe':(180,171,156)
    }
    base=np.zeros((H,W,3),float)+np.array(palette[name],float)
    if name in ['wood','woodlight','walnut','groove','lightoak']:
        # fine grain along Y, with knots and longitudinal bands.
        bands=np.sin(xx*74+3.0*np.sin(yy*9)+2*medium)+np.sin(xx*188+5*medium)
        streak=(bands*.36+np.sin(xx*37+medium*10)*.32)*15 + fine*1.0
        if name=='groove':
            streak-=((np.mod(xx*12,1)<.08).astype(float))*35
        base+=(streak+large*11)[...,None]*np.array([.95,.83,.65])
        if name in ('wood','woodlight'):
            base+=np.sin(xx*8+yy*2.0)[...,None]*np.array([5,4,1])
    elif name in ['marble','stone','tile','pavement','concrete','darkmarble',
 'greymarble','lightmarble','smokestone','softtaupe','taupegrey']:
        veins=np.sin((xx*.90+yy*.47+medium*.30)*85)+np.sin(xx*25-yy*11+medium*23)
        if name in ['marble','darkmarble','greymarble','lightmarble']:
            mask=(veins>1.50) | (np.sin(xx*15+yy*8+medium*16)>.985)
            base-=mask[...,None]*np.array([29,27,25])
            base+=medium[...,None]*np.array([12,12,12])
        else:
            base+=medium[...,None]*np.array([8,8,8])
        if name in ('tile','stone','pavement'):
            lines=((np.mod(xx*4,1)<.012)|(np.mod(yy*4,1)<.012))
            base-=lines[...,None]*np.array([32,29,26])
            if name=='pavement':
                base-=(((np.mod(yy*8,1)<.013))).astype(float)[...,None]*12
        base+=fine[...,None]*2.4
    elif name in ['cream','fabric','sofa','rug','bedlinen','curtain']:
        weave=(np.sin(xx*513)+np.sin(yy*613))*2.2
        base+=(weave+medium*9+fine*1.4)[...,None]
        if name=='rug':
            frame=((xx<.055)|(xx>.945)|(yy<.055)|(yy>.945))
            base-=frame[...,None]*np.array([27,24,22])
        if name=='curtain':
            base+=np.sin(xx*46)[...,None]*3.5
    else:
        base+=medium[...,None]*8+fine[...,None]*2
    img=Image.fromarray(np.uint8(np.clip(base,0,255)),'RGB')
    out=TEX_DIR/f'{name}_v20.png';img.save(out,optimize=True)
    TEX_MAP[name]=img
for name in TEXTURED: make_texture(name)

_old_mat=mat
def mat(color,alpha=1):
    if color not in TEX_MAP:return _old_mat(color,alpha)
    key=('v20',color,alpha)
    if key not in MATS:
        MATS[key]=PBRMaterial(
          name=f'v20_{color}',baseColorFactor=np.array([255,255,255,round(255*alpha)],np.uint8),
          baseColorTexture=TEX_MAP[color], metallicFactor=.03,
          roughnessFactor=.90 if color in ('fabric','sofa','rug','curtain','bedlinen','cream') else .63 if color in ('wood','woodlight','walnut') else .48,
          alphaMode='BLEND' if alpha<.99 else 'OPAQUE',doubleSided=True)
    return MATS[key]

def texture_uv(mesh,color):
    # Triangle-separated vertices give each box face correct local UV projection.
    # Existing furniture shape and physical coordinates remain unchanged.
    coords=np.array(mesh.triangles,dtype=np.float64)
    nf=len(coords)
    if nf==0:return mesh,None
    normals=np.asarray(mesh.face_normals)
    fmajor=np.argmax(abs(normals),axis=1)
    uv=np.zeros((nf,3,2),float)
    for axis in [0,1,2]:
        selected=fmajor==axis
        if not np.any(selected):continue
        xyz=coords[selected]
        if axis==0: u=xyz[:,:,[1,2]]
        elif axis==1: u=xyz[:,:,[0,2]]
        else: u=xyz[:,:,[0,1]]
        uv[selected]=u
    ts=TEX_TILING[color]
    uv[:,:,0]*=ts[0];uv[:,:,1]*=ts[1]
    # Preserve split triangles for separate face texture axes; glTF export supports this.
    faces=np.arange(nf*3,dtype=np.int64).reshape(nf,3)
    output=trimesh.Trimesh(vertices=coords.reshape(-1,3),faces=faces,process=False,validate=False)
    return output,uv.reshape(-1,2)
old_add_mesh=add_mesh
def add_mesh(name, floor,cat, mesh,color,alpha=1,reference='ILLUSTRATIVE'):
    if color in TEXTURED and len(mesh.faces)<35:
        mesh,uv=texture_uv(mesh,color)
        mesh.visual=TextureVisuals(uv=uv,material=mat(color,alpha))
    else:
        mesh.visual=TextureVisuals(uv=np.zeros((len(mesh.vertices),2)),material=mat(color,alpha))
    node=f'F{floor}__{cat}__{name}'
    SC.add_geometry(mesh,geom_name=node,node_name=node)
    parts.append({'node':node,'floor':floor,'category':cat,'reference':reference,'color':color})
    counts[cat]+=1
    return mesh


for f in range(3):
 floor_base(f);stair_core(f)
 if f>=1:finish_upper_shell(f)
 else:
  # KT06 has front main entrance in front wall
  box('front_tread_1',0,'EXTERIOR',18.85,19.76,.62,5.36,.57,.65,'pavement')
  box('front_tread_2',0,'EXTERIOR',19.76,20.7,.62,5.36,.48,.56,'pavement')
  box('front_tread_3',0,'EXTERIOR',20.7,21.85,.62,5.36,.39,.48,'pavement')
for f in [1,2]:
 b=L[f];plaque('balcony_projection',f,'BALCONY',18.85,20.25,0,6,b-.22,'concrete',.22)
 railings(f,b,18.85,20.25)
kitchen();living();bedrooms();roof()


# V19: cosmetic geometry enhancement atop KT06-09 traced floor zones.
# All additions are design suggestions, NOT measurements from architectural sheets.
def detail_box(name,f,x0,x1,y0,y1,z0,z1,col,cat='DECOR'):
  return box(name,f,cat,x0,x1,y0,y1,z0,z1,col,reference='DESIGN_COSMETIC_V19')

def detail_bar(name,f,a,b,r,col,cat='DECOR'):
  return bar(name,f,cat,a,b,r,col)

def fancy_frame(f,name,xa,xb,ya,yb,base,height):
  # Decorative reveal along the opening; leaves the doorway itself traversable.
  t=.034
  detail_box(name+'_left',f,xa-t,xa+t,ya-t,ya+t,base,base+height,'walnut','TRIM')
  detail_box(name+'_right',f,xb-t,xb+t,yb-t,yb+t,base,base+height,'walnut','TRIM')
  detail_box(name+'_head',f,xa,xb,ya-t,yb+t,base+height-.035,base+height+.035,'walnut','TRIM')

def v19_wood_floor(f,xa,xb,ya,yb,b,tag):
  # Narrow plank subdivisions of nominal floor finish; product width only visual.
  count=int((xb-xa)/.26)
  for j in range(count):
    xx=xa+j*(xb-xa)/count
    detail_box(f'{tag}_plank_{j}',f,xx+.004,xx+.026,ya+.05,yb-.05,b+.031,b+.037,'woodlight','FINISH_V19')
  for k in range(3):
    yy=ya+(yb-ya)*(k+1)/4
    detail_box(f'{tag}_plank_cross_{k}',f,xa+.09,xb-.07,yy,yy+.005,b+.032,b+.037,'wood','FINISH_V19')

def v19_baseboards(f,xa,xb,y,b,name):
  for z0,z1 in [(b+.02,b+.10),(b+.12,b+.14)]:
    detail_box(f'{name}_base_{round(z0-b,2)}',f,xa,xb,y-.022,y+.022,z0,z1,'white','TRIM')

def v19_bed_detail(f,name,xa,xb,ya,yb,b):
  # Rounded bed scarf and several fabric folds; extras are cosmetic.
  for k in range(8):
    yy=ya+.16+k*(yb-ya-.32)/8
    # slight undulation across the duvet using narrow rounded textile strips
    ellip(f'{name}_quilt_seam_{k}',f,'TEXTILE',
      xa+.77+(k%3)*.042, yy,b+.77,.68,.012,.007,'bedlinen',.98)
  ellip(f'{name}_foot_throw',f,'TEXTILE',xb-.33,(ya+yb)/2,b+.81,.22,(yb-ya)*.46,.085,'fabric')
  for k in range(2):
    y=ya+.38+k*.70
    ellip(f'{name}_pillow_detail_{k}',f,'TEXTILE',xa+.30,y,b+.77,.19,.28,.055,'cream')
  for s,yy in [('left',ya-.19),('right',yb+.11)]:
    detail_box(f'{name}_{s}_bedside_handle',f,xa+.18,xa+.47,yy,yy+.018,b+.30,b+.33,'brass','HANDLE')
  # Thin inner wood trims on upholstered headboard
  for j in range(6):
    yy=ya+j*(yb-ya)/6
    detail_box(f'{name}_headboard_wood_seam_{j}',f,xa-.162,xa-.153,yy,yy+.025,b+.34,b+1.18,'walnut','TRIM')

def v19_bath_detail(f,name,x0,b):
  y0=4.42
  # glass door pull and metal hinges to read as a shower screen
  detail_bar(f'{name}_screen_pull',f,(x0+1.065,4.94,b+.88),(x0+1.065,4.94,b+1.33),.012,'chrome','BATH_FITTING')
  for z in [b+.45,b+1.64]:
    detail_box(f'{name}_screen_hinge_{z:.2f}',f,x0+1.037,x0+1.078,4.52,4.59,z,z+.075,'chrome','BATH_FITTING')
  # Towel rack and towel rectangle on the side wall
  detail_bar(f'{name}_towel_rail',f,(x0+.22,4.43,b+1.52),(x0+.75,4.43,b+1.52),.014,'chrome','BATH_FITTING')
  detail_box(f'{name}_hanging_towel',f,x0+.34,x0+.62,4.45,4.48,b+.95,b+1.5,'cream','TEXTILE')
  # Soap bottle, hand basin, shower drainage
  cyl(f'{name}_soap_dispenser',f,'BATH_FITTING',x0+1.90,5.50,b+.96,.047,.18,'white')
  detail_box(f'{name}_drain_grate',f,x0+.32,x0+.49,5.63,5.66,b+.067,b+.077,'metal','BATH_FITTING')
  # mirror rim and edge lights, not an extra wall
  detail_box(f'{name}_mirror_top',f,x0+1.18,x0+2.03,5.927,5.944,b+2.31,b+2.34,'brass','TRIM')
  for xx in [x0+1.18,x0+2.02]:
    detail_box(f'{name}_mirror_side_{xx:.2f}',f,xx,xx+.017,5.927,5.944,b+1.22,b+2.34,'brass','TRIM')
  for k in range(4):
    yy=4.55+k*.36
    detail_box(f'{name}_marble_joint_{k}',f,x0+.05,x0+.065,yy,yy+.009,b+.09,b+2.3,'stone','TRIM')

def v19_kitchen_detail():
  f=0;b=L[0]
  # 3D raised marble-counter front edge and slim inset wood grain panels.
  detail_box('island_counter_shadow',f,.27,6.60,.875,.905,b+.80,b+.85,'stone','COUNTER')
  for i in range(9):
    xx=.4+i*.67
    detail_box(f'upper_cut_reveal_{i}',f,xx,xx+.012,.54,.552,b+1.56,b+2.52,'groove','TRIM')
  for i in range(6):
    xx=.43+i*.85
    detail_box(f'cupboard_knob_{i}',f,xx+.74,xx+.775,.545,.575,b+1.85,b+1.89,'brass','HANDLE')
  # tiny dark burner grills and stove indicators
  for cx,cy in [(3.78,.42),(4.33,.42),(3.78,.66),(4.33,.66)]:
    for side in [-.065,.065]:
      detail_bar(f'hob_grill_{cx}_{cy}_{side}',f,(cx-.09,cy+side,b+.924),(cx+.09,cy+side,b+.924),.004,'coal','KITCHEN_FIXTURE')
  # Dining chair curved dark-leg support rods
  for i in range(6):
    x=2.40+(i%3)*.77;y=1.86 if i<3 else 4.07
    for xx in [x-.20,x+.20]:
      detail_bar(f'dining_chair_cross_{i}_{xx:.2f}',f,(xx,y-.13,b+.22),(xx,y+.13,b+.22),.012,'walnut','CHAIR')
  detail_box('under_counter_linear_light_strip',f,.47,6.2,.55,.57,b+1.56,b+1.586,'warm','LIGHT')
  # Painting frames along side wall
  for xx in [1.9,4.3]:
    detail_box(f'kitchen_slim_art_frame_{xx}',f,xx,xx+.45,5.86,5.895,b+1.12,b+1.79,'walnut','ART')
    detail_box(f'kitchen_slim_art_canvas_{xx}',f,xx+.045,xx+.405,5.896,5.905,b+1.19,b+1.73,'cream','ART')
  v19_baseboards(f,.15,6.8,5.84,b,'kitchen')

def v19_living_detail():
  f=0;b=L[0]
  # stitched piping across sofa cushions
  for i in range(3):
    xx=14.09+i*1.07
    detail_bar(f'sofa_seat_piping_{i}',f,(xx,.84,b+.64),(xx,1.88,b+.64),.013,'cream','TEXTILE')
  detail_box('coffeemat_rim',f,14.27,16.75,2.42,4.04,b+.031,b+.038,'woodlight','FINISH_V19')
  # Thin walnut accents at TV wall
  for k in range(2):
    xx=[12.1,17.68][k]
    detail_box(f'tv_wall_brass_trim_{k}',f,xx,xx+.017,5.89,5.913,b+.15,b+2.61,'brass','TRIM')
  for xx in [13.9,16.9]:
    detail_box(f'tv_cabinet_underlight_{xx}',f,xx,xx+.3,5.19,5.75,b+.08,b+.09,'warm','LIGHT')
  # Living room corner plant additional leaf layers
  for k in range(5):
    ellip(f'living_planter_leaf_{k}',f,'PLANT',17.82+(-.12+k*.062),4.72,b+1.46,.13,.085,.18,'olive')
  v19_baseboards(f,11.28,18.62,5.83,b,'living')
  for x in [13.1,16.6]:
    detail_box(f'living_wall_sconce_{x}',f,x,x+.24,5.72,5.77,b+2.14,b+2.22,'brass','LIGHT')
    ellip(f'living_wall_light_{x}',f,'LIGHT',x+.12,5.70,b+2.25,.10,.075,.10,'warm')

def v19_bedroom_details():
  for f in [1,2]:
    b=L[f]
    v19_bed_detail(f,'rear',.55,2.65,1.35,3.04,b)
    v19_bath_detail(f,f'rear_wc_{f}',3.25,b)
    v19_wood_floor(f,.18,6.81,.18,3.98,b,'rear')
    v19_baseboards(f,.15,6.8,5.82,b,'rear')
    # curtain top pelmet, fabric mullions
    detail_box(f'rear_curtain_pelmet_{f}',f,.20,1.76,.28,.38,b+2.58,b+2.72,'woodlight','TRIM')
    if f==1:
      v19_bed_detail(f,'front',13.28,15.4,.89,2.74,b)
      v19_bath_detail(f,'front_wc_1',11.25,b)
      v19_wood_floor(f,14.7,18.7,3.05,5.77,b,'front')
      v19_baseboards(f,11.20,18.65,5.83,b,'front')
      detail_box('front_curtain_pelmet',f,17.1,18.55,5.72,5.84,b+2.6,b+2.70,'walnut','TRIM')
    else:
      # terrace paving inset grout joints and succulent pots
      for k in range(17):
        xx=11.2+k*.51
        detail_box(f'terrace_paver_joint_{k}',f,xx,xx+.008,.15,5.72,b+.063,b+.066,'stone','FINISH_V19')
      for i,xx in enumerate([12.65,19.4]):
        cyl(f'terrace_pot_{i}',f,'PLANT',xx,4.86,b+.09,.25,.40,'stone')
        for k in range(4):
          ellip(f'terrace_pot_leaf_{i}_{k}',f,'PLANT',xx+(-.15+k*.10),4.86,b+.60,.12,.11,.18,'olive')

v19_kitchen_detail()
v19_living_detail()
v19_bedroom_details()
print('V19 inherited modeled details:',len(parts),'objects total')

# V20 additional real 3D elements, attached to each of the PDF-zoned rooms.
# Decorative geometry has illustrative dimensions; never label these as CAD verified.

def tube_path(name,f,cat,points,r,col):
  for i in range(1,len(points)):
    bar(f'{name}_seg_{i}',f,cat,points[i-1],points[i],r,col)

def premium_living():
 f=0;b=L[0]
 # Sculpted 3-seater sofa: curved cushions, stitching and light wood side table.
 for i in range(3):
  cx=14.68+i*1.08
  ellip(f'upholstered_seat_sculpt_{i}',f,'SOFA',cx,1.53,b+.65,.51,.40,.16,'cream')
  ellip(f'sofa_backrest_sculpt_{i}',f,'SOFA',cx,.91,b+.81,.49,.20,.39,'sofa')
  bar(f'couch_piping_{i}',f,'TEXTILE',(cx-.46,1.21,b+.68),(cx+.46,1.21,b+.68),.008,'fabric')
 for i,cy in enumerate([1.10,1.90]):
  ellip(f'armrest_{i}',f,'SOFA',14.00 if i==0 else 17.45,cy,b+.64,.15,.35,.35,'fabric')
 # walnut framed wall panels: dark contrasting timber for legibility.
 for i in range(18):
  x=12.31+i*.28
  box(f'feature_wall_wood_slat_{i}',f,'MEDIA',x,x+.055,5.80,5.93,b+.10,b+2.64,'walnut')
 # sculpture & books on console, intentionally schematic.
 for i in range(5):
  xx=13.40+i*.19
  box(f'bookshelf_book_{i}',f,'DECOR',xx,xx+.09,5.04,5.2,b+.63,b+.87,'woodlight' if i%2 else 'cream')
 ellip('console_sculpture',f,'DECOR',17.15,5.1,b+.72,.10,.15,.20,'marble')
 # low table carved organic shape.
 ellip('coffee_round_secondary',f,'COFFEE',15.63,3.23,b+.49,.54,.48,.035,'walnut')
 # textured upholstery seams on lounge chair
 for i,(x,y) in enumerate([(13.52,3.46),(17.24,3.53)]):
  ellip(f'lounge_arm_sculpt_{i}',f,'SOFA',x-.35,y,b+.69,.13,.32,.21,'cream')
  ellip(f'lounge_arm_sculpt2_{i}',f,'SOFA',x+.35,y,b+.69,.13,.32,.21,'cream')
 # pendant lighting arcs
 tube_path('arc_lamp',f,'LIGHT',[(17.76,3.82,b+.02),(17.8,3.82,b+1.65),(17.61,3.57,b+2.08),(17.30,3.31,b+2.18)],.019,'coal')
 cyl('arc_lamp_shade',f,'LIGHT',17.30,3.31,b+2.11,.28,.10,'warm')
 # visible ceiling track lights, over lounge in cutaway.
 for x in [13.1,16.5]:
  box(f'ceiling_light_housing_{x}',f,'LIGHT',x,x+.30,4.86,5.08,b+2.94,b+3.04,'coal')
  for xx in [x+.04,x+.24]:
   cyl(f'ceiling_spot_{xx}',f,'LIGHT',xx,4.96,b+2.89,.038,.06,'warm')

def premium_kitchen():
 f=0;b=L[0]
 # Wood oven/appliance fronts, thin recessed tile joints and island details.
 box('integrated_oven_back',f,'KITCHEN_FIXTURE',4.75,5.45,.795,.834,b+.13,b+.72,'coal')
 box('oven_glass',f,'GLASS',4.82,5.38,.834,.845,b+.22,b+.59,'glass',.40)
 bar('oven_handle',f,'HANDLE',(4.87,.85,b+.65),(5.32,.85,b+.65),.010,'chrome')
 box('dishwasher_front',f,'CABINET',2.02,2.62,.790,.808,b+.07,b+.77,'woodlight')
 bar('dishwasher_handle',f,'HANDLE',(2.16,.823,b+.67),(2.48,.823,b+.67),.013,'brass')
 for x in np.arange(.45,6.35,.45):
  bar(f'backsplash_joint_vertical_{x:.2f}',f,'FINISH',(x,.121,b+.9),(x,.121,b+1.55),.0026,'stone')
 # wall-mounted decorative cabinetry end gables
 for x in [.43,6.26]:
  box(f'cabinet_end_solid_{x}',f,'CABINET',x,x+.05,.13,.58,b+1.54,b+2.58,'walnut')
 # Natural pendant with stepped shades
 for i,x in enumerate([2.70,3.28,3.86]):
  cyl(f'pendant_wood_shade_{i}',f,'LIGHT',x,3.0,b+2.06,.19,.055,'walnut')
  cyl(f'pendant_diffuser_{i}',f,'LIGHT',x,3.0,b+1.98,.105,.048,'warm')
  bar(f'pendant_brass_cap_{i}',f,'LIGHT',(x,3.0,b+2.15),(x,3.0,b+2.22),.031,'brass')
 # Dining chair cushions curved and back frames
 for i in range(6):
  x=2.40+(i%3)*.77;y=1.86 if i<3 else 4.07
  ellip(f'dining_seat_cushion_{i}',f,'CHAIR',x,y,b+.52,.25,.22,.055,'cream')
  for dx in [-.23,.23]:
   bar(f'chair_back_side_{i}_{dx}',f,'CHAIR',(x+dx,y+(.2 if i<3 else -.20),b+.44),(x+dx,y+(.20 if i<3 else -.20),b+.92),.021,'walnut')
  bar(f'chair_back_crossbar_{i}',f,'CHAIR',(x-.23,y+(.20 if i<3 else -.20),b+.88),
       (x+.23,y+(.20 if i<3 else -.20),b+.88),.022,'walnut')
 # Extra indoor floor pots and green herbs by the sink
 for i,x in enumerate([.87,1.12,5.02]):
  cyl(f'counter_planter_{i}',f,'PLANT',x,.41,b+.90,.085,.16,'white')
  ellip(f'herb_leaves_{i}',f,'PLANT',x,.41,b+1.16,.17,.11,.17,'olive')

def premium_bedroom(f,which,xa,xb,ya,yb):
 b=L[f]
 # Tucked duvet with layered quilt strips and upholstery.
 span=(yb-ya)
 for k in range(9):
  yy=ya+span*(k+.4)/10
  ellip(f'{which}_quilt_softfold_{k}_f{f}',f,'TEXTILE',(xa+xb)/2+.12,yy,b+.757,.80,.015,.012,'bedlinen')
 # Folded blanket at the foot of bed, with texture contrast.
 box(f'{which}_throw_f{f}',f,'TEXTILE',xb-.54,xb-.16,ya+.16,yb-.16,b+.755,b+.816,'fabric')
 for k in [0,1]:
  y=ya+.32+k*.70
  ellip(f'{which}_second_pillow_f{f}_{k}',f,'TEXTILE',xa+.38,y,b+.78,.29,.27,.06,'white')
 # Premium padded headboard panels
 for k in range(6):
  y=ya+k*span/6
  ellip(f'{which}_headboard_pad_f{f}_{k}',f,'TEXTILE',xa-.15,y+span/12,b+.88,.058,span/12,.36,'cream')
 # Bedside storage with protruding drawer lip
 for yy in [ya-.22,yb+.04]:
  box(f'{which}_nighstand_drawer_{yy:.2f}_f{f}',f,'FURNITURE',xa+.15,xa+.45,yy-.01,yy+.18,b+.20,b+.34,'walnut')
  bar(f'{which}_bedside_pull_{yy:.2f}_f{f}',f,'HANDLE',(xa+.27,yy+.18,b+.26),(xa+.4,yy+.18,b+.26),.007,'brass')
 # wall linear reading lamps
 for yy in [ya-.12,yb+.08]:
  bar(f'{which}_reader_arm_{yy:.2f}_f{f}',f,'LIGHT',(xa-.2,yy,b+1.58),(xa+.04,yy,b+1.56),.012,'brass')
  ellip(f'{which}_reader_light_{yy:.2f}_f{f}',f,'LIGHT',xa+.04,yy,b+1.54,.085,.075,.035,'warm')

def premium_wetroom(f,name,x0):
 b=L[f]
 # Rounded basin bowl (within approximation zone), shelf and glass hardware.
 ellip(f'{name}_sink_inner_f{f}',f,'BATH_FITTING',x0+1.64,5.48,b+.937,.28,.19,.028,'white')
 ellip(f'{name}_sink_drain_f{f}',f,'BATH_FITTING',x0+1.64,5.48,b+.967,.021,.021,.003,'chrome')
 box(f'{name}_vanity_open_shelf_f{f}',f,'BATH',x0+1.15,x0+2.07,5.27,5.33,b+.28,b+.33,'woodlight')
 for y in [4.61,5.58]:
  box(f'{name}_shower_glass_hinge_f{f}_{y}',f,'BATH_FITTING',x0+1.02,x0+1.10,y,y+.085,b+1.01,b+1.17,'chrome')
 bar(f'{name}_shower_vertical_pull_f{f}',f,'BATH_FITTING',(x0+1.08,5.10,b+.92),(x0+1.08,5.10,b+1.32),.017,'chrome')
 # Wall towel stack and small toiletries.
 for k in range(3):
  box(f'{name}_towel_stack_f{f}_{k}',f,'TEXTILE',x0+1.3,x0+1.76,5.14,5.22,b+.38+k*.095,b+.45+k*.095,'cream')
 cyl(f'{name}_soap_dispenser_f{f}',f,'BATH_FITTING',x0+1.97,5.33,b+.95,.037,.15,'white')

def premium_rooftop():
 f=3;b=L[3]
 # Small plinth under water tank, matching KT09 location.
 box('tank_steel_support',f,'ROOF_EQUIPMENT',3.04,3.74,3.44,4.12,b+.01,b+.28,'metal')
 for xx in [3.14,3.66]:
  for yy in [3.56,4.02]:
   bar(f'tank_mount_{xx}_{yy}',f,'ROOF_EQUIPMENT',(xx,yy,b+.02),(xx,yy,b+.36),.024,'chrome')
 # Solar panel glossy glass / individual tube glazing
 box('solar_anti_reflective_glass',f,'SOLAR',4.61,5.74,3.17,4.04,b+.36,b+.372,'solar')
 for i,xx in enumerate(np.linspace(4.69,5.63,6)):
  bar(f'solar_absorber_{i}',f,'SOLAR',(xx,3.24,b+.375),(xx,3.98,b+.375),.014,'metal')
 # roof access brushed metal threshold
 box('roof_door_threshold',f,'ROOF_ACCESS',8.55,9.7,5.22,5.45,b,b+.04,'metal')

premium_living()
premium_kitchen()
premium_bedroom(1,'rear',.55,2.65,1.35,3.04)
premium_bedroom(1,'front',13.28,15.4,.89,2.74)
premium_bedroom(2,'rear',.55,2.65,1.35,3.04)
premium_wetroom(1,'rear_wc',3.25)
premium_wetroom(1,'front_wc',11.25)
premium_wetroom(2,'rear_wc',3.25)
premium_rooftop()


print('V20 detailed real mesh furniture count',len(parts))

# V21 — LUXURY REFERENCE STYLE. Architectural placement anchored to KT06–KT09.
# DECORATIVE OBJECTS ARE VISUAL DESIGN ONLY, not material approvals or construction dimensions.
from math import pi
def luxury_box(name,f,cat,x0,x1,y0,y1,z0,z1,col,alpha=1):
 return box('L21_'+name,f,cat,x0,x1,y0,y1,z0,z1,col,alpha,reference='STYLE_REFERENCE_VISUAL_2026_NOV')

def luxury_bar(name,f,cat,a,b,r,col):
 return bar('L21_'+name,f,cat,a,b,r,col)

def luxury_torus(name,f,cat,x,y,z,R=.52,t=.015,col='gold'):
 mesh=trimesh.creation.torus(major_radius=R,minor_radius=t,major_sections=64,minor_sections=8)
 mesh.apply_translation([x,y,z])
 return add_mesh('L21_'+name,f,cat,mesh,col,reference='STYLE_REFERENCE_VISUAL_2026_NOV')

def luxury_lamp(name,f,x,y,z,r=.18):
 luxury_torus(name+'_gold_ring',f,'LIGHT',x,y,z,r,.013,'gold')
 luxury_torus(name+'_warm_diffuser',f,'LED',x,y,z-.016,r-.005,.011,'warmled')
 luxury_bar(name+'_suspensionA',f,'LIGHT',(x-.12,y,z),(x-.12,y,z+.28),.005,'gold')
 luxury_bar(name+'_suspensionB',f,'LIGHT',(x+.12,y,z),(x+.12,y,z+.28),.005,'gold')

def luxury_room_lighting(f,x0,x1,y0,y1,z,name):
 # Emissive golden cove strips near floor-to-ceiling cutaway, no complete ceiling to obscure interiors
 for yy in [y0,y1]:
  luxury_box(f'{name}_led_y_{yy:.1f}',f,'LED',x0+.1,x1-.1,yy-.018,yy+.018,z-.018,z+.005,'warmled')
  luxury_box(f'{name}_gold_cove_y_{yy:.1f}',f,'LIGHT',x0+.08,x1-.08,yy-.040,yy-.027,z-.08,z+.006,'gold')
 for xx in [x0,x1]:
  luxury_box(f'{name}_led_x_{xx:.1f}',f,'LED',xx-.018,xx+.018,y0+.09,y1-.09,z-.018,z+.005,'warmled')
 for i in range(max(2,int((x1-x0)/1.45))):
  x=x0+(i+.5)*(x1-x0)/max(2,int((x1-x0)/1.45))
  cyl(f'L21_{name}_downlight_{i}',f,'LED',x,y1-.12,z-.16,.050,.03,'warmled')

def luxury_lift_and_stair(f):
 b=L[f]
 # Reference: central brushed-metal/glass elevator surrounded by taupe-grey marble.
 # PDF KT06–08 retains 4.15 m core and U-shaped stairs; this is finish and design concept.
 # Shaft in PDF shown approx x8.5–9.9; these new cladding parts do not relocate it.
 for i,(xa,xb) in enumerate([(8.20,8.42),(9.93,10.15)]):
  luxury_box(f'lift_marble_pier_{i}',f,'LIFT',xa,xb,.83,.97,b+.03,b+3.05,'darkmarble')
  luxury_box(f'lift_gold_pier_{i}',f,'TRIM',xa+.03,xa+.05,.81,.84,b+.18,b+2.90,'gold')
 luxury_box('lift_marble_header',f,'LIFT',8.20,10.15,.83,.98,b+2.38,b+3.08,'darkmarble')
 luxury_box('lift_backlit_architrave',f,'LED',8.27,10.07,.80,.822,b+2.35,b+2.39,'warmled')
 luxury_box('lift_lobby_grey_stone',f,'FINISH',7.58,10.65,2.45,3.88,b+.034,b+.059,'greymarble')
 # Lift front glass and double doors; transparent within existing jamb.
 for i,(xa,xb) in enumerate([(8.63,9.21),(9.23,9.81)]):
  luxury_box(f'lift_glass_leaf_{i}',f,'LIFT_GLASS',xa,xb,.805,.820,b+.20,b+2.24,'smokeglass',.24)
  for x in [xa,xb]:
   luxury_bar(f'lift_glass_frame_{i}_{x:.2f}',f,'TRIM',(x,.791,b+.18),(x,.791,b+2.26),.014,'gold')
 luxury_bar('lift_transom_top',f,'TRIM',(8.63,.79,b+2.25),(9.81,.79,b+2.25),.023,'gold')
 for yy in [.13,.95,1.47,2.32]:
  # modeled translucent tempered-glass balustrade
  if yy in (.95,1.47):
   luxury_box(f'stair_glass_side_{yy}',f,'STAIR_GLASS',7.32,10.83,yy-.016,yy+.016,b+.82,b+1.51,'clearglass',.17)
  luxury_bar(f'stair_bronze_cap_{yy}',f,'STAIR_RAIL',(7.2,yy,b+.92),(10.82,yy,b+2.34),.023,'bronze')
 # Individual stair-step underside/warm strips, matching symbolic U-stair in KT12.
 for k in range(10):
  xx=7.12+k*.195
  z=b+.19+k*.166
  luxury_box(f'stair_A_underglow_{k}',f,'LED',xx+.013,xx+.182,.169,.198,z-.024,z-.009,'warmled')
  xx2=10.88-k*.195
  zz=b+1.89+k*.144
  luxury_box(f'stair_B_underglow_{k}',f,'LED',xx2-.177,xx2-.014,2.265,2.286,zz-.019,zz-.004,'warmled')
  # slate treads with brass nosing
  luxury_box(f'stair_A_dark_tread_{k}',f,'STAIR',xx+.004,xx+.183,.24,.89,z+.004,z+.031,'smokestone')
  luxury_box(f'stair_B_dark_tread_{k}',f,'STAIR',xx2-.181,xx2-.003,1.52,2.23,zz+.004,zz+.031,'smokestone')
 # Real decorative lift call panel near entrance
 luxury_box('lift_call_brass_trim',f,'LIFT',10.20,10.26,.80,.86,b+1.06,b+1.88,'gold')
 luxury_box('lift_call_black',f,'LIFT',10.203,10.26,.79,.803,b+1.10,b+1.83,'graphite')
 cyl(f'L21_lift_button_{f}',f,'LIGHT',10.23,.774,b+1.44,.025,.012,'warmled')

def luxury_marble_floor(f,xa,xb,ya,yb,base,name):
 # Visual marble tiles 750mm and delicate grout lines; no claims of floor-spec exactness.
 luxury_box(name+'_tile_base',f,'FINISH',xa,xb,ya,yb,base+.034,base+.052,'lightmarble')
 for j in range(1,int((xb-xa)/.75)+1):
  x=xa+j*.75
  if x>=xb:break
  luxury_box(f'{name}_tile_grout_x_{j}',f,'FINISH',x-.004,x+.004,ya,yb,base+.052,base+.053,'softtaupe')
 for j in range(1,int((yb-ya)/.75)+1):
  y=ya+j*.75
  if y>=yb:break
  luxury_box(f'{name}_tile_grout_y_{j}',f,'FINISH',xa,xb,y-.004,y+.004,base+.052,base+.053,'softtaupe')

def luxury_ground():
 f=0;b=L[0]
 luxury_marble_floor(f,.18,6.78,.18,5.80,b,'kitchen_marble_floor')
 luxury_marble_floor(f,7.20,10.92,2.53,5.72,b,'lobby_marble_floor')
 luxury_marble_floor(f,11.32,18.62,.18,5.78,b,'living_marble_floor')
 # Kitchen light charcoal upper cabinets, full-height built-in fridge and oven column; keep KT06 location.
 luxury_box('kitchen_taupe_cabinet_skin',f,'CABINET',.29,6.63,.80,.833,b+.17,b+.74,'taupegrey')
 for k in range(10):
  x=.40+k*.58
  luxury_bar(f'kitchen_lip_{k}',f,'TRIM',(x,.835,b+.70),(x+.35,.835,b+.70),.009,'gold')
 luxury_box('kitchen_upper_taupe_skin',f,'CABINET',.24,6.71,.57,.602,b+1.65,b+2.45,'taupegrey')
 luxury_box('kitchen_gold_led',f,'LED',.31,6.59,.61,.638,b+1.60,b+1.635,'warmled')
 luxury_box('kitchen_premium_worktop',f,'COUNTER',.23,6.76,.36,.96,b+.83,b+.89,'lightmarble')
 luxury_box('kitchen_fridge_side',f,'KITCHEN_FIXTURE',6.07,6.70,.76,1.15,b+.04,b+2.49,'graphite')
 luxury_box('kitchen_fridge_black_glass',f,'KITCHEN_FIXTURE',6.24,6.61,.745,.76,b+.32,b+2.18,'graphite')
 for yy in [1.85,2.95,4.05]:
  # marble dinner island stools are already at fixed original dining layout; add upholstered back.
  luxury_box(f'kitchen_slat_feature_{yy:.2f}',f,'TRIM',5.88,5.91,yy,yy+.14,b+.38,b+2.60,'walnut')
 luxury_room_lighting(f,.27,6.72,.20,5.72,b+2.97,'kitchen')
 for yy in [2.57,3.54]:
  luxury_lamp(f'kitchen_pendant_{yy:.2f}',f,2.94,yy,b+2.56,.31)
 # LIVING: mirror-like TV wall, white sofa already modeled in initial furniture.
 luxury_box('living_tv_feature_marble',f,'MEDIA',13.05,17.90,5.71,5.765,b+.28,b+2.75,'darkmarble')
 for k in range(9):
  x=13.11+k*.54
  luxury_box(f'feature_gold_vertical_{k}',f,'TRIM',x,x+.018,5.688,5.710,b+.31,b+2.74,'gold')
 # Large black television on TV wall (front surface facing inward)
 luxury_box('feature_black_tv',f,'MEDIA',14.17,17.18,5.63,5.68,b+1.08,b+2.08,'graphite')
 luxury_box('feature_gold_tv_base',f,'TRIM',14.08,17.29,5.65,5.69,b+.80,b+.83,'gold')
 # Gold-edged marble coffee table top; original proportions retained.
 luxury_box('coffee_marbled_top',f,'COFFEE',14.31,16.52,2.52,3.95,b+.55,b+.585,'lightmarble')
 luxury_box('coffee_marbled_brass_edge',f,'TRIM',14.34,16.49,2.52,2.545,b+.54,b+.57,'gold')
 # Tall full-length sliding glass near front, black metal mullions (matches luxury reference)
 for yy in [1.13,2.08,3.04,4.03,4.96]:
  luxury_bar(f'front_glass_black_mullion_{yy:.2f}',f,'FRAME',(18.79,yy,b+.06),(18.79,yy,b+2.88),.026,'graphite')
 luxury_room_lighting(f,11.22,18.70,.18,5.74,b+3.01,'living')
 for i,(x,y,r) in enumerate([(13.50,2.53,.44),(14.08,2.80,.53),(13.85,2.43,.64)]):
  luxury_lamp('lounge_ring_'+str(i),f,x,y,b+2.64-i*.07,r)
 # Tall wall marble around center lobby extending slightly into view.
 luxury_box('lobby_backlit_dark_marble',f,'FEATURE',10.85,11.08,3.51,5.57,b+.15,b+2.86,'darkmarble')
 luxury_bar('lobby_bronze_vertical',f,'TRIM',(10.82,3.51,b+.23),(10.82,3.51,b+2.86),.012,'gold')
 luxury_lift_and_stair(f)

def luxury_upstairs(f):
 b=L[f]
 luxury_lift_and_stair(f)
 # Luxury bedroom warm veneer feature walls and linen bed textiles.
 for xa,xb,cn in ([(.35,3.95,'rear')]+ ([(13.0,17.15,'front')] if f==1 else [])):
  y=5.66
  luxury_box(f'{cn}_headboard_back_wood',f,'WARDROBE',xa,xb,y,y+.045,b+.28,b+2.66,'lightoak')
  for j in range(int((xb-xa)/.24)):
   x=xa+j*.24
   luxury_box(f'{cn}_headboard_slat_{j}',f,'TRIM',x,x+.027,y-.035,y+.016,b+.30,b+2.65,'walnut')
  luxury_bar(f'{cn}_wall_led',f,'LED',(xa+.12,y-.04,b+2.62),(xb-.13,y-.04,b+2.62),.013,'warmled')
  luxury_room_lighting(f,xa+.1,xb-.1,.20,5.7,b+3.0,cn)
 # Modern glass shower with metal lines, shower curtain and polished gray marble restroom.
 for i,x0 in enumerate(([3.25,11.25] if f==1 else [3.25])):
  luxury_box(f'wc_wall_marble_{i}',f,'BATH_WALL',x0+.02,x0+2.83,5.80,5.83,b+.10,b+2.65,'greymarble')
  for k in range(4):
   yy=4.4+k*.32
   luxury_box(f'wc_horizontal_stone_joint_{i}_{k}',f,'FINISH',x0+.03,x0+2.78,yy,yy+.006,b+.06,b+.062,'softtaupe')
  luxury_box(f'wc_glass_door_{i}',f,'GLASS',x0+1.05,x0+1.073,4.65,5.72,b+.09,b+2.13,'clearglass',.16)
  luxury_bar(f'wc_gold_handle_{i}',f,'HANDLE',(x0+1.083,5.2,b+.94),(x0+1.083,5.2,b+1.29),.013,'gold')
  luxury_bar(f'wc_backlit_mirror_{i}',f,'LED',(x0+1.2,5.9,b+2.31),(x0+2.12,5.9,b+2.31),.014,'warmled')
 if f==2:
  # Terrace landscaped perimeter aligned to front open span 11.15 to 18.85.
  for i,x in enumerate(np.linspace(11.70,18.40,7)):
   luxury_box(f'terrace_long_planter_{i}',f,'PLANTER',x,x+.58,5.28,5.74,b+.08,b+.58,'greymarble')
   cyl(f'L21_terrace_olive_trunk_{i}',f,'PLANT',x+.30,5.48,b+.49,.055,.66,'walnut')
   ellip(f'L21_terrace_olive_crown_{i}',f,'PLANT',x+.30,5.48,b+1.32,.28,.25,.38,'olive')
   luxury_box(f'terrace_planter_strip_{i}',f,'LED',x+.02,x+.55,5.73,5.75,b+.39,b+.42,'warmled')
  luxury_lamp('terrace_pendant',f,14.67,2.77,b+2.4,.38)
  luxury_box('terrace_table_top_marble',f,'COUNTER',13.28,16.17,2.43,3.86,b+.64,b+.70,'lightmarble')

def luxury_roof():
 f=3;b=L[3]
 # KT09 roof only over rear+stair; no fake coverage over entire front terrace.
 luxury_box('roof_technical_tank_rim',f,'ROOF_EQUIPMENT',3.00,3.78,3.39,4.17,b+.04,b+.12,'gold')
 luxury_box('roof_solar_toughened_glass',f,'SOLAR',4.68,5.70,3.21,4.02,b+.375,b+.384,'smokeglass',.26)
 # Roof access coping realistic taupe concrete trim
 for x in [7.23,11.02]:
  luxury_box(f'roof_lift_penthouse_pier_{x}',f,'ROOF_ACCESS',x,x+.08,.95,5.65,b+.16,b+2.02,'lightmarble')

luxury_ground()
luxury_upstairs(1)
luxury_upstairs(2)
luxury_roof()
print('V21 luxury geometry added. Total objects:',len(parts))



# Layout category and visibility metadata preserved in JSON next to GLB.
meta={
 'project':'NHA V21 — luxury glass elevator, marble, brass, warm light, detailed furniture; PDF KT06-KT09 axis plan',
 'basis':'KT01, KT06, KT07, KT08, KT09, KT10, KT12 from original 14-page PDF',
 'not_v16_import':True,
 'v21_design_reference':'User supplied three images: luxury interior mood, house program diagram, three-storey furnished exploded axonometric. These photos are not measured CAD drawings.',
 'v21_styling':'Gray marble elevator, warm gold LEDs, clear balustrades, taupe joinery, cream furnishings, textured stone/wood. All product dimensions and placements are illustrative and must be reviewed by architect.',
 'axes_m':{'x':[0,7,11.15,18.85],'width':6,'levels_kt10':[.8,4.7,8.3,11.7]},
 'coordinate_system':'X rear-to-front, Y cross width A-B, Z up; GLB mesh in metres',
 'status':'CONCEPT_VISUALISATION_NOT_CONSTRUCTION_CAD',
 'known_dimensions':MEAS,
 'assumptions':[
  'All joinery materials, colours, floor finishes and furnishing geometry are creative design placeholders; PDF does not specify product models.',
  'Wall widths, exact door/window coordinates and frame dimensions require original CAD/shop drawings.',
  'KT10 and KT11 upper heights conflict. Display uses KT10 only.',
  'Roof equipment sizes not supplied by PDF. Stair/elevator geometry conceptual, lift cabin note 1340x850 is not a shaft specification.'
 ],
 'counts_by_category':dict(counts),'object_count':len(parts),
 'objects':parts
}
(OUT/'V21_model_provenance.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False))

# Full GLB; layers are named with a predictable F{floor}__CAT__name prefix.
outglb=OUT/'NHA_V21_LUXURY_CUTAWAY_THEO_PDF.glb'
outglb.write_bytes(SC.export(file_type='glb'))
print('GLB',outglb.stat().st_size,'bytes',len(parts),'nodes',len(MATS),'materials')

# DXF 3D: actual geometry export as editable 3D MESH objects, 1 unit=mm.
doc=ezdxf.new('R2013');doc.header['$INSUNITS']=4;msp=doc.modelspace()
for part in parts:
 name=part['node']; geo=SC.geometry[name]
 lay='F'+str(part['floor'])+'_'+part['category']
 if lay not in doc.layers:
  doc.layers.add(lay,dxfattribs={'color': 7})
 msh=msp.add_mesh(dxfattribs={'layer':lay})
 with msh.edit_data() as d:
  d.vertices=[tuple(map(float,v*1000)) for v in geo.vertices]
  d.faces=[tuple(int(i) for i in face) for face in geo.faces]
dxf=OUT/'NHA_V21_LUXURY_CAD_3D.dxf';doc.saveas(dxf)
print('DXF',dxf.stat().st_size,'bytes')
print('COUNT',list(counts.items())[:30])

# User instructions
(OUT/'README_V21.txt').write_text('''NHÀ V21 - MÔ HÌNH 3D SANG TRỌNG CẮT LỚP NỘI THẤT CHI TIẾT TỪ PDF 14 TRANG

- File NHA_V21_LUXURY_CUTAWAY_THEO_PDF.glb: vật thể 3D thật, từng khối có tên và phân tầng. Xem bằng trang index.html hoặc GLB viewer.
- File NHA_V21_LUXURY_CAD_3D.dxf: lưới hình học 3D theo lớp, 1 đơn vị = 1 mm, không phải hồ sơ thi công.
- File V21_model_provenance.json: nguồn, thông số từ PDF, danh sách giả định.

TRỤC CÓ SỐ GHI: 6.000 mm ngang; 18.850 mm dài; 7.000 + 4.150 + 7.700 mm.
KT07: 2 phòng ngủ và 2 WC. KT08: 1 phòng ngủ + WC sau và sân thượng trước.
KT09: mái phía sau + lõi thang + phần vươn 1.100 mm, không che sân trước.

TẤT CẢ các đồ nội thất, tủ, sofa, thiết bị bếp/WC, thiết bị mái và vật liệu là thiết kế minh họa phát triển mới để có hình dạng đẹp, chưa phải định vị/kích thước được phê duyệt.
KT10 và KT11 mâu thuẫn cao độ: dùng KT10 chỉ để trình bày.

Bản V18 được dựng ĐỘC LẬP từ mặt bằng PDF, không nhập file GLB/CAD V16 vào làm cơ sở hình học.
''',encoding='utf-8')