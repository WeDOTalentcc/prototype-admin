# Análise Comparativa: Video to Text

## Ferramentas de Transcrição na Plataforma LIA

Data da análise: 16 de Dezembro de 2025

---

## Ferramentas Atuais Integradas

### 1. Deepgram (Speech-to-Text)

| Aspecto | Detalhes |
|---------|----------|
| **Custo** | $0.0043/minuto (~$0.26/hora) |
| **Modelo** | Pay-as-you-go |
| **Formatos Suportados** | MP3, WAV, OGG, FLAC, WebM |
| **Latência** | Baixa (streaming disponível) |
| **Idiomas** | 30+ idiomas incluindo português |
| **Uso na LIA** | Triagem por voz, entrevistas, gravações de áudio |

**Arquivo de implementação:** `lia-agent-system/app/services/deepgram_service.py`

### 2. Google Gemini (Audio/Video to Text)

| Aspecto | Detalhes |
|---------|----------|
| **Custo** | Incluso nos Replit Credits (custo muito baixo) |
| **Modelo** | Gemini Flash 2.5 via Replit AI Integrations |
| **Formatos de Áudio** | MP3, M4A, WAV, OGG, WebM, FLAC |
| **Formatos de Vídeo** | MP4, MPEG, WebM, MOV (QuickTime) |
| **Idiomas** | 100+ idiomas |
| **Uso na LIA** | Transcrição multimodal, análise de vídeos de candidatos |

**Arquivo de implementação:** `lia-agent-system/app/services/gemini_voice_service.py`

---

## Análise do Apify "Video to Text"

### Informações do Actor

- **Nome:** Video to Text
- **Desenvolvedor:** nextapi
- **URL:** https://apify.com/nextapi/video-to-text

### Estrutura de Preços Apify

| Métrica | Free | Starter | Scale | Business |
|---------|------|---------|-------|----------|
| Actor usage | $0.10/1000 | $0.10/1000 | $0.10/1000 | $0.10/1000 |
| Segundos | $3.47/1000 | $3.31/1000 | $3.16/1000 | $3.00/1000 |

**Custo por hora de vídeo (plano Free):**
- 1 hora = 3600 segundos
- Custo = 3.6 × $3.47 = **$12.49/hora**

---

## Comparação de Custos

| Serviço | Custo/Segundo | Custo/Minuto | Custo/Hora |
|---------|---------------|--------------|------------|
| **Deepgram** | $0.00007 | $0.0043 | **$0.26** |
| **Gemini (Replit)** | ~incluso | ~incluso | **~$0.05*** |
| **Apify Video to Text** | $0.00347 | $0.208 | **$12.49** |

*Gemini via Replit Credits - custo estimado baseado em uso típico

### Diferença de Custo

| Comparação | Fator |
|------------|-------|
| Deepgram vs Apify | **48x mais barato** |
| Gemini vs Apify | **~250x mais barato** |

---

## Funcionalidades Comparadas

| Funcionalidade | Deepgram | Gemini | Apify |
|----------------|----------|--------|-------|
| Transcrição de áudio | ✅ | ✅ | ✅ |
| Transcrição de vídeo nativo | ❌ | ✅ | ✅ |
| Streaming em tempo real | ✅ | ❌ | ❌ |
| Multilíngue | ✅ | ✅ | ✅ |
| Detecção automática de idioma | ✅ | ✅ | ✅ |
| Pontuação automática | ✅ | ✅ | ✅ |
| Timestamps | ✅ | ✅ | ✅ |
| Diarização (múltiplos falantes) | ✅ | ✅ | ? |
| API REST | ✅ | ✅ | ✅ |
| Integração nativa LIA | ✅ | ✅ | ❌ |

---

## Recomendação

### Não migrar para Apify Video to Text

**Motivos:**

1. **Custo proibitivo**: 48x a 250x mais caro que nossas soluções atuais
2. **Funcionalidade redundante**: Deepgram + Gemini já cobrem todos os casos de uso
3. **Integração adicional**: Apify requer integração extra sem benefícios claros
4. **Latência**: Apify adiciona camada de processamento desnecessária

### Uso Recomendado do Apify

O Apify é excelente para **web scraping**, onde já o utilizamos:

- ✅ Scraping de perfis LinkedIn
- ✅ Análise de websites corporativos
- ✅ Extração de dados públicos

Mas **não é competitivo** para transcrição de áudio/vídeo.

---

## Arquitetura Atual de Transcrição

```
┌─────────────────────────────────────────────────────────────┐
│                    Plataforma LIA                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────┐    │
│  │  Audio Input    │    │     Video Input             │    │
│  │  (MP3, WAV...)  │    │     (MP4, MOV, WebM)        │    │
│  └────────┬────────┘    └──────────────┬──────────────┘    │
│           │                            │                    │
│           ▼                            ▼                    │
│  ┌─────────────────┐    ┌─────────────────────────────┐    │
│  │    Deepgram     │    │      Google Gemini          │    │
│  │  $0.0043/min    │    │    (Replit Credits)         │    │
│  │  Streaming STT  │    │    Multimodal Analysis      │    │
│  └────────┬────────┘    └──────────────┬──────────────┘    │
│           │                            │                    │
│           └────────────┬───────────────┘                    │
│                        ▼                                    │
│           ┌─────────────────────────┐                       │
│           │   Transcrição Unificada │                       │
│           │   + Análise de Contexto │                       │
│           └─────────────────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Conclusão

Manter a arquitetura atual com **Deepgram + Gemini** é a decisão mais econômica e eficiente. O Apify Video to Text não oferece vantagens que justifiquem seu custo significativamente maior.

### Próximos Passos (se necessário)

1. **Para reduzir custos ainda mais**: Migrar 100% para Gemini (já incluso nos Replit Credits)
2. **Para streaming real-time**: Manter Deepgram para casos de baixa latência
3. **Para volume alto**: Negociar enterprise pricing com Deepgram

---

*Documento gerado para referência interna da equipe de desenvolvimento.*
