"""Apply the customer's five-sided flap outline (2026-10-22)."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
import io, subprocess

A=Path(__file__).resolve().parent.parent/'assets'
for name in ('flap_outer','flap_inner'):
    path=A/(name+'.png')
    if name=='flap_outer':
        im=Image.open(A.parent/'env.png').crop((0,0,418,153)).convert('RGBA')
    else:
        im=Image.open(io.BytesIO(subprocess.check_output(['git','show','48e41c7:assets/flap_inner.png'],cwd=A.parent))).convert('RGBA')
    src=np.array(im.resize((836,306)))
    yy,xx=np.mgrid[:380,:836].astype(np.float32)
    sy=yy/380*305
    # Map each horizontal cross-section to the old triangular texture.
    fraction=sy/306
    left=434*fraction
    right=836-(836-434)*fraction
    new_fraction=np.maximum(0,(yy-64)/316)
    new_left=434*new_fraction
    new_right=836-(836-434)*new_fraction
    sx=left+(xx-new_left)/np.maximum(1,new_right-new_left)*(right-left)
    sx=np.clip(sx,left+2,np.maximum(left+2,right-3)).astype(np.float32)
    rgb=cv2.remap(src[:,:,:3],sx,sy.astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    alpha=Image.new('L',(3344,1520))
    ImageDraw.Draw(alpha).polygon([(0,0),(3344,0),(3344,256),(1736,1520),(0,256)],fill=255)
    result=Image.fromarray(rgb).convert('RGBA')
    result.putalpha(alpha.resize((836,380),Image.Resampling.LANCZOS))
    result.save(path)
    result.save(A/(name+'.webp'),quality=90,method=6)
