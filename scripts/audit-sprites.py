"""Generate labeled contact sheets of the actual catalog frames for visual review."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import pygame
from boxhead.core.catalog import catalog

pygame.init();pygame.display.set_mode((1,1))
cat=catalog();out=Path('build/sprite-audit');out.mkdir(parents=True,exist_ok=True)
font=pygame.font.Font(None,20)
keys=list(cat._entries)
for page in range((len(keys)+7)//8):
    canvas=pygame.Surface((1160,8*118));canvas.fill((28,32,42))
    for row,key in enumerate(keys[page*8:page*8+8]):
        sheet=cat.sheet(key);frames=sheet.animation().frames
        canvas.blit(font.render(key,True,(235,235,235)),(8,row*118+5))
        indices=list(range(min(5,len(frames))))
        if len(frames)>5:indices+=list(range(max(5,len(frames)-4),len(frames)))
        for col,index in enumerate(indices):
            f=frames[index];box=pygame.Rect(8+col*126,row*118+28,112,84)
            pygame.draw.rect(canvas,(45,49,58),box)
            pygame.draw.line(canvas,(70,74,85),box.midtop,box.midbottom)
            pygame.draw.line(canvas,(70,74,85),box.midleft,box.midright)
            scale=min(100/f.get_width(),76/f.get_height())
            img=pygame.transform.scale(f,(round(f.get_width()*scale),round(f.get_height()*scale)))
            canvas.blit(img,img.get_rect(center=box.center))
            canvas.blit(font.render(str(index),True,(210,210,210)),(box.x+2,box.y+2))
    path=out/f'page-{page}.png';pygame.image.save(canvas,path);print(path)
pygame.quit()
