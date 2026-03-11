# Guia Completo: Prompt Engineering para Extração de EVP e Competências com Claude AI

## Introdução

A extração de informações subjetivas como a Proposta de Valor ao Empregado (EVP) e as competências-chave de uma empresa é uma tarefa que exige mais do que simples busca por palavras-chave. Requer raciocínio contextual, compreensão de nuances culturais e capacidade de inferência. Este guia apresenta as melhores práticas de prompt engineering para garantir que o Claude AI execute essa tarefa com precisão e consistência.

## 1. Os Três Pilares do Prompt Eficaz

A construção de um prompt robusto para inferência repousa sobre três elementos fundamentais:

### 1.1 Definição de Persona (Role-Playing)

Instruir o Claude a assumir a identidade de um especialista ativa o conhecimento do modelo relacionado àquela área. Um prompt que começa com "Você é um especialista em Estratégia de RH e Cultura Organizacional" orienta o modelo a utilizar padrões de raciocínio mais sofisticados e contextualmente apropriados.

A persona funciona como um filtro cognitivo, direcionando o modelo a considerar aspectos que um especialista real consideraria. Ao extrair EVP, um especialista em RH pensaria em benefícios tangíveis (salário, benefícios) e intangíveis (propósito, crescimento, cultura). Ao identificar competências, pensaria em habilidades técnicas, comportamentais e atitudinais.

### 1.2 Contexto Rico e Estruturado

A qualidade da inferência é diretamente proporcional à qualidade do contexto fornecido. Ao consolidar dados do Apify, utilize tags XML para diferenciar as fontes:

```xml
<website_content>
(Conteúdo extraído pelo Website Content Crawler em Markdown)
</website_content>

<linkedin_data>
(Dados estruturados do LinkedIn Company Scraper em JSON)
</linkedin_data>
```

Essa estruturação permite que o modelo compreenda a origem de cada informação e possa cruzar dados de diferentes fontes para validar suas inferências. Por exemplo, se a página de carreiras menciona "autonomia" e o perfil do LinkedIn descreve a empresa como "ágil", o modelo pode inferir com mais confiança que a autonomia é um valor central.

### 1.3 Instruções Explícitas e Detalhadas

Seja extremamente claro sobre o que você quer. Defina cada conceito e especifique de onde o modelo deve extrair ou inferir a informação. Em vez de "extraia o EVP", diga:

> O EVP (Proposta de Valor ao Empregado) é a resposta à pergunta: "Por que alguém deveria trabalhar aqui?" Inclua benefícios tangíveis (salário, benefícios, flexibilidade) e intangíveis (propósito, crescimento, cultura). Procure por informações na página de carreiras, na descrição da cultura e em posts sobre a vida na empresa.

## 2. Técnicas Avançadas de Prompt Engineering

### 2.1 Chain-of-Thought (CoT): Forçando o Raciocínio Explícito

A técnica de Chain-of-Thought [1] instrui o modelo a detalhar seu processo de raciocínio passo a passo antes de chegar à resposta final. Para tarefas de inferência, isso é crucial.

Ao forçar o modelo a "pensar em voz alta", você consegue:

1.  **Aumentar a Precisão**: O modelo conecta pistas encontradas no texto de forma mais deliberada.
2.  **Facilitar a Auditoria**: Você pode revisar o raciocínio para entender por que o modelo chegou a uma conclusão.
3.  **Reduzir Alucinações**: O modelo é menos propenso a inventar informações quando precisa justificar suas conclusões.

Utilize tags XML `<thinking>` para delimitar a área de raciocínio:

```xml
<thinking>
1. Analisando a página de carreiras, encontrei menções a "autonomia", "desenvolvimento profissional" e "trabalho com propósito".
2. No LinkedIn, a descrição menciona "inovação" e "impacto".
3. Cruzando essas informações, o EVP parece estar centrado em crescimento e autonomia.
4. Para competências, vejo referências a "pensamento crítico", "colaboração" e "aprendizado contínuo".
</thinking>
```

### 2.2 Few-Shot Prompting: Ensinando pelo Exemplo

O Few-Shot Prompting [2] consiste em fornecer 2 a 3 exemplos de alta qualidade dentro do próprio prompt. Cada exemplo contém um trecho de texto de entrada e a saída JSON desejada.

Os benefícios são múltiplos:

1.  **Estabelece Formato**: O modelo vê exatamente como a saída deve ser estruturada.
2.  **Define Nível de Abstração**: Os exemplos mostram o nível de detalhe esperado. Uma saída muito genérica ou muito específica fica evidente.
3.  **Comunica Tom e Estilo**: O modelo aprende o tom esperado para a resposta.

Exemplo de um bom exemplo (Few-Shot):

```xml
<exemplo>
<texto_entrada>
Página de Carreiras da InovaTech:
"Na InovaTech, você não é apenas um funcionário, é um pioneiro. Oferecemos autonomia para explorar novas ideias, um orçamento generoso para desenvolvimento profissional e a chance de trabalhar com tecnologias de ponta. Nossos times são ágeis e colaborativos, e celebramos a curiosidade e a vontade de resolver problemas complexos."
</texto_entrada>

<json_saida>
{
  "evp": "A InovaTech oferece aos seus colaboradores a oportunidade de serem pioneiros em suas áreas, provendo autonomia, recursos para desenvolvimento e acesso a tecnologias de ponta. A cultura valoriza a agilidade, a colaboração e a resolução de problemas complexos, criando um ambiente ideal para quem busca impacto e crescimento.",
  "competencies": [
    "Autonomia e Proatividade",
    "Curiosidade e Aprendizado Contínuo",
    "Colaboração e Trabalho em Equipe",
    "Resolução de Problemas Complexos",
    "Agilidade e Adaptação"
  ]
}
</json_saida>
</exemplo>
```

## 3. O Prompt Mestre: Combinando Todas as Técnicas

A seguir, um template de prompt que integra persona, contexto estruturado, instruções detalhadas, CoT e Few-Shot:

```xml
<prompt>
<persona>
Você é um especialista em Estratégia de RH e Cultura Organizacional com 15 anos de experiência. Sua tarefa é analisar o conteúdo fornecido sobre uma empresa e extrair sua Proposta de Valor ao Empregado (EVP) e suas competências-chave com precisão e nuance.
</persona>

<contexto>
<website_content>
{CONTEÚDO_DO_SITE_EM_MARKDOWN}
</website_content>

<linkedin_data>
{DADOS_DO_LINKEDIN_EM_JSON}
</linkedin_data>
</contexto>

<definições>
<evp>
A Proposta de Valor ao Empregado (EVP) é a resposta à pergunta: "Por que alguém deveria trabalhar aqui?" Inclua:
- Benefícios tangíveis: salário, benefícios, flexibilidade, equipamento, localização.
- Benefícios intangíveis: propósito, crescimento, cultura, autonomia, impacto.
- Ambiente de trabalho: dinâmica de equipe, liderança, inclusão.

O EVP deve ser um parágrafo coeso e persuasivo, como se fosse escrito para atrair um candidato ideal.
</evp>

<competencies>
As competências-chave são as habilidades, comportamentos e mentalidades que a empresa valoriza e busca em seus colaboradores. Incluem:
- Habilidades técnicas específicas do setor.
- Competências comportamentais: colaboração, comunicação, liderança.
- Atitudes e mentalidades: curiosidade, resiliência, orientação para resultados.

Procure por essas informações em descrições de vagas, valores da empresa, descrições de cultura e na forma como a empresa descreve sua equipe ideal.
</competencies>
</definições>

<instrucoes>
1. Leia cuidadosamente o <contexto> fornecido.
2. Dentro da tag <thinking>, detalhe seu processo de análise:
   - Identifique pistas sobre o EVP em cada fonte.
   - Cruze informações de diferentes fontes para validar suas inferências.
   - Liste as competências que você identifica e justifique cada uma.
3. Preencha o schema JSON com base em seu raciocínio.
4. A resposta final deve estar dentro da tag <answer> e conter APENAS o JSON válido.
</instrucoes>

<exemplos>
<exemplo>
<texto_entrada>
**Página de Carreiras da InovaTech**:
"Na InovaTech, você não é apenas um funcionário, é um pioneiro. Oferecemos autonomia para explorar novas ideias, um orçamento generoso para desenvolvimento profissional e a chance de trabalhar com tecnologias de ponta. Nossos times são ágeis e colaborativos, e celebramos a curiosidade e a vontade de resolver problemas complexos."

**LinkedIn da InovaTech**:
"Liderando a transformação digital com foco em inovação e impacto. Nossos valores: Autonomia, Aprendizado Contínuo, Colaboração."
</texto_entrada>

<json_saida>
{
  "evp": "A InovaTech oferece aos seus colaboradores a oportunidade de serem pioneiros em suas áreas, provendo autonomia genuína, recursos generosos para desenvolvimento profissional e acesso a tecnologias de ponta. A cultura valoriza a agilidade, a colaboração e a resolução de problemas complexos, criando um ambiente ideal para profissionais que buscam impacto, crescimento contínuo e liberdade para explorar novas ideias.",
  "competencies": [
    "Autonomia e Proatividade",
    "Curiosidade e Aprendizado Contínuo",
    "Colaboração e Trabalho em Equipe",
    "Resolução de Problemas Complexos",
    "Agilidade e Adaptação",
    "Pensamento Inovador"
  ]
}
</json_saida>
</exemplo>

<exemplo>
<texto_entrada>
**Página de Carreiras da HumanizeCare**:
"Nossa equipe de enfermagem é o coração da HumanizeCare. Investimos em treinamento contínuo sobre empatia e comunicação, e garantimos um ambiente de trabalho seguro com apoio psicológico. Acreditamos que cuidar de quem cuida é fundamental. Buscamos profissionais que se conectem genuinamente com a dor do outro."

**LinkedIn da HumanizeCare**:
"Transformando o cuidado em saúde. Missão: Humanizar a experiência de pacientes e profissionais. Valores: Empatia, Segurança, Desenvolvimento."
</texto_entrada>

<json_saida>
{
  "evp": "A HumanizeCare proporciona um ambiente de trabalho seguro e focado no bem-estar integral de seus colaboradores. A empresa investe pesadamente em desenvolvimento de habilidades interpessoais como empatia e comunicação, oferece forte apoio psicológico e cria uma cultura onde o cuidado é bidirecional. Atrai profissionais que buscam um trabalho com propósito profundo, conectando-se genuinamente com a missão de humanizar a saúde.",
  "competencies": [
    "Empatia e Inteligência Emocional",
    "Comunicação Interpessoal",
    "Resiliência e Gestão do Estresse",
    "Trabalho com Propósito",
    "Colaboração Interdisciplinar",
    "Cuidado Centrado no Paciente"
  ]
}
</json_saida>
</exemplo>
</exemplos>

<resposta_final>
<thinking>
(Seu raciocínio detalhado aqui)
</thinking>

<answer>
(JSON final aqui)
</answer>
</resposta_final>

</prompt>
```

## 4. Implementação em Python

Para integrar este prompt em sua aplicação, utilize o seguinte código:

```python
import anthropic
import json
from pydantic import BaseModel, Field
from typing import List

class CompanyInsights(BaseModel):
    evp: str = Field(description="Proposta de Valor ao Empregado")
    competencies: List[str] = Field(description="Competências-chave da empresa")

def extract_company_insights(client: anthropic.Anthropic, context: str) -> CompanyInsights:
    master_prompt = f"""
    {PROMPT_MESTRE_ACIMA}
    
    Contexto a analisar:
    {context}
    """
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4096,
        messages=[{"role": "user", "content": master_prompt}]
    )
    
    # Extrai o JSON da resposta
    full_response = response.content[0].text
    start = full_response.find("<answer>") + len("<answer>")
    end = full_response.find("</answer>")
    json_string = full_response[start:end].strip()
    
    parsed_json = json.loads(json_string)
    return CompanyInsights(**parsed_json)
```

## 5. Boas Práticas Adicionais

### 5.1 Validação e Iteração

Após obter a resposta do Claude, valide os resultados:

1.  **Verificação de Completude**: Todos os campos foram preenchidos?
2.  **Verificação de Relevância**: O EVP é específico para a empresa ou genérico demais?
3.  **Verificação de Coerência**: As competências listadas são coerentes com o EVP descrito?

Se alguma validação falhar, refine o prompt ou o contexto fornecido.

### 5.2 Tratamento de Contextos Incompletos

Nem sempre o website da empresa terá informações explícitas sobre EVP e competências. Nesse caso:

1.  **Instrua o Modelo a Inferir**: Deixe claro que o modelo pode inferir com base em pistas indiretas.
2.  **Defina Limites de Confiança**: Considere adicionar um campo `confidence_level` ao schema para indicar o quão confiante o modelo está em suas inferências.
3.  **Use Múltiplas Fontes**: Combine dados do website, LinkedIn, Glassdoor e outras plataformas para enriquecer o contexto.

### 5.3 Otimização de Custo e Latência

Se você está processando muitas empresas:

1.  **Use Prompt Caching**: A Anthropic suporta cache de prompts longos, reduzindo custos em chamadas subsequentes.
2.  **Batch Processing**: Processe múltiplas empresas em lotes para aproveitar economias de escala.
3.  **Modelo Mais Rápido**: Para tarefas simples, considere usar `claude-3-5-haiku` em vez de `claude-3-5-sonnet`.

## Conclusão

Ao utilizar este guia, você está equipado com um framework robusto para extrair informações estratégicas de empresas de forma automatizada e precisa. A combinação de **persona, contexto estruturado, instruções detalhadas, Chain-of-Thought e Few-Shot Prompting** minimiza a ambiguidade e maximiza a qualidade das extrações, transformando texto bruto em inteligência de negócios acionável.

---

### Referências

[1] Anthropic. *Let Claude think (chain of thought prompting) to increase performance*. Recuperado de https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/chain-of-thought

[2] Anthropic. *Use examples (multishot prompting) to guide Claude's behavior*. Recuperado de https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/multishot-prompting
