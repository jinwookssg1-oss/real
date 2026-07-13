import os
import pygame

def Load():
    # 1. 현재 ImageLoad.py 파일이 있는 폴더의 절대 경로를 구합니다.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 그 폴더를 기준으로 이미지 파일의 정확한 경로를 결합합니다.
    player_path = os.path.join(current_dir, "Image", "PlayerPng.png")
    
    # 3. 이미지를 로드합니다.
    Player = pygame.image.load(player_path).convert_alpha()
    return Player