#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2048 Terminal Game
Use arrow keys to move tiles and create 2048.
"""

import random
import sys
import os
import termios
import tty

class Game2048:
    def __init__(self, size=4):
        self.size = size
        self.board = [[0] * size for _ in range(size)]
        self.score = 0
        self.game_over = False
        self.won = False
        self.add_new_tile()
        self.add_new_tile()

    def add_new_tile(self):
        """Add a new tile (2 or 4) to an empty cell"""
        empty_cells = [(i, j) for i in range(self.size) for j in range(self.size) if self.board[i][j] == 0]
        if empty_cells:
            i, j = random.choice(empty_cells)
            self.board[i][j] = 2 if random.random() < 0.9 else 4

    def compress(self, row):
        """Remove zeros and compress to the left"""
        new_row = [num for num in row if num != 0]
        new_row += [0] * (self.size - len(new_row))
        return new_row

    def merge(self, row):
        """Merge same numbers"""
        for i in range(self.size - 1):
            if row[i] != 0 and row[i] == row[i + 1]:
                row[i] *= 2
                row[i + 1] = 0
                self.score += row[i]
                if row[i] == 2048:
                    self.won = True
        return row

    def move_left(self):
        """Move tiles to the left"""
        moved = False
        new_board = []
        for row in self.board:
            compressed = self.compress(row)
            merged = self.merge(compressed)
            final = self.compress(merged)
            new_board.append(final)
            if final != row:
                moved = True
        self.board = new_board
        return moved

    def move_right(self):
        """Move tiles to the right"""
        self.board = [row[::-1] for row in self.board]
        moved = self.move_left()
        self.board = [row[::-1] for row in self.board]
        return moved

    def move_up(self):
        """Move tiles up"""
        self.board = [list(row) for row in zip(*self.board)]
        moved = self.move_left()
        self.board = [list(row) for row in zip(*self.board)]
        return moved

    def move_down(self):
        """Move tiles down"""
        self.board = [list(row) for row in zip(*self.board)]
        moved = self.move_right()
        self.board = [list(row) for row in zip(*self.board)]
        return moved

    def can_move(self):
        """Check if any move is possible"""
        # Check for empty cells
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == 0:
                    return True

        # Check for adjacent same tiles
        for i in range(self.size):
            for j in range(self.size):
                if j < self.size - 1 and self.board[i][j] == self.board[i][j + 1]:
                    return True
                if i < self.size - 1 and self.board[i][j] == self.board[i + 1][j]:
                    return True

        return False

    def display(self):
        """Display the game board"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print("\n" + "=" * 30)
        print("       2048 GAME")
        print("=" * 30)
        print(f"Score: {self.score}\n")

        # Tile colors
        colors = {
            0: '\033[90m',      # Gray
            2: '\033[97m',      # Bright white
            4: '\033[96m',      # Cyan
            8: '\033[93m',      # Yellow
            16: '\033[92m',     # Green
            32: '\033[95m',     # Magenta
            64: '\033[94m',     # Blue
            128: '\033[91m',    # Red
            256: '\033[93m',    # Yellow
            512: '\033[92m',    # Green
            1024: '\033[95m',   # Magenta
            2048: '\033[91m'    # Red
        }
        reset = '\033[0m'

        for row in self.board:
            print("+" + "------+" * self.size)
            print("|", end="")
            for cell in row:
                if cell == 0:
                    print("      |", end="")
                else:
                    color = colors.get(cell, '\033[97m')
                    print(f"{color}{cell:^6}{reset}|", end="")
            print()
        print("+" + "------+" * self.size)

        print("\nArrow keys to move | q: quit")

        if self.won:
            print("\nCongratulations! You reached 2048!")

        if self.game_over:
            print("\nGame Over! No more moves available.")

def get_key():
    """Get keyboard input"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        # Detect ESC sequences
        if ch == '\x1b':
            ch = sys.stdin.read(2)
            if ch == '[A':
                return 'up'
            elif ch == '[B':
                return 'down'
            elif ch == '[C':
                return 'right'
            elif ch == '[D':
                return 'left'
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def main():
    game = Game2048()
    game.display()

    while not game.game_over:
        key = get_key()

        if key == 'q':
            print("\nExiting game.")
            break

        moved = False
        if key == 'up':
            moved = game.move_up()
        elif key == 'down':
            moved = game.move_down()
        elif key == 'left':
            moved = game.move_left()
        elif key == 'right':
            moved = game.move_right()

        if moved:
            game.add_new_tile()
            game.display()

            if not game.can_move():
                game.game_over = True
                game.display()
        elif key in ['up', 'down', 'left', 'right']:
            # Refresh display even when no move was made
            game.display()


if __name__ == "__main__":
    main()
