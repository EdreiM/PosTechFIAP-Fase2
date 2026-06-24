import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def gerar_relatorio_operacional(
    fitness_inicial,
    fitness_final,
    fitness_final_prioridade,
    fitness_target_solution,
    melhoria_fitness,
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
    saldo_autonomia,
):

    prompt = f"""
Você é um analista logístico hospitalar.

Com base nos dados abaixo, gere um RELATÓRIO OPERACIONAL.

Dados:

Fitness final com prioridades:
{fitness_final_prioridade}

Solução ótima benchmark:
{fitness_target_solution}

Fitness inicial:
{fitness_inicial}

Fitness final:
{fitness_final}

Melhoria fitness:
{melhoria_fitness:.2f}%

Melhoria distância:
{melhoria_distancia:.2f}%

Diferença para benchmark:
{diferenca_benchmark:.2f}%

Geração de convergência:
{geracao_convergencia}

Quantidade de cidades prioridade 10:
{prioridade_10}

Quantidade de cidades prioridade 9 ou 10:
{prioridade_9_10}

Média das prioridades das 10 primeiras posições:
{media_top10:.2f}

Carga total calculada:
{carga_total}

Capacidade máxima do veículo:
{capacidade_veiculo}

Distância máxima permitida:
{distancia_maxima_veiculo}

Distância da rota:
{distancia_total_rota}

Autonomia respeitada:
{autonomia_respeitada}

Saldo de autonomia:
{saldo_autonomia}

Rota:

{texto_rota}

Gere:

1. Resumo executivo
2. Eficiência da rota
3. Avaliação das prioridades
4. Análise da convergência
5. Pontos fortes
6. Pontos de melhoria
7. Conclusão final
8. Analise a distribuição das demandas entre as cidades.
9. Informe a carga total transportada.
10. Avalie se a capacidade máxima do veículo foi respeitada.
11. Explique os impactos operacionais caso a capacidade seja excedida.
Utilize linguagem profissional.
12. Avalie se a autonomia máxima do veículo foi respeitada.
13. Informe quanto de autonomia sobrou ou foi excedido.
14. Explique os impactos operacionais da autonomia encontrada.
"""

    resposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return resposta.choices[0].message.content