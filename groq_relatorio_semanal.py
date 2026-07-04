import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def gerar_relatorio_semanal(
    texto_resumo_semanal,
    texto_veiculos,
    relatorio_diario,
):
    prompt = f"""
Você é um analista logístico hospitalar.

Gere um RELATÓRIO OPERACIONAL SEMANAL consolidado sobre entregas de medicamentos e insumos.

Dados consolidados da semana:

{texto_resumo_semanal}

Status por veículo (média/referência da operação):

{texto_veiculos}

Referência do fechamento diário mais recente:

{relatorio_diario}

Gere exatamente estas seções:

1. Resumo da semana
2. Eficiência acumulada das rotas
3. Economia de tempo e recursos
4. Padrões identificados
5. Recomendações estratégicas (próxima semana)

Regras:
- Máximo 350 palavras no total.
- Foque em tendências, padrões e economia — não repita o relatório diário.
- Avalie capacidade e autonomia por veículo quando relevante.
- Sugira melhorias de processo com base nos padrões (ex.: redistribuição, frota, prioridades).
- Linguagem operacional e direta.
- NÃO liste todas as cidades.
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
