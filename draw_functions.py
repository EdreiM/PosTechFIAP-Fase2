# -*- coding: utf-8 -*-
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pygame
from typing import List, Tuple

matplotlib.use("Agg")


def create_plot_surface(
    x: list,
    y: list,
    x_label: str = "Generation",
    y_label: str = "Fitness",
    width: int = 400,
    height: int = 400,
) -> pygame.Surface:
    """Gera superfície do gráfico (cacheável entre frames)."""
    fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    ax.plot(x, y, color="#2563eb", linewidth=2)
    ax.set_ylabel(y_label, fontsize=8)
    ax.set_xlabel(x_label, fontsize=8)
    ax.tick_params(labelsize=7)
    plt.tight_layout()

    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    raw_data = canvas.buffer_rgba()
    size = canvas.get_width_height()
    surf = pygame.image.frombuffer(raw_data, size, "RGBA").copy()
    plt.close(fig)

    return surf


def draw_plot(
    screen: pygame.Surface,
    x: list,
    y: list,
    x_label: str = "Generation",
    y_label: str = "Fitness",
) -> pygame.Surface:
    """Desenha gráfico na tela e retorna superfície para reutilizar."""
    surf = create_plot_surface(x, y, x_label, y_label)
    screen.blit(surf, (0, 0))
    return surf


def draw_cities(
    screen: pygame.Surface,
    cities_locations: List[Tuple[int, int]],
    rgb_color: Tuple[int, int, int],
    node_radius: int,
    x_offset: int = 0,
) -> None:
    for city_location in cities_locations:
        x, y = city_location
        pygame.draw.circle(screen, rgb_color, (x + x_offset, y), node_radius)


def draw_paths(
    screen: pygame.Surface,
    path: List[Tuple[int, int]],
    rgb_color: Tuple[int, int, int],
    width: int = 1,
    x_offset: int = 0,
):
    if len(path) < 2:
        return

    pontos = [(x + x_offset, y) for x, y in path]
    pygame.draw.lines(screen, rgb_color, True, pontos, width=width)
