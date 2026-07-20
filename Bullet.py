import pygame

class Bullet:
    def __init__(self,surface,size=5):
        self.surface = surface
        pygame.draw.circle(surface,(255,255,255),(size // 2, size // 2), size // 2)
        self.x = 0
        self.y = 0
        self.speed_x = 0
        self.speed_y = 0
        
        # ★ 핵심: 현재 이 총알이 화면에서 날아가고 있는 상태인가?
        self.is_active = False

    def launch(self,start_x,start_y,target_x,target_y,speed=12):
        self.x = start_x