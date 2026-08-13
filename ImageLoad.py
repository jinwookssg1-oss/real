import os
import pygame


class Imageload():
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.player_path = os.path.join(current_dir, "Image", "PlayerPng.png")
        self.backGround = os.path.join(current_dir,"Image","Back")

        self.ShotGun_Path = os.path.join(current_dir,"Image","ShotGun")
        self.ShotGun = []
        for a in range(1,8):
            self.ShotGun.append(pygame.image.load(self.ShotGun_Path + f"_{a}.png"))

        self.Tile = pygame.image.load(os.path.join(current_dir, "Image", "Tile.png")).convert_alpha()
        self.Tile = pygame.transform.scale(self.Tile,(64,64))
        self.Player = pygame.image.load(self.player_path).convert_alpha()
        
        pass
    def GetShotGun(self):
        return self.ShotGun
    def GetPlayer(self):
        return self.Player  
    def GetTileTest(self):
        return self.Tile
    