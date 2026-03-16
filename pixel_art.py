"""Shared pixel-art rendering utility — no game logic, pure drawing."""

import pygame


def draw_pixel_art(surface, pixel_map, pixel_size, palette):
    """
    Render a 2-D pixel map onto *surface*.

    pixel_map  : list[list[int]]  — 0 = transparent, positive int = palette key
    pixel_size : int              — real pixels per art pixel
    palette    : dict[int, tuple] — color index -> (R, G, B)
    """
    for row_idx, row in enumerate(pixel_map):
        for col_idx, idx in enumerate(row):
            if idx == 0:
                continue
            pygame.draw.rect(
                surface,
                palette[idx],
                (col_idx * pixel_size, row_idx * pixel_size, pixel_size, pixel_size),
            )
