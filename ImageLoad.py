import os
import pygame


class Imageload():
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.player_path = os.path.join(current_dir, "Image", "PlayerPng.png")
        self.backGround = os.path.join(current_dir, "Image", "Back")
        self.ShotGun_Path = os.path.join(current_dir, "Image", "ShotGun")
        
        # 1. 반복문 안에서 불러오기 -> 크기 조절 -> 최적화를 한 번에 처리
        self.ShotGun = []
        for a in range(1, 8):
            img = pygame.image.load(self.ShotGun_Path + f"_{a}.png").convert_alpha()
            img = pygame.transform.scale(img, (128, 64)) # ◀ 리스트에 넣기 전에 32x16으로 축소
            self.ShotGun.append(img)

        self.Tile = pygame.image.load(os.path.join(current_dir, "Image", "Tile.png")).convert_alpha()
        self.Tile = pygame.transform.scale(self.Tile, (64, 64))
        
        self.Player = pygame.image.load(self.player_path).convert_alpha()
        self.Player = pygame.transform.scale(self.Player, (64, 64))

        # HP 게이지 바깥 프레임 이미지
        self.HpBar = pygame.image.load(
            os.path.join(current_dir, "Image", "HpBar.png")
        ).convert_alpha()

    # 2. 이미 크기가 줄어든 상태이므로 원본을 바로 리턴하면 됩니다.
    def GetShotGun(self, index=0):
        # index 인자를 주면 ShotGun[0]뿐만 아니라 다른 프레임(1~7)도 가져올 수 있어 확장성에 좋습니다.
        return self.ShotGun[index]

    def GetPlayer(self):
        return self.Player  
    def GetTileTest(self):
        return self.Tile
    