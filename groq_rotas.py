import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def gerar_instrucoes_rota(best_solution, city_priorities):

    resumo_rota = ""

    for indice, cidade in enumerate(best_solution[:15], start=1):

        prioridade = city_priorities[cidade]

        resumo_rota += (
            f"{indice}. Cidade {cidade} "
            f"(prioridade {prioridade})\n"
        )

    prompt = f"""
Você é um especialista em logística hospitalar.

Com base na rota abaixo:

{resumo_rota}

Gere:

1. Instruções para equipe de entrega.
2. Resumo operacional da rota.
3. Principais cidades prioritárias.
4. Recomendações de execução.

Use linguagem clara e profissional.
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