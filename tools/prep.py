import cv2, numpy as np
src='reference.jpg'  # запускать из корня проекта
im=cv2.imread(src); H,W=im.shape[:2]
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
def feather(m,k): return cv2.GaussianBlur(m,(k,k),0).astype(np.float32)/255
# stamp: shapes ∩ not-blue
S=np.zeros((H,W),np.uint8)
cv2.ellipse(S,(840,55),(40,44),0,0,360,255,-1)
cv2.line(S,(828,85),(782,132),255,30)
cv2.ellipse(S,(778,135),(26,22),35,0,360,255,-1)
cv2.ellipse(S,(752,162),(40,33),35,0,360,255,-1)
blue=(hsv[...,0]>95)&(hsv[...,0]<135)&(hsv[...,1]>60)
dark=hsv[...,2]<35
M=S.copy(); M[(blue|dark)&(np.arange(H)[:,None]<150)]=0
M=cv2.morphologyEx(M,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(M); k=1+np.argmax(st[1:,4]); M=np.where(lab==k,255,0).astype(np.uint8)
x0,y0,x1,y1=705,5,885,200
stamp=cv2.cvtColor(im,cv2.COLOR_BGR2BGRA); stamp[...,3]=cv2.GaussianBlur(M,(3,3),0)
cv2.imwrite('stamp.png',stamp[y0:y1,x0:x1])
# seal
SC=(642,300); SR=52
sm=np.zeros((H,W),np.uint8); cv2.circle(sm,SC,SR,255,-1)
seal=cv2.cvtColor(im,cv2.COLOR_BGR2BGRA); seal[...,3]=cv2.GaussianBlur(sm,(5,5),0)
cv2.imwrite('seal.png',seal[SC[1]-SR-4:SC[1]+SR+4,SC[0]-SR-4:SC[0]+SR+4])
# envelope: stamp corner <- mirrored left side, seal <- inpaint
ex0,ey0,ex1,ey1=425,148,843,423
mir=im.copy(); cx=ex0+ex1
xs=np.arange(W); src_x=np.clip(cx-xs,0,W-1); mir=im[:,src_x]
cm=cv2.dilate(M,np.ones((15,15),np.uint8)); cm[:ey0-2]=0
f=feather(cm,21)[...,None]
env=(im*(1-f)+mir*f).astype(np.uint8)
env=cv2.inpaint(env,cv2.dilate(sm,np.ones((7,7),np.uint8)),7,cv2.INPAINT_TELEA)
cv2.imwrite('env.png',env[ey0:ey1,ex0:ex1])
# bg: stamp area <- sky shifted left, envelope rect <- inpaint
sh=np.roll(im,170,axis=1)
bm=cv2.dilate(M,np.ones((35,35),np.uint8)); f=feather(bm,41)[...,None]
bg=(im*(1-f)+sh*f).astype(np.uint8)
er=np.zeros((H,W),np.uint8); er[ey0-3:ey1+3,ex0-3:ex1+3]=255
bg=cv2.inpaint(bg,er,15,cv2.INPAINT_TELEA)
cv2.imwrite('bg.jpg',bg,[cv2.IMWRITE_JPEG_QUALITY,88])
cv2.imwrite('dbg_bg.png',bg[0:440,380:900]); cv2.imwrite('dbg_env.png',env[140:430,420:850])
