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
        num_houses = 12
        for _ in range(num_houses):
            # 맵 중앙 안쪽 안전한 좌표 무작위 선택 (시드가 같으므로 결과값도 모든 유저가 완벽히 일치)
            house_x = random.randint(3, width_tiles - 10)
            house_y = random.randint(3, height_tiles - 10)
            
            # 생성할 집의 크기 설정 (가로 3~5칸, 세로 3~5칸 크기)
            house_w = random.randint(3, 5)
            house_h = random.randint(3, 5)
            
            # 선택한 범위에 사각형 모양으로 벽 타일(1)을 덮어씌워 집을 완성
            for hy in range(house_y, house_y + house_h):
                for hx in range(house_x, house_x + house_w):
                    # 플레이어 시작 지점 광장 근처(예: 타일 인덱스 20~27 사이)에는 집이 안 생기도록 처리
                    # 이렇게 해야 플레이어들이 스폰될 때 집 벽에 끼이지 않습니다.
                    if 18 <= hx <= 28 and 18 <= hy <= 28:
                        continue
                    self.map_data[(hx, hy)] = Tile(tile_type=1, is_walkable=False)

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
