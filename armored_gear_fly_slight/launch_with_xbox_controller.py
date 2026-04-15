#!/usr/bin/env python3
"""
Armored Gear: Fly Slight - Xbox Series Controller Launcher
Runs the compiled GameBoy ROM with Xbox Series X/S controller support via mGBA emulator.

Platform: Windows (xbox gamepad input)
Dependencies: pygame (for Xbox controller input), mGBA emulator installed
"""

import os
import sys
import subprocess
import pygame
import time
from pathlib import Path

# ============================================================================
# Xbox Series Controller Button Mapping
# ============================================================================

XBOX_BUTTON_MAP = {
    'A': 'gp_face_1',           # GBA: B button
    'B': 'gp_face_2',           # GBA: A button
    'X': 'gp_face_3',           # GBA: Y button
    'Y': 'gp_face_4',           # GBA: X button
    'LB': 'gp_shoulder_lb',     # GBA: L trigger
    'RB': 'gp_shoulder_rb',     # GBA: R trigger
    'LT': None,                 # Not mapped to GBA
    'RT': None,                 # Not mapped to GBA
    'BACK': 'gp_select',        # GBA: SELECT
    'START': 'gp_start',        # GBA: START
    'LS': None,                 # Not mapped to GBA (not digital)
    'RS': None,                 # Not mapped to GBA (not digital)
    'LSD': 'gp_padzl',          # Left stick down
    'LSU': 'gp_padzu',          # Left stick up
    'LSL': 'gp_padzl',          # Left stick left → also pad
    'LSR': 'gp_padzr',          # Left stick right → also pad
}

GBA_BUTTONS = {
    'A': 0,          # GBA A button
    'B': 1,          # GBA B button
    'SELECT': 2,     # GBA SELECT
    'START': 3,      # GBA START
    'RIGHT': 4,      # GBA D-Pad Right
    'LEFT': 5,       # GBA D-Pad Left
    'UP': 6,         # GBA D-Pad Up
    'DOWN': 7,       # GBA D-Pad Down
    'LB': 8,         # GBA L Shoulder
    'RB': 9,         # GBA R Shoulder
}

# ============================================================================
# Xbox Series Controller Handler
# ============================================================================

class XboxControllerHandler:
    """Handle Xbox Series X/S Controller input and map to GBA buttons."""
    
    def __init__(self):
        """Initialize pygame and controller detection."""
        pygame.init()
        pygame.joystick.init()
        
        self.joystick = None
        self.controller_name = None
        self.button_state = {}
        self.axis_deadzone = 0.5
        self.last_axis_state = {}
        
        self.detect_controller()
    
    def detect_controller(self):
        """Detect and initialize Xbox Series controller."""
        joystick_count = pygame.joystick.get_count()
        
        if joystick_count == 0:
            print("❌ No controllers detected. Connect an Xbox Series X/S controller and try again.")
            sys.exit(1)
        
        # Find Xbox controller
        for i in range(joystick_count):
            js = pygame.joystick.Joystick(i)
            js.init()
            name = js.get_name().lower()
            
            if 'xbox' in name or 'xbox series' in name or 'xinput' in name:
                self.joystick = js
                self.controller_name = js.get_name()
                print(f"✅ Xbox Controller Detected: {self.controller_name}")
                return
        
        # Fallback to first joystick if Xbox not found
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        self.controller_name = self.joystick.get_name()
        print(f"⚠️  Using controller: {self.controller_name}")
    
    def get_button_press(self) -> dict:
        """Poll controller and return button state."""
        if not self.joystick:
            return {}
        
        button_state = {}
        
        # D-Pad / Hat switch
        hats = self.joystick.get_numhats()
        if hats > 0:
            hat_state = self.joystick.get_hat(0)
            button_state['UP'] = hat_state[1] > 0
            button_state['DOWN'] = hat_state[1] < 0
            button_state['LEFT'] = hat_state[0] < 0
            button_state['RIGHT'] = hat_state[0] > 0
        
        # Face buttons (mapped to GBA layout)
        buttons = {
            0: 'A',           # Xbox A → GBA B
            1: 'B',           # Xbox B → GBA A
            2: 'X',           # Xbox X → GBA Y
            3: 'Y',           # Xbox Y → GBA X
            4: 'LB',          # Xbox LB → GBA L
            5: 'RB',          # Xbox RB → GBA R
            6: 'BACK',        # Xbox Back → GBA Select
            7: 'START',       # Xbox Start → GBA Start
        }
        
        for btn_idx, btn_name in buttons.items():
            button_state[btn_name] = self.joystick.get_button(btn_idx)
        
        # Analog sticks at high threshold (digital simulation)
        axes = self.joystick.get_numaxes()
        
        # Left stick (for D-Pad override)
        if axes >= 2:
            lx = self.joystick.get_axis(0)
            ly = self.joystick.get_axis(1)
            
            if lx < -self.axis_deadzone:
                button_state['LEFT'] = True
            if lx > self.axis_deadzone:
                button_state['RIGHT'] = True
            if ly < -self.axis_deadzone:
                button_state['UP'] = True
            if ly > self.axis_deadzone:
                button_state['DOWN'] = True
        
        self.button_state = button_state
        return button_state
    
    def print_status(self):
        """Print current button state (debug)."""
        pressed = [btn for btn, state in self.button_state.items() if state]
        if pressed:
            print(f"  Pressed: {', '.join(pressed)}")

# ============================================================================
# Game Launcher
# ============================================================================

class GameLauncher:
    """Launch Armored Gear: Fly Slight with controller support."""
    
    def __init__(self):
        """Initialize launcher context."""
        self.game_dir = Path(__file__).parent
        self.rom_path = self.select_rom_path()
        self.mgba_path = self.find_mgba()
        self.controller = None

    def detect_rom_type(self, rom_path: Path) -> str:
        """Detect GB vs GBA ROM from header bytes."""
        if not rom_path.exists():
            return "missing"

        raw = rom_path.read_bytes()
        if len(raw) < 0x108:
            return "unknown"

        # GBA ROMs include Nintendo logo bytes at 0x04-0x07.
        if raw[4:8] == bytes([0x24, 0xFF, 0xAE, 0x51]):
            return "gba"

        # GB ROMs include Nintendo logo bytes starting at 0x104.
        if raw[0x104:0x108] == bytes([0xCE, 0xED, 0x66, 0x66]):
            return "gb"

        return "unknown"

    def select_rom_path(self) -> Path:
        """Select a valid ROM path and avoid mislabeled .gba files."""
        env_path = os.environ.get("ARMORED_GEAR_ROM_PATH", "").strip()
        if env_path:
            candidate = Path(env_path)
            if candidate.exists():
                return candidate

        candidates = [
            self.game_dir / "armored_gear_fly_slight.gba",
            self.game_dir / "armored_gear_fly_slight.gb",
            self.game_dir / "armored_gear_fly_slight_native.gba",
        ]

        for candidate in candidates:
            rom_type = self.detect_rom_type(candidate)
            if rom_type in ("gb", "gba"):
                # Reject mislabeled extension pairs to prevent white-screen boot issues.
                if candidate.suffix.lower() == ".gba" and rom_type == "gb":
                    continue
                if candidate.suffix.lower() == ".gb" and rom_type == "gba":
                    continue
                return candidate

        # Fall back to standard name so existing error messages still make sense.
        return self.game_dir / "armored_gear_fly_slight.gb"
    
    def find_mgba(self) -> Path:
        """Find mGBA emulator installation."""
        # Common Windows paths
        search_paths = [
            Path("C:\\Program Files\\mGBA\\mgba.exe"),
            Path("C:\\Program Files (x86)\\mGBA\\mgba.exe"),
            Path("C:\\Games\\mGBA\\mgba.exe"),
            Path(os.path.expandvars("%PROGRAMFILES%\\mGBA\\mgba.exe")),
            Path(os.path.expandvars("%PROGRAMFILES(x86)%\\mGBA\\mgba.exe")),
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(
                ["where", "mgba"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return Path(result.stdout.strip().split('\n')[0])
        except Exception:
            pass
        
        return None
    
    def check_rom(self) -> bool:
        """Verify ROM exists."""
        if not self.rom_path.exists():
            print(f"❌ ROM not found: {self.rom_path}")
            print(f"   Build the game first: cd {self.game_dir} && .\\build.ps1")
            return False

        rom_type = self.detect_rom_type(self.rom_path)
        if rom_type == "unknown":
            print(f"❌ ROM header not recognized: {self.rom_path}")
            return False

        if self.rom_path.suffix.lower() == ".gba" and rom_type == "gb":
            print(f"❌ Refusing to launch mislabeled ROM: {self.rom_path.name}")
            print("   Header is GB, not GBA. Use armored_gear_fly_slight.gb instead.")
            return False
        
        print(f"✅ ROM found: {self.rom_path.name} ({self.rom_path.stat().st_size / 1024:.1f} KB, type={rom_type.upper()})")
        return True
    
    def check_emulator(self) -> bool:
        """Verify mGBA emulator is installed."""
        if not self.mgba_path or not self.mgba_path.exists():
            print("❌ mGBA emulator not found.")
            print("   Install from: https://mgba.io/downloads.html")
            print("   Or install via: choco install mgba-qt")
            return False
        
        print(f"✅ Emulator found: {self.mgba_path}")
        return True
    
    def create_controller_config(self):
        """Create mGBA controller configuration for Xbox controller."""
        config_dir = Path.home() / ".config" / "mgba"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # MGba input config (Qt version uses qt.ini)
        qt_config = Path.home() / ".config" / "mGBA" / "qt.ini"
        
        # Standard mGBA config
        config_file = config_dir / "input.ini"
        
        # Create basic gamepad mapping for mGBA
        gamepad_config = """# mGBA Gamepad Configuration
# Xbox Series X/S Controller Mapping

[1\\Gamepad]
keyA=0x0001
keyB=0x0002
keySelect=0x0004
keyStart=0x0008
keyRight=0x0010
keyLeft=0x0020
keyUp=0x0040
keyDown=0x0080
keyL=0x0100
keyR=0x0200

# Xbox Button Mapping (approximate for mGBA auto-detect)
# This is emulator-specific; some emulators support direct Xbox mapping
"""
        
        try:
            with open(config_file, 'w') as f:
                f.write(gamepad_config)
            print(f"✅ Created controller config: {config_file}")
        except Exception as e:
            print(f"⚠️  Could not create config: {e}")
    
    def launch_game(self):
        """Launch the game ROM with mGBA."""
        if not self.check_rom():
            return False
        
        if not self.check_emulator():
            return False
        
        print("\n" + "="*70)
        print("🎮 Launching Armored Gear: Fly Slight")
        print("="*70)
        
        # Create controller configuration
        self.create_controller_config()
        
        # Launch emulator
        print(f"\n📍 Launch Command:")
        print(f"   {self.mgba_path} {self.rom_path}")
        
        try:
            print("\n🕹️  Please connect Xbox Series Controller and press any button to start...")
            
            # Initialize controller handler (this prompts for controller)
            self.controller = XboxControllerHandler()
            
            print("\n✅ Xbox Controller Ready!")
            print("\nButton Mapping (Xbox → GBA):")
            print("  D-Pad        → D-Pad (movement)")
            print("  A            → GBA B button")
            print("  B            → GBA A button")
            print("  X            → GBA Y button")
            print("  Y            → GBA X button")
            print("  LB           → GBA L Shoulder")
            print("  RB           → GBA R Shoulder")
            print("  Back         → GBA SELECT")
            print("  Start        → GBA START")
            print("  Left Stick   → D-Pad (alternative)")
            
            # Launch emulator
            subprocess.Popen([str(self.mgba_path), str(self.rom_path)])
            
            print("\n⏱️  Emulator launching. Please note:")
            print("   • mGBA should auto-detect your Xbox controller")
            print("   • If not detected, configure in Emulator Settings → Gamepad")
            print("   • Use mGBA's input mapper: Input → Player 1 → Configure")
            
            # Show controller monitor
            self.monitor_controller()
            
        except KeyboardInterrupt:
            print("\n⏹️  Game launcher stopped.")
        except Exception as e:
            print(f"\n❌ Error launching game: {e}")
            return False
        
        return True
    
    def monitor_controller(self):
        """Monitor and display controller input (debug/info)."""
        print("\n" + "="*70)
        print("🎮 Controller Monitor (Press Ctrl+C to exit monitoring)")
        print("="*70 + "\n")
        
        time.sleep(2)  # Let emulator start
        
        try:
            while True:
                pygame.event.pump()  # Update event queue
                buttons = self.controller.get_button_press()
                
                if any(buttons.values()):
                    print(f"  Xbox Input: {', '.join([b for b, p in buttons.items() if p])}")
                
                time.sleep(0.05)  # 20 Hz polling
        
        except KeyboardInterrupt:
            print("\n✅ Controller monitoring stopped.")
        finally:
            pygame.quit()

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("🎮 ARMORED GEAR: FLY SLIGHT")
    print("   Xbox Series X/S Controller Support")
    print("="*70 + "\n")
    
    launcher = GameLauncher()
    
    if launcher.launch_game():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
