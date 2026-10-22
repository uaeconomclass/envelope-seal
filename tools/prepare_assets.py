"""Normalize generated layers to brief dimensions; encode delivery WebP assets."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'assets'
SIZES = {'bg_clean': (2560,1382), 'env_back_inner': (836,550),
         'env_pocket': (836,550), 'flap_outer': (836,306),
         'flap_inner': (836,306), 'seal': (224,224), 'stamp': (360,390),
         'letter': (700,400), 'bg_clean_mobile': (780,1400)}

def main():
    for name, size in SIZES.items():
        path = ASSETS / (name + '.png')
        if not path.exists():
            continue
        im = Image.open(path).convert('RGBA').resize(size, Image.Resampling.LANCZOS)
        if name in ('env_pocket', 'flap_outer', 'flap_inner'):
            # Use the specified hinge/vertex geometry, with antialiased alpha.
            w,h=size
            mask=Image.new('L',(w*4,h*4))
            points=([(0,0),(434,304),(836,0),(836,550),(0,550)]
                    if name=='env_pocket' else [(0,0),(836,0),(434,306)])
            ImageDraw.Draw(mask).polygon([(x*4,y*4) for x,y in points],fill=255)
            mask=mask.resize(size,Image.Resampling.LANCZOS)
            # Preserve generated alpha including its natural paper edge.
            im.putalpha(Image.fromarray(np.minimum(np.asarray(im.getchannel('A')),np.asarray(mask))))
        im.save(path)
        im.save(ASSETS/(name+'.webp'),quality=86,method=6)
    QA=ROOT/'qa'
    QA.mkdir(exist_ok=True)
    layers=[n for n in SIZES if n not in ('bg_clean','bg_clean_mobile') and (ASSETS/(n+'.png')).exists()]
    sheet=Image.new('RGB',(840,len(layers)*180),'#333333')
    for row,name in enumerate(layers):
        im=Image.open(ASSETS/(name+'.png')).convert('RGBA')
        im.thumbnail((390,150))
        for col,color in enumerate(('black','white')):
            tile=Image.new('RGBA',(420,180),color)
            tile.alpha_composite(im,((420-im.width)//2,20))
            ImageDraw.Draw(tile).text((8,3),name,fill='gray')
            sheet.paste(tile.convert('RGB'),(col*420,row*180))
    sheet.save(QA/'alpha_edges.png')
    common=sum((ASSETS/(n+'.webp')).stat().st_size for n in layers)
    for kind,name in [('desktop','bg_clean'),('mobile','bg_clean_mobile')]:
        path=ASSETS/(name+'.webp')
        if path.exists(): print(f'{kind} image bytes: {common+path.stat().st_size}')

if __name__=='__main__': main()
