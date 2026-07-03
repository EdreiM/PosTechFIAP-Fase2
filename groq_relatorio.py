import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def gerar_relatorio_operacional(
    fitness_final,
    melhoria_distancia,
    diferenca_benchmark,
    prioridade_10,
    prioridade_9_10,
    media_top10,
    texto_veiculos,
    total_cidades,
    num_veiculos,
    distancia_aleatoria,
    fitness_target_solution,
):

    prompt = f"""
Você é um analista logístico hospitalar.

Gere um RELATÓRIO OPERACIONAL DIÁRIO de fechamento da operação de entregas.

Dados gerais:

Total de cidades: {total_cidades}
Veículos em operação: {num_veiculos}
Distância total da operação: {fitness_final:.2f}
Melhoria da distância vs início: {melhoria_distancia:.2f}%
Comparativo VRP -> AG: {fitness_final:.2f} | Aleatória: {distancia_aleatoria:.2f} | Ótimo: {fitness_target_solution:.2f}
Diferença para ótimo VRP: {diferenca_benchmark:.2f}%
Cidades com prioridade 10: {prioridade_10}
Cidades com prioridade 9 ou 10: {prioridade_9_10}
Média das prioridades (10 primeiras posições): {media_top10:.2f}

Status por veículo (avalie CADA veículo individualmente):

{texto_veiculos}

Gere exatamente estas seções:

1. Resumo
2. Eficiência da rota
3. Capacidade dos veículos
4. Autonomia dos veículos
5. Prioridades atendidas
6. Recomendações (melhorias no processo para o próximo dia/semana)

Regras:
- Máximo 300 palavras no total.
- Avalie capacidade e autonomia POR VEÍCULO, não pelo total da operação.
- Na seção Recomendações, sugira melhorias práticas (ex.: redistribuir cidades críticas, usar mais veículos, ajustar peso de prioridade).
- Linguagem operacional e direta.
- NÃO liste todas as cidades.
- NÃO repita análise de convergência ou benchmark longo.
- NÃO use linguagem acadêmica.
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
