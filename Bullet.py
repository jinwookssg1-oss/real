import pygame
import math

class Bullet:
    def __init__(self, size=1):
        # 🌟 1. 총알 전용 독립된 작은 도화지(Surface)를 생성합니다.
        # SRCALPHA를 넣어야 총알 주변 배경이 투명해집니다.
        self.surface = pygame.Surface((size, size), pygame.SRCALPHA)

        
        # 🌟 2. 자기 자신(Surface)의 중심에 흰색 원을 그립니다.
        self.bullet = pygame.draw.circle(self.surface, pygame.Color("Yellow"), (size // 2, size // 2), size // 2)
        
        # 좌표 및 속도 초기화
        self.x = 0
        self.y = 0
        self.speed_x = 0
        self.speed_y = 0
        
        # 현재 이 총알이 화면에서 움직이고 있는 상태인가?
        self.is_active = False

    def launch(self, start_x, start_y, target_x, target_y, speed=15):
        # 발사 위치 설정 (보통 플레이어의 화면 중심 좌표)
        self.x = start_x
        self.y = start_y
        
        # 🌟 3. 목표물과의 거리 차이(dx, dy) 계산
        dx = target_x - start_x
        dy = target_y - start_y
        
        # 🌟 4. atan2를 이용해 목표물까지의 정확한 각도(라디안) 계산
        angle_rad = math.atan2(dy, dx)
        
        # 🌟 5. 삼각함수를 이용해 매 프레임 이동할 X축, Y축 속도 분할 분배
        self.speed_x = math.cos(angle_rad) * speed
        self.speed_y = math.sin(angle_rad) * speed
        
        # 총알 활성화
        self.is_active = True

    def update(self):
        # 활성화 상태일 때만 매 프레임 위치 이동
        if self.is_active:
            self.x += self.speed_x
            self.y += self.speed_y
            
            # 🌟 안전장치: 화면 밖으로 멀리 벗어나면 총알을 비활성화 (메모리 아끼기)
            if self.x < -100 or self.x > 2000 or self.y < -100 or self.y > 2000:
                self.is_active = False
            
            

    def draw(self, display):
        # 활성화 상태일 때만 메인 화면(display)에 총알 그리기
        if self.is_active:
            display.blit(self.surface, (int(self.x), int(self.y)))