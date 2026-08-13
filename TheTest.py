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

# 🕹️ [Player 클래스 인스턴스 생성]
p_w = IML.Player.get_width()
p_h = IML.Player.get_height()
my_player = Player(0, 0, (p_w, p_h),IML)
my_player.image = IML.Player

send_data = {
    "posX": 0, 
    "posY": 0, 
    "angle": 0.0,
    "head_rect":[0,0,0,0],
    "body_rect":[0,0,0,0],
    "hp": 100
    
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
    global running, ScreenState, CameraPosX, CameraPosY, Weapon_Angle, Weapon_Pos, screen_shake, server_players, bullets
    global my_player, vision_radius

    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                new_bullet = Bullet(30)
                p_center_scr_x = (my_player.X - CameraPosX) + (IML.Player.get_width() // 2)
                p_center_scr_y = (my_player.Y - CameraPosY) + (IML.Player.get_height() // 2)
                
                gun_rad = math.radians(Weapon_Angle)
                gun_length = 40 
                muzzle_x = p_center_scr_x + (math.cos(gun_rad) * gun_length)
                muzzle_y = p_center_scr_y + (math.sin(gun_rad) * gun_length)

                new_bullet.launch(muzzle_x, muzzle_y, Weapon_Pos[0], Weapon_Pos[1])
                bullets.append(new_bullet)
                screen_shake = 15
               
    Weapon_Pos = pygame.mouse.get_pos()
    
    # 키 입력 처리
    key = pygame.key.get_pressed()
    dx, dy = 0, 0

    my_player.handle_input()
    # 서버 데이터 동기화
    send_data["posX"] = my_player.X
    send_data["posY"] = my_player.Y
    send_data["angle"] = Weapon_Angle 
    send_data["head_rect"] = [my_player.head_hitbox.x, my_player.head_hitbox.y, my_player.head_hitbox.width, my_player.head_hitbox.height]
    send_data["body_rect"] = [my_player.body_hitbox.x, my_player.body_hitbox.y, my_player.body_hitbox.width, my_player.body_hitbox.height]
    send_data["hp"] = my_player.Hp

    try:
        client.send(pickle.dumps(send_data))
        server_raw = client.recv(4096)
        if server_raw:
            server_players = pickle.loads(server_raw)
    except Exception as e:
        print(f"네트워크 통신 오류: {e}")

    # 카메라 이동
    player_center_x = my_player.X + (IML.Player.get_width() // 2)
    player_center_y = my_player.Y + (IML.Player.get_height() // 2)
    target_camera_x = player_center_x - (ScreenX // 2)
    target_camera_y = player_center_y - (ScreenY // 2)
    CameraPosX += (target_camera_x - CameraPosX) * lerp
    CameraPosY += (target_camera_y - CameraPosY) * lerp

    if screen_shake > 0:
        CameraPosX += random.randint(-screen_shake, screen_shake)
        CameraPosY += random.randint(-screen_shake, screen_shake)
        screen_shake -= 1

    player_screen_x = my_player.X - CameraPosX
    player_screen_y = my_player.Y - CameraPosY
    player_center_screen_x = player_screen_x + (IML.Player.get_width() // 2)
    player_center_screen_y = player_screen_y + (IML.Player.get_height() // 2)

    Weapon_Angle = Tool.GetAtn2Angle_Degrees((player_center_screen_x, player_center_screen_y), Weapon_Pos)
    rotated_shotgun = pygame.transform.rotate(IML.ShotGun[0], -Weapon_Angle)
    Shotgun_rect = rotated_shotgun.get_rect()
    Shotgun_rect.center = (player_center_screen_x, player_center_screen_y)

    # ------------------ [게임 월드 그리기] ------------------
    display.fill((0, 0, 200))
    TileGene.draw(display, CameraPosX, CameraPosY)

    player_world_x = my_player.X + (IML.Player.get_width() // 2)
    player_world_y = my_player.Y + (IML.Player.get_height() // 2)

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

        other_world_x = p_info["posX"] + (IML.Player.get_width() // 2)
        other_world_y = p_info["posY"] + (IML.Player.get_height() // 2)
        if not TileGene.is_point_visible_from(player_world_x, player_world_y, other_world_x, other_world_y, vision_radius):
            continue

        other_screen_x = p_info["posX"] - CameraPosX
        other_screen_y = p_info["posY"] - CameraPosY
        display.blit(IML.Player, (other_screen_x, other_screen_y))

        other_center_x = other_screen_x + (IML.Player.get_width() // 2)
        other_center_y = other_screen_y + (IML.Player.get_height() // 2)
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
