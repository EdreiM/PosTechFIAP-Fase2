import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def responder_pergunta(
    pergunta,
    texto_rota,
    analise,
    relatorio
):

    prompt = f"""
Você é um especialista em logística hospitalar.

Você possui acesso aos dados abaixo.

=== ROTA ===

{texto_rota}

=== ANÁLISE ===

{analise}

=== RELATÓRIO ===

{relatorio}

Responda a pergunta do usuário utilizando apenas os dados fornecidos.

Se a resposta não estiver disponível, diga claramente:

"Essa informação não está disponível nos resultados atuais."

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