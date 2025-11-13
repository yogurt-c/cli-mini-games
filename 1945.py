#!/usr/bin/env python3
"""
1945 - Terminal Shooting Game
조작법: A/D 또는 좌/우 방향키로 레인 이동, SPACE로 총알 발사, Q로 종료
"""

import curses
import random
import time
from dataclasses import dataclass
from typing import List, Tuple

# 게임 설정
LANES = 5
GAME_WIDTH = 50
GAME_HEIGHT = 30
PLAYER_CHAR = "▲"
ENEMY_CHAR = "▼"
BOSS_CHAR = "█"
BULLET_CHAR = "|"
ENEMY_BULLET_CHAR = "!"

# 아이템 타입
ITEM_POWER = "P"      # 파워 업
ITEM_RAPIDFIRE = "R"  # 연사력 업
ITEM_SHIELD = "S"     # 실드
ITEM_SCORE = "$"      # 보너스 점수

@dataclass
class GameObject:
    """게임 오브젝트 기본 클래스"""
    x: int
    y: int
    char: str
    active: bool = True
    owner: object = None  # 총알의 소유자 (적 또는 보스)

class Player:
    """플레이어 클래스"""
    def __init__(self):
        self.lane = LANES // 2  # 중앙 레인에서 시작
        self.y = GAME_HEIGHT - 3
        self.health = 3
        self.max_health = 3
        self.power = 1
        self.rapidfire = 1  # 연사력 (낮을수록 빠름)
        self.shield = 0     # 실드 개수
        self.score = 0
        self.shoot_cooldown = 0

    def move_left(self):
        if self.lane > 0:
            self.lane -= 1

    def move_right(self):
        if self.lane < LANES - 1:
            self.lane += 1

    def get_x(self):
        """레인 번호를 X 좌표로 변환"""
        # 각 레인의 중앙: 레인 0 = 5, 레인 1 = 14, 레인 2 = 23, 레인 3 = 32, 레인 4 = 41
        return 5 + self.lane * 9

    def can_shoot(self):
        """발사 가능 여부 확인"""
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = max(1, 6 - self.rapidfire)  # 연사력에 따라 쿨다운 감소
            return True
        return False

    def update_cooldown(self):
        """쿨다운 감소"""
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def shoot(self):
        """총알 발사 - 파워 레벨에 따라 다양한 패턴"""
        bullets = []
        x = self.get_x()
        y = self.y - 1

        if self.power == 1:
            # 레벨 1: 단발
            bullets.append(GameObject(x, y, BULLET_CHAR))
        elif self.power == 2:
            # 레벨 2: 2발 (좌우 약간 벌림)
            bullets.append(GameObject(x - 1, y, BULLET_CHAR))
            bullets.append(GameObject(x + 1, y, BULLET_CHAR))
        elif self.power == 3:
            # 레벨 3: 3발 (중앙 + 좌우)
            bullets.append(GameObject(x, y, BULLET_CHAR))
            bullets.append(GameObject(x - 2, y, BULLET_CHAR))
            bullets.append(GameObject(x + 2, y, BULLET_CHAR))
        elif self.power == 4:
            # 레벨 4: 5발 (넓은 범위)
            for i in range(-2, 3):
                bullets.append(GameObject(x + i, y, BULLET_CHAR))
        else:  # power >= 5
            # 레벨 5: 7발 + 양옆 레인까지
            for i in range(-3, 4):
                bullets.append(GameObject(x + i, y, BULLET_CHAR))
            # 양옆 레인에도 발사
            if self.lane > 0:
                left_x = 5 + (self.lane - 1) * 8
                bullets.append(GameObject(left_x, y, BULLET_CHAR))
            if self.lane < LANES - 1:
                right_x = 5 + (self.lane + 1) * 8
                bullets.append(GameObject(right_x, y, BULLET_CHAR))

        return bullets

    def power_up(self):
        """파워 업그레이드"""
        self.power = min(self.power + 1, 5)

    def rapidfire_up(self):
        """연사력 업그레이드"""
        self.rapidfire = min(self.rapidfire + 1, 5)

    def add_shield(self):
        """실드 추가"""
        self.shield = min(self.shield + 1, 3)

    def take_damage(self):
        """데미지 받기"""
        if self.shield > 0:
            self.shield -= 1
            return False  # 죽지 않음
        else:
            self.health -= 1
            return self.health <= 0  # 체력이 0이면 죽음

class Enemy:
    """적 클래스"""
    def __init__(self, lane: int, y: int = 0):
        self.lane = lane
        self.y = y
        self.health = 1
        self.active = True
        self.shoot_cooldown = 0

    def get_x(self):
        return 5 + self.lane * 9

    def move(self):
        """아래로 이동"""
        self.y += 1
        if self.y >= GAME_HEIGHT:
            self.active = False

    def shoot(self):
        """총알 발사"""
        if self.shoot_cooldown <= 0 and random.random() < 0.05:
            self.shoot_cooldown = 20
            return GameObject(self.get_x(), self.y + 1, ENEMY_BULLET_CHAR, owner=self)
        self.shoot_cooldown -= 1
        return None

class Boss:
    """보스 클래스"""
    def __init__(self):
        self.lane = LANES // 2
        self.y = 2
        self.health = 20
        self.max_health = 20
        self.active = True
        self.move_direction = 1
        self.shoot_cooldown = 0

    def get_x(self):
        return 5 + self.lane * 9

    def move(self):
        """좌우로 이동"""
        if random.random() < 0.1:
            if self.move_direction == 1 and self.lane < LANES - 1:
                self.lane += 1
            elif self.move_direction == -1 and self.lane > 0:
                self.lane -= 1
            else:
                self.move_direction *= -1

    def shoot(self):
        """여러 방향으로 총알 발사"""
        bullets = []
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = 15
            # 보스는 3발 발사
            bullets.append(GameObject(self.get_x(), self.y + 1, ENEMY_BULLET_CHAR, owner=self))
            if self.lane > 0:
                bullets.append(GameObject(5 + (self.lane - 1) * 9, self.y + 1, ENEMY_BULLET_CHAR, owner=self))
            if self.lane < LANES - 1:
                bullets.append(GameObject(5 + (self.lane + 1) * 9, self.y + 1, ENEMY_BULLET_CHAR, owner=self))
        self.shoot_cooldown -= 1
        return bullets

class Item:
    """아이템 클래스"""
    def __init__(self, lane: int, y: int, item_type: str = None):
        self.lane = lane
        self.y = y
        self.active = True
        # 아이템 타입을 랜덤으로 결정
        if item_type is None:
            self.item_type = random.choice([ITEM_POWER, ITEM_RAPIDFIRE, ITEM_SHIELD, ITEM_SCORE])
        else:
            self.item_type = item_type

    def get_x(self):
        return 5 + self.lane * 9

    def move(self):
        self.y += 1
        if self.y >= GAME_HEIGHT:
            self.active = False

class Game:
    """게임 메인 클래스"""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.player = Player()
        self.bullets: List[GameObject] = []
        self.enemy_bullets: List[GameObject] = []
        self.enemies: List[Enemy] = []
        self.items: List[Item] = []
        self.boss = None
        self.frame = 0
        self.stage = 1
        self.enemy_spawn_rate = 50
        self.last_boss_score = -100  # 마지막 보스 등장 점수 추적

        # Curses 설정
        curses.curs_set(0)  # 커서 숨기기
        self.stdscr.nodelay(1)  # 논블로킹 입력
        self.stdscr.timeout(50)  # 50ms 타임아웃

        # 터미널 크기 확인
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        if self.max_y < GAME_HEIGHT + 2 or self.max_x < GAME_WIDTH + 30:
            raise Exception(f"터미널 크기가 너무 작습니다! 최소 {GAME_HEIGHT + 2}행 x {GAME_WIDTH + 30}열이 필요합니다.")

    def spawn_enemy(self):
        """적 생성 - 스테이지에 따라 난이도 증가"""
        # 스테이지별로 스폰 확률과 최대 적 수 증가
        spawn_rate = min(0.08 + (self.stage - 1) * 0.02, 0.2)  # 최대 20%
        max_enemies = min(10 + (self.stage - 1) * 2, 20)  # 최대 20마리

        if random.random() < spawn_rate and len(self.enemies) < max_enemies:
            lane = random.randint(0, LANES - 1)
            enemy = Enemy(lane)
            # 스테이지가 높을수록 적 체력 증가
            if self.stage >= 3:
                enemy.health = 1 + (self.stage - 2) // 2
            self.enemies.append(enemy)

    def spawn_boss(self):
        """보스 생성 - 스테이지에 따라 난이도 증가"""
        if self.boss is None:
            boss = Boss()
            # 스테이지별로 보스 체력 증가
            boss.max_health = 20 + (self.stage - 1) * 10
            boss.health = boss.max_health
            self.boss = boss

    def spawn_item(self, lane: int, y: int):
        """아이템 생성"""
        if random.random() < 0.3:
            self.items.append(Item(lane, y))

    def update(self):
        """게임 상태 업데이트"""
        self.frame += 1

        # 플레이어 쿨다운 업데이트
        self.player.update_cooldown()

        # 보스 스테이지 체크 (200점마다 보스 등장, 중복 방지)
        if self.boss is None and self.player.score >= 200:
            boss_threshold = (self.player.score // 200) * 200
            if boss_threshold > self.last_boss_score:
                self.spawn_boss()
                self.last_boss_score = boss_threshold

        # 적 생성 (보스가 없을 때만)
        if self.boss is None:
            self.spawn_enemy()

        # 플레이어 총알 이동
        for bullet in self.bullets:
            if bullet.active:
                bullet.y -= 1
                if bullet.y < 0:
                    bullet.active = False

        # 적 총알 이동
        for bullet in self.enemy_bullets:
            if bullet.active:
                bullet.y += 1
                if bullet.y >= GAME_HEIGHT:
                    bullet.active = False

        # 적 이동 및 발사
        for enemy in self.enemies:
            if enemy.active:
                enemy.move()
                # 스테이지에 따라 적 발사 확률 증가
                shoot_chance = 0.05 + (self.stage - 1) * 0.01
                if enemy.shoot_cooldown <= 0 and random.random() < shoot_chance:
                    enemy.shoot_cooldown = max(10, 20 - self.stage)
                    enemy_bullet = GameObject(enemy.get_x(), enemy.y + 1, ENEMY_BULLET_CHAR, owner=enemy)
                    self.enemy_bullets.append(enemy_bullet)
                enemy.shoot_cooldown -= 1

        # 보스 이동 및 발사
        if self.boss and self.boss.active:
            self.boss.move()
            boss_bullets = self.boss.shoot()
            if boss_bullets:
                self.enemy_bullets.extend(boss_bullets)

        # 아이템 이동
        for item in self.items:
            if item.active:
                item.move()

        # 충돌 감지
        self.check_collisions()

        # 비활성 오브젝트 제거
        self.bullets = [b for b in self.bullets if b.active]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.active]
        self.enemies = [e for e in self.enemies if e.active]
        self.items = [i for i in self.items if i.active]

    def check_collisions(self):
        """충돌 감지"""
        player_x = self.player.get_x()

        # 플레이어 총알과 적 충돌
        for bullet in self.bullets:
            if not bullet.active:
                continue

            for enemy in self.enemies:
                # X 좌표 범위를 넓혀서 충돌 감지 (±2 픽셀)
                if enemy.active and abs(enemy.get_x() - bullet.x) <= 2 and abs(enemy.y - bullet.y) < 2:
                    enemy.health -= 1
                    bullet.active = False

                    # 적 체력이 0이 되면 처치
                    if enemy.health <= 0:
                        enemy.active = False
                        self.player.score += 10
                        self.spawn_item(enemy.lane, enemy.y)
                        # 적이 죽으면 그 적이 발사한 총알도 제거
                        for eb in self.enemy_bullets:
                            if eb.owner == enemy:
                                eb.active = False
                    break

            # 보스와 충돌
            if self.boss and self.boss.active:
                # 보스도 범위를 넓혀서 충돌 감지 (±3 픽셀, 보스가 더 크므로)
                if abs(self.boss.get_x() - bullet.x) <= 3 and abs(self.boss.y - bullet.y) < 2:
                    self.boss.health -= 1
                    bullet.active = False
                    if self.boss.health <= 0:
                        self.boss.active = False
                        self.player.score += 100
                        # 보스가 죽으면 보스가 발사한 총알도 제거
                        for eb in self.enemy_bullets:
                            if eb.owner == self.boss:
                                eb.active = False
                        self.boss = None
                        self.stage += 1

        # 적 총알과 플레이어 충돌
        for bullet in self.enemy_bullets:
            if bullet.active and bullet.x == player_x and abs(bullet.y - self.player.y) < 2:
                self.player.take_damage()
                bullet.active = False

        # 아이템과 플레이어 충돌
        for item in self.items:
            if item.active and abs(item.get_x() - player_x) < 3 and abs(item.y - self.player.y) < 2:
                # 아이템 타입별 효과 적용
                if item.item_type == ITEM_POWER:
                    self.player.power_up()
                elif item.item_type == ITEM_RAPIDFIRE:
                    self.player.rapidfire_up()
                elif item.item_type == ITEM_SHIELD:
                    self.player.add_shield()
                elif item.item_type == ITEM_SCORE:
                    self.player.score += 50
                item.active = False

        # 적과 플레이어 충돌
        for enemy in self.enemies:
            if enemy.active and enemy.get_x() == player_x and abs(enemy.y - self.player.y) < 2:
                self.player.take_damage()
                enemy.active = False

    def safe_addstr(self, y, x, text):
        """안전한 문자 출력 (터미널 범위 체크)"""
        try:
            if 0 <= y < self.max_y and 0 <= x < self.max_x:
                self.stdscr.addstr(y, x, text)
        except:
            pass

    def render(self):
        """화면 렌더링"""
        self.stdscr.clear()

        # 게임 테두리
        for i in range(GAME_HEIGHT):
            self.safe_addstr(i, 0, "|")
            self.safe_addstr(i, GAME_WIDTH - 1, "|")
        self.safe_addstr(0, 0, "+" + "-" * (GAME_WIDTH - 2) + "+")
        self.safe_addstr(GAME_HEIGHT - 1, 0, "+" + "-" * (GAME_WIDTH - 2) + "+")

        # 레인 구분선 (각 레인 사이)
        for lane in range(1, LANES):
            # 레인 간격: 9, 구분선은 각 레인 중간(약 4~5칸 뒤)
            x = 5 + lane * 9 - 5
            for y in range(1, GAME_HEIGHT - 1):
                self.safe_addstr(y, x, ":")

        # 플레이어
        self.safe_addstr(self.player.y, self.player.get_x(), PLAYER_CHAR)

        # 플레이어 총알
        for bullet in self.bullets:
            if bullet.active and 0 < bullet.y < GAME_HEIGHT - 1:
                self.safe_addstr(bullet.y, bullet.x, bullet.char)

        # 적 총알
        for bullet in self.enemy_bullets:
            if bullet.active and 0 < bullet.y < GAME_HEIGHT - 1:
                self.safe_addstr(bullet.y, bullet.x, bullet.char)

        # 적 (체력에 따라 다른 표시)
        for enemy in self.enemies:
            if enemy.active and 0 < enemy.y < GAME_HEIGHT - 1:
                # 체력이 1이면 일반, 2 이상이면 강화된 적 표시
                if enemy.health == 1:
                    self.safe_addstr(enemy.y, enemy.get_x(), ENEMY_CHAR)
                elif enemy.health == 2:
                    self.safe_addstr(enemy.y, enemy.get_x(), "▽")  # 체력 2
                else:
                    self.safe_addstr(enemy.y, enemy.get_x(), "◈")  # 체력 3+

        # 보스
        if self.boss and self.boss.active:
            boss_x = self.boss.get_x()
            self.safe_addstr(self.boss.y, boss_x - 1, "[")
            self.safe_addstr(self.boss.y, boss_x, BOSS_CHAR)
            self.safe_addstr(self.boss.y, boss_x + 1, "]")
            # 보스 체력바
            health_bar = "=" * (self.boss.health * 20 // self.boss.max_health)
            self.safe_addstr(0, GAME_WIDTH + 2, f"BOSS HP: [{health_bar:20}]")

        # 아이템 (타입별로 다른 문자 표시)
        for item in self.items:
            if item.active and 0 < item.y < GAME_HEIGHT - 1:
                self.safe_addstr(item.y, item.get_x(), item.item_type)

        # 게임 정보
        self.safe_addstr(1, GAME_WIDTH + 2, f"Stage: {self.stage}")
        self.safe_addstr(2, GAME_WIDTH + 2, f"Score: {self.player.score}")
        self.safe_addstr(3, GAME_WIDTH + 2, f"Health: {'♥' * self.player.health}")
        self.safe_addstr(4, GAME_WIDTH + 2, f"Shield: {'◆' * self.player.shield}")
        self.safe_addstr(5, GAME_WIDTH + 2, f"Power: {self.player.power}/5")
        self.safe_addstr(6, GAME_WIDTH + 2, f"RapidFire: {self.player.rapidfire}/5")

        self.safe_addstr(8, GAME_WIDTH + 2, "Items:")
        self.safe_addstr(9, GAME_WIDTH + 2, f"  {ITEM_POWER}: Power Up")
        self.safe_addstr(10, GAME_WIDTH + 2, f"  {ITEM_RAPIDFIRE}: Rapid Fire")
        self.safe_addstr(11, GAME_WIDTH + 2, f"  {ITEM_SHIELD}: Shield")
        self.safe_addstr(12, GAME_WIDTH + 2, f"  {ITEM_SCORE}: +50 Score")

        self.safe_addstr(14, GAME_WIDTH + 2, "Controls:")
        self.safe_addstr(15, GAME_WIDTH + 2, "A/D or ←/→: Move")
        self.safe_addstr(16, GAME_WIDTH + 2, "SPACE: Shoot")
        self.safe_addstr(17, GAME_WIDTH + 2, "Q: Quit")

        self.stdscr.refresh()

    def handle_input(self):
        """키 입력 처리"""
        try:
            key = self.stdscr.getch()

            if key == ord('q') or key == ord('Q'):
                return False
            elif key == ord('a') or key == ord('A') or key == curses.KEY_LEFT:
                self.player.move_left()
            elif key == ord('d') or key == ord('D') or key == curses.KEY_RIGHT:
                self.player.move_right()
            elif key == ord(' '):
                # 연사력 체크 후 발사
                if self.player.can_shoot():
                    bullets = self.player.shoot()
                    self.bullets.extend(bullets)

        except:
            pass

        return True

    def run(self):
        """게임 메인 루프"""
        running = True

        while running and self.player.health > 0:
            running = self.handle_input()
            self.update()
            self.render()
            time.sleep(0.05)

        # 게임 오버
        self.stdscr.clear()
        msg = f"GAME OVER! Final Score: {self.player.score}"
        stage_msg = f"Stage: {self.stage}"
        self.stdscr.addstr(GAME_HEIGHT // 2 - 1, (GAME_WIDTH - len(stage_msg)) // 2, stage_msg)
        self.stdscr.addstr(GAME_HEIGHT // 2, (GAME_WIDTH - len(msg)) // 2, msg)
        self.stdscr.addstr(GAME_HEIGHT // 2 + 2, (GAME_WIDTH - 20) // 2, "Press Q to exit")
        self.stdscr.refresh()
        self.stdscr.nodelay(0)

        # Q 키를 누를 때까지 대기
        while True:
            key = self.stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                break

def main(stdscr):
    """메인 함수"""
    try:
        game = Game(stdscr)
        game.run()
    except Exception as e:
        # 오류 메시지 표시
        stdscr.clear()
        stdscr.addstr(0, 0, f"Error: {str(e)}")
        stdscr.addstr(2, 0, "터미널 창을 최대화하거나 크게 조정한 후 다시 실행해주세요.")
        stdscr.addstr(3, 0, f"필요한 크기: 최소 {GAME_HEIGHT + 2}행 x {GAME_WIDTH + 30}열")
        stdscr.addstr(5, 0, "Press any key to exit...")
        stdscr.refresh()
        stdscr.nodelay(0)
        stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)
