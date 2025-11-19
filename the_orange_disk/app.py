# -*- coding: utf-8 -*-

# This file contains the main application class, state management,
# and event handling logic.

import pygame
import sys
import time
import os
import threading
import gc
from queue import Queue

# POPRAWKA: Importujemy CONFIG_PATH, którego brakowało
from .config import *
from .backend import *
from .animations import Spark, Orb
from .drawing import Drawing

class TheOrangeDiskApp:
    def __init__(self):
        # --- Application State ---
        self.running = True
        self.state = "BOOT_ANIMATION"
        self.menu_index = 0
        self.settings_menu_index = 0
        self.message_text = ""
        self.loading_text = ""
        self.frame_count = 0

        # --- Ripping State ---
        self.progress_percent = 0.0
        self.progress_text = ""
        self.cancel_ripping = False
        self.rip_process = None
        self.rip_total_seconds = 1
        self.rip_total_bytes = 1

        # --- System & Disc State ---
        self.game_name = "Unknown"
        self.sudo_password = ""
        self.keyboard_callback = None
        self.keyboard_input = ""
        self.save_path = ""
        self.pending_action = None
        self.disc_type = "UNKNOWN"
        self.disc_sectors = 0
        self.drive_path = None
        self.last_drive_check = 0

        # --- Threading & Animation ---
        self.action_queue = Queue()
        self.boot_anim_timer = time.time()
        self.boot_sparks = [Spark(is_boot_anim=True) for _ in range(150)]
        self.menu_orbs = [Orb() for _ in range(5)]
        self.bg_image = None

        # --- Language & Settings ---
        self.translations = TRANSLATIONS
        self.current_lang = "EN" # Default to English for first launch
        self.load_settings()

        # --- Modules ---
        self.drawing = Drawing(self)
        self.init_gui()
        self.check_drive_status_async()

    def load_settings(self):
        """Loads the preferred language from the config file."""
        log(f"Loading settings from: {CONFIG_PATH}")
        try:
            with open(CONFIG_PATH, "r") as f:
                lang = f.read().strip().upper()
                if lang in ["EN", "PL"]:
                    self.current_lang = lang
                    log(f"Loaded language: {lang}")
        except FileNotFoundError:
            log("Config file not found. Defaulting to English.")
            self.current_lang = "EN"
        except Exception as e:
            log(f"Error loading settings: {e}. Defaulting to English.")
            self.current_lang = "EN"

    def save_settings(self):
        """Saves the current language to the config file."""
        log(f"Saving language ({self.current_lang}) to: {CONFIG_PATH}")
        try:
            with open(CONFIG_PATH, "w") as f:
                f.write(self.current_lang)
        except Exception as e:
            log(f"!!! CRITICAL ERROR: Could not save settings: {e}")

    def get_string(self, key, **kwargs):
        """Gets a translated string by its key."""
        try:
            template = self.translations.get(key, {}).get(self.current_lang, f"<{key}>")
            return template.format(**kwargs)
        except Exception as e:
            log(f"Translation error for key '{key}': {e}")
            return f"<{key}_ERROR>"

    def init_gui(self):
        """Initializes Pygame, the display, and fonts."""
        log("Initializing GUI...")
        pygame.init()
        pygame.mouse.set_visible(False)

        info = pygame.display.Info()
        self.real_width, self.real_height = info.current_w, info.current_h
        self.monitor = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.screen = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        self.clock = pygame.time.Clock()

        try:
            assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'backgrounds')
            bg_path = os.path.join(assets_dir, "pexels-felix-mittermeier-956981.jpg")
            if os.path.exists(bg_path):
                self.bg_image = pygame.image.load(bg_path).convert()
                self.bg_image = pygame.transform.scale(self.bg_image, (INTERNAL_WIDTH, INTERNAL_HEIGHT))
        except Exception as e:
            log(self.get_string("LOADING_BG_ERROR", e=e))
            self.bg_image = None

        try:
            self.font_title = pygame.font.SysFont("sans", 64, bold=True)
            self.font_med = pygame.font.SysFont("sans", 42)
            self.font_small = pygame.font.SysFont("sans", 28)
            self.font_mono = pygame.font.SysFont("monospace", 28)
        except:
            log(self.get_string("FONT_ERROR"))
            self.font_title = pygame.font.Font(None, 64)
            self.font_med = pygame.font.Font(None, 42)
            self.font_small = pygame.font.Font(None, 28)
            self.font_mono = pygame.font.Font(None, 28)

        self.init_joysticks()
        self.kb_layouts = {
            "lower": [['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'DEL'], ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'ENTER'], ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', '-', '_'], ['SHIFT', 'z', 'x', 'c', 'v', 'b', 'n', 'm', '.', 'SPACE']],
            "upper": [['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', 'DEL'], ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'ENTER'], ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', '+', '='], ['SHIFT', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', 'SPACE']]
        }

    def init_joysticks(self):
        if not pygame.joystick.get_init(): pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joy in self.joysticks: joy.init()

    def close_gui(self):
        log("Closing GUI...")
        try:
            if pygame.joystick.get_init():
                for joy in self.joysticks: joy.quit()
                pygame.joystick.quit()
            if pygame.get_init(): pygame.quit()
        except: pass
        gc.collect()

    def run(self):
        """The main application loop."""
        while self.running:
            if not pygame.get_init(): self.init_gui()
            if self.state in ("MENU", "SETTINGS", "HOW_TO", "ABOUT"): self.check_drive_status_async()
            self.process_action_queue()
            self.handle_events()
            self.drawing.draw_frame() # Use the drawing module
            self.clock.tick(30)
            self.frame_count += 1
        self.close_gui()
        sys.exit()

    def check_drive_status_async(self):
        current_time = time.time()
        if current_time - self.last_drive_check > 2.0:
            log("Checking drive status...")
            self.last_drive_check = current_time
            self.drive_path = get_drive_device_path()
            log(f"Drive present: {self.drive_path is not None}")

    def process_action_queue(self):
        while not self.action_queue.empty():
            try:
                action, data = self.action_queue.get_nowait()
                log(f"ACTION_QUEUE: Executing '{action}'")
                if action == "SET_STATE": self.state = data
                elif action == "SHOW_ERROR": self.show_error(data)
                elif action == "SHOW_MESSAGE": self.show_message(data)
                elif action == "SET_LOADING_TEXT":
                    self.state = "LOADING"
                    self.loading_text = self.get_string(data['key'], **data.get('kwargs', {}))
                elif action == "START_KEYBOARD":
                    self.state = "KEYBOARD"
                    self.message_text = self.get_string(data['key'], **data.get('kwargs', {}))
                    self.keyboard_input = ""
                    self.keyboard_callback = data['callback']
                elif action == "EXECUTE_LAUNCH_DETACHED": self.launch_game_detached_from_queue(data)
                elif action == "EXECUTE_RIP_FLOW": self.start_ripping_flow()
                elif action == "UPDATE_PROGRESS":
                    self.progress_percent = data.get('percent', self.progress_percent)
                    self.progress_text = self.get_string(data['text_key'], **data.get('kwargs', {}))
            except Exception as e:
                log(f"Action queue error: {e}")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if event.type in [pygame.KEYDOWN, pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION]:
                self.process_input(event)

    def process_input(self, event):
        is_enter = (event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_SPACE]) or \
                   (event.type == pygame.JOYBUTTONDOWN and event.button == 0)
        is_back = (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or \
                  (event.type == pygame.JOYBUTTONDOWN and event.button == 1)
        dx, dy = 0, 0
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: dy = -1
            if event.key == pygame.K_DOWN: dy = 1
            if event.key == pygame.K_LEFT: dx = -1
            if event.key == pygame.K_RIGHT: dx = 1
        elif event.type == pygame.JOYHATMOTION:
            dx, dy = event.value[0], -event.value[1]

        if self.state == "BOOT_ANIMATION":
            if is_enter or is_back:
                self.state = "MENU"
                self.frame_count = 0
        elif self.state == "MENU":
            menu_options = self.get_main_menu_options()
            if dy != 0: self.menu_index = (self.menu_index + dy) % len(menu_options)
            if is_enter: self.execute_menu_option()
            if is_back: self.running = False
        elif self.state == "SETTINGS":
            settings_options = self.get_settings_menu_options()
            if dy != 0: self.settings_menu_index = (self.settings_menu_index + dy) % len(settings_options)
            if is_enter: self.execute_settings_option()
            if is_back: self.state = "MENU"
        elif self.state in ["HOW_TO", "ABOUT"]:
            if is_back or is_enter: self.state = "MENU"
        elif self.state == "KEYBOARD":
            # ... (keyboard logic)
            pass
        elif self.state == "LOADING":
            if is_back:
                self.cancel_ripping = True
                self.state = "MENU"
        elif self.state in ["MESSAGE", "ERROR"]:
            if is_enter or is_back: self.state = "MENU"

    def get_main_menu_options(self):
        return [
            self.get_string("PLAY_GAME"), self.get_string("RIP_DISC"),
            self.get_string("HOW_TO_USE"), self.get_string("ABOUT"),
            self.get_string("SETTINGS"), self.get_string("EXIT")
        ]

    def get_settings_menu_options(self):
        lang_key = "SETTINGS_LANGUAGE_EN" if self.current_lang == "EN" else "SETTINGS_LANGUAGE_PL"
        return [self.get_string(lang_key), self.get_string("SETTINGS_BACK")]

    def execute_menu_option(self):
        opt = self.get_main_menu_options()[self.menu_index]
        if opt in (self.get_string("PLAY_GAME"), self.get_string("RIP_DISC")) and not self.drive_path:
            self.show_error("DRIVE_NOT_FOUND_ERROR")
            return
        if opt == self.get_string("EXIT"): self.running = False
        elif opt == self.get_string("SETTINGS"): self.state = "SETTINGS"
        elif opt == self.get_string("HOW_TO_USE"): self.state = "HOW_TO"
        elif opt == self.get_string("ABOUT"): self.state = "ABOUT"
        elif opt == self.get_string("PLAY_GAME"):
            self.pending_action = "LAUNCH"
            self.check_prerequisites_and_run()
        elif opt == self.get_string("RIP_DISC"):
            self.pending_action = "RIP"
            self.check_prerequisites_and_run()

    def execute_settings_option(self):
        opt = self.get_settings_menu_options()[self.settings_menu_index]
        if opt == self.get_string("SETTINGS_BACK"):
            self.state = "MENU"
        elif opt in (self.get_string("SETTINGS_LANGUAGE_PL"), self.get_string("SETTINGS_LANGUAGE_EN")):
            self.current_lang = "EN" if self.current_lang == "PL" else "PL"
            self.save_settings()

    def check_prerequisites_and_run(self):
        if not check_drive_permissions(self.drive_path):
            self.start_auto_fix()
        elif not check_tool_installed("isoinfo"):
            self.start_tool_install()
        else:
            if self.pending_action == "LAUNCH": self.launch_game_detection_thread()
            elif self.pending_action == "RIP": self.start_ripping_flow()

    def launch_game_detection_thread(self):
        log("launch_game_detection_thread: Starting...")
        self.action_queue.put(("SET_LOADING_TEXT", {"key": "DETECTING_DISC"}))
        threading.Thread(target=self.launch_game_worker, daemon=True).start()

    def launch_game_worker(self):
        log("launch_game_worker: Thread started.")
        try:
            sectors, file_list_upper = get_disc_info(self.drive_path)
            disc_type = detect_disc_type(sectors, file_list_upper)
            log(f"launch_game_worker: Detected disc type: {disc_type}")
            emulator_cmd, loading_key = "", ""
            if disc_type == "PS1_CD":
                loading_key = "STARTING_PS1"
                appimage = find_appimage("DuckStation")
                emulator_cmd = appimage if appimage else "flatpak run org.duckstation.DuckStation"
            elif disc_type in ("PS2_CD", "PS2_DVD"):
                loading_key = "STARTING_PS2"
                appimage = find_appimage("PCSX2")
                emulator_cmd = appimage if appimage else "flatpak run net.pcsx2.PCSX2 --fullscreen"
            else:
                raise Exception(self.get_string("LAUNCH_ERROR_UNKNOWN"))
            self.action_queue.put(("SET_LOADING_TEXT", {"key": loading_key, "kwargs": {"disc_type": disc_type}}))
            self.action_queue.put(("EXECUTE_LAUNCH_DETACHED", emulator_cmd))
        except Exception as e:
            log(f"!!! THREAD ERROR: {e}")
            self.action_queue.put(("SHOW_ERROR", str(e)))

    def launch_game_detached_from_queue(self, emulator_cmd):
        force_unmount(self.drive_path)
        time.sleep(1)
        
        # OSTATECZNA POPRAWKA: Minimalizuj okno zamiast zamykać GUI
        pygame.display.iconify()

        cmd = emulator_cmd.split() + [self.drive_path]
        if is_sandboxed(): cmd = ["flatpak-spawn", "--host"] + cmd
        
        log(f"Starting detached process: {cmd}")
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True, close_fds=True)
            while process.poll() is None: time.sleep(1)
            log(self.get_string("GAME_OVER"))
        except Exception as e:
            log(f"Error launching game: {e}")

        # Po zakończeniu gry, przywróć stan aplikacji
        # Nie ma potrzeby ponownej inicjalizacji, bo nic nie zamykaliśmy
        self.state = "MENU"
    
    # ... (reszta workerów bez zmian)
