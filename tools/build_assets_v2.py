"""Normalize only the new generated masters, never old inpainted layers."""
from pathlib import Path
import json, subprocess, sys, shutil
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'assets'/'source-v2'
OUT=ROOT/'dist'/'assets'
SIZES={'bg_clean':(2560,1382),'bg_clean_mobile':(780,1400),
       'env_back_inner':(836,550),'env_pocket':(836,550),
       'flap_outer':(836,360),'flap_inner':(836,360),
       'seal':(224,224),'stamp':(360,390),'letter':(700,400),
       'glow_trails':(1200,800)}

def flap_points(scale=1):
    # Trace of the visible paper shoulders; tip sits behind the wax seal.
    points=[(0,0),(418,0),(417,15),(415,23),(410,29),
            (224,176),(220,179),(217,180),(213,178),
            (10,29),(5,24),(2,17)]
    return [(round(x*scale),round(y*scale)) for x,y in points]

def normalize_paper(im,name,size):
    """Map generated paper silhouette to a shared hinge, without edge gaps."""
    bbox=im.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox()
    if bbox: im=im.crop(bbox)
    im=im.resize(size,Image.Resampling.LANCZOS)
    arr=np.array(im)
    w,h=size
    mask=Image.new('L',(w*4,h*4))
    pts=([(0,0),(434,304),(836,0),(836,550),(0,550)] if name=='env_pocket'
         else flap_points(2))
    ImageDraw.Draw(mask).polygon([(x*4,y*4) for x,y in pts],fill=255)
    mask=mask.resize(size,Image.Resampling.LANCZOS)
    target=np.array(mask)
    # Fill subpixel mismatches with the nearest generated opaque paper pixel,
    # avoiding transparent RGB fringes without blurring the paper itself.
    valid=(arr[:,:,3]>180).astype(np.uint8)
    _,indices=cv2.distanceTransformWithLabels(1-valid,cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
    colors=arr[:,:,:3][valid.astype(bool)]
    if len(colors):
        missing=(target>0)&(valid==0)
        arr[:,:,:3][missing]=colors[np.clip(indices[missing]-1,0,len(colors)-1)]
    arr[:,:,3]=target
    return Image.fromarray(arr)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for name,size in SIZES.items():
        path=SOURCE/('bg_final.png' if name=='bg_clean' and (SOURCE/'bg_final.png').exists() else name+'.png')
        if not path.exists(): raise FileNotFoundError(path)
        im=Image.open(path).convert('RGBA')
        native=im.copy()
        if name in ('env_pocket','flap_outer','flap_inner'):
            im=normalize_paper(im,name,size)
        else: im=im.resize(size,Image.Resampling.LANCZOS)
        if name.startswith('bg_'): im=im.convert('RGB')
        if name=='env_back_inner': im=im.convert('RGB')
        if name=='glow_trails':
            arr=np.array(im)
            # Glow does not need 256 noisy opacity levels. Quantize only alpha
            # to compress the overlay while preserving its high-res RGB detail.
            alpha=arr[:,:,3].astype(np.int16)
            arr[:,:,3]=np.clip(np.round(alpha/16)*16,0,255).astype(np.uint8)
            im=Image.fromarray(arr)
        im.save(ROOT/'assets'/(name+'.png'))
        quality=60 if name=='glow_trails' else (78 if name.startswith('bg_') else 82)
        if name=='bg_clean':
            # Retain the generator's native pixels for the web background;
            # resizing to a nominal 2x canvas cannot invent native detail.
            native.convert('RGB').save(OUT/(name+'.webp'),quality=95,method=6)
        else: im.save(OUT/(name+'.webp'),quality=quality,method=6)
    if (SOURCE/'envelope_master.png').exists():
        subprocess.run([sys.executable,str(ROOT/'tools/split_envelope.py')],check=True)
    for path in OUT.glob('*.webp'):shutil.copy2(path,ROOT/'assets'/path.name)
    sizes={p.name:p.stat().st_size for p in OUT.glob('*.webp')}
    common=sum(v for k,v in sizes.items() if not k.startswith('bg_'))
    budget={'desktop':common+sizes['bg_clean.webp'],'mobile':common+sizes['bg_clean_mobile.webp'],'files':sizes}
    (ROOT/'qa').mkdir(exist_ok=True)
    (ROOT/'qa'/'asset-budget.json').write_text(json.dumps(budget,indent=2))
    print(json.dumps(budget))
    layers=[n for n in SIZES if not n.startswith('bg_')]
    sheet=Image.new('RGB',(840,180*len(layers)))
    for row,name in enumerate(layers):
        im=Image.open(ROOT/'assets'/(name+'.png')).convert('RGBA')
        im.thumbnail((400,148))
        for col,color in enumerate(('black','white')):
            tile=Image.new('RGBA',(420,180),color)
            tile.alpha_composite(im,((420-im.width)//2,25))
            ImageDraw.Draw(tile).text((8,5),name,fill='gray')
            sheet.paste(tile.convert('RGB'),(col*420,row*180))
    sheet.save(ROOT/'qa'/'alpha_edges.png')
    assert budget['desktop']<=1_200_000,budget
    assert budget['mobile']<=600_000,budget

if __name__=='__main__':main()
