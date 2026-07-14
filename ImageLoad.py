import os
import pygame


class Imageload():
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.player_path = os.path.join(current_dir, "Image", "PlayerPng.png")
        self.backGround = os.path.join(current_dir,"Image","Back")
        self.Player = pygame.image.load(self.player_path).convert_alpha()
        pass

    def Load():
      
        
        # 2. 그 폴더를 기준으로 이미지 파일의 정확한 경로를 결합합니다.
        
        # 3. 이미지를 로드합니다.
        
        return Player