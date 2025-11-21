# -*- coding: utf-8 -*-

import pygame
import sys
import time
import os
import pathlib
import threading
import gc
import fcntl
import subprocess
import requests
import io
import re
from queue import Queue

from .config import *
from .backend import *
from .animations import Spark, Orb
from .drawing import Drawing

def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)

class TheOrangeDiskApp:
    def __init__(self):
        # ... (stan aplikacji bez zmian) ...
        self.running = True
        self.state = "BOOT_ANIMATION"
        self.menu_index = 0
        self.settings_menu_index = 0
        self.artwork_selection_index = 0
        self.confirmation_index = 0
        self.message_text = ""
        self.loading_text = ""
        self.frame_count = 0
        self.progress_percent = 0.0
        self.progress_text = ""
        self.cancel_ripping = False
        self.rip_process = None
        self.game_name = "Unknown"
        self.rom_path = ""
        self.sudo_password = ""
        self.keyboard_callback = None
        self.keyboard_input = ""
        self.pending_action = None
        self.drive_path = None
        self.last_drive_check = 0
        self.kb_row = 1
        self.kb_col = 0
        self.kb_current_mode = "lower"
        # New artwork structure: organized by type
        self.artwork_data = {
            'grids': [],
            'grids_vertical': [],
            'heroes': [],
            'logos': [],
            'icons': []
        }
        self.artwork_surfaces = {
            'grids': [],
            'grids_vertical': [],
            'heroes': [],
            'logos': [],
            'icons': []
        }
        self.current_artwork_type = 'grids'  # Which type we're currently viewing
        self.artwork_type_index = 0  # Index within current type
        # Track the selected index for each artwork type
        self.artwork_type_indices = {
            'grids': 0,
            'grids_vertical': 0,
            'heroes': 0,
            'logos': 0,
            'icons': 0
        }
        self.selected_artworks = {
            'grid': None,           # Selected horizontal grid artwork path
            'grid_vertical': None,  # Selected vertical grid artwork path
            'hero': None,           # Selected hero artwork path
            'logo': None,           # Selected logo artwork path
            'icon': None            # Selected icon artwork path
        }
        self.action_queue = Queue()
        self.boot_anim_timer = time.time()
        self.boot_sparks = [Spark(is_boot_anim=True) for _ in range(150)]
        self.menu_orbs = [Orb() for _ in range(5)]
        self.bg_image = None
        self.translations = TRANSLATIONS
        self.current_lang = "EN"
        self.load_settings()
        self.drawing = Drawing(self)
        self.init_gui()
        self.check_drive_status_async()

    def ripping_worker(self):
        """Background thread that handles the disc ripping process with non-blocking I/O."""
        force_unmount(self.drive_path)
        main_file, toc_file, cue_file = None, None, None
        try:
            file_ext = "iso" if self.disc_type in ("PS2_CD", "PS2_DVD") else "bin"
            main_file = os.path.join(self.save_path, f"{self.game_name}.{file_ext}")
            toc_file = os.path.join(self.save_path, f"{self.game_name}.toc")
            cue_file = os.path.join(self.save_path, f"{self.game_name}.cue")
            cmd = []
            if self.disc_type == "PS1_CD":
                cmd = ["stdbuf", "-e0", "cdrdao", "read-cd", "--read-raw", "--datafile", main_file, "--device", self.drive_path, "--driver", "generic-mmc:0x20000", toc_file]
            else:
                cmd = ["stdbuf", "-e0", "dd", f"if={self.drive_path}", f"of={main_file}", "bs=2048", "status=progress"]
            if is_sandboxed(): cmd = ["flatpak-spawn", "--host"] + cmd

            # Clear LD_PRELOAD to avoid Steam overlay errors in stderr
            env = os.environ.copy()
            env.pop('LD_PRELOAD', None)
            self.rip_process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, env=env)
            
            if self.rip_process.stderr:
                # OSTATECZNA POPRAWKA: Użyj nieblokującego odczytu, aby GUI się nie zawieszało
                fd = self.rip_process.stderr.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                line_buffer = b""
                while True:
                    if self.cancel_ripping: break
                    try:
                        byte_chunk = self.rip_process.stderr.read(128)
                    except (IOError, OSError):
                        if self.rip_process.poll() is not None: break
                        time.sleep(0.1)
                        continue
                    if not byte_chunk:
                        if self.rip_process.poll() is not None: break
                        else: time.sleep(0.1); continue
                    
                    line_buffer += byte_chunk
                    # Przetwarzaj wiele linii na raz, jeśli przyszły w jednym kawałku
                    # dd używa \r do nadpisywania postępu, więc musimy to obsłużyć
                    while b'\r' in line_buffer or b'\n' in line_buffer:
                        split_char = b'\r' if b'\r' in line_buffer else b'\n'
                        line_bytes, line_buffer = line_buffer.split(split_char, 1)
                        line_str = line_bytes.decode('utf-8', errors='replace').strip()
                        # Parsuj tylko linie z danymi postępu (ignoruj puste i błędy LD_PRELOAD)
                        if line_str and 'LD_PRELOAD' not in line_str:
                            self.parse_rip_progress(line_str)
            
            exit_code = self.rip_process.wait()
            if self.cancel_ripping: return
            if exit_code != 0: raise Exception(f"Rip process exited with code {exit_code}")
            
            self.action_queue.put(("UPDATE_PROGRESS", {"text_key": "RIP_FINALIZING"}))
            if self.disc_type == "PS1_CD":
                try: run_host_command(["toc2cue", toc_file, cue_file])
                except: pass
            if not os.path.exists(main_file) or os.path.getsize(main_file) < 1000000:
                raise Exception(self.get_string("RIP_ERROR_SMALL_FILE"))
            
            log("Ripping successful. Queueing RIP_COMPLETE action.")
            self.action_queue.put(("RIP_COMPLETE", {"rom_path": main_file}))
        except Exception as e:
            log(f"!!! RIPPING WORKER ERROR: {e}")
            if not self.cancel_ripping: self.action_queue.put(("SHOW_ERROR", "RIP_ERROR_CONSOLE"))
        finally:
            if self.rip_process and self.rip_process.poll() is None: self.rip_process.kill(); self.rip_process.wait()
            if self.cancel_ripping:
                log(self.get_string("RIP_CLEANUP"))
                try:
                    if main_file and os.path.exists(main_file): os.remove(main_file)
                    if toc_file and os.path.exists(toc_file): os.remove(toc_file)
                    if cue_file and os.path.exists(cue_file): os.remove(cue_file)
                except Exception as e: log(f"Error during cleanup: {e}")
            self.rip_process, self.cancel_ripping = None, False

    def process_action_queue(self):
        while not self.action_queue.empty():
            try:
                action, data = self.action_queue.get_nowait()
                log(f"ACTION_QUEUE: Executing '{action}'")
                if action == "UPDATE_PROGRESS":
                    self.progress_percent = data.get('percent', self.progress_percent)
                    self.progress_text = self.get_string(data['text_key'], **data.get('kwargs', {}))
                    log(f"GUI Update: Progress set to {self.progress_percent:.2f}%")
                # ... (reszta bez zmian) ...
                elif action == "SET_STATE": self.state = data
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
                elif action == "START_ARTWORK_SEARCH":
                    self.state = "LOADING"
                    self.loading_text = self.get_string("ARTWORK_SEARCHING")
                    threading.Thread(target=self.artwork_search_worker, args=(data,)).start()
                elif action == "SHOW_ARTWORK_CHOOSER":
                    self.artwork_data = data['artwork_data']
                    # Initialize surfaces for each type
                    for art_type in self.artwork_data:
                        self.artwork_surfaces[art_type] = [None] * len(self.artwork_data[art_type])
                    # Reset artwork type indices
                    self.artwork_type_indices = {
                        'grids': 0,
                        'grids_vertical': 0,
                        'heroes': 0,
                        'logos': 0,
                        'icons': 0
                    }
                    # Start with grids (most important)
                    self.current_artwork_type = 'grids'
                    self.artwork_type_index = 0
                    self.state = "ARTWORK_SELECTION"
                    # Download first grid artwork
                    if len(self.artwork_data['grids']) > 0:
                        threading.Thread(target=self.download_artwork_worker, args=('grids', 0)).start()
                elif action == "RIP_COMPLETE":
                    self.rom_path = data['rom_path']
                    threading.Thread(target=self.finalize_rip_worker).start()
            except Exception as e:
                log(f"Action queue error: {e}")

    # ... (reszta pliku bez zmian) ...
    def load_settings(self):
        log(f"Loading settings from: {CONFIG_PATH}")
        try:
            with open(CONFIG_PATH, "r") as f:
                lang = f.read().strip().upper()
                if lang in ["EN", "PL"]: self.current_lang = lang
        except: self.current_lang = "EN"

    def save_settings(self):
        log(f"Saving language ({self.current_lang}) to: {CONFIG_PATH}")
        try:
            with open(CONFIG_PATH, "w") as f: f.write(self.current_lang)
        except Exception as e: log(f"!!! CRITICAL ERROR: Could not save settings: {e}")

    def get_string(self, key, **kwargs):
        try:
            return self.translations.get(key, {}).get(self.current_lang, f"<{key}>").format(**kwargs)
        except Exception as e:
            log(f"Translation error for key '{key}': {e}")
            return f"<{key}_ERROR>"

    def init_gui(self):
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
        except Exception as e: log(self.get_string("LOADING_BG_ERROR", e=e))
        try:
            self.font_title = pygame.font.SysFont("sans", 64, bold=True)
            self.font_large = pygame.font.SysFont("sans", 48, bold=True)
            self.font_med = pygame.font.SysFont("sans", 42)
            self.font_small = pygame.font.SysFont("sans", 28)
            self.font_mono = pygame.font.SysFont("monospace", 28)
        except:
            self.font_title = pygame.font.Font(None, 64)
            self.font_large = pygame.font.Font(None, 48)
            self.font_med = pygame.font.Font(None, 42)
            self.font_small = pygame.font.Font(None, 28)
            self.font_mono = pygame.font.Font(None, 28)
        self.init_joysticks()
        self.kb_layouts = {"lower": [['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'DEL'], ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'ENTER'], ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', '-', '_'], ['SHIFT', 'z', 'x', 'c', 'v', 'b', 'n', 'm', '.', 'SPACE']], "upper": [['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', 'DEL'], ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'ENTER'], ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', '+', '='], ['SHIFT', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', 'SPACE']]}

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
        log("Starting main loop...")
        while self.running:
            try:
                if not pygame.get_init():
                    log("Pygame not initialized, initializing GUI...")
                    self.init_gui()
                if self.state in ("MENU", "SETTINGS", "HOW_TO", "ABOUT"):
                    self.check_drive_status_async()
                self.process_action_queue()
                self.handle_events()
                self.drawing.draw_frame()
                self.clock.tick(30)
                self.frame_count += 1

                # Log state transitions
                if self.frame_count % 300 == 0:  # Every 10 seconds
                    log(f"Running... State: {self.state}, Frame: {self.frame_count}")
            except Exception as e:
                log(f"!!! CRITICAL ERROR in main loop: {e}")
                import traceback
                traceback.print_exc()
                # Try to show error to user
                try:
                    self.show_error(f"Critical error: {str(e)}")
                    self.state = "MENU"
                except:
                    # If we can't even show the error, just exit
                    self.running = False
        log("Main loop ended, closing GUI...")
        self.close_gui()
        log("Exiting application")
        sys.exit()

    def check_drive_status_async(self):
        current_time = time.time()
        if current_time - self.last_drive_check > 2.0:
            self.last_drive_check = current_time
            threading.Thread(target=lambda: setattr(self, 'drive_path', get_drive_device_path()), daemon=True).start()

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
                log("Boot animation ended, transitioning to MENU")
                self.state = "MENU"
        elif self.state == "MENU":
            if dy != 0: self.menu_index = (self.menu_index + dy) % len(self.get_main_menu_options())
            if is_enter: self.execute_menu_option()
            if is_back: self.running = False
        elif self.state == "ARTWORK_SELECTION":
            # Left/Right: Navigate within current artwork type
            if dx != 0:
                current_list = self.artwork_data[self.current_artwork_type]
                if len(current_list) > 0:
                    self.artwork_type_index = (self.artwork_type_index + dx) % len(current_list)
                    # Update the tracked index for this type
                    self.artwork_type_indices[self.current_artwork_type] = self.artwork_type_index
                    # Download if not already loaded
                    if self.artwork_surfaces[self.current_artwork_type][self.artwork_type_index] is None:
                        threading.Thread(target=self.download_artwork_worker,
                                       args=(self.current_artwork_type, self.artwork_type_index)).start()

            # Up/Down: Switch between artwork types (grids, grids_vertical, heroes, logos, icons)
            if dy != 0:
                types_with_data = [t for t in ['grids', 'grids_vertical', 'heroes', 'logos', 'icons'] if len(self.artwork_data[t]) > 0]
                if len(types_with_data) > 1:
                    current_type_idx = types_with_data.index(self.current_artwork_type) if self.current_artwork_type in types_with_data else 0
                    new_type_idx = (current_type_idx + dy) % len(types_with_data)
                    self.current_artwork_type = types_with_data[new_type_idx]
                    # Restore the previously selected index for this type
                    self.artwork_type_index = self.artwork_type_indices[self.current_artwork_type]
                    # Download artwork at this index if not loaded
                    if len(self.artwork_surfaces[self.current_artwork_type]) > self.artwork_type_index:
                        if self.artwork_surfaces[self.current_artwork_type][self.artwork_type_index] is None:
                            threading.Thread(target=self.download_artwork_worker,
                                           args=(self.current_artwork_type, self.artwork_type_index)).start()
                    else:
                        # Index out of range, reset to 0
                        self.artwork_type_index = 0
                        self.artwork_type_indices[self.current_artwork_type] = 0
                        if len(self.artwork_surfaces[self.current_artwork_type]) > 0 and self.artwork_surfaces[self.current_artwork_type][0] is None:
                            threading.Thread(target=self.download_artwork_worker,
                                           args=(self.current_artwork_type, 0)).start()

            if is_enter:
                log("Artwork selected. Proceeding to check prerequisites for ripping.")
                self.check_prerequisites_and_run()
            if is_back: self.state = "MENU"
        elif self.state == "CONFIRM_ADD_TO_STEAM":
            if dx != 0: self.confirmation_index = (self.confirmation_index + dx) % 2
            if is_back: self.state = "MENU"
            if is_enter:
                if self.confirmation_index == 0: self.add_to_steam_and_restart()
                else: self.state = "MENU"
        elif self.state == "SETTINGS":
            # Handle settings menu navigation
            if dy != 0:
                self.settings_menu_index = (self.settings_menu_index + dy) % len(self.get_settings_menu_options())
            if is_enter:
                self.execute_settings_option()
            if is_back:
                self.state = "MENU"
        elif self.state == "HOW_TO":
            # Handle "How to Use" screen - only back button works
            if is_back or is_enter:
                self.state = "MENU"
        elif self.state == "ABOUT":
            # Handle "About" screen - only back button works
            if is_back or is_enter:
                self.state = "MENU"
        elif self.state == "KEYBOARD":
            current_layout = self.kb_layouts[self.kb_current_mode]
            if dy != 0:
                self.kb_row = (self.kb_row + dy) % len(current_layout)
                self.kb_col = min(self.kb_col, len(current_layout[self.kb_row]) - 1)
            if dx != 0:
                self.kb_col = (self.kb_col + dx) % len(current_layout[self.kb_row])
            if is_enter:
                key = current_layout[self.kb_row][self.kb_col]
                if key == "SPACE": self.keyboard_input += " "
                elif key == "DEL": self.keyboard_input = self.keyboard_input[:-1]
                elif key == "ENTER":
                    if self.keyboard_input.strip():  # Only proceed if input is not empty
                        callback = self.keyboard_callback
                        self.keyboard_callback = None
                        try:
                            callback(self.keyboard_input)
                        except Exception as e:
                            log(f"!!! Error in keyboard callback: {e}")
                            import traceback
                            traceback.print_exc()
                            self.state = "MENU"
                    else:
                        log("Empty input, ignoring ENTER")
                elif key == "SHIFT":
                    self.kb_current_mode = "upper" if self.kb_current_mode == "lower" else "lower"
                else:
                    self.keyboard_input += key
            if is_back: self.state = "MENU"

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
            self.action_queue.put(("START_KEYBOARD", {"key": "GAME_NAME_PROMPT", "callback": self.on_game_name_ready_for_artwork}))

    def on_game_name_ready_for_artwork(self, name):
        """
        Called when user enters a game name for ripping.
        Checks if API key is configured before starting artwork search.
        """
        self.game_name = name if name else "Unknown"
        log(f"User entered game name: '{self.game_name}'.")

        # Check if SteamGridDB API key is configured
        from .config import STEAMGRIDDB_API_KEY
        if not STEAMGRIDDB_API_KEY or STEAMGRIDDB_API_KEY == "YOUR_API_KEY_HERE":
            log("SteamGridDB API key not configured. Skipping artwork selection.")
            # Skip artwork selection and go directly to ripping
            self.pending_action = "RIP"
            self.check_prerequisites_and_run()
        else:
            log("Starting artwork search.")
            self.action_queue.put(("START_ARTWORK_SEARCH", self.game_name))

    def artwork_search_worker(self, game_name):
        """
        Background worker that searches for game artwork on SteamGridDB.
        This runs in a separate thread to avoid blocking the UI.
        """
        log(f"Artwork Worker: Searching for '{game_name}'...")
        try:
            # Double-check API key (should have been checked earlier, but just in case)
            log(f"Checking API key...")
            if not STEAMGRIDDB_API_KEY or STEAMGRIDDB_API_KEY == "YOUR_API_KEY_HERE":
                log(f"!!! API key is missing or invalid")
                self.action_queue.put(("SHOW_ERROR", "ARTWORK_API_KEY_MISSING"))
                return

            log(f"Searching game on SteamGridDB...")
            game_id = search_game_on_steamgriddb(game_name)
            log(f"Got game ID: {game_id}")
            if not game_id:
                raise Exception(f"No game ID found for '{game_name}'.")

            log(f"Fetching artwork for game ID {game_id}...")
            artwork_data = get_artwork_from_steamgriddb(game_id)
            log(f"Artwork data received: {[(k, len(v)) for k, v in artwork_data.items()]}")

            # Check if we got any artwork at all
            total_artworks = sum(len(artwork_data[t]) for t in artwork_data)
            log(f"Total artworks: {total_artworks}")
            if total_artworks == 0:
                raise Exception("No artwork found for this game ID.")

            log(f"Artwork Worker: Found {total_artworks} total artworks across all types.")
            log(f"Putting SHOW_ARTWORK_CHOOSER action in queue...")
            self.action_queue.put(("SHOW_ARTWORK_CHOOSER", {"artwork_data": artwork_data}))
            log(f"Action queued successfully")
        except Exception as e:
            log(f"!!! ARTWORK WORKER ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.action_queue.put(("SHOW_ERROR", "ARTWORK_GAME_NOT_FOUND"))

    def download_artwork_worker(self, art_type, index, force_save=False):
        """Download artwork of a specific type and index"""
        try:
            artwork_item = self.artwork_data[art_type][index]
            url = artwork_item['url']
            log(f"Downloading {art_type} artwork index {index} from {url}")
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()
            image_data = response.content
            image_surface = pygame.image.load(io.BytesIO(image_data))

            # Ensure surfaces list is long enough
            while len(self.artwork_surfaces[art_type]) <= index:
                self.artwork_surfaces[art_type].append(None)

            self.artwork_surfaces[art_type][index] = image_surface.convert_alpha()
            log(f"Successfully loaded and converted {art_type} artwork index {index} into memory.")

            if force_save:
                # Save to a persistent location instead of /tmp
                artwork_dir = pathlib.Path.home() / ".cache/the_orange_disk/artwork"
                artwork_dir.mkdir(parents=True, exist_ok=True)
                temp_path = artwork_dir / f"{art_type}_{int(time.time())}.png"
                with open(temp_path, 'wb') as f: f.write(image_data)
                log(f"Artwork saved to: {temp_path}")
                return str(temp_path)
        except Exception as e:
            log(f"!!! ARTWORK DOWNLOAD ERROR for {art_type} index {index}: {e}")
            return None

    def check_prerequisites_and_run(self):
        if not check_drive_permissions(self.drive_path):
            self.start_auto_fix()
        elif not check_tool_installed("isoinfo"):
            self.start_tool_install()
        else:
            if self.pending_action == "LAUNCH": self.launch_game_detection_thread()
            elif self.pending_action == "RIP": self.rip_detection_worker()

    def finalize_rip_worker(self):
        log("Finalizing rip: downloading all selected artworks to files.")

        # Save the currently selected artwork for each type
        for art_type in ['grids', 'grids_vertical', 'heroes', 'logos', 'icons']:
            if len(self.artwork_data[art_type]) > 0:
                # Use the selected index for this type
                index = self.artwork_type_indices.get(art_type, 0)

                # If we have a loaded surface at this index, save it
                if index < len(self.artwork_surfaces[art_type]) and self.artwork_surfaces[art_type][index] is not None:
                    saved_path = self.download_artwork_worker(art_type, index, force_save=True)
                    if saved_path:
                        # Map to Steam's naming convention
                        if art_type == 'grids':
                            self.selected_artworks['grid'] = saved_path
                        elif art_type == 'grids_vertical':
                            self.selected_artworks['grid_vertical'] = saved_path
                        elif art_type == 'heroes':
                            self.selected_artworks['hero'] = saved_path
                        elif art_type == 'logos':
                            self.selected_artworks['logo'] = saved_path
                        elif art_type == 'icons':
                            self.selected_artworks['icon'] = saved_path
                        log(f"Saved {art_type} at index {index}: {saved_path}")

        # Check if we got at least the grid artwork (required)
        if self.selected_artworks['grid']:
            log("Artwork saved. Moving to confirmation screen.")
            self.action_queue.put(("SET_STATE", "CONFIRM_ADD_TO_STEAM"))
        else:
            log("!!! Final artwork download failed.")
            self.action_queue.put(("SHOW_ERROR", "Błąd pobierania finalnej okładki."))

    def add_to_steam_and_restart(self):
        log("Preparing Steam restart task...")
        self.state = "LOADING"
        self.loading_text = self.get_string("ARTWORK_ADDING_TO_STEAM")
        task_file_path = os.path.expanduser("~/.the_orange_disk.task")
        with open(task_file_path, "w") as f:
            f.write(f'GAME_NAME="{self.game_name}"\n')
            f.write(f'ROM_PATH="{self.rom_path}"\n')
            # Write all artwork paths
            f.write(f'ARTWORK_GRID="{self.selected_artworks.get("grid", "")}"\n')
            f.write(f'ARTWORK_GRID_VERTICAL="{self.selected_artworks.get("grid_vertical", "")}"\n')
            f.write(f'ARTWORK_HERO="{self.selected_artworks.get("hero", "")}"\n')
            f.write(f'ARTWORK_LOGO="{self.selected_artworks.get("logo", "")}"\n')
            f.write(f'ARTWORK_ICON="{self.selected_artworks.get("icon", "")}"\n')
        install_dir = os.path.dirname(os.path.dirname(__file__))
        restart_script_path = os.path.join(install_dir, "restart_steam.sh")
        subprocess.Popen([restart_script_path], start_new_session=True)
        self.running = False
    
    def execute_settings_option(self):
        opt = self.get_settings_menu_options()[self.settings_menu_index]
        if opt == self.get_string("SETTINGS_BACK"):
            self.state = "MENU"
        elif opt in (self.get_string("SETTINGS_LANGUAGE_PL"), self.get_string("SETTINGS_LANGUAGE_EN")):
            self.current_lang = "EN" if self.current_lang == "PL" else "PL"
            self.save_settings()
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
        self.state = "MENU"
    def rip_detection_worker(self):
        try:
            self.disc_sectors, file_list_upper = get_disc_info(self.drive_path)
            self.disc_type = detect_disc_type(self.disc_sectors, file_list_upper)
        except Exception as e:
            self.action_queue.put(("SHOW_ERROR", str(e)))
            return
        if self.disc_type == "UNKNOWN":
            self.action_queue.put(("SHOW_ERROR", "DISC_TYPE_UNKNOWN"))
            return
        if self.disc_type == "PS1_CD":
            self.save_path = get_emudeck_rom_path("psx")
            if not check_tool_installed("cdrdao"):
                self.action_queue.put(("SHOW_ERROR", "RIP_PSX_NO_CDRDAO"))
                return
            self.start_ripping_thread()
        elif self.disc_type in ("PS2_CD", "PS2_DVD"):
            self.save_path = get_emudeck_rom_path("ps2")
            self.start_ripping_thread()
    def start_ripping_thread(self):
        self.action_queue.put(("SET_LOADING_TEXT", {"key": "RIP_STARTING", "kwargs": {"game_name": self.game_name}}))
        self.progress_percent, self.rip_total_seconds, self.rip_total_bytes = 0.0, 1, 1
        self.progress_text = self.get_string("RIP_PROGRESS_START")
        self.cancel_ripping = False
        if self.disc_type in ("PS2_CD", "PS2_DVD"):
            self.rip_total_bytes = max(1, self.disc_sectors * 2048)
        threading.Thread(target=self.ripping_worker, daemon=True).start()
    def parse_rip_progress(self, line):
        log(f"RIP_PARSE: {line}")
        try:
            if self.disc_type == "PS1_CD":
                match_total = re.search(r"^\s*\d+\s+DATA\s+.*?\s+(\d{2}):(\d{2}):\d{2}\(\d+\)$", line.strip())
                if match_total:
                    self.rip_total_seconds = max(1, (int(match_total.group(1)) * 60) + int(match_total.group(2)))
                    return
                match_current = re.search(r"^(\d{2}):(\d{2}):\d{2}", line.strip())
                if match_current:
                    curr_m, curr_s = int(match_current.group(1)), int(match_current.group(2))
                    percent = min(100, ((curr_m * 60) + curr_s) / self.rip_total_seconds * 100)
                    total_m, total_s = divmod(self.rip_total_seconds, 60)
                    self.action_queue.put(("UPDATE_PROGRESS", {"percent": percent, "text_key": "RIP_PROGRESS_TIME", "kwargs": {"curr_m": curr_m, "curr_s": curr_s, "total_m": total_m, "total_s": total_s}}))
            else:
                # dd output format: "12345678 bytes (12 MB, 12 MiB) copied, 1 s, 12 MB/s"
                match_bytes = re.search(r"(\d+)\s+bytes", line)
                if match_bytes:
                    current_bytes = int(match_bytes.group(1))
                    percent = min(100, (current_bytes / self.rip_total_bytes) * 100)
                    curr_mb, total_mb = int(current_bytes / 1024 / 1024), int(self.rip_total_bytes / 1024 / 1024)
                    log(f"Progress update: {percent:.1f}% ({curr_mb} MB / {total_mb} MB)")
                    self.action_queue.put(("UPDATE_PROGRESS", {"percent": percent, "text_key": "RIP_PROGRESS_SIZE", "kwargs": {"curr_mb": curr_mb, "total_mb": total_mb}}))
        except Exception as e:
            log(f"Error parsing rip progress: {e}")
    def show_error(self, msg_key):
        self.state = "ERROR"
        self.message_text = self.get_string(msg_key)
    def show_message(self, msg_key):
        self.state = "MESSAGE"
        self.message_text = self.get_string(msg_key)
    def start_auto_fix(self):
        self.action_queue.put(("START_KEYBOARD", {"key": "PERMS_REQUIRED", "callback": self.on_fix_password_ready}))
    def on_fix_password_ready(self, password):
        self.sudo_password = password
        self.action_queue.put(("SET_LOADING_TEXT", {"key": "FIXING_PERMS"}))
        threading.Thread(target=self.auto_fix_worker, daemon=True).start()
    def auto_fix_worker(self):
        try:
            run_sudo_command("modprobe sg", self.sudo_password)
            time.sleep(1)
            run_sudo_command(f"sh -c 'chmod 666 {self.drive_path}'", self.sudo_password)
            run_sudo_command("sh -c 'chmod 666 /dev/sg*'", self.sudo_password)
            run_sudo_command("usermod -a -G optical,disk deck", self.sudo_password)
            self.action_queue.put(("SET_LOADING_TEXT", {"key": "READY_CHECKING_TOOLS"}))
            time.sleep(1)
            if not check_tool_installed("isoinfo"):
                self.action_queue.put(("START_KEYBOARD", {"key": "TOOL_NOT_FOUND", "kwargs": {"tool": "isoinfo"}, "callback": self.on_install_password_ready}))
            else:
                self.action_queue.put(("SET_LOADING_TEXT", {"key": "ALL_READY"}))
                time.sleep(1)
                if self.pending_action == "LAUNCH": self.launch_game_detection_thread()
                elif self.pending_action == "RIP": self.action_queue.put(("EXECUTE_RIP_FLOW", None))
                self.pending_action = None
        except Exception as e:
            self.action_queue.put(("SHOW_ERROR", str(e)))
    def start_tool_install(self):
        self.action_queue.put(("START_KEYBOARD", {"key": "TOOL_NOT_FOUND", "kwargs": {"tool": "isoinfo"}, "callback": self.on_install_password_ready}))
    def on_install_password_ready(self, password):
        self.sudo_password = password
        self.action_queue.put(("SET_LOADING_TEXT", {"key": "INSTALLING_TOOL", "kwargs": {"tool": "cdrkit"}}))
        threading.Thread(target=self.install_worker, daemon=True).start()
    def install_worker(self):
        try:
            run_sudo_command("steamos-readonly disable", self.sudo_password)
            run_sudo_command("pacman-key --init", self.sudo_password)
            run_sudo_command("pacman-key --populate archlinux holo", self.sudo_password)
            run_sudo_command("rm -f /var/cache/pacman/pkg/cdrdao*", self.sudo_password)
            run_sudo_command("rm -f /var/cache/pacman/pkg/cdrkit*", self.sudo_password)
            run_sudo_command("pacman -S cdrdao cdrkit --noconfirm --needed --overwrite '*'", self.sudo_password)
            run_sudo_command("steamos-readonly enable", self.sudo_password)
            self.action_queue.put(("SET_LOADING_TEXT", {"key": "ALL_READY"}))
            time.sleep(1)
            if self.pending_action == "LAUNCH": self.launch_game_detection_thread()
            elif self.pending_action == "RIP": self.action_queue.put(("EXECUTE_RIP_FLOW", None))
            self.pending_action = None
        except Exception as e:
            self.action_queue.put(("SHOW_ERROR", self.get_string("INSTALL_ERROR", e=e)))
