import pygame
from Config import *
from ImageLoad import *
import sys
import math
from TileGenerator import *
fps = 64


pygame.init()
pygame.display.set_caption("전설적인 게임")
displaysurf = pygame.display.set_mode((ScreenX, ScreenY), 0, 32)
clock = pygame.time.Clock()

GuiFont = pygame.font.SysFont("malgungothic",40)

Text = GuiFont.render("비둘기",1,(255,255,255))
#Text.get_rect().center = (ScreenX / 2 , ScreenY / 2)


#움직임
posX = 0
posY = 0


CameraPosX = 0
CameraPosY = 0

lerp = 0.05

target_camera_x = posX - (ScreenX // 2)
target_camera_y = posY - (ScreenY // 2)


IML = Imageload()

TileGene = TileGenerator()





# (초기화 및 변수 선언 부분 생략)

while True: # 아래의 코드를 무한 반복한다.

    # 1. 시스템 이벤트 처리 (창 닫기 버튼용)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # 2. 연속 키 입력 처리 (for문 바깥에 둡니다)
    key = pygame.key.get_pressed()
    
    if key[pygame.K_ESCAPE]:  # ESC 키를 누르고 있으면 종료
        pygame.quit()
        sys.exit()
        
    if key[pygame.K_w]:       # W: 위로 이동
        posY -= PlayerSpd             # 💡 Pygame에서는 위로 갈수록 Y값이 줄어듭니다!
    if key[pygame.K_s]:       # S: 아래로 이동
        posY += PlayerSpd     # 💡 아래로 갈수록 Y값이 늘어납니다!
    if key[pygame.K_a]:       # A: 왼쪽으로 이동
        posX -= PlayerSpd
    if key[pygame.K_d]:       # D: 오른쪽으로 이동
        posX += PlayerSpd

    player_center_x = posX + (IML.Player.get_width() // 2)
    player_center_y = posY + (IML.Player.get_height() // 2)
    
    target_camera_x = player_center_x - (ScreenX // 2)
    target_camera_y = player_center_y - (ScreenY // 2)

    # 3. Lerp 카메라 부드러운 이동 적용
    CameraPosX += (target_camera_x - CameraPosX) * lerp
    CameraPosY += (target_camera_y - CameraPosY) * lerp

    # 4. 플레이어의 화면 상대 좌표 계산
    player_screen_x = posX - CameraPosX
    player_screen_y = posY - CameraPosY
    
    # 5. 화면 그리기 (렌더링 순서 주의: 배경 -> 캐릭터)
    displaysurf.fill((0, 0, 0)) 
  
    # 타일 맵 그리기
    TileGene.draw(displaysurf, CameraPosX, CameraPosY)
    displaysurf.blit(IML.Player, (player_screen_x,player_screen_y))

    
    # 4. 화면 업데이트 (flip과 update는 둘 중 하나만 쓰셔도 됩니다)
    pygame.display.update() 
    clock.tick(fps)

pygame.quit()