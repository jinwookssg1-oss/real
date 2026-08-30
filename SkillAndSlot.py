import pygame

# 글로벌 이미지 로더
image_loader = None

def set_image_loader(loader):
    global image_loader
    image_loader = loader



FONT = None
SKILL_WINDOW_IMAGE = None
QUICK_SLOT_IMAGE = None
SKILL_SLOT_IMAGE = None
SKILL_PANEL_IMAGE = None

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (70, 70, 70)
RED = (255, 100, 100)
BLUE = (100, 100, 255)
YELLOW = (255, 255, 100)


def get_font():
    global FONT
    if FONT is None:
        FONT = pygame.font.SysFont("malgungothic", 14)
    return FONT


def set_ui_assets(skill_window_image, quick_slot_image):
    global SKILL_WINDOW_IMAGE, QUICK_SLOT_IMAGE, SKILL_SLOT_IMAGE, SKILL_PANEL_IMAGE
    SKILL_WINDOW_IMAGE = pygame.transform.smoothscale(skill_window_image, (720, 320))
    SKILL_PANEL_IMAGE = pygame.transform.smoothscale(skill_window_image, (720, 180))
    QUICK_SLOT_IMAGE = pygame.transform.smoothscale(quick_slot_image, (80, 80))
    SKILL_SLOT_IMAGE = pygame.transform.smoothscale(quick_slot_image, (70, 70))


class Skill:
    def __init__(self, name, color, msg, power=10, ability=""):
        self.name = name
        self.color = color
        self.Power = power
        self.Ability = ability
        self.msg = msg

    def Atk(self):
        return self.msg

    def get_info(self):
        return f"{self.name} | 공격력: {self.Power} | 능력: {self.Ability}"


SKILL_BOOK = {
    "달팽이 세개": Skill("달팽이 세개", RED, "달팽이 껍질을 던졌습니다!", 15, "3개의 껍질을 던져 광범위 공격"),
    "레이징 블로우": Skill("레이징 블로우", BLUE, "전방의 적을 연속 베기합니다!", 25, "근거리 연속 공격, 최대 5회"),
    "헤이스트": Skill("헤이스트", YELLOW, "이동속도와 점프력이 상승합니다!", 0, "5초간 이동속도 2배 증가"),
    "매의 눈": Skill("매의 눈", (120, 220, 255), "시야가 넓어집니다!", 0, "3초간 원형 시야"),
    "보호막": Skill("보호막", (100, 255, 180), "보호막이 생겼습니다!", 0, "5초간 피해 무효화"),
}


class SkillWindowItem:
    def __init__(self, x, y, skill_name):
        self.rect = pygame.Rect(x, y, 70, 70)
        self.skill_name = skill_name
        self.is_hovering = False

    def update(self, mouse_pos):
        self.is_hovering = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        global image_loader
        skill = SKILL_BOOK[self.skill_name]
        border_color = (255, 255, 0) if self.is_hovering else BLACK
        border_width = 3 if self.is_hovering else 2
        
        # 스킬 아이콘 이미지가 있으면 표시, 없으면 색상 박스 표시
        if SKILL_SLOT_IMAGE:
            surface.blit(SKILL_SLOT_IMAGE, self.rect)
        else:
            pygame.draw.rect(surface, skill.color, self.rect, border_radius=5)
        
        # 스킬 아이콘 이미지 표시
        if image_loader:
            skill_icon = image_loader.GetSkillIcon(self.skill_name)
            if skill_icon:
                surface.blit(skill_icon, self.rect)
            else:
                pygame.draw.rect(surface, skill.color, self.rect.inflate(-12, -12), border_radius=4)
                text = get_font().render(skill.name[:2], True, BLACK)
                surface.blit(text, text.get_rect(center=self.rect.center))
        else:
            pygame.draw.rect(surface, skill.color, self.rect.inflate(-12, -12), border_radius=4)
            text = get_font().render(skill.name[:2], True, BLACK)
            surface.blit(text, text.get_rect(center=self.rect.center))
        
        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=5)


class QuickSlot:
    def __init__(self, x, y, key_name):
        self.rect = pygame.Rect(x, y, 80, 80)
        self.key_name = key_name
        self.assigned_skill = None
        self.is_hovering = False

    def update(self, mouse_pos):
        self.is_hovering = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        global image_loader
        border_color = (255, 255, 100) if self.is_hovering else WHITE
        border_width = 3 if self.is_hovering else 2
        if QUICK_SLOT_IMAGE:
            surface.blit(QUICK_SLOT_IMAGE, self.rect)
        else:
            pygame.draw.rect(surface, DARK_GRAY, self.rect, border_radius=5)

        content_rect = self.rect.inflate(-12, -12)
        if self.assigned_skill:
            skill = SKILL_BOOK[self.assigned_skill]
            
            # 스킬 아이콘 이미지가 있으면 표시
            if image_loader:
                skill_icon = image_loader.GetSkillIcon(self.assigned_skill)
                if skill_icon:
                    surface.blit(skill_icon, self.rect)
                else:
                    pygame.draw.rect(surface, skill.color, content_rect, border_radius=4)
                    text = get_font().render(skill.name[:2], True, BLACK)
                    surface.blit(text, text.get_rect(center=(self.rect.centerx, self.rect.centery + 5)))
                    power_text = pygame.font.SysFont("malgungothic", 12).render(f"P:{skill.Power}", True, BLACK)
                    surface.blit(power_text, (self.rect.x + 5, self.rect.bottom - 20))
            else:
                pygame.draw.rect(surface, skill.color, content_rect, border_radius=4)
                text = get_font().render(skill.name[:2], True, BLACK)
                surface.blit(text, text.get_rect(center=(self.rect.centerx, self.rect.centery + 5)))
                power_text = pygame.font.SysFont("malgungothic", 12).render(f"P:{skill.Power}", True, BLACK)
                surface.blit(power_text, (self.rect.x + 5, self.rect.bottom - 20))
        else:
            text = get_font().render("EMPTY", True, (150, 150, 150))
            surface.blit(text, text.get_rect(center=self.rect.center))

        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=5)
        key_text = get_font().render(self.key_name, True, border_color)
        surface.blit(key_text, (self.rect.x + 8, self.rect.y + 5))


skill_window = [
    SkillWindowItem(630, 150, "달팽이 세개"),
    SkillWindowItem(860, 150, "레이징 블로우"),
    SkillWindowItem(1090, 150, "헤이스트"),
    SkillWindowItem(630, 240, "매의 눈"),
    SkillWindowItem(860, 240, "보호막"),
]
quick_slots = [
    QuickSlot(880, 920, "Q"),
    QuickSlot(980, 920, "E"),
    QuickSlot(1080, 920, "T"),
]

dragging_skill = None
drag_offset_x = 0
drag_offset_y = 0
mouse_pos = (0, 0)
system_message = "K를 눌러 스킬 창을 열고, 스킬을 드래그해서 하단 슬롯에 장착하세요!"

SKILL_PANEL_RECT = pygame.Rect(600, 870, 720, 180)
SKILL_SOURCE_RECT = pygame.Rect(600, 30, 720, 320)


def draw_skill_panel(surface):
    if SKILL_PANEL_IMAGE:
        surface.blit(SKILL_PANEL_IMAGE, SKILL_PANEL_RECT)
    else:
        pygame.draw.rect(surface, (30, 30, 50), SKILL_PANEL_RECT, border_radius=10)


def draw_skill_window(surface, mouse_pos, is_window_open, dragging_skill):
    if not is_window_open:
        return None

    if SKILL_WINDOW_IMAGE:
        surface.blit(SKILL_WINDOW_IMAGE, SKILL_SOURCE_RECT)
    else:
        pygame.draw.rect(surface, (30, 30, 50), SKILL_SOURCE_RECT, border_radius=10)
    title = pygame.font.SysFont("malgungothic", 16).render("스킬 도감", True, (100, 200, 255))
    surface.blit(title, (SKILL_SOURCE_RECT.x + 15, SKILL_SOURCE_RECT.y + 10))

    hovered_skill = None
    for item in skill_window:
        item.update(mouse_pos)
        item.draw(surface)
        if item.is_hovering:
            hovered_skill = item.skill_name

    if dragging_skill:
        skill = SKILL_BOOK[dragging_skill]
        drag_rect = pygame.Rect(mouse_pos[0] - 35, mouse_pos[1] - 35, 70, 70)
        drag_surface = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.rect(drag_surface, (*skill.color, 200), drag_surface.get_rect(), border_radius=5)
        pygame.draw.rect(drag_surface, (255, 200, 0), drag_surface.get_rect(), 2, border_radius=5)
        surface.blit(drag_surface, drag_rect)
        text = get_font().render(skill.name[:2], True, BLACK)
        surface.blit(text, text.get_rect(center=drag_rect.center))

    guide = pygame.font.SysFont("malgungothic", 11).render("드래그해서 장착!", True, (150, 150, 200))
    surface.blit(guide, (SKILL_SOURCE_RECT.x + 20, SKILL_SOURCE_RECT.bottom - 25))
    return hovered_skill


def draw_skill_tooltip(surface, mouse_pos, skill_name):
    if skill_name is None:
        return
    skill = SKILL_BOOK[skill_name]
    font = pygame.font.SysFont("malgungothic", 12)
    lines = [f"{skill.name}", f"공격력: {skill.Power}", skill.Ability]
    rendered = [font.render(line, True, WHITE) for line in lines]
    padding = 10
    width = max(text.get_width() for text in rendered) + padding * 2
    height = sum(text.get_height() for text in rendered) + padding * 2 + 5
    x = min(mouse_pos[0] + 20, 1920 - width - 10)
    y = min(mouse_pos[1] - 10, 1080 - height - 10)
    rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (20, 20, 40), rect, border_radius=5)
    pygame.draw.rect(surface, skill.color, rect, 2, border_radius=5)
    offset = y + padding
    for text in rendered:
        surface.blit(text, (x + padding, offset))
        offset += text.get_height() + 3
