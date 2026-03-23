from dataclasses import dataclass


@dataclass
class Fighter:
    health: int = 0
    max_health: int = 0
    stamina: int = 0
    max_stamina: int = 0
    stun_timer: int = 0
    invuln_timer: int = 0
    finisher_state: int = 0
    action_flash: int = 0


SPECIALS = [
    ("CHARGE DASH", 14, 14),
    ("SKY CHOMP", 17, 16),
    ("TAIL CYCLONE", 15, 15),
    ("EMBER SPIT", 16, 17),
    ("IRON GUT SLAM", 22, 20),
    ("PHANTOM POUNCE", 18, 18),
    ("HUNGER HOWL", 12, 14),
    ("CROWNBREAKER", 26, 24),
]


class TommyBetaRunSim:
    def __init__(self):
        self.rng = 0xC0FFEE01
        self.frame = 0
        self.level = 1
        self.xp = 0
        self.defeats_this_run = 0
        self.unlocked_specials = 1
        self.finisher_mask = 0
        self.history_hunt = 0
        self.history_cunning = 0
        self.history_endure = 0
        self.tommy = Fighter()
        self.mareaou = Fighter()
        self.enemy_cooldown = 0
        self.set_default_entities()

    def next_rand(self):
        self.rng = (self.rng * 1664525 + 1013904223) & 0xFFFFFFFF
        return self.rng

    def set_default_entities(self):
        self.tommy.max_health = 84 + self.level * 6
        self.tommy.health = self.tommy.max_health
        self.tommy.max_stamina = 72 + self.level * 3
        self.tommy.stamina = self.tommy.max_stamina
        self.tommy.stun_timer = 0
        self.tommy.invuln_timer = 0
        self.tommy.finisher_state = 0
        self.tommy.action_flash = 0

        self.mareaou.max_health = 58 + self.defeats_this_run * 6
        self.mareaou.health = self.mareaou.max_health
        self.mareaou.max_stamina = 60 + self.defeats_this_run * 3
        self.mareaou.stamina = self.mareaou.max_stamina
        self.mareaou.stun_timer = 0
        self.mareaou.invuln_timer = 0
        self.mareaou.finisher_state = 0
        self.mareaou.action_flash = 0

        self.enemy_cooldown = 45 + (self.next_rand() % 50)

    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.level * 100:
            self.xp -= self.level * 100
            self.level += 1

    def apply_damage(self, target: Fighter, dmg: int, stun: int):
        if target.invuln_timer > 0:
            return
        target.health -= dmg
        target.stun_timer += stun
        target.invuln_timer = 10
        target.action_flash = 10

    def spend_stamina(self, fighter: Fighter, cost: int):
        fighter.stamina -= cost
        if fighter.stamina <= 0:
            fighter.stamina = 0
            fighter.stun_timer += 55

    def post_victory(self, special_index: int):
        self.finisher_mask |= 1 << special_index
        self.defeats_this_run += 1
        self.unlocked_specials = 1 + self.defeats_this_run // 3
        if self.unlocked_specials > 8:
            self.unlocked_specials = 8
        self.add_xp(25 + special_index * 5)

    def between_choice(self):
        self.history_cunning += 1
        self.add_xp(14)

    def choose_target_special(self):
        missing_available = [
            index
            for index in range(self.unlocked_specials)
            if not (self.finisher_mask & (1 << index))
        ]
        if missing_available:
            return missing_available[-1]
        return self.unlocked_specials - 1

    def decide_action(self, target_special: int):
        _, target_damage, target_cost = SPECIALS[target_special]
        if self.tommy.stun_timer > 0:
            return None

        if self.mareaou.finisher_state:
            if self.tommy.stamina >= target_cost:
                return "special"
            return None

        if self.mareaou.invuln_timer > 0:
            return None

        safe_bite = self.tommy.stamina > 8
        safe_special = self.tommy.stamina > target_cost
        if safe_special and self.mareaou.health > target_damage + 12:
            return "special"
        if safe_bite and (self.tommy.stamina - 8 >= target_cost or self.mareaou.health > target_damage):
            return "bite"
        if safe_special:
            return "special"
        if safe_bite:
            return "bite"
        return None

    def enemy_action(self):
        if self.mareaou.finisher_state:
            return
        self.enemy_cooldown -= 1
        if self.enemy_cooldown <= 0 and self.mareaou.stun_timer <= 0:
            style = self.next_rand() % 7
            cost = 6 + style
            dmg = 5 + style * 2
            self.spend_stamina(self.mareaou, cost)
            self.apply_damage(self.tommy, dmg, 5 + style)
            self.enemy_cooldown = 35 + (self.next_rand() % 55)

    def update_timers(self):
        if self.tommy.invuln_timer > 0:
            self.tommy.invuln_timer -= 1
        if self.mareaou.invuln_timer > 0:
            self.mareaou.invuln_timer -= 1
        if self.tommy.stun_timer > 0:
            self.tommy.stun_timer -= 1
        if self.mareaou.stun_timer > 0:
            self.mareaou.stun_timer -= 1
        if self.frame % 8 == 0:
            if self.tommy.stamina < self.tommy.max_stamina:
                self.tommy.stamina += 1
            if self.mareaou.stamina < self.mareaou.max_stamina:
                self.mareaou.stamina += 1

    def run_fight(self, target_special: int):
        self.set_default_entities()
        frame_budget = 4000
        while frame_budget > 0:
            self.update_timers()

            action = self.decide_action(target_special)
            if action == "bite":
                bite_combo = (self.frame // 18) % 3
                self.spend_stamina(self.tommy, 8)
                if not self.mareaou.finisher_state:
                    self.apply_damage(self.mareaou, 8 + bite_combo * 2, 6)
            elif action == "special":
                _, damage, cost = SPECIALS[target_special]
                self.spend_stamina(self.tommy, cost)
                if self.mareaou.finisher_state:
                    self.post_victory(target_special)
                    return True
                self.apply_damage(self.mareaou, damage, 10 + target_special % 4)

            if not self.mareaou.finisher_state and self.mareaou.health <= 0:
                self.mareaou.health = 0
                self.mareaou.finisher_state = 1
                self.mareaou.stun_timer = 999

            if self.tommy.health <= 0:
                return False

            self.enemy_action()
            if self.tommy.health <= 0:
                return False

            self.frame += 1
            frame_budget -= 1

        raise AssertionError("AI simulation exceeded fight frame budget")

    def run_to_completion(self):
        fights = 0
        while self.finisher_mask != 0xFF:
            target_special = self.choose_target_special()
            won = self.run_fight(target_special)
            if not won:
                return {
                    "won": False,
                    "fights": fights + 1,
                    "level": self.level,
                    "mask": self.finisher_mask,
                }
            fights += 1
            if self.finisher_mask != 0xFF:
                self.between_choice()
            if fights > 40:
                raise AssertionError("AI needed too many fights to complete the run")
        return {
            "won": True,
            "fights": fights,
            "level": self.level,
            "mask": self.finisher_mask,
            "xp": self.xp,
            "unlocked_specials": self.unlocked_specials,
            "history": (self.history_hunt, self.history_cunning, self.history_endure),
        }


def test_ai_can_complete_100_percent_run():
    sim = TommyBetaRunSim()
    result = sim.run_to_completion()

    assert result["won"] is True
    assert result["mask"] == 0xFF
    assert result["fights"] == 22
    assert result["unlocked_specials"] == 8
    assert result["level"] >= 4