import pygame
from Config import *

fps = 64


pygame.init()
pygame.display.set_caption("전설적인 게임")
displaysurf = pygame.display.set_mode((ScreenX, ScreenY), 0, 32)
clock = pygame.time.Clock()

GuiFont = pygame.font.SysFont("malgungothic",40)

Text = GuiFont.render("비둘기",1,(255,255,255))
Text.get_rect().center = (ScreenX / 2 , ScreenY / 2)
while True: # 아래의 코드를 무한 반복한다.
    for event in pygame.event.get(): # 발생한 입력 event 목록의 event마다 검사
        if event.type == pygame.K_ESCAPE: # event의 type이 QUIT에 해당할 경우
            pygame.quit() # 창을 닫는다
    
    displaysurf.blit(Text,Text.get_rect().center)
    
    pygame.display.update() # 화면을 업데이트한다
    clock.tick(fps) # 화면 표시 회수 설정만큼 루프의 간격을 둔다    