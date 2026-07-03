import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def analisar_resultado(
    fitness_inicial,
    fitness_final,
    fitness_final_prioridade,
    melhoria_fitness,
    melhoria_distancia,
    fitness_target_solution,
    diferenca_benchmark,
    top10_prioridades,
    geracao_convergencia,
    prioridade_10,
    prioridade_9_10,
    media_top10,
    total_cidades,
    num_veiculos,
    distancia_aleatoria,
):

    prompt = f"""
Analise tecnicamente os resultados de um Algoritmo Genético aplicado ao VRP hospitalar.

Dados:

Fitness inicial: {fitness_inicial:.2f}
Fitness final (com prioridades e restrições): {fitness_final_prioridade:.2f}
Distância total da operação ({num_veiculos} veículos): {fitness_final:.2f}
Melhoria do fitness: {melhoria_fitness:.2f}%
Melhoria da distância: {melhoria_distancia:.2f}%
Solução ótima VRP (força bruta): {fitness_target_solution:.2f}
Diferença para o ótimo: {diferenca_benchmark:.2f}%
Distância de rota aleatória: {distancia_aleatoria:.2f}
Geração de convergência: {geracao_convergencia}
Total de cidades: {total_cidades}
Veículos disponíveis: {num_veiculos}

Prioridades nas 10 primeiras posições: {top10_prioridades}
Média das prioridades (top 10): {media_top10:.2f}
Cidades com prioridade 10: {prioridade_10}
Cidades com prioridade 9 ou 10: {prioridade_9_10}

Parâmetros: população 100, gerações 1000, mutação 0.5.

Nota: o AG otimiza VRP com {num_veiculos} veículos, prioridades, capacidade e autonomia por veículo.

Gere uma análise técnica CURTA com exatamente estas seções:

1. Qualidade da solução
2. Convergência
3. Prioridades
4. Benchmark (compare AG vs rota aleatória vs ótimo VRP)
5. Conclusão

Regras:
- Máximo 250 palavras no total.
- Linguagem técnica e direta, sem tom acadêmico.
- NÃO liste cidades.
- NÃO gere plano de entrega.
- NÃO analise a rota completa cidade por cidade.
- Use apenas os dados fornecidos.
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
