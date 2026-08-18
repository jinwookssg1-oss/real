import pygame
import time

class Skill:
    def __init__(self, name, attack_power, icon_color=(200,50,50), radius=80):
        self.name = name
        self.attack_power = attack_power
        self.icon_color = icon_color
        self.radius = radius
        # 아이콘은 간단한 원으로 표시
        self.icon = None

    def get_icon(self, size=48):
        if self.icon is None:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, self.icon_color, (size//2, size//2), size//2 - 4)
            font = pygame.font.SysFont("malgungothic", 14)
            txt = font.render(self.name[:2], True, (255,255,255))
            txt_rect = txt.get_rect(center=(size//2, size//2))
            surf.blit(txt, txt_rect)
            self.icon = surf
        return self.icon

    def activate(self, player, world, skill_effects):
        """스킬이 발동되었을 때 동작. 현재는 시각적 에펙트만 생성하고, 공격력/범위를 함께 기록합니다.

        - player: Player 인스턴스 (발동 위치 기준)
        - world: 호출자가 원하는 임의 객체(여기서는 필요 없음)
        - skill_effects: 리스트에 효과 정보를 추가하면 Game 루프가 그려줌
        """
        center_x = player.X + (player.rect.width // 2)
        center_y = player.Y + (player.rect.height // 2)
        effect = {
            "x": center_x,
            "y": center_y,
            "radius": self.radius,
            "power": self.attack_power,
            "time": pygame.time.get_ticks(),
            "duration": 500, # ms
            "color": self.icon_color,
            "name": self.name,
        }
        skill_effects.append(effect)
        print(f"Skill activated: {self.name} (power={self.attack_power})")
        # 실제 게임 로직(데미지 적용 등)은 여기서 확장할 수 있습니다.
        return effect
