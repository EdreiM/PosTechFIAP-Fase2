import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def gerar_instrucoes_rota(texto_veiculos, prioridade_10, prioridade_9_10):

    prompt = f"""
Você é um coordenador de logística hospitalar.

Com base nos dados dos veículos abaixo, gere INSTRUÇÕES DE ENTREGA para motoristas e equipe.

Dados dos veículos:

{texto_veiculos}

Cidades críticas na operação: {prioridade_10} com prioridade 10, {prioridade_9_10} com prioridade 9 ou 10.

Para CADA veículo, informe:
- Quantidade de cidades a atender
- Carga (atual/máxima)
- Distância (atual/máxima)
- Status operacional (viável ou com restrição)
- Orientação prática de execução (1-2 frases)

Regras:
- Máximo 200 palavras no total.
- NÃO liste todas as cidades de cada rota.
- Priorize orientar sobre cidades com prioridade 9 e 10.
- Linguagem clara para equipe de campo.
- NÃO reorganize a ordem das cidades.
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
