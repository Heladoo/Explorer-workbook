"""Maze generation: a real spanning-tree maze, walked and typeset — never drawn.

A perfect maze (every cell reachable, exactly one path between any two cells)
is a spanning tree over the grid, which is exactly what a randomized
depth-first carve produces. That makes "exactly one solvable path, no stray
dead end near the exit" a property of the algorithm rather than an
instruction handed to an image model — the one thing image models cannot be
trusted to get right (see ``CLAUDE.md``).

Leading underscore keeps this module out of the activity auto-discovery scan.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

#: Bit flags for the wall on each side of a cell. A set bit means that side is
#: a solid wall; a cleared bit means the maze can be walked through there.
NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8

_OPPOSITE = {NORTH: SOUTH, SOUTH: NORTH, EAST: WEST, WEST: EAST}
_DELTA = {NORTH: (-1, 0), SOUTH: (1, 0), EAST: (0, 1), WEST: (0, -1)}
_ALL_WALLS = NORTH | EAST | SOUTH | WEST

#: Corridor columns per difficulty. Bounded by what a chunky child's crayon
#: can draw inside without touching a wall: the printable maze stage is about
#: 176mm wide (A4 minus margins and the page header), and a corridor needs
#: >=13mm of clear width for that — so 13 columns is the practical ceiling,
#: which is why "hard" already sits at it and only "easy"/"medium" had room
#: to move up when the floor turned out to be too easy to feel like a maze.
_COLUMNS = {"easy": 9, "medium": 12, "hard": 13}

#: Usable stage height / width, from the same A4 page geometry (book.css's
#: .page height minus the .page-head) — rows follow this so the maze fills
#: the sheet with roughly square cells instead of a fixed row count.
_STAGE_ASPECT = 210 / 176


def grid_for(difficulty: str) -> tuple[int, int]:
    """``(columns, rows)`` for ``difficulty``, sized to fill one A4 page."""
    columns = _COLUMNS.get(difficulty, _COLUMNS["medium"])
    rows = max(columns, round(columns * _STAGE_ASPECT))
    return columns, rows


@dataclass(frozen=True)
class Maze:
    """A carved grid: ``walls[row][col]`` is the bitmask of closed sides."""

    columns: int
    rows: int
    walls: tuple[tuple[int, ...], ...]


def generate_maze(rng: random.Random, columns: int, rows: int) -> Maze:
    """Carve a perfect maze by randomized depth-first search.

    Every wall starts closed; carving an edge between two unvisited cells
    knocks down both sides of it at once, so the result is always reciprocal
    and, being a spanning tree, has exactly ``rows * columns - 1`` open
    edges and exactly one path between any two cells.
    """
    walls = [[_ALL_WALLS] * columns for _ in range(rows)]
    visited = [[False] * columns for _ in range(rows)]

    stack = [(0, 0)]
    visited[0][0] = True
    while stack:
        row, col = stack[-1]
        directions = [NORTH, EAST, SOUTH, WEST]
        rng.shuffle(directions)
        carved = False
        for direction in directions:
            delta_row, delta_col = _DELTA[direction]
            next_row, next_col = row + delta_row, col + delta_col
            if not (0 <= next_row < rows and 0 <= next_col < columns):
                continue
            if visited[next_row][next_col]:
                continue
            walls[row][col] &= ~direction
            walls[next_row][next_col] &= ~_OPPOSITE[direction]
            visited[next_row][next_col] = True
            stack.append((next_row, next_col))
            carved = True
            break
        if not carved:
            stack.pop()

    return Maze(columns=columns, rows=rows, walls=tuple(tuple(row) for row in walls))


def open_boundary(maze: Maze, row: int, col: int, side: int) -> Maze:
    """Knock down one outer-boundary wall, so a cell on the edge of the grid
    has a doorway leading off the sheet rather than being fully enclosed.

    Unlike an internal carve there is no neighbour on the other side to keep
    in sync — ``side`` faces outside the grid entirely — so this only ever
    touches the one cell. Kept separate from :func:`generate_maze` itself so
    the carve stays a plain, fully-enclosed spanning tree (what
    ``test_the_outer_boundary_is_closed`` checks); opening a doorway is a
    presentation choice layered on top by the caller.
    """
    walls = [list(r) for r in maze.walls]
    walls[row][col] &= ~side
    return Maze(columns=maze.columns, rows=maze.rows, walls=tuple(tuple(r) for r in walls))


def solve(maze: Maze, start: tuple[int, int], goal: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    """The walk from ``start`` to ``goal`` — unique, since a spanning tree has
    exactly one path between any two of its nodes."""
    parents: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    stack = [start]
    while stack:
        row, col = stack.pop()
        if (row, col) == goal:
            break
        for direction in (NORTH, EAST, SOUTH, WEST):
            if maze.walls[row][col] & direction:
                continue
            delta_row, delta_col = _DELTA[direction]
            neighbor = (row + delta_row, col + delta_col)
            if neighbor not in parents:
                parents[neighbor] = (row, col)
                stack.append(neighbor)

    path = [goal]
    while path[-1] != start:
        path.append(parents[path[-1]])
    path.reverse()
    return tuple(path)


def wall_segments(maze: Maze) -> str:
    """SVG path ``d`` data drawing every wall exactly once, in cell units.

    Only each cell's north and west walls are emitted, plus the south edge of
    the last row and the east edge of the last column — so a wall shared by
    two cells is never drawn twice (which would double its printed weight).
    """
    segments: list[str] = []
    for row in range(maze.rows):
        for col in range(maze.columns):
            mask = maze.walls[row][col]
            if mask & NORTH:
                segments.append(f"M{col} {row}H{col + 1}")
            if mask & WEST:
                segments.append(f"M{col} {row}V{row + 1}")
        if maze.walls[row][maze.columns - 1] & EAST:
            segments.append(f"M{maze.columns} {row}V{row + 1}")
    for col in range(maze.columns):
        if maze.walls[maze.rows - 1][col] & SOUTH:
            segments.append(f"M{col} {maze.rows}H{col + 1}")
    return " ".join(segments)


__all__ = [
    "EAST",
    "Maze",
    "NORTH",
    "SOUTH",
    "WEST",
    "generate_maze",
    "grid_for",
    "open_boundary",
    "solve",
    "wall_segments",
]
