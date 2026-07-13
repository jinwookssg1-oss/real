import pygame
from Config import *
from ImageLoad import *
import sys
fps = 64


pygame.init()
pygame.display.set_caption("전설적인 게임")
displaysurf = pygame.display.set_mode((ScreenX, ScreenY), 0, 32)
clock = pygame.time.Clock()

GuiFont = pygame.font.SysFont("malgungothic",40)

Text = GuiFont.render("비둘기",1,(255,255,255))
Text.get_rect().center = (ScreenX / 2 , ScreenY / 2)

posX = 0
posY = 0

IML = Load()

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
        posY -= 1             # 💡 Pygame에서는 위로 갈수록 Y값이 줄어듭니다!
    if key[pygame.K_s]:       # S: 아래로 이동
        posY += 1             # 💡 아래로 갈수록 Y값이 늘어납니다!
    if key[pygame.K_a]:       # A: 왼쪽으로 이동
        posX -= 1
    if key[pygame.K_d]:       # D: 오른쪽으로 이동
        posX += 1

    # 3. 화면 그리기 (잔상이 남지 않도록 먼저 화면을 지워주는 것이 좋습니다)
    displaysurf.fill((0, 0, 0)) # 예: 검은색 바탕으로 화면 청소 (생략 가능)
    
    displaysurf.blit(IML, (posX, posY))
    displaysurf.blit(Text, Text.get_rect().center)
    
    # 4. 화면 업데이트 (flip과 update는 둘 중 하나만 쓰셔도 됩니다)
    pygame.display.update() 
    clock.tick(fps)
