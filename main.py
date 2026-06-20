"""
Mortal Combat Reborn
---------------------
An original, code-drawn 2D fighting prototype built with Pygame.
No copyrighted characters, sprite sheets, audio, or stage art are used.

Run:
    pip install -r requirements.txt
    python main.py
"""

from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pygame

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
WIDTH, HEIGHT = 1280, 720
FPS = 60
FLOOR_Y = 590
STAGE_LEFT, STAGE_RIGHT = 70, WIDTH - 70
ROUND_SECONDS = 99
GRAVITY = 1850

COLORS = {
    "ink": (8, 11, 22),
    "text": (239, 244, 255),
    "muted": (163, 174, 204),
    "cyan": (75, 238, 255),
    "magenta": (255, 79, 205),
    "gold": (255, 204, 83),
    "green": (100, 242, 151),
    "red": (255, 84, 112),
    "purple": (157, 115, 255),
    "dark_panel": (18, 24, 48),
    "panel": (26, 35, 67),
    "white": (255, 255, 255),
}

# Simplified controls: each player has one punch, one kick, one grab,
# one parry/block key, and one super key. Holding the parry key blocks;
# pressing it just before impact creates a parry window.
P1_CONTROLS = {
    "left": pygame.K_a,
    "right": pygame.K_d,
    "up": pygame.K_w,
    "down": pygame.K_s,
    "punch": pygame.K_f,
    "kick": pygame.K_r,
    "block": pygame.K_q,
    "grab": pygame.K_t,
    "super": pygame.K_e,
}

P2_CONTROLS = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "punch": pygame.K_p,
    "kick": pygame.K_k,
    "block": pygame.K_m,
    "grab": pygame.K_o,
    "super": pygame.K_l,
}

ATTACKS: Dict[str, Dict[str, float | int | str | bool]] = {
    "lp": {"startup": 0.03, "active": 0.18, "recovery": 0.12, "damage": 7, "reach": 104, "height": "mid", "kb": 145, "meter": 8, "color": "cyan"},
    "hp": {"startup": 0.11, "active": 0.16, "recovery": 0.20, "damage": 11, "reach": 118, "height": "mid", "kb": 245, "meter": 12, "color": "cyan"},
    "lk": {"startup": 0.04, "active": 0.16, "recovery": 0.14, "damage": 8, "reach": 108, "height": "low", "kb": 165, "meter": 9, "color": "magenta"},
    "hk": {"startup": 0.12, "active": 0.17, "recovery": 0.23, "damage": 14, "reach": 132, "height": "mid", "kb": 325, "meter": 15, "color": "magenta"},
    "air_kick": {"startup": 0.04, "active": 0.12, "recovery": 0.10, "damage": 8, "reach": 65, "height": "air", "kb": 170, "meter": 9, "color": "gold"},
    "launcher": {"startup": 0.18, "active": 0.11, "recovery": 0.30, "damage": 11, "reach": 78, "height": "mid", "kb": 160, "meter": 16, "launch": True, "color": "purple"},
    "fireball": {"startup": 0.17, "active": 0.02, "recovery": 0.22, "damage": 9, "reach": 0, "height": "projectile", "kb": 245, "meter": 13, "projectile": True, "color": "gold"},
    "super": {"startup": 0.35, "active": 0.13, "recovery": 0.45, "damage": 28, "reach": 128, "height": "mid", "kb": 520, "meter": 0, "super": True, "color": "red"},
}

# Original, selectable arenas. Each one is code-drawn so the game stays asset-free.
STAGES = [
    {
        "name": "NEON ROOFTOP",
        "subtitle": "Rainy cyber-city above the electric skyline",
        "top": (12, 16, 42), "bottom": (47, 17, 74),
        "far": (15, 19, 45), "floor": (13, 16, 33), "grid": (39, 75, 117),
        "line": (75, 238, 255), "accent": (255, 79, 205), "hazard": (255, 84, 112),
        "kind": "city",
    },
    {
        "name": "EMBER TEMPLE",
        "subtitle": "Ancient stone courtyard lit by ceremonial fire",
        "top": (61, 18, 18), "bottom": (119, 50, 22),
        "far": (44, 20, 18), "floor": (46, 30, 26), "grid": (117, 62, 38),
        "line": (255, 179, 69), "accent": (255, 96, 76), "hazard": (255, 157, 55),
        "kind": "temple",
    },
    {
        "name": "ARCTIC HANGAR",
        "subtitle": "Frozen research bay under a polar aurora",
        "top": (7, 40, 69), "bottom": (19, 93, 119),
        "far": (10, 45, 72), "floor": (18, 43, 59), "grid": (92, 182, 207),
        "line": (142, 244, 255), "accent": (118, 175, 255), "hazard": (120, 228, 255),
        "kind": "arctic",
    },
    {
        "name": "VOID REACTOR",
        "subtitle": "A collapsing reactor chamber inside a deep-space station",
        "top": (28, 7, 45), "bottom": (10, 8, 28),
        "far": (24, 11, 39), "floor": (20, 13, 35), "grid": (104, 64, 173),
        "line": (177, 115, 255), "accent": (255, 75, 177), "hazard": (232, 88, 255),
        "kind": "reactor",
    },
]

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def sign(value: float) -> int:
    return 1 if value >= 0 else -1


def draw_text(surface: pygame.Surface, font: pygame.font.Font, text: str, pos: Tuple[int, int], color=COLORS["text"], anchor: str = "topleft", shadow: bool = False) -> pygame.Rect:
    image = font.render(text, True, color)
    rect = image.get_rect()
    setattr(rect, anchor, pos)
    if shadow:
        shadow_img = font.render(text, True, (0, 0, 0))
        shadow_rect = shadow_img.get_rect()
        setattr(shadow_rect, anchor, (pos[0] + 2, pos[1] + 2))
        surface.blit(shadow_img, shadow_rect)
    surface.blit(image, rect)
    return rect

# -----------------------------------------------------------------------------
# State classes
# -----------------------------------------------------------------------------

@dataclass
class ControlState:
    left: bool = False
    right: bool = False
    up: bool = False
    down: bool = False
    block: bool = False


@dataclass
class Projectile:
    owner: "Fighter"
    x: float
    y: float
    direction: int
    damage: float
    speed: float = 630
    ttl: float = 2.1
    radius: float = 13
    color: Tuple[int, int, int] = COLORS["gold"]

    def update(self, dt: float) -> None:
        self.x += self.speed * self.direction * dt
        self.ttl -= dt

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), int(self.radius * 2), int(self.radius * 2))

    def draw(self, surface: pygame.Surface) -> None:
        glow = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, 48), (35, 35), 30)
        pygame.draw.circle(glow, (*self.color, 100), (35, 35), 20)
        surface.blit(glow, (self.x - 35, self.y - 35))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius))
        pygame.draw.circle(surface, COLORS["white"], (int(self.x + 3 * self.direction), int(self.y - 3)), 4)


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    life: float
    size: float

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 240 * dt
        self.life -= dt


@dataclass
class Fighter:
    name: str
    color: Tuple[int, int, int]
    accent: Tuple[int, int, int]
    x: float
    y: float
    facing: int
    controls: Dict[str, int]
    is_cpu: bool = False
    skin: Tuple[int, int, int] = (220, 167, 121)
    hair: Tuple[int, int, int] = (26, 21, 31)
    health: float = 100.0
    meter: float = 0.0
    guard: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    width: int = 54
    height: int = 122
    grounded: bool = True
    crouching: bool = False
    blocking: bool = False
    parry_window: float = 0.0
    stun: float = 0.0
    attack: Optional[Dict] = None
    dash_time: float = 0.0
    dash_dir: int = 0
    invuln: float = 0.0
    combo_hits: int = 0
    combo_timer: float = 0.0
    received_combo_hits: int = 0
    breaker_ready: float = 0.0
    last_attacker: Optional["Fighter"] = None
    command_log: deque = field(default_factory=lambda: deque(maxlen=8))
    direction_taps: Dict[int, float] = field(default_factory=dict)
    grab_pressed_time: float = -10.0
    flash: float = 0.0
    afterimages: List[Tuple[float, float, float]] = field(default_factory=list)
    ai_action_timer: float = 0.0
    queued_attack: Optional[str] = None

    @property
    def rect(self) -> pygame.Rect:
        current_height = 84 if self.crouching and self.grounded else self.height
        return pygame.Rect(int(self.x - self.width / 2), int(self.y - current_height), self.width, current_height)

    def head_y(self) -> float:
        return self.rect.top + 20

    def reset_for_round(self, x: float, facing: int) -> None:
        self.x = x
        self.y = FLOOR_Y
        self.facing = facing
        self.health = 100.0
        self.meter = 0.0
        self.guard = 0.0
        self.vx = self.vy = 0.0
        self.grounded = True
        self.crouching = False
        self.blocking = False
        self.parry_window = 0
        self.stun = 0
        self.attack = None
        self.dash_time = 0
        self.invuln = 0
        self.combo_hits = 0
        self.combo_timer = 0
        self.received_combo_hits = 0
        self.breaker_ready = 0
        self.last_attacker = None
        self.command_log.clear()
        self.flash = 0
        self.afterimages.clear()
        self.queued_attack = None

    def record_direction(self, direction_key: str, absolute_dir: int, now: float) -> None:
        # "forward" and "back" are relative to the opponent.
        relative = "forward" if absolute_dir == self.facing else "back"
        self.command_log.append((relative, now))
        last = self.direction_taps.get(absolute_dir, -100)
        if now - last < 0.24 and self.grounded and self.stun <= 0 and self.attack is None:
            self.dash_time = 0.16
            self.dash_dir = absolute_dir
            self.vx = absolute_dir * 550
        self.direction_taps[absolute_dir] = now

    def record_down(self, now: float) -> None:
        self.command_log.append(("down", now))

    def command_recent(self, keys: List[str], now: float, window: float = 0.55) -> bool:
        filtered = [(k, t) for k, t in self.command_log if now - t <= window]
        index = 0
        for key, _ in filtered:
            if index < len(keys) and key == keys[index]:
                index += 1
        return index == len(keys)

    def start_attack(self, attack_name: str, now: float) -> None:
        """Start an action immediately or buffer it so simple button presses never disappear."""
        if self.stun > 0 or self.invuln > 0:
            return
        if self.attack:
            # One buffered action gives the game a responsive arcade feel when F/R is tapped quickly.
            if attack_name in ("lp", "lk", "hp", "hk"):
                self.queued_attack = attack_name
            return
        if not self.grounded and attack_name in ("lp", "hp", "lk", "hk"):
            attack_name = "air_kick"
        info = ATTACKS[attack_name]
        self.attack = {
            "name": attack_name,
            "elapsed": 0.0,
            "hit": False,
            "projectile_spawned": False,
            "info": info,
        }
        self.crouching = False
        self.blocking = False
        if attack_name == "super":
            self.meter = 0.0

    def can_use_super(self) -> bool:
        return self.meter >= 100 and self.attack is None and self.stun <= 0

    def current_hitbox(self) -> Optional[pygame.Rect]:
        if not self.attack:
            return None
        info = self.attack["info"]
        elapsed = self.attack["elapsed"]
        startup = float(info["startup"])
        active_end = startup + float(info["active"])
        if not startup <= elapsed <= active_end or info.get("projectile"):
            return None

        reach = int(info["reach"])
        height = str(info["height"])
        h = 48 if height == "low" else 58
        if height == "low":
            y = self.rect.bottom - 50
        elif height == "air":
            y = self.rect.centery - 18
        else:
            y = self.rect.top + 26
        x = self.rect.right - 4 if self.facing == 1 else self.rect.left - reach + 4
        return pygame.Rect(x, y, reach, h)

    def update(self, dt: float, controls: ControlState, opponent: "Fighter", game: "Game") -> None:
        self.facing = 1 if opponent.x > self.x else -1
        self.parry_window = max(0.0, self.parry_window - dt)
        self.stun = max(0.0, self.stun - dt)
        self.invuln = max(0.0, self.invuln - dt)
        self.flash = max(0.0, self.flash - dt)
        self.breaker_ready = max(0.0, self.breaker_ready - dt)
        self.combo_timer = max(0.0, self.combo_timer - dt)
        if self.combo_timer <= 0:
            self.combo_hits = 0

        self.afterimages = [(x, y, life - dt) for x, y, life in self.afterimages if life - dt > 0]

        if self.guard > 0 and not self.blocking:
            self.guard = max(0, self.guard - 22 * dt)

        if self.attack:
            self.attack["elapsed"] += dt
            info = self.attack["info"]
            if info.get("projectile") and not self.attack["projectile_spawned"] and self.attack["elapsed"] >= float(info["startup"]):
                self.attack["projectile_spawned"] = True
                game.projectiles.append(
                    Projectile(
                        owner=self,
                        x=self.x + self.facing * 42,
                        y=self.head_y() + 24,
                        direction=self.facing,
                        damage=float(info["damage"]),
                        color=COLORS[str(info["color"])],
                    )
                )
                game.spawn_particles(self.x + self.facing * 34, self.head_y() + 24, COLORS[str(info["color"])], 16, 90)
            total = float(info["startup"]) + float(info["active"]) + float(info["recovery"])
            if self.attack["elapsed"] >= total:
                self.attack = None
                if self.queued_attack:
                    queued = self.queued_attack
                    self.queued_attack = None
                    self.start_attack(queued, game.stage_time)

        if self.stun <= 0 and self.attack is None:
            self.crouching = controls.down and self.grounded
            moving_left = controls.left
            moving_right = controls.right
            desired = (-1 if moving_left else 0) + (1 if moving_right else 0)

            backward_held = (self.facing == 1 and moving_left) or (self.facing == -1 and moving_right)
            self.blocking = controls.block or (backward_held and not self.crouching and desired != 0)

            if self.dash_time > 0:
                self.dash_time -= dt
                self.vx = self.dash_dir * 550
                self.afterimages.append((self.x, self.y, 0.28))
            elif desired:
                max_speed = 260 if self.grounded else 180
                accel = 1700 if self.grounded else 680
                self.vx += (desired * max_speed - self.vx) * min(1.0, accel * dt / max_speed)
            else:
                friction = 0.75 if self.grounded else 0.93
                self.vx *= friction
        else:
            self.blocking = False

        if not self.grounded:
            self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y >= FLOOR_Y:
            self.y = FLOOR_Y
            self.vy = 0
            self.grounded = True
        else:
            self.grounded = False

        self.x = clamp(self.x, STAGE_LEFT + self.width / 2, STAGE_RIGHT - self.width / 2)

    def jump(self, controls: ControlState) -> None:
        if self.grounded and self.stun <= 0 and self.attack is None:
            self.vy = -690
            self.grounded = False
            if controls.left:
                self.vx = -245
            elif controls.right:
                self.vx = 245

    def take_hit(self, attacker: "Fighter", info: Dict, game: "Game", source: str = "attack") -> bool:
        if self.invuln > 0:
            return False

        # A parry must be intentionally pressed right before impact.
        if self.parry_window > 0 and self.stun <= 0:
            attacker.stun = 0.48
            attacker.vx = -attacker.facing * 230
            self.meter = min(100, self.meter + 16)
            game.announce("PARRY!", COLORS["gold"], 0.55)
            game.spawn_particles(self.x, self.head_y() + 18, COLORS["gold"], 26, 190)
            return True

        height = str(info["height"])
        can_block = self.blocking and self.stun <= 0 and height != "low"
        if height == "low":
            can_block = self.blocking and self.crouching

        base_damage = float(info["damage"])
        if source == "projectile":
            can_block = self.blocking and not self.crouching

        if can_block:
            chip = max(1.0, base_damage * 0.14)
            self.health -= chip
            self.guard += base_damage * 1.25
            self.meter = min(100, self.meter + 4)
            attacker.meter = min(100, attacker.meter + 3)
            game.spawn_particles(self.x + self.facing * 18, self.head_y() + 34, COLORS["white"], 8, 65)
            if self.guard >= 42:
                self.guard = 0
                self.stun = 0.65
                self.blocking = False
                game.announce("GUARD BREAK!", COLORS["red"], 0.8)
            return True

        if self.last_attacker is attacker and self.combo_timer > 0:
            attacker.combo_hits += 1
        else:
            attacker.combo_hits = 1
        attacker.combo_timer = 1.25
        self.last_attacker = attacker
        self.received_combo_hits = attacker.combo_hits

        reduction = max(0.44, 1.0 - (attacker.combo_hits - 1) * 0.08)
        damage = base_damage * reduction
        self.health -= damage
        attacker.meter = min(100, attacker.meter + float(info.get("meter", 8)))
        self.meter = min(100, self.meter + damage * 0.72)
        self.flash = 0.16
        self.stun = 0.20 + damage * 0.012
        self.vx = attacker.facing * float(info["kb"])
        self.vy = -230 if info.get("launch") else self.vy
        if info.get("launch"):
            self.vy = -610
            self.grounded = False
        if info.get("super"):
            self.stun = 0.82
            game.freeze_frames = 0.15
            game.announce("FINISH SEQUENCE!" if info.get("finisher") else "RESONANCE BREAK!", COLORS["red"], 0.9)

        if self.received_combo_hits >= 6:
            self.breaker_ready = 1.35

        impact_color = COLORS[str(info["color"])]
        game.spawn_particles(self.x - attacker.facing * 10, self.head_y() + 28, impact_color, 20, 220)
        return True

    def try_breaker(self, game: "Game") -> bool:
        if self.breaker_ready <= 0 or self.stun <= 0 or not self.last_attacker:
            return False
        attacker = self.last_attacker
        attacker.stun = 0.9
        attacker.vx = -attacker.facing * 420
        attacker.vy = -320
        attacker.grounded = False
        self.stun = 0
        self.breaker_ready = 0
        self.meter = max(0, self.meter - 28)
        self.invuln = 0.22
        game.announce("COMBO BREAKER!", COLORS["purple"], 0.9)
        game.spawn_particles(self.x, self.head_y() + 32, COLORS["purple"], 36, 260)
        return True

    def draw(self, surface: pygame.Surface) -> None:
        """Draw a clean, original stick fighter with readable punch/kick poses."""
        line_w = 8
        body_color = COLORS["white"] if self.flash > 0 else self.color
        dark = tuple(max(0, c - 55) for c in body_color)
        rect = self.rect
        head = (int(self.x), int(rect.top + 18))
        neck = (int(self.x), int(rect.top + 37))
        shoulder = (int(self.x), int(rect.top + 48))
        hip = (int(self.x), int(rect.top + 83))

        # Ghost trail for dashes.
        for x, y, life in self.afterimages:
            alpha = int(86 * (life / 0.28))
            ghost = pygame.Surface((104, 150), pygame.SRCALPHA)
            cx, cy = 52, 35
            pygame.draw.circle(ghost, (*body_color, alpha), (cx, cy), 15, 4)
            pygame.draw.line(ghost, (*body_color, alpha), (cx, cy + 15), (cx, cy + 58), 6)
            pygame.draw.line(ghost, (*body_color, alpha), (cx, cy + 57), (cx - 18, cy + 93), 6)
            pygame.draw.line(ghost, (*body_color, alpha), (cx, cy + 57), (cx + 18, cy + 93), 6)
            surface.blit(ghost, (x - 52, y - 132))

        # Floor shadow.
        pygame.draw.ellipse(surface, (0, 0, 0), (int(self.x - 36), FLOOR_Y - 7, 72, 14))

        attack_name = self.attack["name"] if self.attack else ""
        punching = attack_name in ("lp", "hp", "fireball", "super", "launcher")
        kicking = attack_name in ("lk", "hk", "air_kick")
        heavy = attack_name in ("hp", "hk", "super", "launcher")
        active = self.attack and self.current_hitbox() is not None

        # Back leg / front leg. Kicks extend the forward leg fully.
        back_knee = (hip[0] - self.facing * 14, FLOOR_Y - 31)
        back_foot = (hip[0] - self.facing * 29, FLOOR_Y - 4)
        front_knee = (hip[0] + self.facing * 15, FLOOR_Y - 30)
        front_foot = (hip[0] + self.facing * 30, FLOOR_Y - 4)
        pygame.draw.line(surface, dark, hip, back_knee, line_w)
        pygame.draw.line(surface, dark, back_knee, back_foot, line_w)

        if kicking:
            kick_len = 122 if heavy else 96
            kick_end = (hip[0] + self.facing * kick_len, hip[1] - (18 if heavy else 6))
            pygame.draw.line(surface, body_color, hip, kick_end, line_w + 1)
            pygame.draw.circle(surface, self.accent, kick_end, 8)
            if active:
                pygame.draw.arc(surface, self.accent, (min(hip[0], kick_end[0]) - 18, kick_end[1] - 20,
                                                      abs(kick_end[0] - hip[0]) + 36, 56),
                                0.15 if self.facing == 1 else math.pi + 0.15,
                                math.pi - 0.15 if self.facing == 1 else math.tau - 0.15, 3)
        else:
            pygame.draw.line(surface, body_color, hip, front_knee, line_w)
            pygame.draw.line(surface, body_color, front_knee, front_foot, line_w)
        pygame.draw.line(surface, COLORS["white"], (back_foot[0] - 4, back_foot[1]), (back_foot[0] + 4, back_foot[1]), 3)
        if not kicking:
            pygame.draw.line(surface, COLORS["white"], (front_foot[0] - 4, front_foot[1]), (front_foot[0] + 4, front_foot[1]), 3)

        # Torso and circular head: intentionally simple stickman design.
        pygame.draw.line(surface, body_color, neck, hip, line_w + 1)
        pygame.draw.circle(surface, self.skin, head, 17)
        pygame.draw.circle(surface, body_color, head, 17, 4)
        eye = (head[0] + self.facing * 7, head[1] - 2)
        pygame.draw.circle(surface, COLORS["ink"], eye, 2)
        pygame.draw.line(surface, self.hair, (head[0] - 10, head[1] - 13), (head[0] + 10, head[1] - 13), 4)

        # Arms. The lead arm extends dramatically during F/P punch, which makes the input obvious.
        rear_elbow = (shoulder[0] - self.facing * 20, shoulder[1] + 22)
        rear_hand = (shoulder[0] - self.facing * 30, shoulder[1] + 43)
        pygame.draw.line(surface, dark, shoulder, rear_elbow, line_w)
        pygame.draw.line(surface, dark, rear_elbow, rear_hand, line_w)
        pygame.draw.circle(surface, dark, rear_hand, 6)

        if punching:
            reach = 126 if heavy else 98
            front_elbow = (shoulder[0] + self.facing * 33, shoulder[1] + (3 if heavy else 13))
            front_hand = (shoulder[0] + self.facing * reach, shoulder[1] + (0 if heavy else 13))
        else:
            front_elbow = (shoulder[0] + self.facing * 22, shoulder[1] + 20)
            front_hand = (shoulder[0] + self.facing * 34, shoulder[1] + 42)
        pygame.draw.line(surface, body_color, shoulder, front_elbow, line_w + 1)
        pygame.draw.line(surface, body_color, front_elbow, front_hand, line_w + 1)
        pygame.draw.circle(surface, self.accent, front_hand, 8)
        if active and punching:
            spark = (front_hand[0] + self.facing * 13, front_hand[1])
            pygame.draw.line(surface, COLORS["gold"], (spark[0] - 10, spark[1]), (spark[0] + 10, spark[1]), 3)
            pygame.draw.line(surface, COLORS["gold"], (spark[0], spark[1] - 10), (spark[0], spark[1] + 10), 3)

        if self.blocking:
            pygame.draw.arc(surface, COLORS["cyan"], (rect.x - 18, rect.y - 8, rect.width + 36, rect.height + 16),
                            math.pi * 0.62, math.pi * 1.38, 3)
        if self.breaker_ready > 0:
            pygame.draw.circle(surface, COLORS["purple"], (int(self.x), int(self.head_y() + 25)), 42, 2)


# -----------------------------------------------------------------------------
# Game controller
# -----------------------------------------------------------------------------

class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Mortal Combat Reborn")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = {
            "tiny": pygame.font.SysFont("consolas", 14, bold=True),
            "small": pygame.font.SysFont("arial", 20, bold=True),
            "medium": pygame.font.SysFont("arial", 32, bold=True),
            "large": pygame.font.SysFont("arial", 58, bold=True),
            "huge": pygame.font.SysFont("arial", 92, bold=True),
        }
        self.running = True
        self.mode = "title"  # title, stage_select, intro, fight, round_end, match_end
        self.vs_cpu = True
        self.pending_vs_cpu = True
        self.stage_index = 0
        self.round_no = 1
        self.wins = [0, 0]
        self.timer = float(ROUND_SECONDS)
        self.round_delay = 0.0
        self.message = ""
        self.message_color = COLORS["text"]
        self.message_timer = 0.0
        self.projectiles: List[Projectile] = []
        self.particles: List[Particle] = []
        self.freeze_frames = 0.0
        self.stage_time = 0.0
        self.p1 = Fighter("VOLT", COLORS["cyan"], COLORS["purple"], 315, FLOOR_Y, 1, P1_CONTROLS,
                          skin=(194, 132, 93), hair=(22, 18, 28))
        self.p2 = Fighter("NYX", COLORS["magenta"], COLORS["gold"], 965, FLOOR_Y, -1, P2_CONTROLS, is_cpu=True,
                          skin=(235, 186, 146), hair=(31, 20, 42))
        self.reset_round(announce=False)

    @property
    def stage(self) -> Dict:
        return STAGES[self.stage_index]

    def reset_round(self, announce: bool = True) -> None:
        self.p1.reset_for_round(330, 1)
        self.p2.reset_for_round(950, -1)
        self.projectiles.clear()
        self.particles.clear()
        self.timer = float(ROUND_SECONDS)
        self.round_delay = 1.4
        self.mode = "intro" if announce else "title"
        if announce:
            label = "FINAL ROUND" if self.round_no == 3 else f"ROUND {self.round_no}"
            self.announce(label, COLORS["gold"], 1.35)

    def start_match(self, vs_cpu: bool, stage_index: Optional[int] = None) -> None:
        self.vs_cpu = vs_cpu
        self.p2.is_cpu = vs_cpu
        if stage_index is not None:
            self.stage_index = stage_index % len(STAGES)
        self.wins = [0, 0]
        self.round_no = 1
        self.stage_time = 0.0
        self.reset_round(announce=True)

    def announce(self, message: str, color: Tuple[int, int, int], duration: float) -> None:
        self.message = message
        self.message_color = color
        self.message_timer = duration

    def spawn_particles(self, x: float, y: float, color: Tuple[int, int, int], count: int, speed: float) -> None:
        for _ in range(count):
            angle = random.random() * math.tau
            power = random.uniform(speed * 0.4, speed)
            self.particles.append(
                Particle(x, y, math.cos(angle) * power, math.sin(angle) * power, color, random.uniform(0.18, 0.5), random.uniform(2, 5))
            )

    def controls_for(self, fighter: Fighter, keys) -> ControlState:
        c = fighter.controls
        return ControlState(
            left=bool(keys[c["left"]]),
            right=bool(keys[c["right"]]),
            up=bool(keys[c["up"]]),
            down=bool(keys[c["down"]]),
            block=bool(keys[c["block"]]),
        )

    def cpu_controls(self, fighter: Fighter, opponent: Fighter, dt: float) -> ControlState:
        state = ControlState()
        fighter.ai_action_timer -= dt
        distance = opponent.x - fighter.x
        abs_distance = abs(distance)
        toward = 1 if distance > 0 else -1
        if abs_distance > 155:
            state.right = toward == 1
            state.left = toward == -1
        elif abs_distance < 92:
            state.left = toward == 1
            state.right = toward == -1

        if opponent.attack and random.random() < 0.16:
            state.block = True
        if fighter.ai_action_timer <= 0 and fighter.stun <= 0 and not fighter.attack:
            roll = random.random()
            if abs_distance > 240 and roll < 0.24:
                fighter.command_log.append(("down", self.stage_time))
                fighter.command_log.append(("forward", self.stage_time))
                fighter.start_attack("fireball", self.stage_time)
            elif abs_distance < 100 and roll < 0.26:
                fighter.start_attack(random.choice(["lp", "lk", "hp", "hk"]), self.stage_time)
            elif abs_distance < 170 and roll < 0.35:
                fighter.start_attack("launcher", self.stage_time)
            fighter.ai_action_timer = random.uniform(0.22, 0.55)
        if random.random() < 0.004 and fighter.grounded:
            fighter.jump(state)
        return state

    def handle_keydown(self, key: int) -> None:
        # ESC is always a quick exit path: it closes the game only from the
        # title screen and returns to the main menu from every other screen.
        if key == pygame.K_ESCAPE:
            if self.mode == "title":
                self.running = False
            else:
                self.mode = "title"
                self.message = ""
                self.message_timer = 0.0
                self.round_delay = 0.0
                self.projectiles.clear()
                self.particles.clear()
            return

        if self.mode == "title":
            if key in (pygame.K_1, pygame.K_2):
                self.pending_vs_cpu = key == pygame.K_1
                self.stage_index = 0
                self.mode = "stage_select"
            return
        if self.mode == "stage_select":
            if key in (pygame.K_LEFT, pygame.K_UP):
                self.stage_index = (self.stage_index - 1) % len(STAGES)
            elif key in (pygame.K_RIGHT, pygame.K_DOWN):
                self.stage_index = (self.stage_index + 1) % len(STAGES)
            elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                self.stage_index = key - pygame.K_1
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_match(self.pending_vs_cpu, self.stage_index)
            return
        if self.mode == "match_end":
            if key in (pygame.K_RETURN, pygame.K_r):
                self.mode = "title"
            return
        if self.mode not in ("fight", "intro"):
            return

        now = self.stage_time
        for fighter in (self.p1, self.p2):
            if fighter.is_cpu:
                continue
            c = fighter.controls
            if key == c["left"]:
                fighter.record_direction("left", -1, now)
            elif key == c["right"]:
                fighter.record_direction("right", 1, now)
            elif key == c["down"]:
                fighter.record_down(now)
            elif key == c["up"]:
                keys = pygame.key.get_pressed()
                fighter.jump(self.controls_for(fighter, keys))
            elif key == c["block"]:
                fighter.parry_window = 0.16
            elif key == c["grab"]:
                fighter.grab_pressed_time = now
                if not fighter.try_breaker(self):
                    self.try_grab(fighter)
            elif key == c["super"]:
                if fighter.can_use_super():
                    opponent = self.p2 if fighter is self.p1 else self.p1
                    fighter.start_attack("super", now)
                    # A full-meter super becomes a dramatic, non-graphic finisher
                    # when the opponent is critically low and within range.
                    if opponent.health <= 18 and abs(fighter.x - opponent.x) < 145:
                        fighter.attack["finisher"] = True
            elif key == c["punch"]:
                # F/P always mean punch. This makes the controls predictable and fixes missed input confusion.
                fighter.start_attack("lp", now)
            elif key == c["kick"]:
                # R/K always mean kick. Specials stay available only to the CPU in this beginner-friendly build.
                fighter.start_attack("lk", now)

    def try_grab(self, attacker: Fighter) -> None:
        defender = self.p2 if attacker is self.p1 else self.p1
        if attacker.attack or attacker.stun > 0 or not attacker.grounded or not defender.grounded:
            return
        if abs(attacker.x - defender.x) > 82:
            return
        if self.stage_time - defender.grab_pressed_time < 0.15:
            attacker.vx = -attacker.facing * 260
            defender.vx = defender.facing * 260
            attacker.stun = defender.stun = 0.22
            self.announce("THROW CLASH", COLORS["gold"], 0.45)
            return
        defender.health -= 12
        defender.stun = 0.58
        defender.vx = attacker.facing * 420
        defender.vy = -240
        defender.grounded = False
        attacker.meter = min(100, attacker.meter + 12)
        self.spawn_particles(defender.x, defender.head_y() + 34, COLORS["gold"], 22, 230)
        self.announce("THROW!", COLORS["gold"], 0.45)

    def resolve_attacks(self) -> None:
        for attacker, defender in ((self.p1, self.p2), (self.p2, self.p1)):
            if not attacker.attack or attacker.attack["hit"]:
                continue
            hitbox = attacker.current_hitbox()
            if not hitbox:
                continue
            info = dict(attacker.attack["info"])
            if attacker.attack.get("finisher"):
                info["finisher"] = True
                info["damage"] = max(float(info["damage"]), defender.health + 1)
            if hitbox.colliderect(defender.rect):
                if info["height"] == "high" and defender.crouching:
                    continue
                attacker.attack["hit"] = True
                defender.take_hit(attacker, info, self)

    def resolve_projectiles(self, dt: float) -> None:
        survivors: List[Projectile] = []
        for projectile in self.projectiles:
            projectile.update(dt)
            opponent = self.p2 if projectile.owner is self.p1 else self.p1
            if projectile.ttl <= 0 or projectile.x < STAGE_LEFT - 20 or projectile.x > STAGE_RIGHT + 20:
                continue
            if projectile.rect().colliderect(opponent.rect):
                opponent.take_hit(projectile.owner, {**ATTACKS["fireball"], "damage": projectile.damage}, self, source="projectile")
                self.spawn_particles(projectile.x, projectile.y, projectile.color, 20, 210)
                continue
            # Projectiles erase each other.
            collided = False
            for other in self.projectiles:
                if other is not projectile and other.owner is not projectile.owner and projectile.rect().colliderect(other.rect()):
                    self.spawn_particles(projectile.x, projectile.y, COLORS["white"], 18, 150)
                    collided = True
                    break
            if not collided:
                survivors.append(projectile)
        self.projectiles = survivors

    def resolve_pushbox(self) -> None:
        gap = 58
        dx = self.p2.x - self.p1.x
        if abs(dx) < gap:
            overlap = gap - abs(dx)
            direction = sign(dx)
            self.p1.x -= direction * overlap / 2
            self.p2.x += direction * overlap / 2
            self.p1.x = clamp(self.p1.x, STAGE_LEFT + self.p1.width / 2, STAGE_RIGHT - self.p1.width / 2)
            self.p2.x = clamp(self.p2.x, STAGE_LEFT + self.p2.width / 2, STAGE_RIGHT - self.p2.width / 2)

    def check_stage_hazards(self, fighter: Fighter, dt: float) -> None:
        # Every arena has soft edge hazards with a stage-specific visual color.
        if fighter.x < STAGE_LEFT + 45 or fighter.x > STAGE_RIGHT - 45:
            damage = 1.05 if self.stage["kind"] == "arctic" else 1.4
            fighter.health -= damage * dt
            if random.random() < 0.16:
                self.spawn_particles(fighter.x, FLOOR_Y - 22, self.stage["hazard"], 2, 70)

    def decide_round(self) -> None:
        if self.mode != "fight":
            return
        p1_down = self.p1.health <= 0
        p2_down = self.p2.health <= 0
        timeout = self.timer <= 0
        if not (p1_down or p2_down or timeout):
            return

        if (p1_down and p2_down) or (timeout and abs(self.p1.health - self.p2.health) < 0.01):
            self.mode = "round_end"
            self.round_delay = 2.1
            self.announce("DRAW — REPLAY ROUND", COLORS["gold"], 1.5)
            return

        if p2_down or (timeout and self.p1.health > self.p2.health):
            winner, winner_idx = self.p1, 0
        else:
            winner, winner_idx = self.p2, 1
        self.wins[winner_idx] += 1
        self.mode = "round_end"
        self.round_delay = 2.4
        label = f"{winner.name} WINS"
        self.announce(label, winner.color, 1.55)

    def update(self, dt: float) -> None:
        self.stage_time += dt
        self.message_timer = max(0, self.message_timer - dt)
        if self.freeze_frames > 0:
            self.freeze_frames -= dt
            return

        if self.mode == "title" or self.mode == "match_end":
            return

        if self.mode == "intro":
            self.round_delay -= dt
            if self.round_delay <= 0:
                self.mode = "fight"
                self.announce("FIGHT!", COLORS["red"], 0.72)
            return

        if self.mode == "round_end":
            self.round_delay -= dt
            if self.round_delay <= 0:
                if max(self.wins) >= 2:
                    winner = self.p1 if self.wins[0] > self.wins[1] else self.p2
                    self.mode = "match_end"
                    self.announce(f"{winner.name} TAKES THE MATCH", winner.color, 99)
                else:
                    self.round_no += 1
                    self.reset_round(announce=True)
            return

        self.timer -= dt
        keys = pygame.key.get_pressed()
        p1_input = self.controls_for(self.p1, keys)
        p2_input = self.cpu_controls(self.p2, self.p1, dt) if self.p2.is_cpu else self.controls_for(self.p2, keys)

        self.p1.update(dt, p1_input, self.p2, self)
        self.p2.update(dt, p2_input, self.p1, self)
        self.resolve_pushbox()
        self.resolve_attacks()
        self.resolve_projectiles(dt)

        for fighter in (self.p1, self.p2):
            self.check_stage_hazards(fighter, dt)

        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        self.decide_round()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw_background(self) -> None:
        stage = self.stage
        top = stage["top"]
        bottom = stage["bottom"]
        for y in range(HEIGHT):
            t = y / HEIGHT
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))

        kind = stage["kind"]
        if kind == "city":
            for i in range(13):
                x = i * 110 - 30
                tower_h = 120 + (i % 4) * 40
                pygame.draw.rect(self.screen, stage["far"], (x, FLOOR_Y - tower_h, 74, tower_h))
                for wy in range(FLOOR_Y - tower_h + 18, FLOOR_Y - 20, 22):
                    if (i + wy // 22) % 2 == 0:
                        pygame.draw.rect(self.screen, stage["line"], (x + 17, wy, 12, 7))
                        pygame.draw.rect(self.screen, stage["accent"], (x + 43, wy + 7, 10, 6))
            # rain streaks
            for i in range(80):
                x = (i * 97 + int(self.stage_time * 180)) % WIDTH
                y = (i * 41) % FLOOR_Y
                pygame.draw.line(self.screen, (100, 180, 230), (x, y), (x - 10, y + 21), 1)
        elif kind == "temple":
            pygame.draw.circle(self.screen, (255, 199, 104), (WIDTH - 190, 146), 68)
            for x in range(60, WIDTH, 180):
                pygame.draw.rect(self.screen, stage["far"], (x, FLOOR_Y - 195, 48, 195))
                pygame.draw.rect(self.screen, (97, 54, 37), (x - 14, FLOOR_Y - 204, 76, 14))
                pygame.draw.line(self.screen, stage["line"], (x + 24, FLOOR_Y - 183), (x + 24, FLOOR_Y - 22), 3)
            for x in (145, WIDTH - 170):
                pygame.draw.circle(self.screen, stage["accent"], (x, FLOOR_Y - 75), 20)
                pygame.draw.circle(self.screen, (255, 204, 83), (x, FLOOR_Y - 79), 12)
        elif kind == "arctic":
            for i in range(6):
                x = i * 235 - 30
                pygame.draw.polygon(self.screen, stage["far"], [(x, FLOOR_Y), (x + 115, FLOOR_Y - 178), (x + 235, FLOOR_Y)])
                pygame.draw.polygon(self.screen, (190, 247, 255), [(x + 72, FLOOR_Y - 67), (x + 115, FLOOR_Y - 178), (x + 158, FLOOR_Y - 67)])
            for i in range(30):
                x = (i * 81 + int(self.stage_time * 15)) % WIDTH
                y = (i * 57 + int(self.stage_time * 26)) % FLOOR_Y
                pygame.draw.circle(self.screen, (215, 251, 255), (x, y), 2)
            pygame.draw.arc(self.screen, stage["accent"], (250, 38, 720, 360), math.pi * 1.08, math.pi * 1.9, 5)
        else:  # reactor
            for i in range(90):
                x = (i * 79) % WIDTH
                y = (i * 43) % (FLOOR_Y - 70)
                size = 1 + (i % 3)
                pygame.draw.circle(self.screen, stage["accent" if i % 3 == 0 else "line"], (x, y), size)
            core_y = FLOOR_Y - 160
            pygame.draw.circle(self.screen, stage["accent"], (WIDTH // 2, core_y), 76, 4)
            pygame.draw.circle(self.screen, stage["line"], (WIDTH // 2, core_y), 50, 3)
            for a in range(0, 360, 45):
                rad = math.radians(a + self.stage_time * 55)
                px = WIDTH // 2 + int(math.cos(rad) * 112)
                py = core_y + int(math.sin(rad) * 72)
                pygame.draw.line(self.screen, stage["accent"], (WIDTH // 2, core_y), (px, py), 2)

        # Floor and perspective lines.
        pygame.draw.rect(self.screen, stage["floor"], (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y))
        for x in range(0, WIDTH + 1, 46):
            pygame.draw.line(self.screen, stage["grid"], (x, FLOOR_Y), (WIDTH // 2 + (x - WIDTH // 2) // 3, HEIGHT), 1)
        for y in range(FLOOR_Y + 14, HEIGHT, 21):
            pygame.draw.line(self.screen, stage["grid"], (0, y), (WIDTH, y), 1)
        pygame.draw.line(self.screen, stage["line"], (0, FLOOR_Y), (WIDTH, FLOOR_Y), 3)

        # Stage hazards.
        for x in (STAGE_LEFT - 30, STAGE_RIGHT - 25):
            pygame.draw.rect(self.screen, stage["far"], (x, FLOOR_Y - 50, 28, 50))
            pygame.draw.line(self.screen, stage["hazard"], (x + 14, FLOOR_Y - 50), (x + 14, FLOOR_Y), 4)
            pygame.draw.circle(self.screen, stage["accent"], (x + 14, FLOOR_Y - 49), 6)

    def draw_hud(self) -> None:
        # Top UI bands
        pygame.draw.rect(self.screen, (5, 8, 18), (0, 0, WIDTH, 108))
        pygame.draw.line(self.screen, (65, 91, 137), (0, 108), (WIDTH, 108), 2)

        def bar(x: int, y: int, w: int, fighter: Fighter, reverse: bool = False) -> None:
            pygame.draw.rect(self.screen, (35, 41, 64), (x, y, w, 24), border_radius=7)
            fill = int(w * clamp(fighter.health, 0, 100) / 100)
            if reverse:
                rect = pygame.Rect(x + w - fill, y, fill, 24)
            else:
                rect = pygame.Rect(x, y, fill, 24)
            pygame.draw.rect(self.screen, fighter.color, rect, border_radius=7)
            pygame.draw.rect(self.screen, (205, 230, 255), (x, y, w, 24), 2, border_radius=7)
            meter_y = y + 32
            pygame.draw.rect(self.screen, (25, 28, 45), (x, meter_y, w, 9), border_radius=4)
            meter_fill = int(w * fighter.meter / 100)
            meter_rect = pygame.Rect(x + (w - meter_fill if reverse else 0), meter_y, meter_fill, 9)
            pygame.draw.rect(self.screen, COLORS["gold"], meter_rect, border_radius=4)
            if fighter.guard > 0:
                pygame.draw.rect(self.screen, COLORS["purple"], (x, meter_y + 14, int(w * fighter.guard / 42), 4), border_radius=2)

        draw_text(self.screen, self.fonts["small"], self.p1.name, (48, 20), self.p1.color)
        draw_text(self.screen, self.fonts["small"], self.p2.name, (WIDTH - 48, 20), self.p2.color, "topright")
        bar(48, 48, 420, self.p1)
        bar(WIDTH - 468, 48, 420, self.p2, reverse=True)

        # round win tokens and timer
        for i in range(2):
            pygame.draw.circle(self.screen, self.p1.color if i < self.wins[0] else (54, 61, 92), (50 + i * 24, 92), 8)
            pygame.draw.circle(self.screen, self.p2.color if i < self.wins[1] else (54, 61, 92), (WIDTH - 50 - i * 24, 92), 8)
        draw_text(self.screen, self.fonts["large"], str(max(0, math.ceil(self.timer))), (WIDTH // 2, 38), COLORS["gold"], "midtop", True)
        draw_text(self.screen, self.fonts["tiny"], f"BEST OF THREE  •  ROUND {self.round_no}", (WIDTH // 2, 94), COLORS["muted"], "midtop")
        draw_text(self.screen, self.fonts["tiny"], self.stage["name"], (WIDTH // 2, 116), self.stage["line"], "midtop")

        if self.p1.combo_hits > 1 and self.p1.combo_timer > 0:
            draw_text(self.screen, self.fonts["medium"], f"{self.p1.combo_hits} HIT", (42, 142), self.p1.color, shadow=True)
        if self.p2.combo_hits > 1 and self.p2.combo_timer > 0:
            draw_text(self.screen, self.fonts["medium"], f"{self.p2.combo_hits} HIT", (WIDTH - 42, 142), self.p2.color, "topright", True)

    def draw_message(self) -> None:
        if self.message_timer <= 0:
            return
        scale = 1.0 + min(0.13, self.message_timer * 0.08)
        font = self.fonts["huge"]
        text = self.message
        shadow = font.render(text, True, (0, 0, 0))
        img = font.render(text, True, self.message_color)
        rect = img.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 44))
        self.screen.blit(shadow, rect.move(4, 5))
        self.screen.blit(img, rect)

    def draw_title(self) -> None:
        self.draw_background()
        title_font = self.fonts["huge"]
        draw_text(self.screen, title_font, "MORTAL", (WIDTH // 2, 135), COLORS["gold"], "midtop", True)
        draw_text(self.screen, title_font, "COMBAT REBORN", (WIDTH // 2, 224), COLORS["red"], "midtop", True)
        draw_text(self.screen, self.fonts["medium"], "ORIGINAL 2D ARENA FIGHTER", (WIDTH // 2, 330), COLORS["cyan"], "midtop")

        panel = pygame.Rect(WIDTH // 2 - 350, 395, 700, 210)
        pygame.draw.rect(self.screen, (13, 18, 38), panel, border_radius=20)
        pygame.draw.rect(self.screen, (77, 105, 154), panel, 2, border_radius=20)
        draw_text(self.screen, self.fonts["medium"], "1  —  VS CPU", (WIDTH // 2, 430), COLORS["text"], "midtop")
        draw_text(self.screen, self.fonts["medium"], "2  —  LOCAL TWO PLAYER", (WIDTH // 2, 474), COLORS["text"], "midtop")
        draw_text(self.screen, self.fonts["small"], "CHOOSE FIGHT TYPE, THEN CHOOSE AN ARENA", (WIDTH // 2, 522), COLORS["muted"], "midtop")
        draw_text(self.screen, self.fonts["tiny"], "ESC  —  EXIT", (WIDTH // 2, 552), COLORS["muted"], "midtop")
        draw_text(self.screen, self.fonts["tiny"], "P1: WASD move • F punch • R kick • Q parry/block • T grab • E super", (WIDTH // 2, 632), COLORS["muted"], "midtop")
        draw_text(self.screen, self.fonts["tiny"], "P2: Arrow keys move • P punch • K kick • M parry/block • O grab • L super", (WIDTH // 2, 654), COLORS["muted"], "midtop")
        draw_text(self.screen, self.fonts["tiny"], "F / P = punch • R / K = kick • E / L = super • ESC = main menu", (WIDTH // 2, 678), COLORS["purple"], "midtop")

    def draw_stage_select(self) -> None:
        # Render the highlighted arena in the background to make the choice visual.
        self.draw_background()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 105))
        self.screen.blit(overlay, (0, 0))
        draw_text(self.screen, self.fonts["large"], "SELECT ARENA", (WIDTH // 2, 70), COLORS["gold"], "midtop", True)
        mode_text = "VS CPU" if self.pending_vs_cpu else "LOCAL TWO PLAYER"
        draw_text(self.screen, self.fonts["small"], mode_text, (WIDTH // 2, 134), COLORS["cyan"], "midtop")
        draw_text(self.screen, self.fonts["tiny"], "LEFT / RIGHT to browse • 1–4 to jump • ENTER to confirm • ESC to return",
                  (WIDTH // 2, 163), COLORS["muted"], "midtop")

        card_w, card_h = 510, 82
        top = 206
        for index, stage in enumerate(STAGES):
            y = top + index * 94
            selected = index == self.stage_index
            rect = pygame.Rect(WIDTH // 2 - card_w // 2, y, card_w, card_h)
            fill = tuple(min(255, c + 22) for c in stage["far"]) if selected else (15, 18, 34)
            pygame.draw.rect(self.screen, fill, rect, border_radius=14)
            pygame.draw.rect(self.screen, stage["line"] if selected else (74, 83, 122), rect, 3 if selected else 1, border_radius=14)
            thumb = pygame.Rect(rect.x + 14, rect.y + 12, 100, 58)
            pygame.draw.rect(self.screen, stage["top"], thumb, border_radius=9)
            pygame.draw.rect(self.screen, stage["accent"], (thumb.x + 12, thumb.bottom - 17, thumb.width - 24, 7), border_radius=3)
            pygame.draw.circle(self.screen, stage["line"], (thumb.centerx, thumb.y + 22), 11)
            draw_text(self.screen, self.fonts["small"], f"{index + 1}. {stage['name']}", (rect.x + 132, rect.y + 16),
                      stage["line"] if selected else COLORS["text"])
            draw_text(self.screen, self.fonts["tiny"], stage["subtitle"], (rect.x + 132, rect.y + 47), COLORS["muted"])

        stage = self.stage
        draw_text(self.screen, self.fonts["medium"], stage["name"], (WIDTH // 2, 613), stage["line"], "midtop", True)
        draw_text(self.screen, self.fonts["small"], stage["subtitle"], (WIDTH // 2, 652), COLORS["text"], "midtop")

    def draw_match_end(self) -> None:
        self.draw_background()
        winner = self.p1 if self.wins[0] > self.wins[1] else self.p2
        draw_text(self.screen, self.fonts["huge"], "MATCH COMPLETE", (WIDTH // 2, 140), COLORS["gold"], "midtop", True)
        draw_text(self.screen, self.fonts["large"], f"{winner.name} WINS", (WIDTH // 2, 270), winner.color, "midtop", True)
        draw_text(self.screen, self.fonts["medium"], f"FINAL SCORE  {self.wins[0]} — {self.wins[1]}", (WIDTH // 2, 350), COLORS["text"], "midtop")
        draw_text(self.screen, self.fonts["medium"], "PRESS ENTER OR R FOR REMATCH MENU", (WIDTH // 2, 470), COLORS["muted"], "midtop")

    def draw(self) -> None:
        if self.mode == "title":
            self.draw_title()
            pygame.display.flip()
            return
        if self.mode == "match_end":
            self.draw_match_end()
            pygame.display.flip()
            return
        if self.mode == "stage_select":
            self.draw_stage_select()
            pygame.display.flip()
            return

        self.draw_background()
        self.p1.draw(self.screen)
        self.p2.draw(self.screen)
        for projectile in self.projectiles:
            projectile.draw(self.screen)
        for particle in self.particles:
            alpha = int(255 * clamp(particle.life / 0.5, 0, 1))
            glow = pygame.Surface((int(particle.size * 5), int(particle.size * 5)), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*particle.color, alpha), (glow.get_width() // 2, glow.get_height() // 2), int(particle.size))
            self.screen.blit(glow, (particle.x - glow.get_width() // 2, particle.y - glow.get_height() // 2))
        self.draw_hud()
        self.draw_message()
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
            self.update(dt)
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
