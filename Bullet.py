import pygame
import math
import time

class Bullet:
    def __init__(self, size=1, damage=10, owner_id=None, weapon_id="pistol"):
        # 🌟 1. 총알 전용 독립된 작은 도화지(Surface)를 생성합니다.
        # SRCALPHA를 넣어야 총알 주변 배경이 투명해집니다.
        self.surface = pygame.Surface((size, size), pygame.SRCALPHA)

        # 🌟 2. 자기 자신(Surface)의 중심에 흰색 원을 그립니다.
        self.bullet = pygame.draw.circle(self.surface, pygame.Color("Yellow"), (size // 2, size // 2), size)

        # 좌표 및 속도 초기화
        self.x = 0
        self.y = 0
        self.speed_x = 0
        self.speed_y = 0

        # 현재 이 총알이 화면에서 움직이고 있는 상태인가?
        self.is_active = False
        self.damage = damage
        self.owner_id = owner_id
        self.weapon_id = weapon_id
        self.angle = 0.0
        self.life_time = 2.5
        self.spawn_time = 0.0

    @property
    def rect(self):
        return pygame.Rect(round(self.x), round(self.y), self.surface.get_width(), self.surface.get_height())

    def launch(self, start_x, start_y, target_x, target_y, speed=15):
        # 발사 위치 설정 (보통 플레이어의 화면 중심 좌표)
        self.x = start_x
        self.y = start_y

        # 🌟 3. 목표물과의 거리 차이(dx, dy) 계산
        dx = target_x - start_x
        dy = target_y - start_y

        # 🌟 4. atan2를 이용해 목표물까지의 정확한 각도(라디안) 계산
        angle_rad = math.atan2(dy, dx)
        self.angle = math.degrees(angle_rad)

        # 🌟 5. 삼각함수를 이용해 매 프레임 이동할 X축, Y축 속도 분할 분배
        self.speed_x = math.cos(angle_rad) * speed
        self.speed_y = math.sin(angle_rad) * speed

        # 총알 활성화
        self.is_active = True
        self.spawn_time = time.monotonic()

    def update(self):
        # 활성화 상태일 때만 매 프레임 위치 이동
        if self.is_active:
            self.x += self.speed_x
            self.y += self.speed_y

            if time.monotonic() - self.spawn_time > self.life_time:
                self.is_active = False

            # 🌟 안전장치: 화면 밖으로 멀리 벗어나면 총알을 비활성화 (메모리 아끼기)
            if self.x < -100 or self.x > 2000 or self.y < -100 or self.y > 2000:
                self.is_active = False

    def draw(self, display, camera_x=0, camera_y=0, zoom=1.0, force_visible=False):
        # 활성화 상태일 때만 메인 화면(display)에 총알 그리기
        if self.is_active:
            if zoom == 1.0:
                display.blit(self.surface, (int(self.x - camera_x), int(self.y - camera_y)))
            else:
                size = max(1, round(self.surface.get_width() * zoom))
                image = pygame.transform.scale(self.surface, (size, size))
                display.blit(image, (round((self.x - camera_x) * zoom), round((self.y - camera_y) * zoom)))
            return

        # 총알은 시야 레이어에서 가려지지 않도록 최종 렌더 단계에서 강제로 다시 그린다.
        # 이 함수는 기존 호출 호환성을 위해 유지하며, force_visible=True가 들어오면
        # 시야 검사를 우회해 최종 레이어에 그린다.