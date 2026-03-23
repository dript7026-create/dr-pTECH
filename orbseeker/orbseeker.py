import pygame
import sys
import random
import time
from collections import deque

# OrbSeeker - simplified single-file prototype
# Run: pip install -r requirements.txt
# Then: python orbseeker.py

WIDTH, HEIGHT = 960, 640
FPS = 60

WHITE = (255,255,255)
BLACK = (0,0,0)
SKY = (30,40,90)
SAND = (212,175,55)
SEA = (20,90,140)
GREEN = (80,160,60)
ORANGE = (220,120,20)
RED = (200,30,30)
PURPLE = (120,60,160)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont('consolas', 18)


class Player:
    def __init__(self):
        self.x = WIDTH//2
        self.y = HEIGHT//2
        self.speed = 180
        self.hunger = 100
        self.thirst = 100
        self.health = 100
        self.gold = 0
        self.inventory = {'food':0,'water':0,'seeds':0,'maps':[], 'orbs':0}
        self.on_raft = False

player = Player()

state = 'island'  # island, tournament, map_explore, orb_boss
running = True

# Island farm plots
farm_plots = []  # list of (x,y, planted_time, growth_seconds)

# Maps data
MAP_COUNT = 5
maps = []
for i in range(MAP_COUNT):
    maps.append({'id':i, 'width':1600, 'height':1200, 'orb': False, 'explored':False})

# place 7 orbs across maps
orb_positions = []
total_orbs = 7
for orb_id in range(total_orbs):
    m = random.randrange(MAP_COUNT)
    x = random.randint(100, maps[m]['width']-100)
    y = random.randint(100, maps[m]['height']-100)
    maps[m]['orb'] = maps[m].get('orb', False) or True
    orb_positions.append({'map':m,'x':x,'y':y,'collected':False})

current_map = None
camera_x, camera_y = 0,0

def draw_text(s, x, y, c=WHITE):
    surf = font.render(s, True, c)
    screen.blit(surf, (x,y))

def island_screen(dt):
    global state
    screen.fill(SKY)
    # draw sea
    pygame.draw.rect(screen, SEA, (0, HEIGHT//2+40, WIDTH, HEIGHT//2))
    # island
    pygame.draw.circle(screen, SAND, (WIDTH//2, HEIGHT//2+50), 140)
    # palm
    pygame.draw.rect(screen, (120,80,30), (WIDTH//2-10, HEIGHT//2-60, 20, 80))
    pygame.draw.polygon(screen, GREEN, [(WIDTH//2-60, HEIGHT//2-60),(WIDTH//2, HEIGHT//2-140),(WIDTH//2+60, HEIGHT//2-60)])
    # raft
    raft_rect = pygame.Rect(WIDTH//2+160, HEIGHT//2+80, 80, 30)
    pygame.draw.rect(screen, (120,80,50), raft_rect)
    draw_text("Raft (R to launch)", raft_rect.x-10, raft_rect.y-20)
    # player and monkey
    pygame.draw.circle(screen, PURPLE, (WIDTH//2-40, HEIGHT//2+40), 16)
    draw_text("Roju", WIDTH//2-56, HEIGHT//2+60)
    pygame.draw.circle(screen, ORANGE, (WIDTH//2-10, HEIGHT//2+20), 10)
    draw_text("Monkey", WIDTH//2-30, HEIGHT//2+5)

    # farm plots
    draw_text("Farm (F): plant seeds, harvest food/water", 10,10)
    draw_text(f"Hunger: {int(player.hunger)}  Thirst: {int(player.thirst)}  Food: {player.inventory['food']}  Water: {player.inventory['water']}", 10, 30)
    draw_text(f"Seeds: {player.inventory['seeds']}  Maps: {len(player.inventory['maps'])}  Orbs: {player.inventory['orbs']}", 10,50)

    # farm plots draw
    fx = 80
    for i,plot in enumerate(farm_plots):
        x = fx + i*60
        y = HEIGHT//2+140
        pygame.draw.rect(screen, (100,60,30), (x,y,40,30))
        planted = plot[2]
        growth = plot[3]
        elapsed = time.time()-planted
        pct = min(1.0, elapsed/growth)
        pygame.draw.rect(screen, (50,200,80), (x, y-10, int(40*pct),6))
        if pct>=1.0:
            draw_text("Ready", x, y-30)

    # island menu hints
    draw_text("Press T to send monkey on Tournament (mandatory first run). Press M to open map menu.", 10, HEIGHT-30)

    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_r:
                # launch raft -> transition to tournament or map depending
                if len(player.inventory['maps'])==0:
                    state='tournament'
                else:
                    state='map_select'
            if ev.key==pygame.K_t:
                state='tournament'
            if ev.key==pygame.K_f:
                handle_farm()
            if ev.key==pygame.K_m:
                state='map_select'

def handle_farm():
    # simple farm UI: plant if seeds, harvest ready
    global farm_plots
    # plant into a new plot if seeds
    if player.inventory['seeds']>0 and len(farm_plots)<5:
        farm_plots.append((len(farm_plots), 0, time.time(), 20))
        player.inventory['seeds']-=1
        return
    # harvest ready
    for i,plot in enumerate(list(farm_plots)):
        planted = plot[2]; growth = plot[3]
        if time.time()-planted >= growth:
            player.inventory['food'] += 1
            player.inventory['water'] += 1
            farm_plots.pop(i)
            return

def tournament_screen(dt):
    # simple RPS tournament; monkey vs AI; win grants a map and seeds
    global state
    screen.fill((40,30,60))
    draw_text("Tournament - Winged Monkey flies to compete", 10,10)
    draw_text("Choose: 1=Rock  2=Paper  3=Scissors. Win best of 3.", 10,40)
    rounds = tournament_screen.rounds
    draw_text(f"Score: You {rounds['player']} - Opp {rounds['ai']}", 10,70)
    draw_text("Press 1/2/3 to play. Press ESC to return (abort).", 10, HEIGHT-30)

    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_ESCAPE:
                state='island'; return
            if ev.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                choice = {pygame.K_1:0, pygame.K_2:1, pygame.K_3:2}[ev.key]
                ai = random.randint(0,2)
                res = (choice - ai) % 3
                if res==1:
                    tournament_screen.rounds['player']+=1
                elif res==2:
                    tournament_screen.rounds['ai']+=1
                # else tie
                if tournament_screen.rounds['player']>=2:
                    # win: award a map and seeds
                    new_map = random.randrange(MAP_COUNT)
                    if new_map not in player.inventory['maps']:
                        player.inventory['maps'].append(new_map)
                    player.inventory['seeds'] += 2
                    state='island'
                    tournament_screen.rounds={'player':0,'ai':0}
                    return
                if tournament_screen.rounds['ai']>=2:
                    # lose: return to island
                    state='island'
                    tournament_screen.rounds={'player':0,'ai':0}
                    return

tournament_screen.rounds={'player':0,'ai':0}

def map_select_screen(dt):
    global state, current_map, camera_x, camera_y
    screen.fill((10,10,40))
    draw_text("Map Select - choose a map to travel to by pressing its number.",10,10)
    for i in range(MAP_COUNT):
        unlocked = i in player.inventory['maps']
        draw_text(f"{i+1}. Map {i} {'(Unlocked)' if unlocked else '(Locked)'}", 10, 40+20*i, WHITE if unlocked else (120,120,120))
    draw_text("Press ESC to return.", 10, HEIGHT-30)
    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_ESCAPE:
                state='island'; return
            if pygame.K_1 <= ev.key <= pygame.K_9:
                idx = ev.key - pygame.K_1
                if idx < MAP_COUNT and idx in player.inventory['maps']:
                    current_map = maps[idx]
                    camera_x, camera_y = 0,0
                    state='map_explore'

def map_explore_screen(dt):
    global camera_x, camera_y, state, current_map
    screen.fill((20,70,30))
    if not current_map:
        state='island'; return
    # draw simple world grid
    world_w, world_h = current_map['width'], current_map['height']
    # player movement
    keys = pygame.key.get_pressed()
    dx = dy = 0
    if keys[pygame.K_LEFT]: dx -= 1
    if keys[pygame.K_RIGHT]: dx += 1
    if keys[pygame.K_UP]: dy -= 1
    if keys[pygame.K_DOWN]: dy += 1
    # normalize
    if dx!=0 and dy!=0:
        dx *= 0.7071; dy *= 0.7071
    player.x += dx * player.speed * dt
    player.y += dy * player.speed * dt
    # clamp to world edges
    player.x = max(0, min(world_w, player.x))
    player.y = max(0, min(world_h, player.y))

    # camera centers on player
    camx = int(player.x - WIDTH//2)
    camy = int(player.y - HEIGHT//2)
    camera_x, camera_y = camx, camy

    # draw background tiles (simple)
    for i in range(-1,3):
        for j in range(-1,3):
            rx = i*400 - (camx%400)
            ry = j*300 - (camy%300)
            pygame.draw.rect(screen, (40+i*10,70+j*10,40), (rx,ry,400,300))

    # draw orbs and enemies for this map
    mapidx = current_map['id']
    for orb in orb_positions:
        if orb['map']==mapidx and not orb['collected']:
            ox = orb['x'] - camx; oy = orb['y'] - camy
            pygame.draw.circle(screen, ORANGE, (int(ox),int(oy)), 12)
    # draw player
    px = int(player.x - camx); py = int(player.y - camy)
    pygame.draw.circle(screen, PURPLE, (px,py), 12)
    draw_text("Press I to interact (search), B to return to island (link node)", 10, HEIGHT-30)

    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_b:
                # return to island
                state='island'; return
            if ev.key==pygame.K_i:
                # check nearby orbs
                for orb in orb_positions:
                    if orb['map']==mapidx and not orb['collected']:
                        dist = ((player.x-orb['x'])**2 + (player.y-orb['y'])**2)**0.5
                        if dist < 40:
                            # found orb node -> trigger guardian
                            state='orb_boss'
                            map_for_boss = mapidx
                            orb_for_boss = orb
                            orb_boss_screen.setup(map_for_boss, orb_for_boss)
                            return

def orb_boss_screen(dt):
    # placeholder; uses QTE sequence to beat guardian
    screen.fill((10,10,10))
    draw_text("ORB GUARDIAN: follow the sequence!", 10,10)
    orb_boss_screen.draw(dt)
    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type==pygame.KEYDOWN:
            orb_boss_screen.handle_key(ev.key)

class OrbBoss:
    def __init__(self):
        self.seq = deque()
        self.index = 0
        self.start = 0
        self.time_limit = 6.0
        self.active = False
    def setup(self, mapidx, orb):
        self.seq = deque([random.choice([pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_j, pygame.K_k, pygame.K_l]) for _ in range(6)])
        self.index = 0
        self.start = time.time()
        self.time_limit = 6.0
        self.mapidx = mapidx
        self.orb = orb
        self.active = True
    def draw(self, dt):
        # show sequence
        seq_list = list(self.seq)
        s = ' '.join([chr(k) for k in seq_list])
        draw_text("Sequence: " + s, 10,40)
        elapsed = time.time()-self.start
        draw_text(f"Time: {elapsed:.1f}/{self.time_limit}", 10,70)
        draw_text(f"Progress: {self.index}/{len(self.seq)}", 10,100)
        if elapsed > self.time_limit:
            # failed
            self.active=False
            orb_boss_screen.fail()
    def handle_key(self, key):
        if not self.active: return
        correct = list(self.seq)[self.index]
        if key==correct:
            self.index+=1
            if self.index>=len(self.seq):
                self.active=False
                orb_boss_screen.win(self.orb)
        else:
            self.active=False
            orb_boss_screen.fail()

orb_boss = OrbBoss()

def orb_boss_win(orb):
    orb['collected']=True
    player.inventory['orbs'] += 1
    # create a fast link node: allow return to island
    draw_text("Orb acquired! Returning to island...", WIDTH//2-120, HEIGHT//2)
    pygame.display.flip()
    pygame.time.delay(800)
    global state
    state='island'

def orb_boss_fail():
    # penalty
    player.health -= 10
    draw_text("You failed. Guardian repelled you.", WIDTH//2-120, HEIGHT//2)
    pygame.display.flip()
    pygame.time.delay(800)
    global state
    state='island'

orb_boss_screen.setup = orb_boss.setup
orb_boss_screen.draw = orb_boss.draw
orb_boss_screen.handle_key = orb_boss.handle_key
orb_boss_screen.win = orb_boss_win
orb_boss_screen.fail = orb_boss_fail

def update_survival(dt):
    # hunger/thirst decrease;
    player.hunger -= 1.0 * dt * 2
    player.thirst -= 1.5 * dt * 2
    if player.hunger <=0:
        player.health -= 5*dt
    if player.thirst <=0:
        player.health -= 8*dt

def main():
    global state
    last = time.time()
    while True:
        dt = clock.tick(FPS)/1000.0
        update_survival(dt)
        if state=='island':
            island_screen(dt)
        elif state=='tournament':
            tournament_screen(dt)
        elif state=='map_select':
            map_select_screen(dt)
        elif state=='map_explore':
            map_explore_screen(dt)
        elif state=='orb_boss':
            orb_boss_screen(dt)

        # draw footer
        draw_text(f"Health: {int(player.health)}", WIDTH-160, 10)
        pygame.display.flip()

if __name__=='__main__':
    try:
        main()
    except Exception as e:
        print('Error:', e)
        pygame.quit()
        raise
