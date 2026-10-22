"""Retain reference pixels; replace only removed envelope, stamp and glyphs."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parent.parent
ref=np.array(Image.open(root/'reference.jpg').convert('RGB'))
clean=np.array(Image.open(root/'assets/source-v2/bg_clean.png').convert('RGB').resize((1280,691),Image.Resampling.LANCZOS))
# Preserve all existing room/city detail. The old stamp needs a complete
# silhouette mask, including its dark rim (the old color extraction omitted it).
mask=np.zeros((691,1280),np.uint8)
cv2.fillPoly(mask,[np.array([(424,145),(838,145),(847,428),(418,428)])],255)
cv2.ellipse(mask,(839,56),(46,53),25,0,360,255,-1)
cv2.line(mask,(827,85),(777,139),255,45)
cv2.ellipse(mask,(755,156),(46,40),32,0,360,255,-1)
blend=cv2.GaussianBlur(mask,(9,9),0)[:,:,None].astype(float)/255
out=(ref*(1-blend)+clean*blend).astype(np.uint8)
text=np.zeros(mask.shape,np.uint8)
gray=cv2.cvtColor(ref,cv2.COLOR_RGB2GRAY)
text[448:625,390:890]=(gray[448:625,390:890]>65).astype(np.uint8)*255
text=cv2.dilate(text,np.ones((5,5),np.uint8))
out=cv2.inpaint(out,text,7,cv2.INPAINT_TELEA)
im=Image.fromarray(out).resize((2560,1382),Image.Resampling.LANCZOS)
im.save(root/'assets/bg_clean.png')
im.save(root/'dist/assets/bg_clean.webp',quality=95,method=6)
