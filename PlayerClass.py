import pygame
from Config import *
from ImageLoad import *

class Player:
    def __init__(self, x, y, size, IML: Imageload):
        self.image = IML.GetPlayer()
        self.X = x
        self.Y = y
        self.size = size
       
        self.Hp = 100
        self.MaxHp = 100
        self.rect = self.image.get_rect(topleft=(x, y))

        self.normal_speed = 5
        self.dash_speed = 15      # 대쉬 중일 때의 속도
        
        # --- 대쉬 관련 변수 세팅 ---
        self.dash_duration = 200   # 대쉬 지속 시간: 0.2초 (200밀리초)
        self.dash_cooldown = 1500  # 대쉬 쿨타임: 1.5초 (1500밀리초)
        
        self.last_dash_time = -1500 # 게임 시작하자마자 바로 대쉬할 수 있게 설정
        self.is_dashing = False    # 현재 대쉬 중인지 상태를 저장
        self.dash_end_time = 0     # 대쉬가 끝나는 시각을 기록할 변수

        # 대쉬 방향을 기억할 변수
        self.dash_dir_x = 0
        self.dash_dir_y = 0

        # 히트박스 최초 설정
        p_width = self.rect.width
        p_height = self.rect.height
        self.head_hitbox = pygame.Rect(x + (p_width // 4), y, p_width // 2, p_height // 3)
        self.body_hitbox = pygame.Rect(x, y + (p_height // 3), p_width, (p_height // 3) * 2)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()

        # 1. 일반적인 이동 방향 계산 (방향키 입력)
        dx = 0
        dy = 0
        if keys[pygame.K_a]:  dx = -1
        if keys[pygame.K_d]:  dx = 1
        if keys[pygame.K_w]:  dy = -1
        if keys[pygame.K_s]:  dy = 1

        # 2. 대쉬 키(LSHIFT) 입력 확인 및 대쉬 시작 조건
        if keys[pygame.K_LSHIFT] and not self.is_dashing:
            # 쿨타임이 지났고, 멈춰있지 않고 움직이는 중일 때만 대쉬 발동
            if current_time - self.last_dash_time >= self.dash_cooldown and (dx != 0 or dy != 0):
                self.is_dashing = True
                self.last_dash_time = current_time
                self.dash_end_time = current_time + self.dash_duration # 0.2초 뒤 종료 예약
                
                # 대쉬를 시작한 시점의 이동 방향을 고정 (대쉬 중 방향 전환 방지)
                self.dash_dir_x = dx
                self.dash_dir_y = dy
                print("대쉬 시작!")

        # 3. 속도 결정 및 대쉬 종료 체크
        if self.is_dashing:
            if current_time > self.dash_end_time:
                self.is_dashing = False # 0.2초가 지나면 대쉬 강제 종료
                print("대쉬 종료, 일반 속도로 전환")
                speed = self.normal_speed
            else:
                speed = self.dash_speed # 0.2초 안에는 대쉬 속도 유지
                # 대쉬 중에는 처음에 고정된 방향으로만 이동
                dx = self.dash_dir_x
                dy = self.dash_dir_y
        else:
            speed = self.normal_speed

        # 4. [수정 포인트] 계산된 최종 이동량(방향 * 속도)을 Move 함수로 전달!
        final_dx = dx * speed
        final_dy = dy * speed
        
        if final_dx != 0 or final_dy != 0:
            self.Move(final_dx, final_dy)

    def Move(self, dx, dy):
        # 내부 좌표 갱신
        self.X += dx
        self.Y += dy
        
        # 이미지 rect 이동
        self.rect.x += dx
        self.rect.y += dy
        
        # 두 히트박스 동시 이동 (이제 대쉬 속도에 맞춰 완벽하게 따라옵니다)
        self.head_hitbox.x += dx
        self.head_hitbox.y += dy
        
        self.body_hitbox.x += dx
        self.body_hitbox.y += dy

    def draw(self, surface, camera_x=0, camera_y=0):
        # 카메라 위치를 차감하여 화면용 상대 좌표 계산
        screen_x = self.rect.x - camera_x
        screen_y = self.rect.y - camera_y
        
        # 화면 좌표 기준 캐릭터 렌더링
        surface.blit(self.image, (screen_x, screen_y))
        
        # 시각적 확인용 화면 렌더링용 Rect 계산
        render_head = pygame.Rect(self.head_hitbox.x - camera_x, self.head_hitbox.y - camera_y, self.head_hitbox.width, self.head_hitbox.height)
        render_body = pygame.Rect(self.body_hitbox.x - camera_x, self.body_hitbox.y - camera_y, self.body_hitbox.width, self.body_hitbox.height)
        
        # 화면에 히트박스 테두리 그리기 (머리: 노랑, 몸통: 초록)
        pygame.draw.rect(surface, (255, 255, 0), render_head, 2)
        pygame.draw.rect(surface, (0, 255, 0), render_body, 2)
