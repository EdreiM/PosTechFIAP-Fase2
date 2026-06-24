import pygame
from pygame.locals import *
import random
import itertools
from genetic_algorithm import (
    mutate,
    order_crossover,
    generate_random_population,
    calculate_fitness,
    calculate_distance_only,
    sort_population,
    default_problems,
    city_priorities,
    city_demands
)
from draw_functions import draw_paths, draw_plot, draw_cities
import sys
import numpy as np
import pygame
from benchmark_att48 import *

from groq_analysis import analisar_resultado
from groq_relatorio import gerar_relatorio_operacional
from groq_perguntas import responder_pergunta

# Define constant values
# pygame
WIDTH, HEIGHT = 800, 400
NODE_RADIUS = 10
FPS = 30
PLOT_X_OFFSET = 450

# GA
N_CITIES = 15
POPULATION_SIZE = 100
N_GENERATIONS = 1000
MUTATION_PROBABILITY = 0.5

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)


# Initialize problem
# Using Random cities generation
# cities_locations = [(random.randint(NODE_RADIUS + PLOT_X_OFFSET, WIDTH - NODE_RADIUS), random.randint(NODE_RADIUS, HEIGHT - NODE_RADIUS))
#                     for _ in range(N_CITIES)]


# # # Using Deault Problems: 10, 12 or 15
# WIDTH, HEIGHT = 800, 400
# cities_locations = default_problems[15]


# Using att48 benchmark
WIDTH, HEIGHT = 1500, 800
att_cities_locations = np.array(att_48_cities_locations)
max_x = max(point[0] for point in att_cities_locations)
max_y = max(point[1] for point in att_cities_locations)
scale_x = (WIDTH - PLOT_X_OFFSET - NODE_RADIUS) / max_x
scale_y = HEIGHT / max_y
cities_locations = [(int(point[0] * scale_x + PLOT_X_OFFSET),
                     int(point[1] * scale_y)) for point in att_cities_locations]
target_solution = [cities_locations[i-1] for i in att_48_cities_order]



# ----- Using att48 benchmark


# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSP Solver using Pygame")
clock = pygame.time.Clock()
generation_counter = itertools.count(start=1)  # Start the counter at 1

# Gera prioridades para cada cidade do benchmark

random.seed(42)

for city in cities_locations:
    city_priorities[city] = random.randint(1, 10)
    city_demands[city] = random.randint(5, 30)

print("\nPRIORIDADES DAS CIDADES")
print("-" * 50)

for indice, (cidade, prioridade) in enumerate(city_priorities.items(), start=1):
    print(f"Cidade {indice}: Prioridade {prioridade}")

# Agora que as prioridades já existem,
# calculamos a fitness da solução ótima ATT48
fitness_target_solution = calculate_distance_only(
    target_solution
)

print(f"Solução ótima ATT48: {fitness_target_solution:.2f}")
print(f"Quantidade de cidades: {len(target_solution)}")  
# Create Initial Population 
# TODO:- use some heuristic like Nearest Neighbour our Convex Hull to initialize
population = generate_random_population(cities_locations, POPULATION_SIZE)
best_fitness_values = []
best_solutions = []




# Guarda a fitness da primeira geração
fitness_inicial = None
melhor_fitness_global = float("inf")

geracoes_sem_melhora = 0

LIMITE_SEM_MELHORA = 100

geracao_convergencia = None
# Main game loop

running = True
generation = 0 

### while running:
while running and generation < N_GENERATIONS:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

    generation = next(generation_counter)

    screen.fill(WHITE)

    population_fitness = [calculate_fitness(
        individual) for individual in population]

    population, population_fitness = sort_population(
        population,  population_fitness)

    best_fitness = calculate_fitness(population[0])

    if best_fitness < melhor_fitness_global:

        melhor_fitness_global = best_fitness
        geracoes_sem_melhora = 0

    else:
        geracoes_sem_melhora += 1

    best_solution = population[0]

    # Salva a fitness da primeira geração
    if fitness_inicial is None:
        fitness_inicial = best_fitness

    best_fitness_values.append(best_fitness)
    best_solutions.append(best_solution)

    draw_plot(screen, list(range(len(best_fitness_values))),
              best_fitness_values, y_label="Fitness - Distance (pxls)")

    draw_cities(screen, cities_locations, RED, NODE_RADIUS)
    draw_paths(screen, best_solution, BLUE, width=3)
    draw_paths(screen, population[1], rgb_color=(128, 128, 128), width=1)

    if generation % 50 == 0:

        print(
            f"Generation {generation}: "
            f"Best fitness = {round(best_fitness, 2)} | "
            f"Sem melhora = {geracoes_sem_melhora}"
        )

    if geracoes_sem_melhora >= LIMITE_SEM_MELHORA:

        geracao_convergencia = generation

        print("\nConvergência detectada.")
        print(
            f"Sem melhoria por "
            f"{LIMITE_SEM_MELHORA} gerações."
        )

        break

    new_population = [population[0]]  # Keep the best individual: ELITISM

    while len(new_population) < POPULATION_SIZE:

        # selection
        # simple selection based on first 10 best solutions
        # parent1, parent2 = random.choices(population[:10], k=2)

        # solution based on fitness probability
        probability = 1 / np.array(population_fitness)
        parent1, parent2 = random.choices(population, weights=probability, k=2)

        # child1 = order_crossover(parent1, parent2)
        child1 = order_crossover(parent1, parent2)

        child1 = mutate(child1, MUTATION_PROBABILITY)

        new_population.append(child1)

    population = new_population

    pygame.display.flip()
    clock.tick(FPS)


# TODO: save the best individual in a file if it is better than the one saved.


# Fitness usado pelo AG (distância + prioridade)
fitness_final_prioridade = best_fitness_values[-1]

# Distância real da rota
fitness_final = calculate_distance_only(
    best_solution
)

# ==========================
# DIVISÃO EM VEÍCULOS
# ==========================

NUM_VEICULOS = 3

rotas_veiculos = [
    [] for _ in range(NUM_VEICULOS)
]

for indice, cidade in enumerate(best_solution):

    veiculo = indice % NUM_VEICULOS

    rotas_veiculos[veiculo].append(cidade)

print("\nROTAS DOS VEÍCULOS")
print("=" * 50)

for indice, rota in enumerate(rotas_veiculos, start=1):

    carga = sum(
        city_demands[cidade]
        for cidade in rota
    )

    distancia = calculate_distance_only(rota)

    print(f"Veículo {indice}")
    print(f"Cidades: {len(rota)}")
    print(f"Carga: {carga}")
    print(f"Distância: {distancia:.2f}")
    print("-" * 50)


# Autonomia máxima definida no algoritmo
distancia_maxima_veiculo = 9000

# Distância total da rota encontrada
distancia_total_rota = fitness_final

# Verifica se respeitou a autonomia
autonomia_respeitada = (
    distancia_total_rota <= distancia_maxima_veiculo
)

# Quanto sobrou ou excedeu
saldo_autonomia = (
    distancia_maxima_veiculo
    - distancia_total_rota
)

# Calcula a melhoria percentual usando a mesma métrica do algoritmo:
# distância + penalidade de prioridade.
melhoria_percentual = (
    (fitness_inicial - fitness_final_prioridade)
    / fitness_inicial
) * 100

diferenca_benchmark = (
    (fitness_final - fitness_target_solution)
    / fitness_target_solution
) * 100

print("\n" + "=" * 60)
print("RESULTADOS FINAIS")
print("=" * 60)

print(f"Fitness inicial: {fitness_inicial:.2f}")
print(f"Fitness final:   {fitness_final:.2f}")
print(f"Fitness com prioridade: {fitness_final_prioridade:.2f}")
melhoria_prioridade = (
    (fitness_inicial - fitness_final_prioridade)
    / fitness_inicial
) * 100

melhoria_distancia = (
    (fitness_inicial - fitness_final)
    / fitness_inicial
) * 100

print(
    f"Melhoria (fitness): "
    f"{melhoria_prioridade:.2f}%"
)

print(
    f"Melhoria (distância): "
    f"{melhoria_distancia:.2f}%"
)


print(f"Solução ótima:  {fitness_target_solution:.2f}")
print(f"Diferença para ótimo: {diferenca_benchmark:.2f}%")

print(f"Autonomia máxima: {distancia_maxima_veiculo:.2f}")
print(f"Distância da rota: {distancia_total_rota:.2f}")

if autonomia_respeitada:

    print(
        f"Autonomia respeitada. "
        f"Sobrou {saldo_autonomia:.2f}"
    )

else:

    print(
        f"Autonomia excedida em "
        f"{abs(saldo_autonomia):.2f}"
    )
print("\nTOP 10 CIDADES DA ROTA FINAL")
print("-" * 50)

for indice, cidade in enumerate(best_solution[:10], start=1):

    prioridade = city_priorities[cidade]

    print(
        f"Posição {indice} -> Prioridade {prioridade}"
    )


top10_prioridades = []

for cidade in best_solution[:10]:
    top10_prioridades.append(
        city_priorities[cidade]
    )    

rota_detalhada = []

for indice, cidade in enumerate(best_solution, start=1):

    prioridade = city_priorities[cidade]

    nome_cidade = f"Cidade {indice}"

    rota_detalhada.append({
        "ordem": indice,
        "nome": nome_cidade,
        "x": cidade[0],
        "y": cidade[1],
        "prioridade": prioridade,
        "demanda": city_demands[cidade]
    })
# ==========================
# ANÁLISE DA IA (GROQ)
# ==========================

# Quantidade de cidades prioridade 10
prioridade_10 = sum(
    1 for cidade in rota_detalhada
    if cidade["prioridade"] == 10
)

# Quantidade de cidades prioridade 9 ou 10
prioridade_9_10 = sum(
    1 for cidade in rota_detalhada
    if cidade["prioridade"] >= 9
)

# Média das prioridades das 10 primeiras posições
media_top10 = (
    sum(top10_prioridades)
    / len(top10_prioridades)
)

# Soma toda a demanda da rota
carga_total = sum(
    item["demanda"]
    for item in rota_detalhada
)



# Capacidade máxima do veículo
capacidade_veiculo = 400

print(f"Carga total da rota: {carga_total}")
print(f"Capacidade do veículo: {capacidade_veiculo}")

texto_rota = ""

for item in rota_detalhada:

    texto_rota += (
        f"Ordem {item['ordem']} | "
        f"Nome={item['nome']} | "
        f"X={item['x']} | "
        f"Y={item['y']} | "
        f"Prioridade={item['prioridade']} | "
        f"Demanda={item['demanda']}\n"
    )

if geracao_convergencia is None:
    geracao_convergencia = generation

analise = analisar_resultado(
    fitness_inicial,
    fitness_final,
    fitness_final_prioridade,
    melhoria_prioridade,
    melhoria_distancia,
    fitness_target_solution,
    diferenca_benchmark,
    top10_prioridades,
    texto_rota,
    geracao_convergencia,
    prioridade_10,
    prioridade_9_10,
    media_top10
)

print("\n" + "=" * 60)
print("ANÁLISE DA IA")
print("=" * 60)

print(analise)

relatorio = gerar_relatorio_operacional(
    fitness_inicial,
    fitness_final,
    fitness_final_prioridade,
    fitness_target_solution,
    melhoria_prioridade,
    melhoria_distancia,
    diferenca_benchmark,
    geracao_convergencia,
    prioridade_10,
    prioridade_9_10,
    media_top10,
    carga_total,
    capacidade_veiculo,
    texto_rota,
    distancia_maxima_veiculo,
    distancia_total_rota,
    autonomia_respeitada,
    saldo_autonomia
)

print("\n" + "=" * 60)
print("RELATÓRIO OPERACIONAL")
print("=" * 60)

print(relatorio)

print("\n" + "=" * 60)
print("CONSULTA EM LINGUAGEM NATURAL")
print("=" * 60)

while True:

    pergunta = input(
        "\nDigite uma pergunta (ou 'sair'): "
    )

    if pergunta.lower() == "sair":
        break

    resposta = responder_pergunta(
        pergunta,
        texto_rota,
        analise,
        relatorio
    )

    print("\nResposta:")
    print(resposta)

if geracao_convergencia is None:
    geracao_convergencia = generation
# Salva o resultado em arquivo texto

with open("melhor_rota.txt", "w", encoding="utf-8") as arquivo:

    arquivo.write("RESULTADOS DO ALGORITMO GENÉTICO\n")

    
    arquivo.write("PARÂMETROS UTILIZADOS\n")
    arquivo.write("-" * 50 + "\n")

    arquivo.write(f"População: {POPULATION_SIZE}\n")
    arquivo.write(f"Gerações: {N_GENERATIONS}\n")
    arquivo.write(f"Taxa de mutação: {MUTATION_PROBABILITY}\n")
    arquivo.write(f"Cidades: {len(cities_locations)}\n\n")

    arquivo.write(
        f"Geração de convergência: {geracao_convergencia}\n\n"
    )
    
    arquivo.write("PRIORIDADES DAS CIDADES\n")
    arquivo.write("-" * 50 + "\n")

    for indice, (cidade, prioridade) in enumerate(city_priorities.items(), start=1):
        arquivo.write(f"Cidade {indice}: prioridade {prioridade}\n")

    arquivo.write("\n")
   
    arquivo.write("=" * 50 + "\n\n")

    arquivo.write(f"Fitness inicial: {fitness_inicial:.2f}\n")
    arquivo.write(f"Fitness final: {fitness_final:.2f}\n")
    arquivo.write(f"Fitness com prioridade: {fitness_final_prioridade:.2f}\n")
    arquivo.write(
        f"Melhoria (fitness): {melhoria_prioridade:.2f}%\n"
    )

    arquivo.write(
        f"Melhoria (distância): {melhoria_distancia:.2f}%\n\n"
    )

    arquivo.write(
        f"Solução ótima: {fitness_target_solution:.2f}\n\n"
    )

    arquivo.write(
        f"Diferença para ótimo: {diferenca_benchmark:.2f}%\n\n"
    )




    arquivo.write("Melhor rota encontrada:\n")

    for indice, cidade in enumerate(best_solution, start=1):

        prioridade = city_priorities[cidade]

        arquivo.write(
            f"{indice}. {cidade} | Prioridade: {prioridade}\n"
        )

    arquivo.write("\n\n")
    arquivo.write("=" * 50 + "\n")
    arquivo.write("ANÁLISE GERADA PELA IA\n")
    arquivo.write("=" * 50 + "\n\n")

    arquivo.write(analise)
    arquivo.write("\n\n")
    arquivo.write("=" * 50 + "\n")
    arquivo.write("RELATÓRIO OPERACIONAL\n")
    arquivo.write("=" * 50 + "\n\n")
    arquivo.write(relatorio)

    arquivo.write("\n\n")
    arquivo.write("=" * 50 + "\n")
    arquivo.write("ROTA DETALHADA\n")
    arquivo.write("=" * 50 + "\n\n")

    for item in rota_detalhada:

        arquivo.write(
            f"Ordem: {item['ordem']} | "
            f"X: {item['x']} | "
            f"Y: {item['y']} | "
            f"Prioridade: {item['prioridade']} | "
            f"Demanda: {item['demanda']}\n"
        )


# exit software
pygame.quit()
sys.exit()
