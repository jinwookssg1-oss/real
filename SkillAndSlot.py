import pygame
import sys
from Tool_Cordinate import *


# [수정] 전역 font 변수는 선언만 해두고, 초기화는 지연시킵니다.
FONT = None

def get_font():
    """pygame.init()이 호출된 이후에 안전하게 폰트를 가져오는 헬퍼 함수"""
    global FONT
    if FONT is None:
        try:
            # 메인에서 이미 init을 했으므로 안전하게 호출됩니다.
            FONT = pygame.font.SysFont("malgungothic", 14)
        except:
            FONT = pygame.font.SysFont("arial", 14)
    return FONT

# 색상 정의
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
DARK_GRAY = (70, 70, 70)
BLACK = (0, 0, 0)
RED = (255, 100, 100)
BLUE = (100, 100, 255)
YELLOW = (255, 255, 100)

class Skill:
    def __init__(self, name, color, msg, power=10, ability=""):
        self.name = name
        self.color = color
        self.Power = power  # 스킬의 공격력
        self.Ability = ability  # 스킬의 특수 능력 설명
        self.msg = msg  # 스킬 사용 메시지
    
    def Atk(self):
        return self.msg
    
    def get_info(self):
        """스킬 정보 반환"""
        return f"{self.name} | 공격력: {self.Power} | 능력: {self.Ability}"

# 사용할 스킬 도감
SKILL_BOOK = {
    "달팽이 세개": Skill("달팽이 세개", RED, "🐚 달팽이 껍질을 던졌습니다!", power=15, ability="3개의 껍질을 던져 광범위 공격"),
    "레이징 블로우": Skill("레이징 블로우", BLUE, "⚔️ 전방의 적을 연속 베기합니다!", power=25, ability="근거리 연속 공격, 최대 5회"),
    "헤이스트": Skill("헤이스트", YELLOW, "🏃 이동속도와 점프력이 상승합니다!", power=0, ability="5초간 이동속도 2배 증가")
}

# 3. UI 컴포넌트 클래스
class SkillWindowItem:
    """스킬창(K) 내부에 고정되어 있는 스킬 항목"""
    def __init__(self, x, y, skill_name):
        self.rect = pygame.Rect(x, y, 70, 70)
        self.skill_name = skill_name
        self.is_hovering = False  # 마우스 호버 상태

    def update(self, mouse_pos):
        """마우스 호버 상태 업데이트"""
        self.is_hovering = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        skill = SKILL_BOOK[self.skill_name]
        
        # 호버 상태에 따라 다른 색상
        border_color = (255, 255, 0) if self.is_hovering else BLACK
        border_width = 3 if self.is_hovering else 2
        
        pygame.draw.rect(surface, skill.color, self.rect, border_radius=5)
        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=5)
        
        # 안전하게 폰트를 호출하여 렌더링
        font_obj = get_font()
        text = font_obj.render(skill.name[:2], True, BLACK)  # 처음 2글자 표시
        surface.blit(text, (self.rect.centerx - text.get_width()//2, self.rect.centery - text.get_height()//2))

class QuickSlot:
    """화면 하단의 단축키 슬롯 (Q, W, E 등)"""
    def __init__(self, x, y, key_name):
        self.rect = pygame.Rect(x, y, 80, 80)
        self.key_name = key_name
        self.assigned_skill = None  # 장착된 스킬 이름
        self.is_hovering = False  # 마우스 호버 상태

    def update(self, mouse_pos):
        """마우스 호버 상태 업데이트"""
        self.is_hovering = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        # 호버 상태에 따라 테두리 강조
        border_color = (255, 255, 100) if self.is_hovering else WHITE
        border_width = 3 if self.is_hovering else 2
        
        # 슬롯 배경
        pygame.draw.rect(surface, DARK_GRAY, self.rect, border_radius=5)
        
        # 안전하게 폰트를 호출
        font_obj = get_font()
        small_font = pygame.font.SysFont("malgungothic", 12)

        # 스킬이 장착되어 있다면 스킬 색상으로 채움
        if self.assigned_skill:
            skill = SKILL_BOOK[self.assigned_skill]
            pygame.draw.rect(surface, skill.color, self.rect, border_radius=5)
            
            # 스킬 이름 글자 표시
            text = font_obj.render(skill.name[:2], True, BLACK)
            text_rect = text.get_rect(center=(self.rect.centerx, self.rect.centery + 5))
            surface.blit(text, text_rect)
            
            # 공격력 표시
            power_text = small_font.render(f"P:{skill.Power}", True, BLACK)
            surface.blit(power_text, (self.rect.x + 5, self.rect.y + self.rect.height - 20))
        else:
            # 비어있을 때는 "EMPTY" 표시
            empty_text = font_obj.render("EMPTY", True, (150, 150, 150))
            empty_rect = empty_text.get_rect(center=(self.rect.centerx, self.rect.centery))
            surface.blit(empty_text, empty_rect)
        
        # 슬롯 테두리 및 단축키 이름 표시
        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=5)
        key_text = font_obj.render(self.key_name, True, border_color)
        surface.blit(key_text, (self.rect.x + 8, self.rect.y + 5))

# 4. UI 인스턴스 배치
# 스킬창 아이템 등록 (우측 상단 배치)
skill_window = [
    SkillWindowItem(1650, 50, "달팽이 세개"),
    SkillWindowItem(1650, 130, "레이징 블로우"),
    SkillWindowItem(1650, 210, "헤이스트")
]

# 하단 단축키 슬롯 등록 (Q, W, E)
quick_slots = [
    QuickSlot(1650, 500, "Q"),
    QuickSlot(1760, 500, "W"),
    QuickSlot(1870, 500, "E")
]

# 5. 드래그 앤 드롭 상태 변수
dragging_skill = None  # 현재 드래그 중인 스킬 이름
drag_offset_x = 0
drag_offset_y = 0
mouse_pos = (0, 0)
system_message = "🎮 K를 눌러 스킬 창을 열고, 스킬을 드래그해서 하단 슬롯(Q,W,E)에 장착하세요!"

def draw_skill_window(surface, mouse_pos, is_window_open, dragging_skill):
    """스킬 창 패널 그리기"""
    if not is_window_open:
        return None  # 툴팁 없음
    
    # 스킬 창 배경 패널
    panel_x, panel_y = 1630, 30
    panel_width, panel_height = 220, 300
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    
    # 배경
    pygame.draw.rect(surface, (30, 30, 50), panel_rect, border_radius=10)
    # 테두리
    pygame.draw.rect(surface, (100, 150, 255), panel_rect, 3, border_radius=10)
    
    # 제목
    font_obj = get_font()
    title_font = pygame.font.SysFont("malgungothic", 16)
    title = title_font.render("📖 스킬 도감", True, (100, 200, 255))
    surface.blit(title, (panel_x + 15, panel_y + 10))
    
    # 각 스킬 아이템 그리기
    hovered_skill = None  # 현재 호버된 스킬
    for item in skill_window:
        item.update(mouse_pos)
        item.draw(surface)
        if item.is_hovering:
            hovered_skill = item.skill_name
    
    # 드래그 중인 스킬 마우스 따라가기
    if dragging_skill:
        skill = SKILL_BOOK[dragging_skill]
        drag_rect = pygame.Rect(mouse_pos[0] - 35, mouse_pos[1] - 35, 70, 70)
        
        # 반투명 배경
        drag_surface = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.rect(drag_surface, (*skill.color, 200), drag_surface.get_rect(), border_radius=5)
        pygame.draw.rect(drag_surface, (255, 200, 0), drag_surface.get_rect(), 2, border_radius=5)
        
        surface.blit(drag_surface, drag_rect)
        
        # 스킬 이름
        text = font_obj.render(skill.name[:2], True, BLACK)
        text_rect = text.get_rect(center=drag_rect.center)
        surface.blit(text, text_rect)
    
    # 안내 문구
    guide_font = pygame.font.SysFont("malgungothic", 11)
    guide_text = guide_font.render("드래그해서 장착!", True, (150, 150, 200))
    surface.blit(guide_text, (panel_x + 20, panel_y + panel_height - 25))
    
    return hovered_skill  # 호버된 스킬 반환

def draw_skill_tooltip(surface, mouse_pos, skill_name):
    """스킬 툴팁 그리기 (마우스 클릭 불가능)"""
    if skill_name is None:
        return
    
    skill = SKILL_BOOK[skill_name]
    font_obj = get_font()
    tooltip_font = pygame.font.SysFont("malgungothic", 12)
    
    # 툴팁 텍스트 생성
    lines = [
        f"📋 {skill.name}",
        f"⚔️ 공격력: {skill.Power}",
        f"✨ {skill.Ability}"
    ]
    
    # 텍스트 크기 계산
    max_width = 0
    text_surfaces = []
    for line in lines:
        text_surf = tooltip_font.render(line, True, WHITE)
        text_surfaces.append(text_surf)
        max_width = max(max_width, text_surf.get_width())
    
    # 툴팁 배경 크기 계산
    tooltip_padding = 10
    tooltip_width = max_width + tooltip_padding * 2
    tooltip_height = sum(t.get_height() for t in text_surfaces) + tooltip_padding * 2 + 5
    
    # 마우스 위치에서 약간 옆에 표시
    tooltip_x = min(mouse_pos[0] + 20, 1920 - tooltip_width - 10)
    tooltip_y = min(mouse_pos[1] - 10, 1080 - tooltip_height - 10)
    
    tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
    
    # 툴팁 배경 그리기
    pygame.draw.rect(surface, (20, 20, 40), tooltip_rect, border_radius=5)
    pygame.draw.rect(surface, skill.color, tooltip_rect, 2, border_radius=5)
    
    # 텍스트 그리기
    y_offset = tooltip_y + tooltip_padding
    for text_surf in text_surfaces:
        surface.blit(text_surf, (tooltip_x + tooltip_padding, y_offset))
        y_offset += text_surf.get_height() + 3
