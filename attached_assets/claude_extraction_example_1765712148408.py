'''
Este script demonstra como usar o Claude AI para extrair a Proposta de Valor ao Empregado (EVP) 
e as competências-chave de uma empresa a partir de um texto de contexto, usando técnicas avançadas de prompt engineering.
'''

import anthropic
import json
from pydantic import BaseModel, Field
from typing import List

# 1. Definição do Schema de Saída com Pydantic
# Isso garante que a saída do modelo seja estruturada e possa ser validada.
class CompanyInsights(BaseModel):
    evp: str = Field(description="Um parágrafo conciso que resume a Proposta de Valor ao Empregado. Deve responder à pergunta: 'Por que alguém deveria trabalhar aqui?'.")
    competencies: List[str] = Field(description="Uma lista das competências e habilidades-chave que a empresa valoriza em seus colaboradores.")

# 2. Construção do Prompt Mestre
# Este template combina Persona, Contexto, Instruções, Chain-of-Thought e Exemplos (Few-Shot).
def get_master_prompt(company_context: str) -> str:
    return f'''<prompt>
<persona>
Você é um especialista em Estratégia de RH e Cultura Organizacional. Sua tarefa é analisar o conteúdo fornecido sobre uma empresa e extrair sua Proposta de Valor ao Empregado (EVP) e suas competências-chave.
</persona>

<contexto>
{company_context}
</contexto>

<instrucoes>
Analise o <contexto> fornecido e siga os seguintes passos:

1.  **Raciocínio (Chain-of-Thought)**: Dentro da tag `<thinking>`, detalhe seu processo de análise para inferir o EVP e as competências.
    *   Para o **EVP**, identifique os benefícios tangíveis e intangíveis que a empresa oferece. Procure por informações na página de carreiras, na descrição da cultura, em posts de blog sobre a vida na empresa e em benefícios mencionados. O EVP é a soma de tudo que o funcionário ganha em troca de seu trabalho.
    *   Para as **Competências**, procure por habilidades, comportamentos e mentalidades valorizadas. Analise a linguagem usada nas descrições de vagas, nos valores da empresa e na forma como ela descreve sua equipe.

2.  **Extração Estruturada**: Com base no seu raciocínio, preencha o schema JSON definido em `CompanyInsights`. A resposta final deve conter APENAS o objeto JSON dentro da tag `<answer>`.
</instrucoes>

<exemplos>
<exemplo>
<texto_exemplo>
**Página de Carreiras da InovaTech**:
"Na InovaTech, você não é apenas um funcionário, é um pioneiro. Oferecemos autonomia para explorar novas ideias, um orçamento generoso para desenvolvimento profissional e a chance de trabalhar com tecnologias de ponta. Nossos times são ágeis e colaborativos, e celebramos a curiosidade e a vontade de resolver problemas complexos."
</texto_exemplo>
<json_exemplo>
{{
  "evp": "A InovaTech oferece aos seus colaboradores a oportunidade de serem pioneiros em suas áreas, provendo autonomia, recursos para desenvolvimento e acesso a tecnologias de ponta. A cultura valoriza a agilidade, a colaboração e a resolução de problemas complexos, criando um ambiente ideal para quem busca impacto e crescimento.",
  "competencies": [
    "Autonomia e Proatividade",
    "Curiosidade e Aprendizado Contínuo",
    "Colaboração e Trabalho em Equipe",
    "Resolução de Problemas Complexos",
    "Agilidade e Adaptação"
  ]
}}
</json_exemplo>
</exemplo>
</exemplos>

<resposta_final>
<thinking>
(Aqui você irá detalhar seu raciocínio)
</thinking>
<answer>
(Aqui você irá gerar o JSON final)
</answer>
</resposta_final>

</prompt>'''

# 3. Função para Chamar a API e Extrair os Dados
def extract_company_insights(client: anthropic.Anthropic, context: str) -> CompanyInsights:
    '''
    Envia o prompt para a API do Claude e retorna o objeto Pydantic validado.
    '''
    master_prompt = get_master_prompt(context)

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": master_prompt}
            ]
        )

        # Extrai o conteúdo da resposta
        full_response_text = response.content[0].text

        # Isola o JSON dentro das tags <answer>
        start_tag = "<answer>"
        end_tag = "</answer>"
        start_index = full_response_text.find(start_tag) + len(start_tag)
        end_index = full_response_text.find(end_tag)
        json_string = full_response_text[start_index:end_index].strip()

        # Converte a string JSON para um dicionário Python
        parsed_json = json.loads(json_string)

        # Valida e cria o objeto Pydantic
        company_profile = CompanyInsights(**parsed_json)
        return company_profile

    except Exception as e:
        print(f"Ocorreu um erro ao processar a resposta da API: {e}")
        return None

# 4. Exemplo de Execução
if __name__ == "__main__":
    # Inicialize o cliente do Anthropic (requer a variável de ambiente ANTHROPIC_API_KEY)
    try:
        api_client = anthropic.Anthropic()
    except ImportError:
        print("A biblioteca da Anthropic não está instalada. Instale com: pip install anthropic")
        exit()
    except Exception as e:
        print(f"Erro ao inicializar o cliente da Anthropic: {e}")
        print("Certifique-se de que a variável de ambiente ANTHROPIC_API_KEY está configurada.")
        exit()

    # Contexto de exemplo (simulando dados do Apify)
    example_context = '''
    <website_content>
    ## Página de Carreiras da TechFront
    Na TechFront, nós empoderamos nossos engenheiros a tomar decisões. Você terá a liberdade de escolher suas ferramentas e a flexibilidade de horário que precisa para fazer seu melhor trabalho. Oferecemos um plano de saúde premium, acesso ilimitado a cursos online e um programa de mentoria com líderes da indústria. Buscamos pessoas que não têm medo de falhar, que aprendem rápido e que são obcecadas por entregar valor ao cliente.
    </website_content>
    <linkedin_data>
    {
        "name": "TechFront Solutions",
        "description": "Liderando a inovação em soluções de nuvem com foco total no sucesso do cliente. Nossos valores são: Cliente em Primeiro Lugar, Inovação Constante e Transparência Radical.",
        "employeeCount": 250
    }
    </linkedin_data>
    '''

    print("Analisando o contexto da empresa para extrair EVP e competências...")
    insights = extract_company_insights(api_client, example_context)

    if insights:
        print("\n--- Insights Extraídos com Sucesso ---\n")
        print("Proposta de Valor ao Empregado (EVP):")
        print(insights.evp)
        print("\nCompetências-Chave:")
        for competency in insights.competencies:
            print(f"- {competency}")
        print("\n------------------------------------\n")
        # Você pode acessar os dados como um dicionário também
        # print(insights.model_dump_json(indent=2))
