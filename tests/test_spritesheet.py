import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
import pygame
from boxhead.core.spritesheet import cut_grid
from boxhead.core.catalog import SpriteCatalog


class SpriteCropTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1,1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_explicit_crop_excludes_neighbor(self):
        image=pygame.Surface((40,20),pygame.SRCALPHA)
        image.fill((255,0,0,255),(0,0,10,10))
        image.fill((0,255,0,255),(12,0,10,10))
        frame=cut_grid(image,(20,20),rows=1,columns=1,source_rects=[[0,0,10,10]])[0][0]
        self.assertEqual(frame.get_bounding_rect(),pygame.Rect(5,5,10,10))
        self.assertEqual(frame.get_at((10,10)),(255,0,0,255))

    def test_trim_aligns_feet_without_enlarging_small_frames(self):
        image=pygame.Surface((64,32),pygame.SRCALPHA)
        image.fill((255,255,255,255),(2,1,8,12))
        image.fill((255,255,255,255),(50,12,8,12))
        frames=cut_grid(image,(32,32),rows=1,columns=2,trim=True,anchor='bottom',padding=4)[0]
        self.assertEqual(frames[0].get_bounding_rect(),pygame.Rect(12,16,8,12))
        self.assertEqual(frames[0].get_bounding_rect(),frames[1].get_bounding_rect())

    def test_uniform_scale_keeps_relative_effect_sizes(self):
        image=pygame.Surface((40,20),pygame.SRCALPHA)
        image.fill((255,255,255,255))
        a,b=cut_grid(image,(16,16),rows=1,columns=2,
                     source_rects=[[0,0,20,20],[20,0,10,10]],uniform_scale=True,padding=2)[0]
        self.assertEqual(a.get_bounding_rect().size,(12,12))
        self.assertEqual(b.get_bounding_rect().size,(6,6))

    def test_cleanup_removes_declarative_region(self):
        image=pygame.Surface((20,20),pygame.SRCALPHA);image.fill((255,0,0,255))
        frame=cut_grid(image,(20,20),rows=1,columns=1,
                       frame_cleanup={'0':{'clear_rects':[[0,0,5,5]]}})[0][0]
        self.assertEqual(frame.get_at((2,2)).a,0)
        self.assertEqual(frame.get_at((10,10)).a,255)

    def test_whole_catalog_crops_and_character_anchors(self):
        cat=SpriteCatalog();cat.preload()
        for key,entry in cat._entries.items():
            sheet=cat.sheet(key)
            self.assertEqual(len(sheet.animation().frames),entry['frames'])
            if entry.get('trim') and entry.get('anchor')=='bottom':
                for f in sheet.animation().frames:
                    bounds=f.get_bounding_rect()
                    if bounds.width:
                        self.assertEqual(bounds.bottom,entry['frame_size'][1]-entry['padding'],key)
                        self.assertLessEqual(abs(bounds.centerx-f.get_width()//2),1,key)


if __name__=='__main__':unittest.main()
