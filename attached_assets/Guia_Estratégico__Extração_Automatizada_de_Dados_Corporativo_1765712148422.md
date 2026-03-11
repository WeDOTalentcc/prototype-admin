# Guia Estratégico: Extração Automatizada de Dados Corporativos com Apify e Claude AI

## 1. Introdução

Este documento apresenta uma arquitetura detalhada para a construção de um pipeline de extração de dados corporativos, utilizando a plataforma **Apify** para coleta de dados em larga escala e o modelo de linguagem **Claude AI** para interpretação e estruturação inteligente das informações. O objetivo é automatizar a captura de dados estratégicos, como **missão, visão, valores, Proposta de Valor ao Empregado (EVP)** e **competências-chave**, a partir de fontes públicas na web, como o website da empresa e seu perfil no LinkedIn.

A combinação dessas tecnologias permite transformar dados não estruturados e semi-estruturados em um formato JSON limpo e validado, pronto para ser consumido por agentes de IA para tarefas subsequentes, como a elaboração de pitches de vendas, definição de perfis de candidatos e criação de conteúdo de recrutamento.

## 2. Estratégia de Fontes de Dados: A Abordagem Multi-Fonte

Para obter um perfil corporativo completo e preciso, é fundamental adotar uma estratégia de coleta de dados multi-fonte. Nenhuma fonte única contém todas as informações necessárias, e a combinação de diferentes perspectivas enriquece a análise. As fontes de dados primárias recomendadas são:

*   **Website da Empresa**: A fonte mais rica para conteúdo qualitativo e autêntico. Páginas como "Sobre Nós", "Missão", "Valores", "Carreiras" e o blog corporativo são minas de ouro para entender a cultura da empresa, seu propósito e sua Proposta de Valor ao Empregado (EVP).

*   **Perfil da Empresa no LinkedIn**: Oferece dados mais estruturados, como a descrição oficial da empresa, número de funcionários, setor, localidades e crescimento do quadro de colaboradores. A análise da linguagem utilizada nas postagens e na descrição pode revelar aspectos da cultura e das competências valorizadas.

*   **Outras Fontes (Opcional)**: Plataformas como Glassdoor, Crunchbase e até mesmo o Google Maps podem fornecer dados complementares, como avaliações de funcionários (insights para o EVP), informações sobre rodadas de investimento e presença física.

## 3. Coleta de Dados com Apify

Apify é a ferramenta de escolha para a fase de coleta de dados devido à sua robustez, escalabilidade e ao seu marketplace de "Actors" (scrapers pré-construídos) que aceleram o desenvolvimento. Para este pipeline, recomendamos dois Actors principais:

| Actor (Scraper) | Propósito | Dados Extraídos (Exemplos) |
| :--- | :--- | :--- |
| **Website Content Crawler** | Extrair o conteúdo textual completo de um website. | Texto de páginas específicas (Sobre, Carreiras), artigos de blog, descrições de produtos. |
| **LinkedIn Company Scraper** | Coletar dados estruturados e semi-estruturados de perfis de empresas no LinkedIn. | Descrição da empresa, número de funcionários, setor, website, localidades, posts recentes. |

O **Website Content Crawler** [1] é particularmente poderoso por ser projetado para alimentar modelos de IA, extraindo conteúdo em formato Markdown, que preserva a semântica e a estrutura do texto, facilitando a interpretação pelo Claude AI. Já o **LinkedIn Company Scraper** [2] fornece uma base de dados estruturada que serve como um excelente ponto de partida e complemento ao conteúdo do site.

## 4. Extração Inteligente com Claude AI

Após a coleta dos dados brutos com o Apify, o Claude AI entra em ação para ler, interpretar e extrair as informações estratégicas de forma estruturada. A funcionalidade de **Structured Outputs** do Claude [3] é essencial para garantir que a saída seja um JSON válido e em conformidade com um schema pré-definido.

### Definindo o Schema de Saída com Pydantic

Para garantir a consistência e a validação dos dados, utilizamos a biblioteca Pydantic em Python para definir o schema do nosso objeto de saída.

```python
from pydantic import BaseModel, Field
from typing import List

class CompanyProfile(BaseModel):
    mission: str = Field(description="A declaração de missão da empresa. O propósito fundamental da sua existência.")
    vision: str = Field(description="A declaração de visão da empresa. O que ela aspira ser no futuro.")
    values: List[str] = Field(description="Uma lista dos valores fundamentais que guiam a cultura e as decisões da empresa.")
    evp: str = Field(description="A Proposta de Valor ao Empregado (EVP). O que a empresa oferece aos seus funcionários em troca de seu trabalho.")
    competencies: List[str] = Field(description="Uma lista das competências e habilidades-chave que a empresa valoriza em seus colaboradores.")
```

### Exemplo de Prompt e Chamada da API

Com o schema definido, podemos construir um prompt que instrui o Claude a preencher essa estrutura com base nos dados coletados. O contexto (`CONTEXTO_DA_EMPRESA`) seria a concatenação do conteúdo extraído pelo `Website Content Crawler` e dos dados do `LinkedIn Company Scraper`.

```python
import anthropic

client = anthropic.Anthropic()

CONTEXTO_DA_EMPRESA = """
# Conteúdo do Website (Markdown)
...

# Dados do LinkedIn (JSON)
...
"""

response = client.beta.messages.parse(
    model="claude-3-5-sonnet-20240620",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": f"""Analise o seguinte contexto sobre uma empresa e extraia as informações solicitadas, preenchendo o schema JSON fornecido.

            Contexto:
            {CONTEXTO_DA_EMPRESA}

            Se uma informação não estiver explicitamente declarada, infira-a com base no texto como um todo. Por exemplo, o EVP pode ser inferido a partir da página de carreiras e dos benefícios mencionados. As competências podem ser inferidas a partir das descrições de vagas ou da cultura da empresa.
            """
        }
    ],
    output_format=CompanyProfile,
)

print(response.parsed_output.model_dump_json(indent=2))
```

## 5. Arquitetura do Pipeline: Visão Geral

O fluxo de trabalho completo pode ser visualizado na seguinte arquitetura:

| Fase | Ferramenta | Ação | Input | Output |
| :--- | :--- | :--- | :--- | :--- |
| **1. Coleta** | Apify | **LinkedIn Company Scraper**: Extrai dados do perfil no LinkedIn. | URL do LinkedIn | JSON com dados da empresa |
| | Apify | **Website Content Crawler**: Extrai conteúdo do site. | URL do Website | Texto em Markdown |
| **2. Agregação** | (Seu Código) | Consolida os dados coletados em um único contexto. | JSON e Markdown | String de Contexto |
| **3. Extração** | Claude AI | **Structured Outputs**: Analisa o contexto e extrai os dados. | String de Contexto | JSON validado (CompanyProfile) |
| **4. Consumo** | Agente de IA | Utiliza os dados estruturados para tarefas específicas. | JSON validado | Pitch de vendas, perfil de candidato, etc. |

## 6. Melhores Práticas

*   **Prompts Detalhados**: Ao interagir com o Claude, seja explícito sobre o que você precisa. Forneça definições claras de cada campo (como no `description` do Pydantic) e dê exemplos se necessário.
*   **Inferência Guiada**: Instrua o modelo a inferir informações quando elas não estiverem explícitas, mas sempre com base no texto fornecido. Isso é crucial para campos como EVP e competências.
*   **Respeito aos Termos de Serviço**: Ao fazer web scraping, sempre verifique o arquivo `robots.txt` dos sites e evite sobrecarregar os servidores com um número excessivo de requisições.
*   **Manuseio de Cookies**: Para scrapers que exigem login (como o do LinkedIn), utilize extensões de navegador como a `Cookie-Editor` para exportar os cookies de uma sessão autenticada e fornecê-los ao Actor do Apify.

## 7. Conclusão

A implementação deste pipeline automatizado de extração de dados oferece uma vantagem competitiva significativa, permitindo que sua equipe de inteligência de mercado, recrutamento ou vendas acesse informações estratégicas de forma rápida, consistente e escalável. Ao delegar a coleta e a estruturação de dados para Apify e Claude AI, seus agentes de IA e analistas podem se concentrar em tarefas de maior valor, como a geração de insights e a tomada de decisões estratégicas.

---

### Referências

[1] Apify. *Website Content Crawler*. Recuperado de https://apify.com/apify/website-content-crawler

[2] Apify. *Linkedin company scraper*. Recuperado de https://apify.com/curious_coder/linkedin-company-scraper

[3] Anthropic. *Structured outputs - Claude Docs*. Recuperado de https://platform.claude.com/docs/en/build-with-claude/structured-outputs
