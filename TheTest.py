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
from Weapon import WeaponState, WEAPONS, WEAPON_KEYS

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
set_ui_assets(IML.SkillWindow, IML.QuickSlot)
TileGene = TileGenerator()
# [커스텀 가능] 맵 가로/세로 타일 수입니다. 타일 크기와 곱해 전체 월드 크기가 결정됩니다.
TileGene.generate_map(200, 200, seed_value=init_data["seed"])

# [커스텀 가능] HP 프레임의 화면 표시 크기입니다. 원본 비율을 유지해 한 번만 축소합니다.
HP_FRAME_SIZE = (360, 120)
HpBarFrame = pygame.transform.smoothscale(IML.HpBar, HP_FRAME_SIZE)

# 🕹️ [Player 클래스 인스턴스 생성 - 랜덤 스폰]
p_w = IML.Player.get_width()
p_h = IML.Player.get_height()

# [커스텀 가능] 안전 스폰을 찾을 타일 좌표 범위입니다.
safe_spawn = TileGene.find_safe_spawn(40, 160, 40, 160)
spawn_tile_x, spawn_tile_y = safe_spawn or (100, 100)
spawn_world_x = spawn_tile_x * TileGene.tile_size
spawn_world_y = spawn_tile_y * TileGene.tile_size

my_player = Player(spawn_world_x, spawn_world_y, (p_w, p_h), IML, TileGene)
my_player.image = IML.Player
print(f"🎮 플레이어가 ({spawn_tile_x}, {spawn_tile_y}) 타일에 스폰되었습니다.")

# 보내는 데이터 - 멀티플레이 동기화용
# [커스텀 가능] 서버로 보낼 플레이어 동기화 데이터입니다.
send_data = {
    # 플레이어 정보
    "posX": 0,          # 플레이어 X 좌표
    "posY": 0,          # 플레이어 Y 좌표
    "hp": 100,          # 플레이어 체력
    
    # 무기 정보
    "angle": 0.0,       # 무기(총) 각도
    "weapon_id": "pistol",
    "magazine_ammo": 12,
    "reserve_ammo": 36,
    
    # 발사한 총알 정보 (여러 개 가능)
    "bullets": [],      # [{"x": x, "y": y, "angle": angle}, ...]
}

CameraPosX = 0
CameraPosY = 0
camera_fov = max(1.0, min(CAMERA_FOV, CAMERA_FOV_MAX))
camera_zoom = 1.0 / camera_fov
lerp = 0.05

Weapon_Angle = 0
Weapon_Pos = (0, 0)

running = True
bullets = []
remote_bullets = []
processed_bullet_events = set()
screen_shake = 0
server_players = {}

# [커스텀 가능] 시야 모양, 거리, 부채꼴 각도, 직사각형/선 폭을 조정합니다.
vision_radius = 450
vision_shapes = (VISION_CIRCLE, VISION_CONE, VISION_RECTANGLE, VISION_LINE)
vision_shape_index = 0
vision_fov_angle = 90
vision_width = 220

skill_window_open = False
weapon_state = WeaponState()
vision_shape_override = None

def draw_ui_gauge(surface, x, y, current_val, max_val):
    """투명 중앙이 뚫린 HP 프레임 안쪽에 HP 게이지를 그립니다."""
    
    frame_width, frame_height = HpBarFrame.get_size()
    ratio = max(0, min(current_val, max_val)) / max(1, max_val)

    # HpBar.png의 중앙 투명 영역 비율에 맞춘 내부 게이지 영역
    inner_x = int(frame_width * 0.11)
    inner_y = int(frame_height * 0.34)
    inner_width = int(frame_width * 0.78)
    inner_height = int(frame_height * 0.27)
    
    inner_rect = pygame.Rect(x + inner_x, y + inner_y, inner_width, inner_height)

    # 1. 배경 사각형 그리기 (피가 달았을 때 비어있는 공간을 나타낼 어두운 색)
    bg_color = pygame.Color("gray20")  # 어두운 회색 (또는 (40, 40, 40))
    pygame.draw.rect(surface, bg_color, inner_rect)

    # 2. 체력 비율에 따른 게이지 색상 결정 (인자 fill_color 대신 실시간 계산)
    if current_val >= 100:
        hp_color = pygame.Color("green")
    elif current_val <= 80:
        hp_color = pygame.Color("yellow")      # 체력이 80 이하로 떨어지면 빨간색
    else:
        hp_color = pygame.Color("red")   # 체력이 81~99 사이면 노란색
        
    # 3. 현재 체력만큼 게이지 채워 그리기
    fill_rect = inner_rect.copy()
    fill_rect.width = int(inner_rect.width * ratio)
    
    if fill_rect.width > 0:
        pygame.draw.rect(surface, hp_color, fill_rect)

    # 4. 중앙 게이지 위에 테두리 이미지를 올려 프레임이 게이지를 감쌉니다.
    surface.blit(HpBarFrame, (x, y))


def draw_ammo_status(surface):
    """현재 무기와 탄창/예비 탄약을 화면 오른쪽 아래에 표시합니다."""
    config = weapon_state.config
    ammo_font = pygame.font.SysFont("malgungothic", 24)
    name_text = ammo_font.render(config.name, True, (255, 220, 120))
    if weapon_state.is_reloading_now():
        ammo_text = ammo_font.render("재장전 중...", True, (255, 180, 120))
    else:
        ammo_text = ammo_font.render(weapon_state.ammo_text(), True, (255, 255, 255))
    surface.blit(name_text, (ScreenX - 210, ScreenY - 72))
    surface.blit(ammo_text, (ScreenX - 80, ScreenY - 72))



def MainView():
    global running, ScreenState
    gf = GuiFont.render("안녕하살법 전설적인 테스트", 1, pygame.Color("White"))
    display.blit(gf, (20, 20))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                ScreenState = "GameView"


def handle_quit(_event, _mouse_pos):
    global running
    running = False


def activate_quick_slot(key):
    global system_message
    key_name = pygame.key.name(key).upper()
    slot = next((slot for slot in quick_slots if slot.key_name == key_name), None)
    message = (
        SKILL_BOOK[slot.assigned_skill].Atk()
        if slot and slot.assigned_skill
        else f"💨 [{key_name}] 슬롯이 비어있습니다."
    )
    system_message = message


def select_weapon(weapon_id):
    global system_message, vision_shape_override
    if weapon_state.select(weapon_id):
        vision_shape_override = None
        system_message = f"무기 변경: {weapon_state.config.name}"


def reload_weapon():
    global system_message
    if weapon_state.is_reloading_now():
        system_message = "이미 재장전 중입니다."
        return
    if weapon_state.config.projectile and weapon_state.magazine_ammo >= weapon_state.config.magazine_size:
        system_message = "탄창이 이미 가득 찼습니다."
        return
    if weapon_state.config.projectile and weapon_state.reserve_ammo <= 0:
        system_message = "예비 탄약이 없습니다."
        return

    if weapon_state.start_reload():
        system_message = f"{weapon_state.config.name} 재장전 중..."
    else:
        system_message = "재장전할 탄환이 없습니다."


def handle_key_event(event, _mouse_pos):
    global skill_window_open, dragging_skill
    key_actions = {
        pygame.K_ESCAPE: lambda _key: handle_quit(None, None),
        pygame.K_k: lambda _key: toggle_skill_window(),
        pygame.K_v: lambda _key: cycle_vision_shape(),
        pygame.K_r: lambda _key: reload_weapon(),
        pygame.K_1: lambda _key: select_weapon("pistol"),
        pygame.K_2: lambda _key: select_weapon("rifle"),
        pygame.K_3: lambda _key: select_weapon("shotgun"),
        pygame.K_4: lambda _key: select_weapon("sniper"),
        pygame.K_5: lambda _key: select_weapon("smg"),
        pygame.K_6: lambda _key: select_weapon("knife"),
    }
    key_actions.get(event.key, activate_quick_slot)(event.key)


def toggle_skill_window():
    global skill_window_open, dragging_skill
    skill_window_open = not skill_window_open
    dragging_skill = None


def cycle_vision_shape():
    global vision_shape_index, vision_shape_override, system_message
    vision_shape_index = (vision_shape_index + 1) % len(vision_shapes)
    vision_shape_override = vision_shapes[vision_shape_index]
    shape_name = vision_shape_override
    system_message = f"시야 모양: {shape_name}"


def fire_bullet():
    global bullets, screen_shake, system_message
    config = weapon_state.config

    if weapon_state.is_reloading_now():
        system_message = "재장전 중입니다."
        return
    if not weapon_state.can_fire():
        if config.projectile and weapon_state.magazine_ammo == 0:
            reload_weapon()
        elif not config.projectile:
            system_message = f"{config.name} 공격은 아직 준비 중입니다. 데미지: {config.damage}"
        return

    center_x, center_y = get_player_world_center(
        my_player.X,
        my_player.Y,
        IML.Player.get_width(),
        IML.Player.get_height(),
    )
    current_mouse_pos = pygame.mouse.get_pos()
    player_screen_center = get_player_screen_center(
        my_player.X,
        my_player.Y,
        IML.Player.get_width(),
        IML.Player.get_height(),
        CameraPosX,
        CameraPosY,
        camera_zoom,
    )
    base_angle = math.radians(
        Tool.GetAtn2Angle_Degrees(player_screen_center, current_mouse_pos)
    )
    muzzle_x = center_x + math.cos(base_angle) * 40
    muzzle_y = center_y + math.sin(base_angle) * 40
    weapon_state.consume_round()
    screen_shake = min(12, screen_shake + int(config.recoil * 2))

    for _ in range(config.pellets):
        shot_angle = base_angle + math.radians(random.uniform(-config.spread_degrees, config.spread_degrees))
        new_bullet = Bullet(
            config.bullet_size,
            damage=config.damage,
            owner_id=my_id,
            weapon_id=weapon_state.weapon_id,
        )
        new_bullet.launch(
            muzzle_x,
            muzzle_y,
            muzzle_x + math.cos(shot_angle) * 1000,
            muzzle_y + math.sin(shot_angle) * 1000,
            speed=config.bullet_speed,
        )
        new_bullet.just_fired = True
        new_bullet.life_time = config.bullet_lifetime
        bullets.append(new_bullet)

    if config.projectile and weapon_state.magazine_ammo == 0:
        reload_weapon()


def handle_mouse_down(event, mouse_pos):
    global dragging_skill
    if event.button != 1:
        return

    available_items = skill_window if skill_window_open else ()
    dragging_skill = next(
        (item.skill_name for item in available_items if item.rect.collidepoint(mouse_pos)),
        None,
    )
    if dragging_skill is None:
        fire_bullet()


def handle_mouse_up(event, mouse_pos):
    global dragging_skill, system_message
    if event.button != 1 or not dragging_skill:
        return

    slot = next(
        (slot for slot in quick_slots if slot.rect.collidepoint(mouse_pos)),
        None,
    )
    if slot:
        skill = SKILL_BOOK[dragging_skill]
        slot.assigned_skill = dragging_skill
        system_message = (
            f"⌨️ [{slot.key_name}] 슬롯에 [{skill.name}] 장착! "
            f"(공격력: {skill.Power})"
        )
    dragging_skill = None


def handle_game_events():
    mouse_pos = pygame.mouse.get_pos()
    event_handlers = {
        pygame.QUIT: handle_quit,
        pygame.KEYDOWN: handle_key_event,
        pygame.MOUSEBUTTONDOWN: handle_mouse_down,
        pygame.MOUSEBUTTONUP: handle_mouse_up,
    }
    for event in pygame.event.get():
        handler = event_handlers.get(event.type)
        if handler:
            handler(event, mouse_pos)


def GameView():
    global running, CameraPosX, CameraPosY, Weapon_Angle, Weapon_Pos, camera_fov, camera_zoom
    global screen_shake, server_players, bullets, remote_bullets, processed_bullet_events, MousePos

    MousePos = pygame.mouse.get_pos()
    handle_game_events()
    Weapon_Pos = pygame.mouse.get_pos()
    
    my_player.handle_input()
    weapon_state.update_reload()

    # ★ [정리] 서버 데이터 동기화 - 필요한 움직임 데이터만 전송
    send_data["posX"] = my_player.X
    send_data["posY"] = my_player.Y
    send_data["hp"] = my_player.Hp
    send_data["angle"] = Weapon_Angle
    send_data["weapon_id"] = weapon_state.weapon_id
    send_data["magazine_ammo"] = weapon_state.magazine_ammo
    send_data["reserve_ammo"] = weapon_state.reserve_ammo
    
    # ★ [정리] 총알 정보 - 이번 프레임에서 새로 발사된 총알만 전송
    send_data["bullets"] = [
        {
            "x": bullet.x,
            "y": bullet.y,
            "angle": bullet.angle,
            "weapon_id": bullet.weapon_id,
        }
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
            own_snapshot = server_players.get(my_id)
            if own_snapshot:
                weapon_id = own_snapshot.get("weapon_id", weapon_state.weapon_id)
                if weapon_id in WEAPONS:
                    weapon_state.weapon_id = weapon_id
                weapon_state.magazine_ammo = own_snapshot.get(
                    "magazine_ammo", weapon_state.magazine_ammo
                )
                weapon_state.reserve_ammo = own_snapshot.get(
                    "reserve_ammo", weapon_state.reserve_ammo
                )
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
    target_camera_x, target_camera_y = get_camera_target(player_center_x, player_center_y, ScreenX, ScreenY, camera_zoom)
    CameraPosX += (target_camera_x - CameraPosX) * lerp
    CameraPosY += (target_camera_y - CameraPosY) * lerp

    if screen_shake > 0:
        CameraPosX += random.randint(-screen_shake, screen_shake)
        CameraPosY += random.randint(-screen_shake, screen_shake)
        screen_shake -= 1

    CameraPosX, CameraPosY = TileGene.clamp_camera(
        CameraPosX, CameraPosY, ScreenX, ScreenY, camera_zoom
    )

    player_screen_x, player_screen_y = world_to_screen(my_player.X, my_player.Y, CameraPosX, CameraPosY, camera_zoom)
    player_center_screen_x, player_center_screen_y = get_player_screen_center(my_player.X, my_player.Y, IML.Player.get_width(), IML.Player.get_height(), CameraPosX, CameraPosY, camera_zoom)

    Weapon_Angle = Tool.GetAtn2Angle_Degrees((player_center_screen_x, player_center_screen_y), Weapon_Pos)
    shotgun_image = IML.ShotGun[0] if camera_zoom == 1.0 else pygame.transform.smoothscale(
        IML.ShotGun[0], (round(IML.ShotGun[0].get_width() * camera_zoom), round(IML.ShotGun[0].get_height() * camera_zoom))
    )
    rotated_shotgun = pygame.transform.rotate(shotgun_image, -Weapon_Angle)
    Shotgun_rect = rotated_shotgun.get_rect()
    Shotgun_rect.center = (player_center_screen_x, player_center_screen_y)

    current_vision = weapon_state.config
    current_vision_shape = vision_shape_override or current_vision.vision_shape
    visibility_cache = {}

    def is_visible(point_x, point_y):
        point = (point_x, point_y)
        if point not in visibility_cache:
            visibility_cache[point] = TileGene.is_point_visible_from(
                player_world_x,
                player_world_y,
                point_x,
                point_y,
                current_vision.vision_radius,
                vision_shape=current_vision_shape,
                direction_angle=Weapon_Angle,
                fov_angle=current_vision.vision_fov,
                vision_width=current_vision.vision_width,
            )
        return visibility_cache[point]

    # ------------------ [게임 월드 그리기] ------------------
    display.fill((0, 0, 200))
    TileGene.draw(display, CameraPosX, CameraPosY, camera_zoom)

    player_world_x, player_world_y = get_player_world_center(my_player.X, my_player.Y, IML.Player.get_width(), IML.Player.get_height())

    for bullet in bullets:
        bullet.update()
        bullet.draw(display, CameraPosX, CameraPosY, camera_zoom)

        if bullet.is_active:
            for p_id, p_info in server_players.items():
                if int(p_id) == my_id:
                    continue
                head, body = Player.hitboxes_for_position(
                    p_info["posX"], p_info["posY"], IML.Player.get_width(), IML.Player.get_height()
                )
                if head.colliderect(bullet.rect) or body.colliderect(bullet.rect):
                    bullet.is_active = False
                    break
    bullets = [b for b in bullets if b.is_active]

    # 서버 스냅샷에는 같은 발사 이벤트가 모든 플레이어 항목에 포함될 수
    # 있으므로 event_id 기준으로 한 번만 생성합니다.
    for p_info in server_players.values():
        for bullet_info in p_info.get("bullets", []):
            event_id = bullet_info.get("event_id")
            if event_id in processed_bullet_events:
                continue
            processed_bullet_events.add(event_id)
            if bullet_info.get("owner_id") == my_id:
                continue
            weapon_id = bullet_info.get("weapon_id", "pistol")
            config = WEAPONS.get(weapon_id, WEAPONS["pistol"])
            enemy_bullet = Bullet(
                config.bullet_size,
                damage=config.damage,
                owner_id=bullet_info.get("owner_id"),
                weapon_id=weapon_id,
            )
            angle = math.radians(bullet_info.get("angle", 0.0))
            enemy_bullet.launch(
                bullet_info["x"], bullet_info["y"],
                bullet_info["x"] + math.cos(angle) * 1000,
                bullet_info["y"] + math.sin(angle) * 1000,
                speed=config.bullet_speed,
            )
            remote_bullets.append(enemy_bullet)

    for bullet in remote_bullets:
        bullet.update()
        if bullet.is_active and my_player.check_bullet_hit(bullet.rect, bullet.damage):
            bullet.is_active = False
        bullet.draw(display, CameraPosX, CameraPosY, camera_zoom)
    remote_bullets = [b for b in remote_bullets if b.is_active]

    # 다른 플레이어 그리기
    for p_id, p_info in server_players.items():
        if int(p_id) == my_id:
            continue

        other_world_x, other_world_y = get_player_world_center(p_info["posX"], p_info["posY"], IML.Player.get_width(), IML.Player.get_height())
        if not is_visible(other_world_x, other_world_y):
            continue

        other_screen_x, other_screen_y = world_to_screen(p_info["posX"], p_info["posY"], CameraPosX, CameraPosY, camera_zoom)
        other_image = IML.Player if camera_zoom == 1.0 else pygame.transform.scale(
            IML.Player, (round(IML.Player.get_width() * camera_zoom), round(IML.Player.get_height() * camera_zoom))
        )
        display.blit(other_image, (other_screen_x, other_screen_y))

        other_center_x, other_center_y = get_player_screen_center(p_info["posX"], p_info["posY"], IML.Player.get_width(), IML.Player.get_height(), CameraPosX, CameraPosY, camera_zoom)
        other_gun = IML.GetShotGun() if camera_zoom == 1.0 else pygame.transform.scale(
            IML.GetShotGun(), (round(IML.GetShotGun().get_width() * camera_zoom), round(IML.GetShotGun().get_height() * camera_zoom))
        )
        other_rotated_gun = pygame.transform.rotate(other_gun, -p_info["angle"])
        other_gun_rect = other_rotated_gun.get_rect()
        other_gun_rect.center = (other_center_x, other_center_y)
        display.blit(other_rotated_gun, other_gun_rect)

    # 내 캐릭터 및 무기 그리기
    my_player.draw(display, CameraPosX, CameraPosY, camera_zoom)
    display.blit(rotated_shotgun, Shotgun_rect)



    
    # 시야 바깥 영역을 검게 덮어서, 보이지 않는 영역은 아예 안 보이게 처리
    dark_overlay = pygame.Surface((ScreenX, ScreenY), pygame.SRCALPHA)
    dark_overlay.fill((0, 0, 0, 0))

    # 맵 바깥은 월드 타일이 없으므로 항상 검게 처리합니다.
    map_screen_left = -CameraPosX * camera_zoom
    map_screen_top = -CameraPosY * camera_zoom
    map_screen_right = (TileGene.map_width * TileGene.tile_size - CameraPosX) * camera_zoom
    map_screen_bottom = (TileGene.map_height * TileGene.tile_size - CameraPosY) * camera_zoom
    pygame.draw.rect(dark_overlay, (0, 0, 0, 255), (0, 0, ScreenX, max(0, map_screen_top)))
    pygame.draw.rect(dark_overlay, (0, 0, 0, 255), (0, min(ScreenY, map_screen_bottom), ScreenX, max(0, ScreenY - map_screen_bottom)))
    pygame.draw.rect(dark_overlay, (0, 0, 0, 255), (0, 0, max(0, map_screen_left), ScreenY))
    pygame.draw.rect(dark_overlay, (0, 0, 0, 255), (min(ScreenX, map_screen_right), 0, max(0, ScreenX - map_screen_right), ScreenY))

    start_tile_x = max(0, int(CameraPosX // TileGene.tile_size))
    end_tile_x = min(TileGene.map_width, int((CameraPosX + ScreenX / camera_zoom) // TileGene.tile_size) + 1)
    start_tile_y = max(0, int(CameraPosY // TileGene.tile_size))
    end_tile_y = min(TileGene.map_height, int((CameraPosY + ScreenY / camera_zoom) // TileGene.tile_size) + 1)


    # 시야 범위 밖의 타일을 검게 덮기 / 타일 객체 순환하면서 시야밖에 있다면 검고 투명한 색으로 전환
    for tile_y in range(start_tile_y, end_tile_y):
        for tile_x in range(start_tile_x, end_tile_x):
            tile = TileGene.map_data.get((tile_x, tile_y))
            if not tile:
                continue

            world_x = tile_x * TileGene.tile_size
            world_y = tile_y * TileGene.tile_size
            screen_x = (world_x - CameraPosX) * camera_zoom
            screen_y = (world_y - CameraPosY) * camera_zoom

            if not is_visible(
                world_x + TileGene.tile_size // 2,
                world_y + TileGene.tile_size // 2,
            ):
                pygame.draw.rect(
                    dark_overlay,
                    (0, 0, 0, 200),
                    pygame.Rect(screen_x, screen_y, TileGene.tile_size * camera_zoom, TileGene.tile_size * camera_zoom)
                )

    display.blit(dark_overlay, (0, 0))

    # 시야 밖에 있어도 총알은 항상 보이도록 최종 레이어에서 다시 그립니다.
    for bullet in bullets:
        bullet.draw(display, CameraPosX, CameraPosY, camera_zoom, force_visible=True)

    for bullet in remote_bullets:
        bullet.draw(display, CameraPosX, CameraPosY, camera_zoom, force_visible=True)

    # =================================================================
    # 📊 고정 UI 그리기 영역 (시야 레이어보다 위에 그려야 선명하게 보입니다)
    # =================================================================
    ui_x = 30
    ui_y = 80  
    draw_ui_gauge(display, ui_x, ui_y, my_player.Hp, my_player.MaxHp)
    
    hp_text = GuiFont.render(f"HP: {my_player.Hp} / {my_player.MaxHp}", True, (255, 255, 255))
    display.blit(hp_text, (ui_x + HP_FRAME_SIZE[0] + 15, ui_y + 42))

    id_text = GuiFont.render(f"ID: {my_id}", True, (255, 255, 255))
    display.blit(id_text, (20, 20))
    
    # --- [퀵슬롯 배경과 스킬 소스창] ---
    draw_skill_panel(display)
    hovered_skill = draw_skill_window(display, MousePos, skill_window_open, dragging_skill)
    
    # 스킬 도감 (스킬창 닫혀있을 때는 안 보임 - draw_skill_window에서 처리)
    # for item in skill_window:
    #     item.draw(display)

    # 하단 퀵슬롯 (�익슬롯은 항상 보임)
    for slot in quick_slots:
        slot.update(MousePos)  # 호버 상태 업데이트
        slot.draw(display)

    draw_ammo_status(display)
    
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
    vision_status = f"시야: {current_vision_shape} [V]"
    vision_text = GuiFont.render(vision_status, True, (255, 220, 120))
    display.blit(vision_text, (ScreenX - 300, 55))
    fov_text = GuiFont.render(f"카메라 FOV: {camera_fov:.2f} / 최대 {CAMERA_FOV_MAX:.2f}", True, (180, 230, 255))
    display.blit(fov_text, (ScreenX - 420, 90))
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
