# -*- coding: utf-8 -*-
import math
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pygame
from typing import List, Optional, Set, Tuple

matplotlib.use("Agg")


def indices_veiculos_ociosos(rotas: List[List]) -> List[int]:
    """Índices de veículos sem entregas na execução."""
    return [i for i, rota in enumerate(rotas) if not rota]


def posicoes_marcadores_veiculos_ociosos(
    depot_xy: Tuple[float, float],
    num_ociosos: int,
    raio_orbita: float = 28,
) -> List[Tuple[int, int]]:
    """Posições em arco semicircular abaixo do depósito (H)."""
    if num_ociosos <= 0:
        return []

    dx, dy = depot_xy
    if num_ociosos == 1:
        angulos = [math.pi / 2]
    else:
        inicio = math.radians(35)
        fim = math.radians(145)
        angulos = [
            inicio + (fim - inicio) * i / (num_ociosos - 1)
            for i in range(num_ociosos)
        ]

    return [
        (int(dx + raio_orbita * math.cos(a)), int(dy + raio_orbita * math.sin(a)))
        for a in angulos
    ]


def montar_legenda_veiculos(
    rotas: List[List],
    nomes_cores: List[str],
) -> str:
    """Texto da legenda separando veículos em rota e ociosos no hospital."""
    ativos = [i for i, rota in enumerate(rotas) if rota]
    ociosos = [i for i, rota in enumerate(rotas) if not rota]
    partes = []
    if ativos:
        partes.append(
            "Em rota: " + ", ".join(nomes_cores[i] for i in ativos)
        )
    if ociosos:
        partes.append(
            "No hospital: "
            + ", ".join(f"{nomes_cores[i]} (ocioso)" for i in ociosos)
        )
    return " | ".join(partes)


def _posicao_label_trecho(
    p0: Tuple[int, int],
    p1: Tuple[int, int],
    offset: float = 14,
) -> Tuple[int, int]:
    """Ponto ao longo do trecho p0→p1 para label do veículo."""
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    dist = math.hypot(dx, dy) or 1.0
    return (
        int(p0[0] + dx * offset / dist),
        int(p0[1] + dy * offset / dist),
    )


def _desenhar_label_veiculo_rota_pygame(
    screen: pygame.Surface,
    x: int,
    y: int,
    cor: Tuple[int, int, int],
    label: str,
) -> None:
    font = pygame.font.SysFont("Arial", 9, bold=True)
    texto = font.render(label, True, cor)
    fundo = pygame.Surface(
        (texto.get_width() + 4, texto.get_height() + 2), pygame.SRCALPHA
    )
    fundo.fill((255, 255, 255, 200))
    screen.blit(fundo, (x - 2, y - 1))
    screen.blit(texto, (x, y))


def _desenhar_marcador_veiculo_ocioso_pygame(
    screen: pygame.Surface,
    x: int,
    y: int,
    cor: Tuple[int, int, int],
    label: str,
    raio: int = 7,
) -> None:
    pygame.draw.circle(screen, cor, (x, y), raio)
    pygame.draw.circle(screen, (203, 213, 225), (x, y), raio, width=1)
    font = pygame.font.SysFont("Arial", 8, bold=True)
    texto = font.render(label, True, (255, 255, 255))
    screen.blit(
        texto,
        (x - texto.get_width() // 2, y - texto.get_height() // 2),
    )


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
    remanescentes: Optional[Set[Tuple[int, int]]] = None,
) -> None:
    """Desenha depósito, cidades, rotas, labels V{n} e marcadores ociosos."""
    dx, dy = proj.projeta(depot)
    raio_depot = node_radius + 4
    remanescentes_set = remanescentes or set()

    for indice, rota in enumerate(rotas):
        if not rota:
            continue
        cor = cores_veiculos[indice % len(cores_veiculos)]
        pontos = [proj.projeta(depot)]
        pontos.extend(proj.projeta(c) for c in rota)
        pontos.append(proj.projeta(depot))
        if len(pontos) >= 2:
            pygame.draw.lines(screen, cor, False, pontos, width=3)
            if len(pontos) >= 2:
                lx, ly = _posicao_label_trecho(pontos[0], pontos[1])
                _desenhar_label_veiculo_rota_pygame(
                    screen, lx, ly, cor, f"V{indice + 1}"
                )

    ociosos = indices_veiculos_ociosos(rotas)
    posicoes = posicoes_marcadores_veiculos_ociosos((dx, dy), len(ociosos))
    for pos, indice in zip(posicoes, ociosos):
        cor = cores_veiculos[indice % len(cores_veiculos)]
        _desenhar_marcador_veiculo_ocioso_pygame(
            screen, pos[0], pos[1], cor, f"V{indice + 1}"
        )

    pygame.draw.circle(screen, (22, 101, 52), (dx, dy), raio_depot)
    pygame.draw.circle(screen, (255, 255, 255), (dx, dy), raio_depot, width=2)
    font = pygame.font.SysFont("Arial", 12, bold=True)
    label = font.render("H", True, (255, 255, 255))
    screen.blit(
        label,
        (dx - label.get_width() // 2, dy - label.get_height() // 2),
    )

    for cidade in cities:
        cx, cy = proj.projeta(cidade)
        if cidade in remanescentes_set:
            pygame.draw.circle(screen, (148, 163, 184), (cx, cy), node_radius)
            pygame.draw.circle(
                screen, (100, 116, 139), (cx, cy), node_radius, width=1
            )
        else:
            pygame.draw.circle(screen, (239, 68, 68), (cx, cy), node_radius)
            pygame.draw.circle(
                screen, (127, 29, 29), (cx, cy), node_radius, width=1
            )
