import pygame
from Config import *
from ImageLoad import *
import math
from TileGenerator import *
from Bullet import *
import Tool
import random
import os
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
# [커스텀 가능] 게임 전체에서 사용할 기본 폰트입니다. 서체와 크기를 여기서 조정합니다.
GuiFont = pygame.font.Font(
    os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
            ),"Font","HeirofLightRegular.ttf"
            ), 30)




# --- [네트워크 초기화] ---
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
client.connect((ServerIp, ServerPort))

init_data = pickle.loads(client.recv(1024))
my_id = init_data["init_id"]
print(f"내 아이디:{my_id}번 입니다.")


map = random.seed(init_data["seed"])  # 시드 고정
IML = Imageload()
set_ui_assets(IML.SkillWindow, IML.QuickSlot)
set_image_loader(IML)  # SkillAndSlot에 이미지 로더 전달
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
skill_cooldowns = {}
vision_skill_until = 0
shield_until = 0
haste_until = 0
active_bombs = []
active_explosions = []
pending_treasure_destroys = []
screen_shake = 0
server_players = {}
# 시야 밖을 검게 덮을 때 재사용하는 투명 레이어입니다.
vision_overlay = pygame.Surface((ScreenX, ScreenY), pygame.SRCALPHA)
# 방향과 모양이 크게 바뀔 때만 시야 폴리곤을 다시 계산합니다.
visibility_polygon_cache = {}
mouse_fire_hold = False

def draw_visibility_geometry(surface, geometry, camera_x, camera_y, zoom):
    """시야 부분을 마스크에서 투명하게 뚫습니다."""
    if geometry.is_empty:
        return
    polygons = geometry.geoms if geometry.geom_type == "MultiPolygon" else (geometry,)
    for polygon in polygons:
        points = [
            ((world_x - camera_x) * zoom, (world_y - camera_y) * zoom)
            for world_x, world_y in polygon.exterior.coords
        ]
        if len(points) >= 3:
            pygame.draw.polygon(surface, (0, 0, 0, 0), points)

def load_effect_sound(filename):
    """효과음 파일이 아직 없어도 게임이 실행되도록 선택적으로 로드합니다."""
    sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Sound", filename)
    try:
        return pygame.mixer.Sound(sound_path)
    except (pygame.error, OSError) as error:
        print(f"[사운드 로드 실패] {filename}: {error}")
        return None


def play_effect_sound(sound, filename):
    if sound is None:
        return
    try:
        sound.play()
    except pygame.error as error:
        print(f"[사운드 재생 실패] {filename}: {error}")


skill_sounds = {
    "달팽이 세개": load_effect_sound("skill_bomb.wav"),
    "레이징 블로우": load_effect_sound("skill_attack.wav"),
    "헤이스트": load_effect_sound("skill_haste.wav"),
    "매의 눈": load_effect_sound("skill_vision.wav"),
    "보호막": load_effect_sound("skill_shield.wav"),
}
chest_sound = load_effect_sound("chest_open.wav")

# 무기 설정을 기본값으로 사용하고, 스킬이 잠시 시야 모양만 덮어씁니다.
vision_shapes = (VISION_CIRCLE, VISION_CONE, VISION_RECTANGLE, VISION_LINE)
vision_shape_index = 0

skill_window_open = False
weapon_state = WeaponState()
vision_shape_override = None

def draw_ui_gauge(surface, x, y, current_val, max_val):
    """투명 중앙이 뚫린 HP 프레임 안쪽에 HP 게이지를 그립니다."""
    
    frame_width, frame_height = HpBarFrame.get_size()
    ratio = max(0, min(current_val, max_val)) / max(1, max_val)

    global hp_color
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
    elif current_val <= 60:
        hp_color = pygame.Color("red")      # 체력이 60 이하로 떨어지면 노란색
    elif current_val <= 80:
        hp_color = pygame.Color("yellow")   # 체력이 81~99 사이면 노란색
        
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
    # [커스텀 가능] 탄약 표시 폰트: 서체("malgungothic"), 크기(24)
    ammo_font = GuiFont
    name_text = ammo_font.render(config.name, True, (255, 220, 120))
    if weapon_state.is_reloading_now():
        ammo_text = ammo_font.render("재장전 중...", True, (255, 180, 120))
    else:
        ammo_text = ammo_font.render(weapon_state.ammo_text(), True, (255, 255, 255))
    surface.blit(name_text, (ScreenX - 210, ScreenY - 72))
    surface.blit(ammo_text, (ScreenX - 80, ScreenY - 72))


def draw_quick_slot_cooldowns(surface):
    """스킬 쿨타임을 각 슬롯에 표시합니다."""
    now = pygame.time.get_ticks()
    for slot in quick_slots:
        if not slot.assigned_skill:
            continue
        end_time = skill_cooldowns.get(slot.assigned_skill, 0)
        if end_time <= now:
            continue
        remain = max(0.0, (end_time - now) / 1000.0)
        overlay = pygame.Surface((slot.rect.width, slot.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 170), overlay.get_rect(), border_radius=8)
        surface.blit(overlay, slot.rect.topleft)
        # [커스텀 가능] 쿨타임 표시 폰트: 서체("malgungothic"), 크기(14)
        text = GuiFont.render(f"{remain:.1f}s", True, (255, 255, 255))
        surface.blit(text, (slot.rect.centerx - text.get_width() / 2, slot.rect.centery - 8))


def MainView():
    global running, ScreenState
    # [커스텀 가능] 메인 화면 타이틀 (GuiFont는 기본 폰트)
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


def GameOverView():
    global running
    title = GuiFont.render("게임 오버", True, (220, 50, 50))
    guide = GuiFont.render("ESC를 눌러 종료하세요", True, (255, 255, 255))
    display.blit(title, title.get_rect(center=(ScreenX // 2, ScreenY // 2 - 60)))
    display.blit(guide, guide.get_rect(center=(ScreenX // 2, ScreenY // 2 + 70)))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False


def handle_quit(_event, _mouse_pos):
    global running
    running = False


def activate_quick_slot(key):
    global system_message, vision_shape_override, vision_skill_until, shield_until, haste_until
    key_name = pygame.key.name(key).upper()
    slot = next((slot for slot in quick_slots if slot.key_name == key_name), None)
    if not slot or not slot.assigned_skill:
        system_message = f"[{key_name}] 슬롯이 비어있습니다."
        return

    skill_name = slot.assigned_skill
    now = pygame.time.get_ticks()
    if now < skill_cooldowns.get(skill_name, 0):
        remain = (skill_cooldowns[skill_name] - now) / 1000
        system_message = f"{skill_name} 재사용 대기: {remain:.1f}초"
        return

    skill_cooldowns[skill_name] = now + 5000
    play_effect_sound(skill_sounds.get(skill_name), skill_name)
    if skill_name == "달팽이 세개":
        target_x, target_y = screen_to_world(*pygame.mouse.get_pos(), CameraPosX, CameraPosY, camera_zoom)
        active_bombs.append({"x": target_x, "y": target_y, "explode_at": now + 600})
        system_message = "폭탄을 설치했습니다."
    elif skill_name == "레이징 블로우":
        base_angle = math.atan2(
            pygame.mouse.get_pos()[1] - get_player_screen_center(
                my_player.X, my_player.Y, IML.Player.get_width(), IML.Player.get_height(),
                CameraPosX, CameraPosY, camera_zoom
            )[1],
            pygame.mouse.get_pos()[0] - get_player_screen_center(
                my_player.X, my_player.Y, IML.Player.get_width(), IML.Player.get_height(),
                CameraPosX, CameraPosY, camera_zoom
            )[0],
        )
        center_x, center_y = get_player_world_center(
            my_player.X, my_player.Y, IML.Player.get_width(), IML.Player.get_height()
        )
        for spread in (-12, 0, 12):
            angle = base_angle + math.radians(spread)
            skill_bullet = Bullet(8, damage=SKILL_BOOK[skill_name].Power, owner_id=my_id)
            skill_bullet.launch(center_x, center_y, center_x + math.cos(angle) * 1000,
                                center_y + math.sin(angle) * 1000, speed=22)
            bullets.append(skill_bullet)
        system_message = "레이징 블로우를 사용했습니다."
    elif skill_name == "헤이스트":
        haste_until = now + 5000
        system_message = "5초 동안 달리기 속도가 증가합니다."
    elif skill_name == "매의 눈":
        vision_shape_override = VISION_CIRCLE
        vision_skill_until = now + 3000
        system_message = "3초 동안 원형으로 넓게 봅니다."
    elif skill_name == "보호막":
        shield_until = now + 5000
        system_message = "5초 동안 피해를 받지 않습니다."


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


def activate_skill_or_reload(key):
    key_name = pygame.key.name(key).upper()
    slot = next((slot for slot in quick_slots if slot.key_name == key_name), None)
    if slot and slot.assigned_skill:
        activate_quick_slot(key)
    else:
        reload_weapon()


def handle_key_event(event, _mouse_pos):
    global skill_window_open, dragging_skill
    key_actions = {
        pygame.K_ESCAPE: lambda _key: handle_quit(None, None),
        pygame.K_k: lambda _key: toggle_skill_window(),
        pygame.K_v: lambda _key: cycle_vision_shape(),
        pygame.K_q: lambda _key: activate_quick_slot(_key),
        pygame.K_e: lambda _key: activate_quick_slot(_key),
        pygame.K_t: lambda _key: activate_quick_slot(_key),
        pygame.K_r: lambda _key: reload_weapon(),
        pygame.K_f: lambda _key: activate_skill_or_reload(_key),
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
    """V 키로 현재 시야 모양을 순서대로 변경합니다."""
    global vision_shape_index, vision_shape_override, system_message
    vision_shape_index = (vision_shape_index + 1) % len(vision_shapes)
    vision_shape_override = vision_shapes[vision_shape_index]
    shape_name = vision_shape_override
    system_message = f"시야 모양: {shape_name}" 


def fire_knife():
    """칼 공격: 근거리 범위 내의 모든 적에게 데미지를 줍니다."""
    global screen_shake, system_message
    config = weapon_state.config
    
    center_x, center_y = get_player_world_center(
        my_player.X,
        my_player.Y,
        IML.Player.get_width(),
        IML.Player.get_height(),
    )
    
    # 칼 공격 범위 (데미지를 줄 최대 거리)
    knife_range = 150
    
    # 근처 서버 플레이어 찾기
    attacked_count = 0
    for p_id, p_info in server_players.items():
        if int(p_id) == my_id:
            continue
        
        enemy_center_x = p_info["posX"] + IML.Player.get_width() / 2
        enemy_center_y = p_info["posY"] + IML.Player.get_height() / 2
        
        # 거리 계산
        distance = math.sqrt((center_x - enemy_center_x)**2 + (center_y - enemy_center_y)**2)
        if distance <= knife_range:
            attacked_count += 1
    
    weapon_state.consume_round()
    screen_shake = min(8, screen_shake + 3)
    
    if attacked_count > 0:
        system_message = f"칼 공격! {config.damage} 데미지 × {attacked_count}명"
    else:
        system_message = f"칼 휘둘렀습니다. (데미지: {config.damage})"


def fire_bullet():
    global bullets, screen_shake, system_message
    config = weapon_state.config

    if weapon_state.is_reloading_now():
        system_message = "재장전 중입니다."
        return
    
    # 칼 공격 특수 처리
    if not config.projectile:
        if not weapon_state.can_fire():
            system_message = f"{config.name} 공격은 아직 준비 중입니다."
            return
        fire_knife()
        return
    
    if not weapon_state.can_fire():
        if config.projectile and weapon_state.magazine_ammo == 0:
            reload_weapon()
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
    global dragging_skill, mouse_fire_hold
    if event.button != 1:
        return

    available_items = skill_window if skill_window_open else ()
    dragging_skill = next(
        (item.skill_name for item in available_items if item.rect.collidepoint(mouse_pos)),
        None,
    )
    if dragging_skill is None:
        mouse_fire_hold = weapon_state.config.automatic
        fire_bullet()


def handle_mouse_up(event, mouse_pos):
    global dragging_skill, system_message, mouse_fire_hold
    if event.button != 1:
        mouse_fire_hold = False
        return
    mouse_fire_hold = False
    if not dragging_skill:
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
    global running, ScreenState, CameraPosX, CameraPosY, Weapon_Angle, Weapon_Pos, camera_fov, camera_zoom
    global screen_shake, server_players, bullets, remote_bullets, processed_bullet_events, MousePos, system_message
    global vision_shape_override, vision_skill_until, shield_until, haste_until
    global active_bombs, active_explosions, pending_treasure_destroys
    global visibility_polygon_cache, mouse_fire_hold

    MousePos = pygame.mouse.get_pos()
    if my_player.Hp <= 0:
        ScreenState = "GameOver"
        return
    handle_game_events()
    Weapon_Pos = pygame.mouse.get_pos()

    if mouse_fire_hold and weapon_state.config.automatic and weapon_state.can_fire():
        fire_bullet()

    my_player.handle_input()
    weapon_state.update_reload()

    now = pygame.time.get_ticks()
    if vision_skill_until and now >= vision_skill_until:
        vision_skill_until = 0
        vision_shape_override = None
    my_player.normal_speed = 10 if now < haste_until else 5

    pending_bombs = []
    for bomb in active_bombs:
        if now < bomb["explode_at"]:
            pending_bombs.append(bomb)
            continue
        active_explosions.append({"x": bomb["x"], "y": bomb["y"], "until": now + 350})
        for p_id, p_info in server_players.items():
            distance = math.hypot(p_info["posX"] - bomb["x"], p_info["posY"] - bomb["y"])
            if distance <= 120:
                p_info["hp"] = max(0, p_info.get("hp", 100) - 30)
    active_bombs = pending_bombs
    active_explosions = [explosion for explosion in active_explosions if now < explosion["until"]]

    # ★ [정리] 서버 데이터 동기화 - 필요한 움직임 데이터만 전송
    send_data["posX"] = my_player.X
    send_data["posY"] = my_player.Y
    send_data["hp"] = my_player.Hp
    send_data["angle"] = Weapon_Angle
    send_data["weapon_id"] = weapon_state.weapon_id
    send_data["magazine_ammo"] = weapon_state.magazine_ammo
    send_data["reserve_ammo"] = weapon_state.reserve_ammo
    send_data["destroyed_treasures"] = list(pending_treasure_destroys)
    
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
            synchronized_treasures = set()
            for player_snapshot in server_players.values():
                synchronized_treasures.update(
                    tuple(treasure) for treasure in player_snapshot.get("destroyed_treasures", [])
                )
            for tile_x, tile_y in synchronized_treasures:
                TileGene.destroy_treasure(tile_x, tile_y)
            pending_treasure_destroys.clear()
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
    # 무기의 시야 설정과 일시적인 스킬 오버라이드를 합칩니다.
    current_vision = weapon_state.config
    current_vision_shape = vision_shape_override or current_vision.vision_shape
    # 같은 프레임에서 같은 대상은 한 번만 벽 가림을 계산합니다.
    visibility_cache = {}

    def is_visible(point_x, point_y):
        """다른 플레이어가 현재 시야 안에 있는지 확인합니다."""
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
            if TileGene.check_wall_collision(bullet.rect):
                bullet.is_active = False
                continue
            destroyed_treasure = TileGene.destroy_treasure_at(bullet.rect)
            if destroyed_treasure:
                pending_treasure_destroys.append(destroyed_treasure)
                play_effect_sound(chest_sound, "chest_open.wav")
                empty_slot = next((slot for slot in quick_slots if slot.assigned_skill is None), None)
                if empty_slot:
                    empty_slot.assigned_skill = random.choice(list(SKILL_BOOK))
                    system_message = f"보물상자에서 [{empty_slot.assigned_skill}] 획득!"
                else:
                    system_message = "보물상자를 열었지만 스킬 슬롯이 가득 찼습니다."
                bullet.is_active = False
                continue
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
        if bullet.is_active and TileGene.check_wall_collision(bullet.rect):
            bullet.is_active = False
        if bullet.is_active and shield_until <= pygame.time.get_ticks() and my_player.check_bullet_hit(bullet.rect, bullet.damage):
            bullet.is_active = False
        bullet.draw(display, CameraPosX, CameraPosY, camera_zoom)
    remote_bullets = [b for b in remote_bullets if b.is_active]

    if my_player.Hp <= 0:
        ScreenState = "GameOver"
        return

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



    
    # 화면 전체를 어둡게 한 뒤, 아래에서 시야 폴리곤만 투명하게 뚫습니다.
    dark_overlay = vision_overlay
    # 완전한 검정이 아니라 뒤의 맵이 살짝 보이는 반투명 검정입니다.
    dark_overlay.fill((0, 0, 0, 170))

    # 맵 바깥은 월드 타일이 없으므로 항상 검게 처리합니다.
    map_screen_left = -CameraPosX * camera_zoom
    map_screen_top = -CameraPosY * camera_zoom
    map_screen_right = (TileGene.map_width * TileGene.tile_size - CameraPosX) * camera_zoom
    map_screen_bottom = (TileGene.map_height * TileGene.tile_size - CameraPosY) * camera_zoom
    pygame.draw.rect(dark_overlay, (0, 0, 0, 255), (0, 0, ScreenX, max(0, map_screen_top)))
    pygame.draw.rect(dark_overlay, (0, 0, 0, 255), (0, min(ScreenY, map_screen_bottom), ScreenX, max(0, ScreenY - map_screen_bottom)))
    pygame.draw.rect(dark_overlay, (0, 0, 0, 255), (0, 0, max(0, map_screen_left), ScreenY))
    pygame.draw.rect(dark_overlay, (0, 0, 0, 255), (min(ScreenX, map_screen_right), 0, max(0, ScreenX - map_screen_right), ScreenY))

    # 위치 8픽셀, 방향 4도 단위로 묶어 마우스 이동 중 재계산을 줄입니다.
    polygon_cache_key = (
        round(player_world_x / 8),
        round(player_world_y / 8),
        round(Weapon_Angle / 4),
        current_vision_shape,
        current_vision.vision_radius,
        current_vision.vision_fov,
        current_vision.vision_width,
    )
    if polygon_cache_key not in visibility_polygon_cache:
        # 캐시가 없을 때만 벽과 광선이 포함된 폴리곤을 계산합니다.
        visibility_polygon_cache[polygon_cache_key] = TileGene.get_visibility_polygon(
            player_world_x,
            player_world_y,
            current_vision.vision_radius,
            vision_shape=current_vision_shape,
            direction_angle=Weapon_Angle,
            fov_angle=current_vision.vision_fov,
            vision_width=current_vision.vision_width,
            ray_samples=None,  # 자동 최적화 (저격총 직선은 8, 기타는 12)
        )
        # [최적화] 캐시 크기를 128로 증대 (저격총 직선은 각도 변화가 많음)
        if len(visibility_polygon_cache) > 128:
            visibility_polygon_cache.pop(next(iter(visibility_polygon_cache)))
    visibility_polygon = visibility_polygon_cache[polygon_cache_key]
    if visibility_polygon:
        # 월드 폴리곤을 현재 카메라 좌표로 변환해 어두운 레이어를 뚫습니다.
        draw_visibility_geometry(dark_overlay, visibility_polygon, CameraPosX, CameraPosY, camera_zoom)

    display.blit(dark_overlay, (0, 0))

    # 시야 밖에 있어도 총알은 항상 보이도록 최종 레이어에서 다시 그립니다.
    for bullet in bullets:
        bullet.draw(display, CameraPosX, CameraPosY, camera_zoom, force_visible=True)

    for bullet in remote_bullets:
        bullet.draw(display, CameraPosX, CameraPosY, camera_zoom, force_visible=True)

    # 폭탄과 폭발 범위는 시야 효과 위에 표시합니다.
    for bomb in active_bombs:
        bomb_screen = world_to_screen(bomb["x"], bomb["y"], CameraPosX, CameraPosY, camera_zoom)
        pygame.draw.circle(display, (255, 170, 40), (round(bomb_screen[0]), round(bomb_screen[1])),
                           max(5, round(12 * camera_zoom)), 3)
    for explosion in active_explosions:
        explosion_screen = world_to_screen(
            explosion["x"], explosion["y"], CameraPosX, CameraPosY, camera_zoom
        )
        pygame.draw.circle(
            display,
            (255, 80, 20),
            (round(explosion_screen[0]), round(explosion_screen[1])),
            max(10, round(120 * camera_zoom)),
            5,
        )

    if shield_until > pygame.time.get_ticks():
        shield_center = get_player_screen_center(
            my_player.X, my_player.Y, IML.Player.get_width(), IML.Player.get_height(),
            CameraPosX, CameraPosY, camera_zoom
        )
        # Protect.png 이미지가 있으면 반투명으로 표시
        if IML.Protect:
            protect_size = max(50, int(90 * camera_zoom))
            protect_scaled = pygame.transform.scale(IML.Protect, (protect_size, protect_size))
            protect_scaled.set_alpha(150)  # 150/255 = 약 60% 투명도
            protect_rect = protect_scaled.get_rect(center=shield_center)
            display.blit(protect_scaled, protect_rect)
        else:
            # Protect.png가 없으면 파란 원으로 표시
            pygame.draw.circle(display, (100, 220, 255),
                               (round(shield_center[0]), round(shield_center[1])),
                               max(20, round(45 * camera_zoom)), 4)

    # =================================================================
    # 📊 고정 UI 그리기 영역 (시야 레이어보다 위에 그려야 선명하게 보입니다)
    # =================================================================
    ui_x = 30
    ui_y = 80  
    draw_ui_gauge(display, ui_x, ui_y, my_player.Hp, my_player.MaxHp)
    
    # [커스텀 가능] HP 텍스트 표시 폰트 (GuiFont 사용)
    hp_text = GuiFont.render(f"HP: {my_player.Hp} / {my_player.MaxHp}", True, (255, 255, 255))
    display.blit(hp_text, (ui_x + HP_FRAME_SIZE[0] + 15, ui_y + 42))

    # [커스텀 가능] 플레이어 ID 표시 폰트 (GuiFont 사용)
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

    draw_quick_slot_cooldowns(display)
    draw_ammo_status(display)
    
    # ★ [추가] 스킬 툴팁 그리기 (마우스 raycast 무시 - 드래그 중이 아닐 때만)
    if skill_window_open and hovered_skill and dragging_skill is None:
        draw_skill_tooltip(display, MousePos, hovered_skill)

    # 시스템 메시지
    if system_message:
        # [커스텀 가능] 시스템 메시지 텍스트 폰트 (GuiFont 사용)
        message_text = GuiFont.render(system_message, True, (255, 255, 255))
        display.blit(message_text, (30, ScreenY - 40))
    
    # 스킬 창 상태 표시 (우측 상단)
    skill_status = "📖 스킬 창: [OPEN - K]" if skill_window_open else "📖 스킬 창: [닫음 - K]"
    # [커스텀 가능] 스킬 상태 폰트 (GuiFont 사용)
    status_text = GuiFont.render(skill_status, True, (100, 200, 255) if skill_window_open else (100, 100, 100))
    display.blit(status_text, (ScreenX - 300, 20))
    vision_status = f"시야: {current_vision_shape} [V]"
    # [커스텀 가능] 시야 정보 폰트 (GuiFont 사용)
    vision_text = GuiFont.render(vision_status, True, (255, 220, 120))
    display.blit(vision_text, (ScreenX - 300, 55))
    # [커스텀 가능] 카메라 FOV 정보 폰트 (GuiFont 사용)
    fov_text = GuiFont.render(f"카메라 FOV: {camera_fov:.2f} / 최대 {CAMERA_FOV_MAX:.2f}", True, (180, 230, 255))
    display.blit(fov_text, (ScreenX - 420, 90))
    # ------------------ [그리기 끝] ------------------


while running: 
    display.fill((0,0,0))
    if ScreenState == "MainView":
        MainView()
    elif ScreenState == "GameView":
        GameView()
    elif ScreenState == "GameOver":
        GameOverView()
    pygame.display.update() 
    clock.tick(fps)

pygame.quit()
