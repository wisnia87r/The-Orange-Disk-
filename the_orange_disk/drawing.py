# -*- coding: utf-8 -*-

import pygame
import time
import math
import io
from .config import *

class Drawing:
    def __init__(self, app_instance):
        self.app = app_instance

    def get_pulse_color(self):
        pulse = (math.sin(self.app.frame_count * 0.1) + 1) / 2
        r = int(PS2_TEXT[0] + (PS2_TEXT_BRIGHT[0] - PS2_TEXT[0]) * pulse)
        g = int(PS2_TEXT[1] + (PS2_TEXT_BRIGHT[1] - PS2_TEXT[1]) * pulse)
        b = int(PS2_TEXT[2] + (PS2_TEXT_BRIGHT[2] - PS2_TEXT[2]) * pulse)
        return (r, g, b)

    def draw_text_shadow(self, text, font, color, center_pos, shadow_color=PS2_SHADOW, shadow_offset=3):
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
        if shape == "CROSS":
            pygame.draw.line(self.app.screen, PS1_BLUE, (x - size // 2, y - size // 2), (x + size // 2, y + size // 2), 4)
            pygame.draw.line(self.app.screen, PS1_BLUE, (x + size // 2, y - size // 2), (x - size // 2, y + size // 2), 4)
        elif shape == "CIRCLE":
            pygame.draw.circle(self.app.screen, PS1_RED, (x, y), size // 2, 3)

    def draw_ps2_background(self):
        if self.app.bg_image:
            self.app.screen.blit(self.app.bg_image, (0, 0))
        else:
            self.app.screen.fill(PS2_VOID_DARK)
        # Smaller header bar - just 50px instead of 80px
        pygame.draw.rect(self.app.screen, (0, 0, 0, 150), (0, 0, INTERNAL_WIDTH, 50))
        pygame.draw.line(self.app.screen, (100, 100, 150), (0, 50), (INTERNAL_WIDTH, 50), 1)
        # Simple centered title
        self.draw_text_shadow("The Orange Disk", self.app.font_large, PS1_ORANGE, (INTERNAL_WIDTH // 2, 25), shadow_offset=2)

    def draw_boot_animation(self):
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
        self.draw_text_shadow(self.app.get_string(title_key), self.app.font_title, PS1_ORANGE, (INTERNAL_WIDTH // 2, 150))
        start_y = 250
        for i, key in enumerate(content_keys):
            self.draw_text_shadow(self.app.get_string(key), self.app.font_small, PS2_TEXT, (INTERNAL_WIDTH // 2, start_y + i * 50))
        footer_y = INTERNAL_HEIGHT - 50
        self.draw_button_icon("CIRCLE", INTERNAL_WIDTH // 2 - 50, footer_y)
        self.draw_text_shadow(self.app.get_string("SETTINGS_BACK"), self.app.font_small, PS2_TEXT, (INTERNAL_WIDTH // 2 + 20, footer_y))

    def draw_keyboard_state(self):
        self.draw_text_shadow(self.app.message_text, self.app.font_small, PS1_ORANGE, (INTERNAL_WIDTH // 2, 150))
        pygame.draw.rect(self.app.screen, (0, 0, 0), (INTERNAL_WIDTH // 2 - 300, 200, 600, 50))
        pygame.draw.rect(self.app.screen, PS2_TEXT, (INTERNAL_WIDTH // 2 - 300, 200, 600, 50), 2)
        display_text = self.app.keyboard_input
        if "hasło" in self.app.message_text.lower() or "password" in self.app.message_text.lower():
            display_text = "*" * len(self.app.keyboard_input)
        if (self.app.frame_count // 15) % 2 == 0: display_text += "_"
        self.draw_text_shadow(display_text, self.app.font_med, PS2_TEXT, (INTERNAL_WIDTH // 2, 225))
        start_y, key_size, gap = 300, 60, 10
        current_layout = self.app.kb_layouts[self.app.kb_current_mode]
        total_width = len(current_layout[0]) * (key_size + gap)
        start_x = (INTERNAL_WIDTH - total_width) // 2
        for r, row_keys in enumerate(current_layout):
            for c, key in enumerate(row_keys):
                x, y = start_x + c * (key_size + gap), start_y + r * (key_size + gap)
                is_active = (r == self.app.kb_row and c == self.app.kb_col)
                bg_color = self.get_pulse_color() if is_active else (40, 40, 60)
                if key == "SHIFT" and self.app.kb_current_mode == "upper": bg_color = PS1_GREEN
                txt_color = (0, 0, 0) if is_active else PS2_TEXT
                pygame.draw.rect(self.app.screen, bg_color, (x, y, key_size, key_size))
                pygame.draw.rect(self.app.screen, (100, 100, 150), (x, y, key_size, key_size), 2)
                font = self.app.font_small if len(key) < 3 else pygame.font.SysFont("sans", 16, bold=True)
                txt = font.render(key, True, txt_color)
                self.app.screen.blit(txt, txt.get_rect(center=(x + key_size // 2, y + key_size // 2)))

    def draw_loading_state(self):
        self.draw_text_shadow(self.app.loading_text, self.app.font_med, PS2_TEXT, (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 - 100))
        bar_width, bar_height = 600, 40
        bar_x, bar_y = (INTERNAL_WIDTH - bar_width) // 2, INTERNAL_HEIGHT // 2
        pygame.draw.rect(self.app.screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(self.app.screen, PS2_TEXT, (bar_x, bar_y, bar_width, bar_height), 3)
        filled_width = int((self.app.progress_percent / 100) * bar_width)
        if filled_width > 0:
            pygame.draw.rect(self.app.screen, self.get_pulse_color(), (bar_x, bar_y, filled_width, bar_height))
        self.draw_text_shadow(self.app.progress_text, self.app.font_small, PS2_TEXT, (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 + 70))
        if "Zgrywanie" in self.app.loading_text or "Ripping" in self.app.loading_text:
            self.draw_button_icon("CIRCLE", INTERNAL_WIDTH // 2 - 60, INTERNAL_HEIGHT - 100)
            self.draw_text_shadow(self.app.get_string("CANCEL_BUTTON"), self.app.font_small, (150, 150, 150), (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 100))

    def draw_message_state(self, title_key, title_color):
        self.draw_text_shadow(self.app.get_string(title_key), self.app.font_title, title_color, (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 - 50))
        self.draw_text_shadow(self.app.message_text, self.app.font_small, PS2_TEXT, (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 + 50))
        self.draw_text_shadow(self.app.get_string("CONFIRM_BUTTON"), self.app.font_small, (150, 150, 150), (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 100))

    def draw_artwork_selection_state(self):
        # Title - use medium font to avoid overlap
        self.draw_text_shadow(self.app.get_string("ARTWORK_SELECT"), self.app.font_large, PS1_ORANGE, (INTERNAL_WIDTH // 2, 100))

        # Show current artwork type - split into two lines for clarity
        type_names = {
            'grids': 'Horizontal Grid (Library Banner)',
            'grids_vertical': 'Vertical Grid (Library Capsule)',
            'heroes': 'Hero Banner (Top Background)',
            'logos': 'Logo (Game Title)',
            'icons': 'Icon (Desktop Mode)'
        }
        current_type_name = type_names.get(self.app.current_artwork_type, self.app.current_artwork_type)

        # Split the type name into main name and description
        if '(' in current_type_name:
            main_name, description = current_type_name.split('(', 1)
            description = '(' + description
            self.draw_text_shadow(main_name.strip(), self.app.font_med, PS1_ORANGE, (INTERNAL_WIDTH // 2, 140))
            self.draw_text_shadow(description, self.app.font_small, PS2_TEXT, (INTERNAL_WIDTH // 2, 165))
        else:
            self.draw_text_shadow(current_type_name, self.app.font_med, PS1_ORANGE, (INTERNAL_WIDTH // 2, 140))

        # Counter
        counter_text = f"{self.app.artwork_type_index + 1}/{len(self.app.artwork_data[self.app.current_artwork_type])}"
        self.draw_text_shadow(counter_text, self.app.font_small, GRAYED_OUT, (INTERNAL_WIDTH // 2, 190))

        # Instructions
        instructions = "↑↓: Change Type  |  ←→: Browse  |  Enter: Confirm"
        self.draw_text_shadow(instructions, self.app.font_small, GRAYED_OUT, (INTERNAL_WIDTH // 2, 215))

        # Display current artwork (large preview) - adjusted position and size
        current_surfaces = self.app.artwork_surfaces[self.app.current_artwork_type]
        if len(current_surfaces) > self.app.artwork_type_index:
            surface = current_surfaces[self.app.artwork_type_index]
            if surface:
                # Scale to fit nicely - leave room for header and thumbnails
                max_width, max_height = 700, 380
                surf_width, surf_height = surface.get_size()
                scale = min(max_width / surf_width, max_height / surf_height)
                new_width = int(surf_width * scale)
                new_height = int(surf_height * scale)
                scaled_surface = pygame.transform.smoothscale(surface, (new_width, new_height))

                # Center it in the available space (between instructions and thumbnails)
                x = (INTERNAL_WIDTH - new_width) // 2
                y = 250 + (430 - new_height) // 2  # Center in space between y=250 and y=680

                # Draw border
                pygame.draw.rect(self.app.screen, PS1_ORANGE, (x - 5, y - 5, new_width + 10, new_height + 10), 3)
                self.app.screen.blit(scaled_surface, (x, y))
            else:
                # Loading placeholder
                x, y = INTERNAL_WIDTH // 2 - 150, 350
                pygame.draw.rect(self.app.screen, GRAYED_OUT, (x, y, 300, 200))
                self.draw_text_shadow("Loading...", self.app.font_med, PS2_TEXT, (INTERNAL_WIDTH // 2, 450))

        # Show thumbnails of other types at the bottom
        thumb_y = INTERNAL_HEIGHT - 110
        thumb_size = 70
        thumb_spacing = 100
        types_with_data = [t for t in ['grids', 'grids_vertical', 'heroes', 'logos', 'icons'] if len(self.app.artwork_data[t]) > 0]
        start_x = (INTERNAL_WIDTH - (len(types_with_data) * thumb_spacing)) // 2

        for i, art_type in enumerate(types_with_data):
            x = start_x + i * thumb_spacing
            # Highlight current type
            if art_type == self.app.current_artwork_type:
                pygame.draw.rect(self.app.screen, PS1_ORANGE, (x - 3, thumb_y - 3, thumb_size + 6, thumb_size + 6), 2)

            # Draw thumbnail or placeholder - use the currently selected index for this type
            selected_index = self.app.artwork_type_indices.get(art_type, 0)
            if len(self.app.artwork_surfaces[art_type]) > selected_index and self.app.artwork_surfaces[art_type][selected_index]:
                thumb = pygame.transform.smoothscale(self.app.artwork_surfaces[art_type][selected_index], (thumb_size, thumb_size))
                self.app.screen.blit(thumb, (x, thumb_y))
            else:
                pygame.draw.rect(self.app.screen, GRAYED_OUT, (x, thumb_y, thumb_size, thumb_size))

            # Label - use short unique names for thumbnails
            thumb_labels = {
                'grids': 'H-Grid',
                'grids_vertical': 'V-Grid',
                'heroes': 'Hero',
                'logos': 'Logo',
                'icons': 'Icon'
            }
            label = thumb_labels.get(art_type, art_type)
            self.draw_text_shadow(label, self.app.font_small, PS2_TEXT if art_type != self.app.current_artwork_type else PS1_ORANGE, (x + thumb_size // 2, thumb_y + thumb_size + 15))

    def draw_confirmation_state(self):
        self.draw_text_shadow(self.app.get_string("ARTWORK_ADD_TO_STEAM_PROMPT"), self.app.font_med, PS2_TEXT, (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 - 50))
        options = [self.app.get_string("ARTWORK_YES"), self.app.get_string("ARTWORK_NO")]
        for i, opt in enumerate(options):
            color = PS1_ORANGE if i == self.app.confirmation_index else PS2_TEXT
            self.draw_text_shadow(opt, self.app.font_med, color, (INTERNAL_WIDTH // 2 - 100 + i * 200, INTERNAL_HEIGHT // 2 + 50))

    def draw_version_number(self):
        version_surf = self.app.font_small.render(APP_VERSION, True, GRAYED_OUT)
        version_rect = version_surf.get_rect(bottomright=(INTERNAL_WIDTH - 20, INTERNAL_HEIGHT - 20))
        self.app.screen.blit(version_surf, version_rect)

    def draw_frame(self):
        if not pygame.get_init(): return
        if self.app.state == "BOOT_ANIMATION":
            self.draw_boot_animation()
        else:
            self.draw_ps2_background()
            if self.app.state == "MENU": self.draw_menu_state()
            elif self.app.state == "SETTINGS": self.draw_settings_state()
            elif self.app.state == "HOW_TO": self.draw_info_page("HOW_TO_TITLE", ["HOW_TO_PLAY", "HOW_TO_RIP", "HOW_TO_SETTINGS", "HOW_TO_EXIT"])
            elif self.app.state == "ABOUT": self.draw_info_page("ABOUT_TITLE", ["ABOUT_CREATED_BY"])
            elif self.app.state == "ARTWORK_SELECTION": self.draw_artwork_selection_state()
            elif self.app.state == "CONFIRM_ADD_TO_STEAM": self.draw_confirmation_state()
            elif self.app.state == "KEYBOARD": self.draw_keyboard_state()
            elif self.app.state == "LOADING": self.draw_loading_state()
            elif self.app.state == "MESSAGE": self.draw_message_state("SUCCESS_TITLE", PS1_GREEN)
            elif self.app.state == "ERROR": self.draw_message_state("ERROR_TITLE", PS1_RED)
            self.draw_version_number()
        scale = min(self.app.real_width / INTERNAL_WIDTH, self.app.real_height / INTERNAL_HEIGHT)
        new_w, new_h = int(INTERNAL_WIDTH * scale), int(INTERNAL_HEIGHT * scale)
        scaled_surf = pygame.transform.smoothscale(self.app.screen, (new_w, new_h))
        x_offset, y_offset = (self.app.real_width - new_w) // 2, (self.app.real_height - new_h) // 2
        self.app.monitor.fill(BLACK)
        self.app.monitor.blit(scaled_surf, (x_offset, y_offset))
        pygame.display.flip()
