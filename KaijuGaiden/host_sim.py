import time
import msvcrt

class Entity:
    def __init__(self):
        self.genome_id = 0
        self.growth_tier = 0
        self.variant = 0
        self.vib_signature = 0
        self.hp = 100
        self.max_hp = 100
        self.regen_rate = 2
        self.pending_nanocell_amount = 0
        self.pending_nanocell_polarity = 0
        self.pending_nanocell_timer_ms = 0
        self.visual_cue = 0

def genetics_tick(e: Entity, dt_ms: int):
    # simple regen
    if e.hp < e.max_hp:
        e.hp += int(e.regen_rate * dt_ms / 1000.0)
        if e.hp > e.max_hp:
            e.hp = e.max_hp
    # pending nanocell processing
    if e.pending_nanocell_timer_ms > 0:
        e.pending_nanocell_timer_ms -= dt_ms
        if e.pending_nanocell_timer_ms <= 0:
            # apply effect
            amt = e.pending_nanocell_amount
            if e.pending_nanocell_polarity > 0:
                e.hp = min(e.max_hp, e.hp + amt)
            else:
                e.hp = max(0, e.hp - amt)
            e.pending_nanocell_amount = 0
            e.pending_nanocell_polarity = 0
            e.visual_cue = 0

def deposit_nanocells(e: Entity, amount: int, polarity: int, delay_ms: int):
    e.pending_nanocell_amount += amount
    e.pending_nanocell_polarity = 1 if polarity > 0 else -1
    e.pending_nanocell_timer_ms = delay_ms
    e.visual_cue = polarity

def apply_growth_nano(e: Entity):
    e.growth_tier += 1
    e.max_hp += 10
    e.hp = e.max_hp
    return e.growth_tier

def apply_vibrational_affectation(e: Entity, vib: int):
    # simplistic: change variant based on vib
    e.vib_signature = vib
    e.variant = vib % 5

def get_variant_name(e: Entity):
    names = ['Neutral','Alpha','Beta','Gamma','Omega']
    return names[e.variant % len(names)]

def clear_console():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def print_hud(e: Entity):
    print(f"HP: {e.hp}/{e.max_hp}  Tier: {e.growth_tier}  Variant: {get_variant_name(e)}  Vib:{e.vib_signature}  Pending:{e.pending_nanocell_amount} cue:{e.visual_cue}")

def main():
    e = Entity()
    fps = 60
    dt = int(1000 / fps)
    print("Kaiju Gaiden - Host Simulation")
    print("Controls: A=new game, B=password(stub), S=VN, Q=apply growth, Up=deposit benev, Down=deposit malign, L/R apply vibration (l/r keys)")
    try:
        while True:
            start = time.time()
            # input handling
            while msvcrt.kbhit():
                c = msvcrt.getch()
                try:
                    ch = c.decode('utf-8')
                except:
                    ch = ''
                if ch.lower() == 'q':
                    tier = apply_growth_nano(e)
                    print(f"Applied Growth NanoCell. new tier={tier}")
                elif ch.lower() == 'a':
                    print("New Game (sim)")
                    e = Entity()
                elif ch.lower() == 'b':
                    print("Password stub")
                elif ch == '\r':
                    pass
                elif ch.lower() == 'l':
                    apply_vibrational_affectation(e, 50)
                    print("Applied vibration 50")
                elif ch.lower() == 'r':
                    apply_vibrational_affectation(e, 220)
                    print("Applied vibration 220")
                elif c == b'\xe0':
                    # arrow keys: read next
                    nxt = msvcrt.getch()
                    if nxt == b'H':
                        deposit_nanocells(e, 80, +1, 2000)
                        print("Deposited benevolent nanocells")
                    if nxt == b'P':
                        deposit_nanocells(e, 80, -1, 2000)
                        print("Deposited malignant nanocells")

            genetics_tick(e, dt)
            clear_console()
            print_hud(e)
            # frame sleep
            elapsed = (time.time() - start)
            to_sleep = max(0, dt/1000.0 - elapsed)
            time.sleep(to_sleep)
    except KeyboardInterrupt:
        print('\nExiting')

if __name__ == '__main__':
    main()
