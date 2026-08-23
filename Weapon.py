from dataclasses import dataclass
import time


@dataclass(frozen=True)
class WeaponConfig:
    name: str
    damage: int
    magazine_size: int
    reserve_ammo: int
    fire_interval: float
    bullet_size: int = 5
    bullet_speed: float = 15.0
    pellets: int = 1
    spread_degrees: float = 0.0
    projectile: bool = True
    vision_shape: str = "cone"
    vision_radius: float = 450.0
    vision_fov: float = 90.0
    vision_width: float = 220.0


WEAPONS = {
    "pistol": WeaponConfig("권총", damage=8, magazine_size=12, reserve_ammo=36, fire_interval=0.25, vision_radius=500, vision_fov=95, vision_width=240),
    "rifle": WeaponConfig("라이플", damage=12, magazine_size=20, reserve_ammo=60, fire_interval=0.14, vision_radius=700, vision_fov=75, vision_width=180),
    "shotgun": WeaponConfig(
        "샷건", damage=5, magazine_size=5, reserve_ammo=15,
        fire_interval=0.85, pellets=10, spread_degrees=32.0,
        vision_radius=300, vision_fov=120, vision_width=300,
    ),
    "sniper": WeaponConfig("저격총", damage=30, magazine_size=5, reserve_ammo=15, fire_interval=1.0, vision_shape="line", vision_radius=2000, vision_width=32),
    "smg": WeaponConfig("기관단총", damage=5, magazine_size=50, reserve_ammo=100, fire_interval=0.08, vision_radius=400, vision_fov=130, vision_width=260),
    "knife": WeaponConfig("칼", damage=50, magazine_size=0, reserve_ammo=0, fire_interval=0.5, projectile=False, vision_radius=180, vision_fov=180, vision_width=160),
}

WEAPON_KEYS = ("pistol", "rifle", "shotgun", "sniper", "smg", "knife")


class WeaponState:
    def __init__(self, weapon_id="pistol"):
        self.weapon_id = weapon_id
        self.magazine_ammo = WEAPONS[weapon_id].magazine_size
        self.reserve_ammo = WEAPONS[weapon_id].reserve_ammo
        self.last_fired_at = 0.0

    @property
    def config(self):
        return WEAPONS[self.weapon_id]

    def select(self, weapon_id):
        if weapon_id not in WEAPONS or weapon_id == self.weapon_id:
            return False
        self.weapon_id = weapon_id
        config = self.config
        self.magazine_ammo = config.magazine_size
        self.reserve_ammo = config.reserve_ammo
        self.last_fired_at = 0.0
        return True

    def can_fire(self):
        now = time.monotonic()
        return (
            self.config.projectile
            and self.magazine_ammo > 0
            and now - self.last_fired_at >= self.config.fire_interval
        )

    def consume_round(self):
        self.magazine_ammo -= 1
        self.last_fired_at = time.monotonic()

    def reload(self):
        missing = self.config.magazine_size - self.magazine_ammo
        loaded = min(missing, self.reserve_ammo)
        self.magazine_ammo += loaded
        self.reserve_ammo -= loaded
        return loaded

    def ammo_text(self):
        return f"{self.magazine_ammo}/{self.reserve_ammo}"
