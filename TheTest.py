import pygame
from Config import *
from ImageLoad import *
import math
from TileGenerator import *
from Bullet import *
import Tool
import random
import socket
import pickle
from PlayerClass import Player
from Tool_Cordinate import *
from SkillAndSlot import *
fps = 64

pygame.init()
pygame.display.set_caption("전설적인 게임")
display = pygame.display.set_mode((ScreenX, ScreenY), 0, 32)
clock = pygame.time.Clock()
ScreenState = "MainView"
GuiFont = pygame.font.SysFont("malgungothic", 30)




# --- [네트워크 초기화] ---
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
client.connect((ServerIp, ServerPort))

init_data = pickle.loads(client.recv(1024))
my_id = init_data["init_id"]
print(f"내 아이디:{my_id}번 입니다.")


map = random.seed(init_data["seed"])  # 시드 고정
IML = Imageload()
TileGene = TileGenerator()
TileGene.generate_map(50, 50, seed_value=init_data["seed"])  # 서버에서 받은 시드로 맵 생성

# 🕹️ [Player 클래스 인스턴스 생성 - 랜덤 스폰]
p_w = IML.Player.get_width()
p_h = IML.Player.get_height()

# 플레이어 랜덤 스폰 위치 (타일 좌표 기반, 10~40 범위에서 랜덤)
spawn_tile_x = random.randint(10, 40)
spawn_tile_y = random.randint(10, 40)
spawn_world_x = spawn_tile_x * TileGene.tile_size
spawn_world_y = spawn_tile_y * TileGene.tile_size

my_player = Player(spawn_world_x, spawn_world_y, (p_w, p_h), IML, TileGene)
my_player.image = IML.Player
print(f"🎮 플레이어가 ({spawn_tile_x}, {spawn_tile_y}) 타일에 스폰되었습니다.")

# 보내는 데이터 - 멀티플레이 동기화용
# ★ [정리] 필요한 움직임 데이터만 포함
send_data = {
    # 플레이어 정보
    "posX": 0,          # 플레이어 X 좌표
    "posY": 0,          # 플레이어 Y 좌표
    "hp": 100,          # 플레이어 체력
    
    # 무기 정보
    "angle": 0.0,       # 무기(총) 각도
    
    # 발사한 총알 정보 (여러 개 가능)
    "bullets": [],      # [{"x": x, "y": y, "angle": angle}, ...]
}

CameraPosX = 0
CameraPosY = 0
lerp = 0.05

Weapon_Angle = 0
Weapon_Pos = (0, 0)

running = True
bullets = []
screen_shake = 0
server_players = {}

# 👁️ 시야 범위 반지름
vision_radius = 450

skill_window_open = False

def draw_ui_gauge(surface, x, y, width, height, current_val, max_val, fill_color):
    ratio = max(0, min(current_val, max_val)) / max_val
    fill_width = int(width * ratio)
    bg_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (40, 40, 40), bg_rect)
    if fill_width > 0:
        fill_rect = pygame.Rect(x, y, fill_width, height)
        pygame.draw.rect(surface, fill_color, fill_rect)
    pygame.draw.rect(surface, (255, 255, 255), bg_rect, 2)


def MainView():
    global running, ScreenState
    gf = GuiFont.render("안녕하살법 전설적인 테스트", 1, color=pygame.Color("White"))
    display.blit(gf, (20, 20))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                ScreenState = "GameView"


def GameView():
        # (기존 글로벌 변수에 UI 관련 변수 추가)
    global running, ScreenState, CameraPosX, CameraPosY, Weapon_Angle, Weapon_Pos, screen_shake, server_players, bullets
    global my_player, vision_radius
    global MousePos
    # --- [추가] UI 제어용 글로벌 변수 ---
    global skill_window, quick_slots, dragging_skill, system_message
    global skill_window_open

    MousePos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                
            elif event.key == pygame.K_k:
                skill_window_open = not skill_window_open
                dragging_skill = None

        # 스킬 단축키
            else:
                key_pressed = pygame.key.name(event.key).upper()

                for slot in quick_slots:
                  if slot.key_name == key_pressed:

                       if slot.assigned_skill:
                           system_message = SKILL_BOOK[slot.assigned_skill].Atk()
                       else:
                            system_message = f"💨 [{slot.key_name}] 슬롯이 비어있습니다."
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                # --- [추가] 마우스 좌클릭 시 UI 드래그 시작 체크 ---
                hit_ui = False
                
                # 스킬 창이 열려있을 때만 드래그 시작 가능
                if skill_window_open:
                    for item in skill_window:
                        if item.rect.collidepoint(MousePos):
                            dragging_skill = item.skill_name
                            hit_ui = True
                            break
                
                # UI를 클릭한 게 아니라면 원래대로 총알 발사
                if not hit_ui:
                    new_bullet = Bullet(30)
                    p_center_scr_x, p_center_scr_y = get_player_screen_center(
                        my_player.X, my_player.Y, IML.Player.get_width(), IML.Player.get_height(), CameraPosX, CameraPosY
                    )
                    
                    gun_rad = math.radians(Weapon_Angle)
                    gun_length = 40 
                    muzzle_x = p_center_scr_x + (math.cos(gun_rad) * gun_length)
                    muzzle_y = p_center_scr_y + (math.sin(gun_rad) * gun_length)

                    new_bullet.launch(muzzle_x, muzzle_y, Weapon_Pos[0], Weapon_Pos[1])
                    new_bullet.just_fired = True  # ★ [추가] 새로 발사된 총알 마크
                    bullets.append(new_bullet)
                    screen_shake = 15

        # --- [추가] 마우스 좌클릭을 뗐을 때 슬롯에 장착 처리 ---
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and dragging_skill:
                for slot in quick_slots:
                    if slot.rect.collidepoint(MousePos):
                        slot.assigned_skill = dragging_skill
                        system_message = f"⌨️ [{slot.key_name}] 슬롯에 [{SKILL_BOOK[dragging_skill].name}] 장착! (공격력: {SKILL_BOOK[dragging_skill].Power})"
                        break
                dragging_skill = None # 드래그 종료
               
    Weapon_Pos = pygame.mouse.get_pos()
    
    # 키 입력 처리
    key = pygame.key.get_pressed()
    dx, dy = 0, 0

    my_player.handle_input()
    
    # ★ [정리] 서버 데이터 동기화 - 필요한 움직임 데이터만 전송
    send_data["posX"] = my_player.X
    send_data["posY"] = my_player.Y
    send_data["hp"] = my_player.Hp
    send_data["angle"] = Weapon_Angle
    
    # ★ [정리] 총알 정보 - 이번 프레임에서 새로 발사된 총알만 전송
    send_data["bullets"] = [
        {"x": bullet.x, "y": bullet.y, "angle": Weapon_Angle}
        for bullet in bullets
        if hasattr(bullet, 'just_fired') and bullet.just_fired
    ]
    # 이미 전송된 총알 마크 해제
    for bullet in bullets:
        if hasattr(bullet, 'just_fired'):
            bullet.just_fired = False

    try:
        client.send(pickle.dumps(send_data))
        server_raw = client.recv(4096)
        if server_raw:
            server_players = pickle.loads(server_raw)
            # ★ [정리] 서버에서 받은 플레이어 데이터 구조:
            # server_players[id] = {
            #     "posX": x,          # 상대 플레이어 위치
            #     "posY": y,
            #     "angle": angle,     # 상대 플레이어 무기 각도
            #     "hp": hp,           # 상대 플레이어 체력
            #     "bullets": [...]    # 상대가 발사한 총알들
            # }
    except Exception as e:
        print(f"네트워크 통신 오류: {e}")

    # 카메라 이동
    player_center_x, player_center_y = get_player_world_center(my_player.X, my_player.Y, IML.Player.get_width(), IML.Player.get_height())
    target_camera_x, target_camera_y = get_camera_target(player_center_x, player_center_y, ScreenX, ScreenY)
    CameraPosX += (target_camera_x - CameraPosX) * lerp
    CameraPosY += (target_camera_y - CameraPosY) * lerp

    if screen_shake > 0:
        CameraPosX += random.randint(-screen_shake, screen_shake)
        CameraPosY += random.randint(-screen_shake, screen_shake)
        screen_shake -= 1

    player_screen_x, player_screen_y = world_to_screen(my_player.X, my_player.Y, CameraPosX, CameraPosY)
    player_center_screen_x, player_center_screen_y = get_player_screen_center(my_player.X, my_player.Y, IML.Player.get_width(), IML.Player.get_height(), CameraPosX, CameraPosY)

    Weapon_Angle = Tool.GetAtn2Angle_Degrees((player_center_screen_x, player_center_screen_y), Weapon_Pos)
    rotated_shotgun = pygame.transform.rotate(IML.ShotGun[0], -Weapon_Angle)
    Shotgun_rect = rotated_shotgun.get_rect()
    Shotgun_rect.center = (player_center_screen_x, player_center_screen_y)

    # ------------------ [게임 월드 그리기] ------------------
    display.fill((0, 0, 200))
    TileGene.draw(display, CameraPosX, CameraPosY)

    player_world_x, player_world_y = get_player_world_center(my_player.X, my_player.Y, IML.Player.get_width(), IML.Player.get_height())

    for bullet in bullets:
        bullet.update()
        bullet_x = bullet.x
        bullet_y = bullet.y
        if TileGene.is_point_visible_from(player_world_x, player_world_y, bullet_x, bullet_y, vision_radius):
            bullet.draw(display)
    bullets = [b for b in bullets if b.is_active]

    # 다른 플레이어 그리기
    for p_id, p_info in server_players.items():
        if int(p_id) == my_id:
            continue

        other_world_x, other_world_y = get_player_world_center(p_info["posX"], p_info["posY"], IML.Player.get_width(), IML.Player.get_height())
        if not TileGene.is_point_visible_from(player_world_x, player_world_y, other_world_x, other_world_y, vision_radius):
            continue

        other_screen_x, other_screen_y = world_to_screen(p_info["posX"], p_info["posY"], CameraPosX, CameraPosY)
        display.blit(IML.Player, (other_screen_x, other_screen_y))

        other_center_x, other_center_y = get_player_screen_center(p_info["posX"], p_info["posY"], IML.Player.get_width(), IML.Player.get_height(), CameraPosX, CameraPosY)
        other_rotated_gun = pygame.transform.rotate(IML.ShotGun[0], -p_info["angle"])
        other_gun_rect = other_rotated_gun.get_rect()
        other_gun_rect.center = (other_center_x, other_center_y)
        display.blit(other_rotated_gun, other_gun_rect)

    # 내 캐릭터 및 무기 그리기
    my_player.draw(display, CameraPosX, CameraPosY)
    display.blit(rotated_shotgun, Shotgun_rect)



    
    # 시야 바깥 영역을 검게 덮어서, 보이지 않는 영역은 아예 안 보이게 처리
    dark_overlay = pygame.Surface((ScreenX, ScreenY), pygame.SRCALPHA)
    dark_overlay.fill((0, 0, 0, 0))

    start_tile_x = max(0, int((CameraPosX // TileGene.tile_size) - 2))
    end_tile_x = int(((CameraPosX + ScreenX) // TileGene.tile_size) + 2)
    start_tile_y = max(0, int((CameraPosY // TileGene.tile_size) - 2))
    end_tile_y = int(((CameraPosY + ScreenY) // TileGene.tile_size) + 2)


    # 시야 범위 밖의 타일을 검게 덮기 / 타일 객체 순환하면서 시야밖에 있다면 검고 투명한 색으로 전환
    for tile_y in range(start_tile_y, end_tile_y):
        for tile_x in range(start_tile_x, end_tile_x):
            tile = TileGene.map_data.get((tile_x, tile_y))
            if not tile:
                continue

            world_x = tile_x * TileGene.tile_size
            world_y = tile_y * TileGene.tile_size
            screen_x = world_x - CameraPosX
            screen_y = world_y - CameraPosY

            if not TileGene.is_tile_visible_from(player_world_x, player_world_y, world_x, world_y, vision_radius):
                pygame.draw.rect(
                    dark_overlay,
                    (0, 0, 0, 200),
                    pygame.Rect(screen_x, screen_y, TileGene.tile_size, TileGene.tile_size)
                )

    display.blit(dark_overlay, (0, 0))
    
    
    # =================================================================
    # 📊 고정 UI 그리기 영역 (시야 레이어보다 위에 그려야 선명하게 보입니다)
    # =================================================================
    ui_x = 30
    ui_y = 80  
    ui_width = 250
    ui_height = 25
    
    draw_ui_gauge(display, ui_x, ui_y, ui_width, ui_height, my_player.Hp, my_player.MaxHp, (255, 50, 50))
    
    hp_text = GuiFont.render(f"HP: {my_player.Hp} / {my_player.MaxHp}", True, (255, 255, 255))
    display.blit(hp_text, (ui_x + ui_width + 15, ui_y - 8))

    id_text = GuiFont.render(f"ID: {my_id}", True, (255, 255, 255))
    display.blit(id_text, (20, 20))
    
    # --- [스킬 창 그리기 및 툴팁] ---
    hovered_skill = draw_skill_window(display, MousePos, skill_window_open, dragging_skill)
    
    # 스킬 도감 (스킬창 닫혀있을 때는 안 보임 - draw_skill_window에서 처리)
    # for item in skill_window:
    #     item.draw(display)

    # 하단 퀵슬롯 (�익슬롯은 항상 보임)
    for slot in quick_slots:
        slot.update(MousePos)  # 호버 상태 업데이트
        slot.draw(display)
    
    # ★ [추가] 스킬 툴팁 그리기 (마우스 raycast 무시 - 드래그 중이 아닐 때만)
    if skill_window_open and hovered_skill and dragging_skill is None:
        draw_skill_tooltip(display, MousePos, hovered_skill)

    # 시스템 메시지
    if system_message:
        message_text = GuiFont.render(system_message, True, (255, 255, 255))
        display.blit(message_text, (30, ScreenY - 40))
    
    # 스킬 창 상태 표시 (우측 상단)
    skill_status = "📖 스킬 창: [OPEN - K]" if skill_window_open else "📖 스킬 창: [닫음 - K]"
    status_text = GuiFont.render(skill_status, True, (100, 200, 255) if skill_window_open else (100, 100, 100))
    display.blit(status_text, (ScreenX - 300, 20))
    # ------------------ [그리기 끝] ------------------


while running: 
    display.fill((0,0,0))
    if ScreenState == "MainView":
        MainView()
    elif ScreenState == "GameView":
        GameView()
    pygame.display.update() 
    clock.tick(fps)

pygame.quit()
