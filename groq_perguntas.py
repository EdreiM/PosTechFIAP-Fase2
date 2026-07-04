import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def responder_pergunta(
    pergunta,
    texto_veiculos,
    texto_rota_resumo,
    analise,
    relatorio,
    relatorio_semanal,
    instrucoes,
):

    prompt = f"""
Você é um especialista em logística hospitalar.

=== VEÍCULOS ===

{texto_veiculos}

=== RESUMO DA ROTA ===

{texto_rota_resumo}

=== ANÁLISE TÉCNICA ===

{analise}

=== RELATÓRIO OPERACIONAL DIÁRIO ===

{relatorio}

=== RELATÓRIO OPERACIONAL SEMANAL ===

{relatorio_semanal}

=== INSTRUÇÕES DE ENTREGA ===

{instrucoes}

Responda a pergunta do usuário usando apenas os dados acima.

Regras:
- Responda de forma CURTA e direta (máximo 5 frases).
- Use o relatório diário para perguntas do dia; use o semanal para tendências da semana.
- Só liste a rota completa se o usuário pedir explicitamente.
- Avalie capacidade e autonomia por veículo, não pelo total.
- Se a informação não estiver disponível, diga: "Essa informação não está disponível nos resultados atuais."

Pergunta:

{pergunta}
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
