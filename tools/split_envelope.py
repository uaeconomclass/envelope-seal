"""Registered pocket and flap cut from one generated master, no mismatched seams."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
root=Path(__file__).resolve().parent.parent
A=root/'assets'
im=Image.open(A/'source-v2/envelope_master.png').convert('RGBA')
w,h=im.size
im=im.crop((round(w*.013),round(h*.024),round(w*.987),round(h*.965))).resize((836,550),Image.Resampling.LANCZOS)
points=[(0,0),(836,0),(836,22)]
def bezier(p0,p1,p2,p3):
    for t in np.linspace(0,1,50):
        points.append(tuple((1-t)**3*np.array(p0)+3*(1-t)**2*t*np.array(p1)+3*(1-t)*t*t*np.array(p2)+t**3*np.array(p3)))
bezier((836,22),(836,54),(833,65),(813,80))
points.append((436,373))
bezier((436,373),(423,384),(411,385),(396,373))
points.append((23,79))
bezier((23,79),(4,66),(0,51),(0,22))
mask=Image.new('L',(3344,2200))
ImageDraw.Draw(mask).polygon([(round(x*4),round(y*4)) for x,y in points],fill=255)
mask=mask.resize((836,550),Image.Resampling.LANCZOS)
yy,xx=np.mgrid[:550,:836].astype(np.float32)
# Align the master flap tip with the seal axis x=217 in CSS.
sx=np.where(xx<=434,xx*416/434,416+(xx-434)*420/402).astype(np.float32)
rgb=cv2.remap(np.array(im)[:,:,:3],sx,yy,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
alpha=cv2.remap(np.array(mask),sx,yy,cv2.INTER_LINEAR)
outer=Image.fromarray(rgb[:384]).convert('RGBA');outer.putalpha(Image.fromarray(alpha[:384]))
pocket=Image.fromarray(rgb).convert('RGBA')
pocket.putalpha(Image.fromarray(255-cv2.erode(alpha,np.ones((3,3),np.uint8))))
inner=Image.open(A/'source-v2/flap_inner.png').convert('RGB').resize((836,384),Image.Resampling.LANCZOS)
# Use an uninterrupted paper texture for the inner face, with exactly the
# same silhouette as the outer face (no source triangle alpha can leak in).
inner=Image.open(A/'source-v2/env_back_inner.png').convert('RGB').resize((836,384),Image.Resampling.LANCZOS).convert('RGBA')
inner.putalpha(Image.fromarray(alpha[:384]))
for name,layer in [('flap_outer',outer),('flap_inner',inner),('env_pocket',pocket)]:
    layer.save(A/(name+'.png'))
    layer.save(root/'dist/assets'/(name+'.webp'),quality=90,method=6)
print('Shared envelope geometry: 418x275 body; 418x192 flap; hinge (425,148); tip axis x=642.')
