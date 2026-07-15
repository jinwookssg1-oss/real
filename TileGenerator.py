import pygame
import random

class Tile:
    def __init__(self, tile_type, is_walkable):
        # 대소문자 및 변수명을 아래 메서드들과 일치하도록 통일했습니다.
        self.tile_type = tile_type
        self.is_walkable = is_walkable

# 최적화 맵은 Sprite 상속이 필요 없으므로 제거하여 연산 속도를 높입니다.
class TileGenerator:
    def __init__(self, tile_size=64):
        self.tile_size = tile_size
        self.tile_images = {}  # 타일 이미지 저장소
        self.map_data = {}     # 맵 데이터 딕셔너리
        
        # 이미지 풀링 생성
        self._load_placeholder_images()
        
        # ★ 핵심 수정: 클래스가 생성될 때 기본적으로 맵을 생성하도록 추가
        # 가로 50칸, 세로 50칸 규모의 맵을 기본 생성합니다. (원하는 크기로 변경 가능)
        self.generate_map(50, 50)

    def _load_placeholder_images(self):
        """이미지 풀링: 종류별 이미지를 하나만 만들어두고 돌려씀"""
        # 0: 바닥 (밝은 회색)
        floor = pygame.Surface((self.tile_size, self.tile_size))
        floor.fill((220, 220, 220))
        # 구분하기 쉽도록 가볍게 테두리 선 추가
        pygame.draw.rect(floor, (200, 200, 200), (0, 0, self.tile_size, self.tile_size), 1)
        self.tile_images[0] = floor

        # 1: 파괴 불가능한 외곽벽 (어두운 회색)
        wall = pygame.Surface((self.tile_size, self.tile_size))
        wall.fill((60, 60, 60))
        pygame.draw.rect(wall, (40, 40, 40), (0, 0, self.tile_size, self.tile_size), 2)
        self.tile_images[1] = wall

    def generate_map(self, width_tiles, height_tiles):
        """맵 생성 및 각 타일 인스턴스 데이터 할당"""
        for y in range(height_tiles):
            for x in range(width_tiles):
                # 가장자리는 벽(1), 내부는 바닥(0)
                # 인자 이름을 Tile 클래스의 __init__ 정의와 똑같이 맞췄습니다.
                if x == 0 or x == width_tiles - 1 or y == 0 or y == height_tiles - 1:
                    self.map_data[(x, y)] = Tile(tile_type=1, is_walkable=False)
                else:
                    # 중간중간 랜덤하게 장애물 벽(1)을 섞고 싶다면 아래 주석을 해제하세요.
                    # if random.random() < 0.05:
                    #     self.map_data[(x, y)] = Tile(tile_type=1, is_walkable=False)
                    # else:
                    self.map_data[(x, y)] = Tile(tile_type=0, is_walkable=True)

    def draw(self, surface, camera_x, camera_y):
        """★최적화 핵심: 화면 컬링(Culling) 및 풀링 렌더링★"""
        screen_width, screen_height = surface.get_size()

        # 현재 카메라 위치 기준 화면에 보여야 할 타일의 인덱스 범위 계산
        start_x = max(0, int(camera_x // self.tile_size))
        end_x = int((camera_x + screen_width) // self.tile_size) + 1
        
        start_y = max(0, int(camera_y // self.tile_size))
        end_y = int((camera_y + screen_height) // self.tile_size) + 1

        # 화면 범위 안의 타일만 반복 연산
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.map_data.get((x, y))
                if tile:
                    # 화면 절대 좌표 계산 (카메라 오프셋 적용)
                    screen_x = x * self.tile_size - camera_x
                    screen_y = y * self.tile_size - camera_y

                    # 이미지 풀(Pool)에서 미리 로드된 이미지를 가져와 블릿(Blit)
                    tile_img = self.tile_images[tile.tile_type]
                    surface.blit(tile_img, (screen_x, screen_y))

    def get_tile_at(self, tile_x, tile_y):
        """특정 좌표의 타일 데이터 가져오기 (충돌 및 피격 판정용)"""
        return self.map_data.get((tile_x, tile_y))
