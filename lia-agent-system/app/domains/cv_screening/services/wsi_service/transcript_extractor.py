"""
Transcript → Q/A pair extraction (audit task #496, PR1).

Extraído de `wsi_voice_orchestrator.py` (linhas 574-715 da rev. anterior)
para isolar o domínio de "interpretação de transcript de chamada de voz"
do orquestrador monolítico. Funções aqui são **puras**: recebem strings/
listas de dicts e retornam list[{question, response}], sem tocar em
banco, LLM ou estado de instância.

Estratégia de extração (ordem de tentativa):
1. `extract_from_structured_transcript`: usa speaker labels do payload
   (agent vs user) — preferida quando disponível.
2. `extract_from_raw_transcript`: pattern matching textual sobre
   transcript bruto — fallback quando não há estrutura.

A façade `extract_qa_pairs` aplica essa cascata.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from .models import WSIQuestion

logger = logging.getLogger(__name__)


def extract_qa_pairs(
    transcript: str,
    transcript_object: list[dict[str, Any]] | None,
    questions: list[WSIQuestion],
) -> list[dict[str, Any]]:
    """Façade — extrai pares Q/A com fallback estruturado → bruto.

    Returns:
        Lista de dicts com chaves 'question' (WSIQuestion) e 'response' (str).
    """
    qa_pairs: list[dict[str, Any]] = []

    if transcript_object and len(transcript_object) > 0:
        qa_pairs = extract_from_structured_transcript(transcript_object, questions)

    if not qa_pairs:
        qa_pairs = extract_from_raw_transcript(transcript, questions)

    return qa_pairs


def extract_from_structured_transcript(
    transcript_object: list[dict[str, Any]],
    questions: list[WSIQuestion],
) -> list[dict[str, Any]]:
    """Extrai Q/A pairs de transcript estruturado com speaker labels.

    Faz fuzzy matching por overlap de palavras entre cada pergunta e as
    falas do agente; emparelha cada match com a fala do usuário que veio
    logo em seguida.
    """
    qa_pairs: list[dict[str, Any]] = []

    agent_utterances: list[dict[str, Any]] = []
    user_utterances: list[dict[str, Any]] = []

    for item in transcript_object:
        speaker = item.get('speaker', item.get('role', '')).lower()
        text_content = item.get('text', item.get('content', ''))

        if 'agent' in speaker or 'lia' in speaker or 'assistant' in speaker:
            agent_utterances.append({
                'text': text_content,
                'index': len(agent_utterances),
            })
        elif 'user' in speaker or 'human' in speaker or 'candidato' in speaker:
            user_utterances.append({
                'text': text_content,
                'agent_index': len(agent_utterances) - 1 if agent_utterances else -1,
            })

    for question in questions:
        best_match_idx = -1
        best_score = 0.3

        q_words = set(question.question_text.lower().split())

        for idx, utterance in enumerate(agent_utterances):
            u_words = set(utterance['text'].lower().split())

            if len(q_words) > 0:
                overlap = len(q_words & u_words) / len(q_words)
                if overlap > best_score:
                    best_score = overlap
                    best_match_idx = idx

        if best_match_idx >= 0:
            response_parts: list[str] = []
            for u in user_utterances:
                if u.get('agent_index') == best_match_idx:
                    response_parts.append(u.get('text', ''))

            if response_parts:
                qa_pairs.append({
                    'question': question,
                    'response': ' '.join(response_parts),
                })

    return qa_pairs


def extract_from_raw_transcript(
    transcript: str,
    questions: list[WSIQuestion],
) -> list[dict[str, Any]]:
    """Extrai Q/A pairs de transcript bruto via pattern matching.

    Fallback usado quando não há transcript estruturado. Procura cada
    pergunta no texto (primeiro 6 palavras, com retry para 3) e captura
    o trecho subsequente como resposta. Se nada bater, joga o transcript
    inteiro na primeira pergunta como último recurso.
    """
    qa_pairs: list[dict[str, Any]] = []

    if not transcript or not transcript.strip():
        return qa_pairs

    transcript_lower = transcript.lower()

    for question in questions:
        q_text_lower = question.question_text.lower()
        q_words = q_text_lower.split()[:6]
        search_pattern = ' '.join(q_words)

        q_position = transcript_lower.find(search_pattern)

        if q_position == -1 and len(q_words) > 3:
            search_pattern = ' '.join(q_words[:3])
            q_position = transcript_lower.find(search_pattern)

        if q_position >= 0:
            after_question = transcript[q_position:]

            response_match = re.search(
                r'(?:candidato|user|resposta)[:\s]+(.+?)(?:(?:agente|lia|pergunta)[:\s]|$)',
                after_question,
                re.IGNORECASE | re.DOTALL,
            )

            if response_match:
                response_text = response_match.group(1).strip()
            else:
                paragraphs = after_question.split('\n\n')
                if len(paragraphs) > 1:
                    response_text = paragraphs[1].strip()
                else:
                    sentences = after_question.split('. ')
                    if len(sentences) > 1:
                        response_text = '. '.join(sentences[1:3]).strip()
                    else:
                        response_text = after_question[:500].strip()

            if response_text and len(response_text) > 10:
                qa_pairs.append({
                    'question': question,
                    'response': response_text[:2000],
                })

    if not qa_pairs and questions:
        logger.warning(
            "⚠️  Could not match questions to transcript. "
            "Using full transcript for first question."
        )
        qa_pairs.append({
            'question': questions[0],
            'response': transcript[:3000],
        })

    return qa_pairs
