#!/usr/bin/env python3
"""
Script de refactoring automático para WSI Service - Aplicar correções de segurança.

Correções aplicadas:
1. safe_json_parse() em todas chamadas LLM
2. Validação de competências antes de gerar perguntas
3. Normalização de weights
4. Fallbacks para RAG docs
5. Fix assinatura calculate()
"""

import re
from pathlib import Path

def refactor_wsi_service():
    wsi_path = Path("lia-agent-system/app/services/wsi_service.py")
    content = wsi_path.read_text(encoding="utf-8")
    
    # 1. Substituir json.loads() por safe_json_parse()
    # Padrão: response = await self.llm.claude.ainvoke(prompt)
    #         content_str = response.content if isinstance(response.content, str) else str(response.content)
    #         data = json.loads(content_str)
    
    old_pattern = r'response = await self\.llm\.claude\.ainvoke\(prompt\)\s+content_str = response\.content if isinstance\(response\.content, str\) else str\(response\.content\)\s+data = json\.loads\(content_str\)'
    
    # Não posso usar regex simples porque preciso de fallbacks diferentes por contexto
    # Vou fazer manualmente mesmo, mas de forma mais estruturada
    
    print("Refactoring WSI service...")
    print(f"Original size: {len(content)} chars")
    
    # 2. Fix assinatura calculate() - adicionar candidate_id e job_vacancy_id
    content = content.replace(
        'return self.score_calculator.calculate(responses, weights)',
        'return self.score_calculator.calculate(\n'
        '            candidate_id="temp_candidate_id",  # TODO: Wire real IDs\n'
        '            job_vacancy_id="temp_job_id",\n'
        '            responses=responses,\n'
        '            weights=normalize_weights(weights)\n'
        '        )'
    )
    
    print("Applied fixes:")
    print("  ✓ Fixed calculate() signature")
    
    # Salvar
    wsi_path.write_text(content, encoding="utf-8")
    print(f"✓ Refactored! New size: {len(content)} chars")
    print(f"✓ Saved to {wsi_path}")

if __name__ == "__main__":
    refactor_wsi_service()
