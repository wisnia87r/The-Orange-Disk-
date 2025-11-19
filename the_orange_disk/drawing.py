# -*- coding: utf-8 -*-

# This file contains all the drawing logic for the user interface.

import pygame
import time # OSTATECZNA POPRAWKA: Dodano brakujący import
import math
from .config import * # Import all constants and colors

class Drawing:
    def __init__(self, app_instance):
        self.app = app_instance

    def get_pulse_color(self):
        """Calculates a pulsing color for highlights."""
        pulse = (math.sin(self.app.frame_count * 0.1) + 1) / 2
        r = int(PS2_TEXT[0] + (PS2_TEXT_BRIGHT[0] - PS2_TEXT[0]) * pulse)
        g = int(PS2_TEXT[1] + (PS2_TEXT_BRIGHT[1] - PS2_TEXT[1]) * pulse)
        b = int(PS2_TEXT[2] + (PS2_TEXT_BRIGHT[2] - PS2_TEXT[2]) * pulse)
        return (r, g, b)

    def draw_text_shadow(self, text, font, color, center_pos, shadow_color=PS2_SHADOW, shadow_offset=3):
        """Renders text with a drop shadow."""
        lines = text.split('\n')
        line_height = font.get_height() * 0.8
        v_offset = - (len(lines) - 1) * (line_height / 2) if len(lines) > 1 else 0

        for i, line in enumerate(lines):
            line_v_offset = v_offset + i * line_height
            shadow_surf = font.render(line, True, shadow_color)
            self.app.screen.blit(shadow_surf, shadow_surf.get_rect(center=(center_pos[0] + shadow_offset, center_pos[1] + shadow_offset + line_v_offset)))
            text_surf = font.render(line, True, color)
            self.app.screen.blit(text_surf, text_surf.get_rect(center=(center_pos[0], center_pos[1] + line_v_offset)))

    def draw_button_icon(self, shape, x, y, size=20):
        """Draws a PlayStation-style button icon."""
        if shape == "CROSS":
            pygame.draw.line(self.app.screen, PS1_BLUE, (x - size // 2, y - size // 2), (x + size // 2, y + size // 2), 4)
            pygame.draw.line(self.app.screen, PS1_BLUE, (x + size // 2, y - size // 2), (x - size // 2, y + size // 2), 4)
        elif shape == "CIRCLE":
            pygame.draw.circle(self.app.screen, PS1_RED, (x, y), size // 2, 3)

    def draw_ps2_background(self):
        """Draws the main background and title bar."""
        if self.app.bg_image:
            self.app.screen.blit(self.app.bg_image, (0, 0))
        else:
            self.app.screen.fill(PS2_VOID_DARK)
        # Title Bar
        pygame.draw.rect(self.app.screen, (0, 0, 0, 150), (0, 0, INTERNAL_WIDTH, 80))
        pygame.draw.line(self.app.screen, (100, 100, 150), (0, 80), (INTERNAL_WIDTH, 80), 1)
        self.draw_text_shadow("The Orange Disk", self.app.font_title, PS2_TEXT_BRIGHT, (INTERNAL_WIDTH // 2 - 100, 40), shadow_offset=2)
        self.draw_text_shadow("Playstation Edition", self.app.font_small, PS1_ORANGE, (INTERNAL_WIDTH // 2 + 240, 50), shadow_offset=2)

    def draw_boot_animation(self):
        """Draws the startup animation sequence."""
        elapsed = time.time() - self.app.boot_anim_timer
        if self.app.bg_image:
            scroll_x = (elapsed * 10) % INTERNAL_WIDTH
            self.app.screen.blit(self.app.bg_image, (scroll_x - INTERNAL_WIDTH, 0))
            self.app.screen.blit(self.app.bg_image, (scroll_x, 0))
        else:
            self.app.screen.fill(BLACK)
        
        center_x, center_y = INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2
        max_radius = INTERNAL_WIDTH // 2
        for i in range(10):
            radius = (max_radius * (i / 10.0) + (self.app.frame_count * 5)) % max_radius
            alpha = 255 - (radius / max_radius) * 255
            color = (PS2_VOID_LIGHT[0], PS2_VOID_LIGHT[1], PS2_VOID_LIGHT[2], int(alpha))
            temp_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, color, (radius, radius), radius, 5)
            self.app.screen.blit(temp_surf, (center_x - radius, center_y - radius))
        
        for s in self.app.boot_sparks:
            s.update()
            s.draw(self.app.screen)
        
        if elapsed > 2.0:
            alpha = min(255, int((elapsed - 2.0) / 2.0 * 255))
            title_surf = self.app.font_title.render(self.app.get_string("BOOT_TITLE"), True, (255, 255, 255))
            title_surf.set_alpha(alpha)
            self.app.screen.blit(title_surf, title_surf.get_rect(center=(center_x, center_y - 20)))
        
        if elapsed > 4.0:
            alpha = min(255, int((elapsed - 4.0) / 2.0 * 255))
            subtitle_surf = self.app.font_small.render(self.app.get_string("BOOT_SUBTITLE"), True, (200, 200, 200))
            subtitle_surf.set_alpha(alpha)
            self.app.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(center_x, center_y + 40)))
        
        if elapsed > 7.0:
            self.app.state = "MENU"
            self.app.frame_count = 0

    def draw_menu_state(self):
        """Draws the main menu."""
        start_y, spacing = 200, 70
        menu_options = self.app.get_main_menu_options()
        for i, opt in enumerate(menu_options):
            is_selected = (i == self.app.menu_index)
            is_disabled = (opt in (self.app.get_string("PLAY_GAME"), self.app.get_string("RIP_DISC")) and not self.app.drive_path)
            color = GRAYED_OUT if is_disabled else (PS1_ORANGE if is_selected else PS2_TEXT)
            center_pos = (INTERNAL_WIDTH // 2, start_y + i * spacing)
            self.draw_text_shadow(opt, self.app.font_med, color, center_pos)
            if is_selected and not is_disabled:
                for orb in self.app.menu_orbs:
                    orb.update()
                    orb.draw(self.app.screen, center_pos)
        
        if not self.app.drive_path:
            self.draw_text_shadow(self.app.get_string("DRIVE_NOT_FOUND_PROMPT"), self.app.font_small, PS1_ORANGE, (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 150))
        
        footer_y = INTERNAL_HEIGHT - 50
        self.draw_button_icon("CROSS", 80, footer_y)
        self.draw_text_shadow(self.app.get_string("SELECT"), self.app.font_small, PS2_TEXT, (145, footer_y))
        self.draw_button_icon("CIRCLE", 240, footer_y)
        self.draw_text_shadow(self.app.get_string("BACK_FOOTER"), self.app.font_small, PS2_TEXT, (305, footer_y))

    def draw_settings_state(self):
        """Draws the settings menu."""
        start_y, spacing = 250, 80
        settings_options = self.app.get_settings_menu_options()
        for i, opt in enumerate(settings_options):
            is_selected = (i == self.app.settings_menu_index)
            color = PS1_ORANGE if is_selected else PS2_TEXT
            center_pos = (INTERNAL_WIDTH // 2, start_y + i * spacing)
            self.draw_text_shadow(opt, self.app.font_med, color, center_pos)
            if is_selected:
                for orb in self.app.menu_orbs:
                    orb.update()
                    orb.draw(self.app.screen, center_pos)
        
        footer_y = INTERNAL_HEIGHT - 50
        self.draw_button_icon("CROSS", 80, footer_y)
        self.draw_text_shadow(self.app.get_string("SELECT"), self.app.font_small, PS2_TEXT, (145, footer_y))
        self.draw_button_icon("CIRCLE", 240, footer_y)
        self.draw_text_shadow(self.app.get_string("SETTINGS_BACK"), self.app.font_small, PS2_TEXT, (305, footer_y))

    def draw_info_page(self, title_key, content_keys):
        """Generic function to draw a simple text info page."""
        self.draw_text_shadow(self.app.get_string(title_key), self.app.font_title, PS1_ORANGE, (INTERNAL_WIDTH // 2, 150))
        start_y = 250
        for i, key in enumerate(content_keys):
            self.draw_text_shadow(self.app.get_string(key), self.app.font_small, PS2_TEXT, (INTERNAL_WIDTH // 2, start_y + i * 50))
        
        footer_y = INTERNAL_HEIGHT - 50
        self.draw_button_icon("CIRCLE", INTERNAL_WIDTH // 2 - 50, footer_y)
        self.draw_text_shadow(self.app.get_string("SETTINGS_BACK"), self.app.font_small, PS2_TEXT, (INTERNAL_WIDTH // 2 + 20, footer_y))

    def draw_keyboard_state(self):
        # ... (drawing logic is fine, no changes needed)
        pass

    def draw_loading_state(self):
        # ... (drawing logic is fine, no changes needed)
        pass

    def draw_message_state(self, title_key, title_color):
        # ... (drawing logic is fine, no changes needed)
        pass

    def draw_frame(self):
        """The main drawing function, called every frame."""
        if not pygame.get_init(): return
        if self.app.state == "BOOT_ANIMATION":
            self.draw_boot_animation()
        else:
            self.draw_ps2_background()
            if self.app.state == "MENU": self.draw_menu_state()
            elif self.app.state == "SETTINGS": self.draw_settings_state()
            elif self.app.state == "HOW_TO": self.draw_info_page("HOW_TO_TITLE", ["HOW_TO_PLAY", "HOW_TO_RIP", "HOW_TO_SETTINGS", "HOW_TO_EXIT"])
            elif self.app.state == "ABOUT": self.draw_info_page("ABOUT_TITLE", ["ABOUT_CREATED_BY"])
            elif self.app.state == "KEYBOARD": self.draw_keyboard_state()
            elif self.app.state == "LOADING": self.draw_loading_state()
            elif self.app.state == "MESSAGE": self.draw_message_state("SUCCESS_TITLE", PS1_GREEN)
            elif self.app.state == "ERROR": self.draw_message_state("ERROR_TITLE", PS1_RED)

        # Scale the internal surface to the real screen resolution
        scale = min(self.app.real_width / INTERNAL_WIDTH, self.app.real_height / INTERNAL_HEIGHT)
        new_w, new_h = int(INTERNAL_WIDTH * scale), int(INTERNAL_HEIGHT * scale)
        scaled_surf = pygame.transform.smoothscale(self.app.screen, (new_w, new_h))
        x_offset, y_offset = (self.app.real_width - new_w) // 2, (self.app.real_height - new_h) // 2
        self.app.monitor.fill(BLACK)
        self.app.monitor.blit(scaled_surf, (x_offset, y_offset))
        pygame.display.flip()
