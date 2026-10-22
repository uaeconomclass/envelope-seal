"""Keep reference composition while using generated pixels in removed regions.

Run once after prepare_assets.py. Generated textures repair the old blurred
seal region; original scene pixels outside removed objects remain unchanged.
"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent.parent
A=ROOT/'assets'
ref=np.array(Image.open(ROOT/'reference.jpg').convert('RGB'))
generated=np.array(Image.open(A/'bg_clean.png').convert('RGB').resize((1280,691)))
mask=np.zeros((691,1280),np.uint8)
mask[145:426,422:845]=255
stamp=np.array(Image.open(ROOT/'stamp.png').convert('RGBA'))[:,:,3]
mask[5:200,705:885]=np.maximum(mask[5:200,705:885],stamp)
mask=cv2.dilate(mask,np.ones((9,9),np.uint8))
blend=cv2.GaussianBlur(mask,(9,9),0).astype(float)[:,:,None]/255
bg=ref*(1-blend)+generated*blend
# Text sits on a nearly flat navy area. Remove just glyphs, not the scene.
textmask=np.zeros(mask.shape,np.uint8)
gray=cv2.cvtColor(ref,cv2.COLOR_RGB2GRAY)
textmask[448:622,390:889]=(gray[448:622,390:889]>95).astype(np.uint8)*255
textmask=cv2.dilate(textmask,np.ones((5,5),np.uint8))
bg=cv2.inpaint(bg.astype(np.uint8),textmask,5,cv2.INPAINT_TELEA)

def save(name,im,size):
    im=im.resize(size,Image.Resampling.LANCZOS)
    im.save(A/(name+'.png'))
    im.save(A/(name+'.webp'),quality=90,method=6)

save('bg_clean',Image.fromarray(bg),(2560,1382))
base=np.array(Image.open(ROOT/'env.png').convert('RGB')).astype(float)
tex=np.array(Image.open(A/'env_back_inner.png').convert('RGB').resize((418,275))).astype(float)
detail=tex-cv2.GaussianBlur(tex,(0,0),3)
repair=np.zeros((275,418),np.uint8)
cv2.circle(repair,(217,152),65,255,-1)
repair=cv2.GaussianBlur(repair,(31,31),0)[:,:,None]/255
paper=np.clip(base+detail*repair,0,255).astype(np.uint8)
for name,size,points in [
    ('env_pocket',(836,550),[(0,0),(217,152),(418,0),(418,275),(0,275)]),
    ('flap_outer',(836,306),[(0,0),(418,0),(217,153)])]:
    height=275 if name=='env_pocket' else 153
    im=Image.fromarray(paper[:height]).convert('RGBA')
    alpha=Image.new('L',(418*4,height*4))
    ImageDraw.Draw(alpha).polygon([(x*4,y*4) for x,y in points],fill=255)
    im.putalpha(alpha.resize(im.size,Image.Resampling.LANCZOS))
    save(name,im,size)
print('Reference composition retained; generated detail restores seal patch.')
