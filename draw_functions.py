# -*- coding: utf-8 -*-
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pygame
from typing import List, Tuple

matplotlib.use("Agg")


class ProjecaoMapa:
    """Projeta coordenadas do VRP para o painel direito da janela Pygame."""

    def __init__(
        self,
        cities: List[Tuple[float, float]],
        depot: Tuple[float, float],
        map_x: int,
        map_y: int,
        map_w: int,
        map_h: int,
        margem: int = 25,
    ):
        pontos = list(cities) + [depot]
        xs = [p[0] for p in pontos]
        ys = [p[1] for p in pontos]
        self.map_x = map_x
        self.map_y = map_y
        self.map_w = map_w
        self.map_h = map_h

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        faixa_x = max_x - min_x or 1
        faixa_y = max_y - min_y or 1
        escala = min(
            (map_w - 2 * margem) / faixa_x,
            (map_h - 2 * margem) / faixa_y,
        )
        self._offset_x = map_x + (map_w - faixa_x * escala) / 2
        self._offset_y = map_y + (map_h - faixa_y * escala) / 2
        self._min_x = min_x
        self._min_y = min_y
        self._escala = escala

    def projeta(self, ponto: Tuple[float, float]) -> Tuple[int, int]:
        x = self._offset_x + (ponto[0] - self._min_x) * self._escala
        y = self._offset_y + (ponto[1] - self._min_y) * self._escala
        return int(x), int(y)


def criar_projecao_mapa(
    cities: List[Tuple[float, float]],
    depot: Tuple[float, float],
    map_x: int,
    map_y: int,
    map_w: int,
    map_h: int,
) -> ProjecaoMapa:
    return ProjecaoMapa(cities, depot, map_x, map_y, map_w, map_h)


def desenhar_fundo_paineis(
    screen: pygame.Surface,
    plot_width: int,
    map_x: int,
    height: int,
    map_width: int,
) -> None:
    """Gráfico à esquerda, mapa à direita — áreas separadas."""
    screen.fill((255, 255, 255))
    pygame.draw.rect(
        screen, (248, 250, 252),
        (map_x, 0, map_width, height),
    )
    pygame.draw.line(
        screen, (209, 213, 219),
        (plot_width, 0), (plot_width, height), 2,
    )


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


def draw_mapa_projecao(
    screen: pygame.Surface,
    proj: ProjecaoMapa,
    cities: List[Tuple[int, int]],
    depot: Tuple[int, int],
    rotas: List[List[Tuple[int, int]]],
    cores_veiculos: List[Tuple[int, int, int]],
    node_radius: int = 10,
) -> None:
    """Desenha depósito, cidades e rotas no painel direito (coordenadas projetadas)."""
    dx, dy = proj.projeta(depot)
    raio_depot = node_radius + 4
    pygame.draw.circle(screen, (22, 101, 52), (dx, dy), raio_depot)
    pygame.draw.circle(screen, (255, 255, 255), (dx, dy), raio_depot, width=2)
    font = pygame.font.SysFont("Arial", 12, bold=True)
    label = font.render("H", True, (255, 255, 255))
    screen.blit(
        label,
        (dx - label.get_width() // 2, dy - label.get_height() // 2),
    )

    for indice, rota in enumerate(rotas):
        if not rota:
            continue
        cor = cores_veiculos[indice % len(cores_veiculos)]
        pontos = [proj.projeta(depot)]
        pontos.extend(proj.projeta(c) for c in rota)
        pontos.append(proj.projeta(depot))
        if len(pontos) >= 2:
            pygame.draw.lines(screen, cor, False, pontos, width=3)

    for cidade in cities:
        cx, cy = proj.projeta(cidade)
        pygame.draw.circle(screen, (239, 68, 68), (cx, cy), node_radius)
        pygame.draw.circle(screen, (127, 29, 29), (cx, cy), node_radius, width=1)
