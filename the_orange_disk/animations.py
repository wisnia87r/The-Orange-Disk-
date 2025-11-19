# -*- coding: utf-8 -*-

# This file contains classes for UI animations, like the background
# particles and menu highlights.

import pygame
import random
import math
from .config import INTERNAL_WIDTH, INTERNAL_HEIGHT

class Spark:
    """Represents a single particle in the PS2-style background animation."""
    def __init__(self, is_boot_anim=False):
        self.center_x = INTERNAL_WIDTH // 2
        self.center_y = INTERNAL_HEIGHT // 2
        self.is_boot_anim = is_boot_anim
        self.reset()

    def reset(self):
        if self.is_boot_anim:
            # For the boot animation, sparks explode from the center.
            self.x = self.center_x + random.uniform(-10, 10)
            self.y = self.center_y + random.uniform(-10, 10)
            self.angle = random.uniform(0, 2 * math.pi)
            self.speed = random.uniform(2, 6)
            self.color = random.choice([(200, 200, 255), (255, 255, 255), (150, 150, 200)])
            self.life = random.randint(50, 100)
        else:
            # For the menu background, sparks drift slowly.
            self.x = random.randint(0, INTERNAL_WIDTH)
            self.y = random.randint(0, INTERNAL_HEIGHT)
            self.angle = random.uniform(0, 2 * math.pi)
            self.speed = random.uniform(0.2, 0.8)
            self.color = random.choice([(100, 100, 150), (50, 50, 80)])
            self.life = random.randint(200, 500)

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.life -= 1
        if self.life <= 0:
            self.reset()
        # Bounce off edges in menu mode
        if not self.is_boot_anim:
            if self.x <= 0 or self.x >= INTERNAL_WIDTH: self.angle = math.pi - self.angle
            if self.y <= 0 or self.y >= INTERNAL_HEIGHT: self.angle = -self.angle

    def draw(self, surface):
        # Draw a short line to simulate a tail
        end_x = self.x + math.cos(self.angle) * self.speed * 2
        end_y = self.y + math.sin(self.angle) * self.speed * 2
        pygame.draw.line(surface, self.color, (int(self.x), int(self.y)), (int(end_x), int(end_y)), 1)

class Orb:
    """Represents an orbiting particle around the selected menu item."""
    def __init__(self):
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.02, 0.05) * random.choice([-1, 1])
        self.base_radius_x = random.randint(280, 350)
        self.base_radius_y = random.randint(20, 40)
        self.size = random.randint(2, 5)
        self.color = random.choice([(200, 200, 255), (255, 255, 255), (150, 150, 220)])

    def update(self):
        self.angle += self.speed
        if self.angle > 2 * math.pi: self.angle -= 2 * math.pi
        if self.angle < 0: self.angle += 2 * math.pi

    def draw(self, surface, center_pos):
        x = center_pos[0] + math.cos(self.angle) * self.base_radius_x
        y = center_pos[1] + math.sin(self.angle) * self.base_radius_y
        # Make the orb slightly larger when it's at the "front" of the ellipse
        current_size = int(self.size * 1.5) if math.sin(self.angle) > 0.8 else self.size
        pygame.draw.circle(surface, self.color, (int(x), int(y)), current_size)
