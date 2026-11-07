"""Conway's Game of Life.

This script runs a simple terminal-based Game of Life simulation.
It supports random initial states and a few built-in patterns.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from typing import Iterable, List, Sequence, Tuple

Cell = int
Grid = List[List[Cell]]


class GameOfLife:
    """A Conway's Game of Life board."""

    def __init__(self, rows: int, cols: int, pattern: str = "random", density: float = 0.25) -> None:
        self.rows = rows
        self.cols = cols
        self.grid: Grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self.density = density
        self.seed(pattern)

    def seed(self, pattern: str) -> None:
        """Populate the board with a built-in pattern or a random configuration."""
        if pattern == "random":
            self._randomize()
            return

        if pattern == "glider":
            self._clear()
            self._set_pattern([(1, 2), (2, 3), (3, 1), (3, 2), (3, 3)])
            return

        if pattern == "blinker":
            self._clear()
            self._set_pattern([(1, 0), (1, 1), (1, 2)])
            return

        if pattern == "toad":
            self._clear()
            self._set_pattern([(1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)])
            return

        if pattern == "exploder":
            self._clear()
            self._set_pattern([
                (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
                (0, 2), (1, 2), (3, 2), (4, 2),
            ])
            return

        if pattern == "pulsar":
            self._clear()
            coords = [
                (0, 2), (0, 3), (0, 4), (0, 8), (0, 9), (0, 10),
                (2, 0), (2, 5), (2, 7), (2, 12),
                (3, 0), (3, 5), (3, 7), (3, 12),
                (4, 0), (4, 5), (4, 7), (4, 12),
                (5, 2), (5, 3), (5, 4), (5, 8), (5, 9), (5, 10),
                (7, 2), (7, 3), (7, 4), (7, 8), (7, 9), (7, 10),
                (8, 0), (8, 5), (8, 7), (8, 12),
                (9, 0), (9, 5), (9, 7), (9, 12),
                (10, 0), (10, 5), (10, 7), (10, 12),
                (12, 2), (12, 3), (12, 4), (12, 8), (12, 9), (12, 10),
            ]
            self._set_pattern(coords)
            return

        raise ValueError(f"Unknown pattern: {pattern!r}")

    def _clear(self) -> None:
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

    def _randomize(self) -> None:
        self.grid = [
            [1 if random.random() < self.density else 0 for _ in range(self.cols)]
            for _ in range(self.rows)
        ]

    def _set_pattern(self, cells: Iterable[Tuple[int, int]]) -> None:
        for row, col in cells:
            if 0 <= row < self.rows and 0 <= col < self.cols:
                self.grid[row][col] = 1

    def neighbors(self, row: int, col: int) -> int:
        total = 0
        for r in range(-1, 2):
            for c in range(-1, 2):
                if r == 0 and c == 0:
                    continue
                rr = (row + r) % self.rows
                cc = (col + c) % self.cols
                total += self.grid[rr][cc]
        return total

    def step(self) -> None:
        next_grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for row in range(self.rows):
            for col in range(self.cols):
                live = self.grid[row][col]
                count = self.neighbors(row, col)
                if live and count in (2, 3):
                    next_grid[row][col] = 1
                elif not live and count == 3:
                    next_grid[row][col] = 1
        self.grid = next_grid

    def render(self) -> str:
        lines = []
        for row in self.grid:
            lines.append(" ".join("#" if cell else "." for cell in row))
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Conway's Game of Life")
    parser.add_argument("--rows", type=int, default=20, help="Number of rows in the grid")
    parser.add_argument("--cols", type=int, default=40, help="Number of columns in the grid")
    parser.add_argument("--pattern", type=str, default="random", choices=[
        "random", "glider", "blinker", "toad", "exploder", "pulsar"
    ], help="Initial pattern")
    parser.add_argument("--density", type=float, default=0.25, help="Chance for a cell to be alive in random mode")
    parser.add_argument("--delay", type=float, default=0.15, help="Delay in seconds between generations")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    game = GameOfLife(args.rows, args.cols, pattern=args.pattern, density=args.density)

    try:
        while True:
            clear_screen()
            print(game)
            time.sleep(args.delay)
            game.step()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
