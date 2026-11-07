"""Conway's Game of Life.

This script runs a simple terminal-based Game of Life simulation.
It supports random initial states and a few built-in patterns.
"""

from __future__ import annotations

import argparse
import math
import random
import tkinter as tk
from typing import Iterable, List, Tuple

try:
    import torch  # type: ignore[import-not-found]
except ImportError:
    torch = None

GRID_ROWS = 100
GRID_COLS = 100
CELL_SIZE = 8

Cell = int
Grid = List[List[Cell]]


class GameOfLife:
    """A Conway's Game of Life board."""

    def __init__(
        self, rows: int, cols: int, pattern: str = "random", density: float = 0.25,
        device: str = "auto",
    ) -> None:
        if rows < 1 or cols < 1:
            raise ValueError("Grid dimensions must be positive")
        self.rows = rows
        self.cols = cols
        self.grid: Grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self.density = density
        self.seed(pattern)
        if device == "cuda" and (torch is None or not torch.cuda.is_available()):
            raise RuntimeError("CUDA was requested, but PyTorch with CUDA support is unavailable")
        self.device = "cuda" if device == "cuda" or (
            device == "auto" and torch is not None and torch.cuda.is_available()
        ) else "cpu"

    def seed(self, pattern: str) -> None:
        """Populate the board with a built-in pattern or a random configuration."""
        if pattern == "empty":
            self._clear()
            return

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
        if self.device == "cuda":
            # Use a binary tensor and toroidal shifts to evaluate every cell in parallel.
            board = torch.as_tensor(self.grid, dtype=torch.uint8, device="cuda")
            neighbors = torch.zeros_like(board, dtype=torch.int16)
            for row_shift in (-1, 0, 1):
                for col_shift in (-1, 0, 1):
                    if row_shift or col_shift:
                        neighbors += torch.roll(board, shifts=(row_shift, col_shift), dims=(0, 1))
            alive = (board != 0) & ((neighbors == 2) | (neighbors == 3))
            born = (board == 0) & (neighbors == 3)
            self.grid = (alive | born).to(torch.uint8).cpu().tolist()
            return

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Conway's Game of Life")
    parser.add_argument("--rows", type=int, default=GRID_ROWS, help="Number of rows in the grid")
    parser.add_argument("--cols", type=int, default=GRID_COLS, help="Number of columns in the grid")
    parser.add_argument("--pattern", type=str, default="empty", choices=[
        "empty", "random", "glider", "blinker", "toad", "exploder", "pulsar"
    ], help="Initial pattern")
    parser.add_argument("--density", type=float, default=0.25, help="Chance for a cell to be alive in random mode")
    parser.add_argument("--delay", type=float, default=0.15, help="Delay in seconds between generations")
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto",
                        help="Compute device (auto uses CUDA when available)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    game = GameOfLife(args.rows, args.cols, pattern=args.pattern, density=args.density, device=args.device)
    initial_grid = [row[:] for row in game.grid]
    root = tk.Tk()
    root.title(f"Conway's Game of Life ({game.device.upper()})")
    display_scale = max(
        1,
        math.ceil(args.cols * CELL_SIZE / 1200),
        math.ceil(args.rows * CELL_SIZE / 900),
    )
    display_cols = math.ceil(args.cols / display_scale)
    display_rows = math.ceil(args.rows / display_scale)
    canvas = tk.Canvas(
        root,
        width=display_cols * CELL_SIZE,
        height=display_rows * CELL_SIZE,
        background="white",
        highlightthickness=0,
    )
    canvas.pack()

    image_item = None
    board_image = None

    def draw_board() -> None:
        nonlocal image_item, board_image
        # A compact PPM image avoids creating and updating millions of Canvas items.
        pixels = bytearray()
        for out_row in range(display_rows):
            row = game.grid[min(out_row * display_scale, args.rows - 1)]
            for out_col in range(display_cols):
                pixels.extend(b"\xff\xff\xff" if row[min(out_col * display_scale, args.cols - 1)] else b"\x00\x00\x00")
        ppm = f"P6\n{display_cols} {display_rows}\n255\n".encode("ascii") + pixels
        board_image = tk.PhotoImage(data=ppm, format="PPM").zoom(CELL_SIZE)
        if image_item is None:
            image_item = canvas.create_image(0, 0, anchor="nw", image=board_image)
        else:
            canvas.itemconfigure(image_item, image=board_image)

    draw_board()

    timer_id = None

    def update() -> None:
        nonlocal timer_id
        timer_id = None
        game.step()
        draw_board()
        timer_id = root.after(max(1, int(args.delay * 1000)), update)

    started = False

    def toggle_cell(event: tk.Event) -> None:
        if started:
            return
        col = event.x // (CELL_SIZE * display_scale)
        row = event.y // (CELL_SIZE * display_scale)
        if 0 <= row < args.rows and 0 <= col < args.cols:
            game.grid[row][col] = 1 - game.grid[row][col]
            draw_board()

    canvas.bind("<Button-1>", toggle_cell)

    def start_game() -> None:
        nonlocal started, timer_id
        if not started:
            started = True
            start_button.configure(state=tk.DISABLED)
            randomize_button.configure(state=tk.DISABLED)
            timer_id = root.after(max(1, int(args.delay * 1000)), update)

    def randomize_game() -> None:
        nonlocal initial_grid
        if started:
            return
        game.seed("random")
        initial_grid = [row[:] for row in game.grid]
        draw_board()

    def reset_game() -> None:
        nonlocal started, timer_id
        if timer_id is not None:
            root.after_cancel(timer_id)
            timer_id = None
        started = False
        game.grid = [row[:] for row in initial_grid]
        start_button.configure(state=tk.NORMAL)
        randomize_button.configure(state=tk.NORMAL)
        draw_board()

    start_button = tk.Button(root, text="Start", command=start_game)
    start_button.pack()
    randomize_button = tk.Button(root, text="Randomize", command=randomize_game)
    randomize_button.pack()
    reset_button = tk.Button(root, text="Reset", command=reset_game)
    reset_button.pack()
    root.mainloop()


if __name__ == "__main__":
    main()
