import pygame
import random
import math
from ImageLoad import Imageload

class Tile:
    def __init__(self, tile_type, is_walkable):
        self.tile_type = tile_type
        self.is_walkable = is_walkable

class TileGenerator:
    def __init__(self, tile_size=64):
        self.IML = Imageload()  # Imageload 인스턴스 생성
        self.tile_size = tile_size
        self.tile_images = {}  # 타일 이미지 저장소
        self.map_data = {}     # 맵 데이터 딕셔너리
        
        # 이미지 풀링 생성
        self._load_placeholder_images()
        
        # ⚠️ [멀티플레이 최적화 수정] 
        # 서버에서 시드(Seed)를 받아오기 전에 생성자가 먼저 작동하므로,
        # 인스턴스 초기화 단계에서의 임의 맵 생성(generate_map) 구문은 제거했습니다.

    def _load_placeholder_images(self):
        """이미지 풀링: 바닥과 집 벽면 타일을 시각적으로 디자인"""
        # -------------------------------------
        # 0: 기본 바닥 (부드러운 잔디/흙 느낌의 연녹색)
        # -------------------------------------
        floor = pygame.Surface((self.tile_size, self.tile_size))
        floor.fill((140, 180, 130)) # 연녹색 톤의 바닥 색상
        # 도트 느낌의 잔디 디테일 선 추가
        pygame.draw.rect(floor, (130, 170, 120), (0, 0, self.tile_size, self.tile_size), 1)
        self.tile_images[0] = floor

        # -------------------------------------
        # 1: 집 벽면 / 장애물 벽 타일 (붉은 벽돌 및 지붕 느낌)
        # -------------------------------------
        wall = pygame.Surface((self.tile_size, self.tile_size))
        
        wall.blit(self.IML.GetTileTest(), (0, 0))  # 벽돌 텍스처 이미지 로드
        
        self.tile_images[1] = wall
        
        # -------------------------------------
        # 2: 문 타일 (갈색, 열림 표시)
        # -------------------------------------
        door = pygame.Surface((self.tile_size, self.tile_size))
        door.fill((140, 180, 130))  # 바닥색
        pygame.draw.rect(door, (101, 67, 33), (10, 10, self.tile_size - 20, self.tile_size - 20))  # 문 모양
        pygame.draw.rect(door, (255, 200, 100), (10, 10, self.tile_size - 20, self.tile_size - 20), 2)  # 테두리
        pygame.draw.circle(door, (200, 150, 50), (self.tile_size - 20, self.tile_size // 2), 3)  # 손잡이
        self.tile_images[2] = door
        
        # -------------------------------------
        # 3: 보물상자 (황금색)
        # -------------------------------------
        treasure = pygame.Surface((self.tile_size, self.tile_size))
        treasure.fill((140, 180, 130))  # 바닥색
        pygame.draw.rect(treasure, (200, 150, 50), (15, 20, self.tile_size - 30, 25))  # 상자 본체
        pygame.draw.rect(treasure, (255, 200, 0), (15, 20, self.tile_size - 30, 25), 2)  # 테두리
        pygame.draw.line(treasure, (150, 100, 0), (self.tile_size // 2, 20), (self.tile_size // 2, 45), 2)  # 뚜껑
        self.tile_images[3] = treasure

    def generate_map(self, width_tiles, height_tiles, seed_value=None):
        """★멀티플레이 동동화 핵심★: 서버 시드로 난수를 고정하여 모두에게 똑같은 집을 배치합니다."""
        if seed_value is not None:
            random.seed(seed_value) # 👈 이 구문이 돌면서 모든 유저 컴퓨터의 난수 발생 순서가 고정됩니다.

        self.map_data.clear() # 기존 데이터 초기화

        # 1. 일단 전체 맵을 다 바닥(0)으로 초기화
        for y in range(height_tiles):
            for x in range(width_tiles):
                self.map_data[(x, y)] = Tile(tile_type=0, is_walkable=True)

        # 2. 외곽 테두리 영역을 겉벽(1)으로 채우기
        for y in range(height_tiles):
            for x in range(width_tiles):
                if x == 0 or x == width_tiles - 1 or y == 0 or y == height_tiles - 1:
                    self.map_data[(x, y)] = Tile(tile_type=1, is_walkable=False)

        # 3. 맵 중간중간 무작위 위치에 '집' 형태 구조물 빌드 (예: 12채 생성)
        # ★ [개선] 집의 윤곽선만 벽으로 생성 (내부는 비워 플레이어가 드나들 수 있음)
        # ★ [추가] 문과 보물상자 추가
        num_houses = 12
        for _ in range(num_houses):
            # 맵 중앙 안쪽 안전한 좌표 무작위 선택 (시드가 같으므로 결과값도 모든 유저가 완벽히 일치)
            house_x = random.randint(3, width_tiles - 10)
            house_y = random.randint(3, height_tiles - 10)
            
            # 생성할 집의 크기 설정 (가로 3~5칸, 세로 3~5칸 크기)
            house_w = random.randint(3, 5)
            house_h = random.randint(3, 5)
            
            # 플레이어 시작 지점 광장 근처(예: 타일 인덱스 20~27 사이)에는 집이 안 생기도록 처리
            if 18 <= house_x <= 28 and 18 <= house_y <= 28:
                continue
            
            # 집의 윤곽선만 벽으로 생성 (테두리만 1, 내부는 바닥 0)
            for hy in range(house_y, house_y + house_h):
                for hx in range(house_x, house_x + house_w):
                    # 집의 테두리(위, 아래, 좌, 우)만 벽으로 설정
                    is_border = (hy == house_y or hy == house_y + house_h - 1 or 
                                 hx == house_x or hx == house_x + house_w - 1)
                    
                    if is_border:
                        self.map_data[(hx, hy)] = Tile(tile_type=1, is_walkable=False)
                    else:
                        # 내부는 바닥으로 유지 (집 내부는 이동 가능)
                        self.map_data[(hx, hy)] = Tile(tile_type=0, is_walkable=True)
            
            # ★ [추가] 집에 문 배치 (테두리 중 랜덤한 위치, 4개 방향 중 선택)
            door_sides = [
                # (x, y) - 위, 아래, 좌, 우
                (random.randint(house_x + 1, house_x + house_w - 2), house_y),  # 위쪽
                (random.randint(house_x + 1, house_x + house_w - 2), house_y + house_h - 1),  # 아래쪽
                (house_x, random.randint(house_y + 1, house_y + house_h - 2)),  # 좌측
                (house_x + house_w - 1, random.randint(house_y + 1, house_y + house_h - 2))  # 우측
            ]
            door_pos = random.choice(door_sides)
            self.map_data[door_pos] = Tile(tile_type=2, is_walkable=True)  # 문은 통과 가능
            
            # ★ [추가] 집에 확률적으로 보물상자 배치 (40% 확률)
            if random.random() < 0.4 and house_w > 2 and house_h > 2:
                treasure_x = random.randint(house_x + 1, house_x + house_w - 2)
                treasure_y = random.randint(house_y + 1, house_y + house_h - 2)
                self.map_data[(treasure_x, treasure_y)] = Tile(tile_type=3, is_walkable=True)  # 보물상자

    def draw(self, surface, camera_x, camera_y):
        """화면 컬링(Culling) 렌더링"""
        screen_width, screen_height = surface.get_size()

        start_x = max(0, int(camera_x // self.tile_size))
        end_x = int((camera_x + screen_width) // self.tile_size) + 1
        
        start_y = max(0, int(camera_y // self.tile_size))
        end_y = int((camera_y + screen_height) // self.tile_size) + 1

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.map_data.get((x, y))
                if tile:
                    screen_x = x * self.tile_size - camera_x
                    screen_y = y * self.tile_size - camera_y

                    tile_img = self.tile_images[tile.tile_type]
                    surface.blit(tile_img, (screen_x, screen_y))

    def get_tile_at(self, tile_x, tile_y):
        return self.map_data.get((tile_x, tile_y))

    def is_point_visible_from(self, player_x, player_y, point_x, point_y, max_radius=250):
        """월드 좌표의 점이 플레이어 시야 안에 있고, 벽에 가려지지 않았는지 검사합니다."""
        dist = math.hypot(point_x - player_x, point_y - player_y)
        if dist > max_radius:
            return False

        steps = max(1, int(dist / 4))
        for i in range(1, steps + 1):
            t = i / steps
            sample_x = player_x + (point_x - player_x) * t
            sample_y = player_y + (point_y - player_y) * t
            tile_x = int(sample_x // self.tile_size)
            tile_y = int(sample_y // self.tile_size)
            tile = self.map_data.get((tile_x, tile_y))
            if tile and tile.tile_type == 1:
                return False

        return True

    def is_tile_visible_from(self, player_x, player_y, tile_world_x, tile_world_y, max_radius=250):
        """타일의 중심에서 플레이어까지 직선으로 보이는지 확인. 벽이 있으면 가려짐."""
        center_x = tile_world_x + (self.tile_size // 2)
        center_y = tile_world_y + (self.tile_size // 2)
        return self.is_point_visible_from(player_x, player_y, center_x, center_y, max_radius)
    
    def get_wall_rects(self, surface, camera_x, camera_y):
        """현재 화면 범위 안에 있는 집 벽 타일들의 '절대 좌표 Rect'를 추출 (시야 차단 연산 연동용)"""
        screen_width, screen_height = surface.get_size()
        wall_rects = []

        start_x = max(0, int(camera_x // self.tile_size))
        end_x = int((camera_x + screen_width) // self.tile_size) + 1
        
        start_y = max(0, int(camera_y // self.tile_size))
        end_y = int((camera_y + screen_height) // self.tile_size) + 1

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.map_data.get((x, y))
                if tile and tile.tile_type == 1:
                    world_x = x * self.tile_size
                    world_y = y * self.tile_size
                    rect = pygame.Rect(world_x, world_y, self.tile_size, self.tile_size)
                    wall_rects.append(rect)
                    
        return wall_rects

    def is_walkable(self, world_x, world_y):
        """월드 좌표가 이동 가능한 지형인지 확인"""
        tile_x = int(world_x // self.tile_size)
        tile_y = int(world_y // self.tile_size)
        tile = self.map_data.get((tile_x, tile_y))
        
        if tile is None:
            return False  # 맵 범위 밖
        
        return tile.is_walkable
    
    def check_collision(self, rect):
        """Rect와 벽이 충돌하는지 확인 (rect의 중심을 기준)"""
        # Rect의 4개 모서리와 중심을 체크
        points_to_check = [
            (rect.left, rect.top),      # 좌상단
            (rect.right, rect.top),     # 우상단
            (rect.left, rect.bottom),   # 좌하단
            (rect.right, rect.bottom),  # 우하단
            (rect.centerx, rect.centery) # 중심
        ]
        
        for x, y in points_to_check:
            if not self.is_walkable(x, y):
                return True  # 충돌 감지
        
        return False  # 충돌 없음
