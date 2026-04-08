import os

src = '/home/runner/workspace/lia-agent-system/app/domains/cv_screening/services/wsi_service.py'
pkg = '/home/runner/workspace/lia-agent-system/app/domains/cv_screening/services/wsi_service'

content = open(src).read()
lines = content.split('\n')

# Known line boundaries from grep output (1-based):
# Line 37: OceanTraitScore (dataclass) - models start
# Line 135: Competency
# Line 145: CompetencySuggestion
# Line 154: WSIQuestion
# Line 170: ResponseAnalysis
# Line 189: WSIResult
# Line 205: StructuredReport
# Line 219: CandidateFeedback
# Line 235: WSIService
# Line 706: WSIQuestionGenerator
# Line 1547: WSIResponseAnalyzer
# Line 1615: WSIScoreCalculator
# Line 1732: WSIReportGenerator
# Singleton + factory near end

# Find exact singleton/factory lines
singleton_line = None
factory_line = None
tool_fn_line = None
for i, line in enumerate(lines):
    if 'wsi_service = WSIService()' in line and singleton_line is None:
        singleton_line = i + 1
    if 'def get_wsi_service' in line and factory_line is None:
        factory_line = i + 1
    if 'def generate_wsi_questions_tool' in line and tool_fn_line is None:
        tool_fn_line = i + 1

print(f"Singleton at line {singleton_line}")
print(f"Tool fn at line {tool_fn_line}")
print(f"Factory at line {factory_line}")

# Extract sections (0-indexed slices from 1-based line numbers)
header = lines[0:36]  # lines 1-36 (imports, module docstring, logger)
models_body = lines[36:234]  # lines 37-234 (OceanTraitScore through CandidateFeedback)
wsi_service_body = lines[234:705]  # lines 235-705 (WSIService class)
question_gen_body = lines[705:1546]  # lines 706-1546 (WSIQuestionGenerator)
response_analyzer_body = lines[1546:1614]  # lines 1547-1614 (WSIResponseAnalyzer)
score_calc_body = lines[1614:1731]  # lines 1615-1731 (WSIScoreCalculator)
report_gen_body = lines[1731:singleton_line-1]  # lines 1732 to just before singleton
tail = lines[singleton_line-1:]  # singleton, tool fn, factory

print(f"Header lines: {len(header)}")
print(f"Models body lines: {len(models_body)}")
print(f"WSIService body lines: {len(wsi_service_body)}")
print(f"QuestionGenerator body lines: {len(question_gen_body)}")
print(f"ResponseAnalyzer body lines: {len(response_analyzer_body)}")
print(f"ScoreCalc body lines: {len(score_calc_body)}")
print(f"ReportGen body lines: {len(report_gen_body)}")
print(f"Tail lines: {len(tail)}")

os.makedirs(pkg, exist_ok=True)

# ---- models.py ----
models_imports = '''\"""
WSI Data Models - Dataclasses and Pydantic models.
\"""
import json
import logging
from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# F2 Big Five Pipeline — modelos e constantes (spec WSI F2.5/F3/F5)
# ---------------------------------------------------------------------------

'''

models_content = models_imports + '\n'.join(models_body) + '\n'
with open(f'{pkg}/models.py', 'w') as f:
    f.write(models_content)
print(f"models.py written: {len(models_content.splitlines())} lines")

# ---- question_generator.py ----
# Header needs: json, logging, re, uuid, Callable, Any, Literal, dataclass imports
# Plus OceanTraitScore, SENIORITY_BIGFIVE_TOP_N, Competency, WSIQuestion from .models
# Plus SENIORITY_DISTRIBUTIONS, llm_service
qgen_imports = '''\"""
WSI Question Generator - Generates scientific questions based on WSI frameworks.
\"""
import json
import logging
import re
import uuid
from collections.abc import Callable
from typing import Any, Literal

from app.domains.cv_screening.constants.wsi_constants import SENIORITY_DISTRIBUTIONS
from app.services.llm import llm_service

from .models import (
    Competency,
    OceanTraitScore,
    SENIORITY_BIGFIVE_TOP_N,
    WSIQuestion,
)

logger = logging.getLogger(__name__)

'''
qgen_content = qgen_imports + '\n'.join(question_gen_body) + '\n'
with open(f'{pkg}/question_generator.py', 'w') as f:
    f.write(qgen_content)
print(f"question_generator.py written: {len(qgen_content.splitlines())} lines")

# ---- response_analyzer.py ----
ranalyzer_imports = '''\"""
WSI Response Analyzer - Deterministic response scoring.
\"""
import logging
from typing import Any

from app.domains.cv_screening.services.wsi_deterministic_scorer import (
    DeterministicWSIResult,
    calculate_wsi_deterministic,
)

from .models import ResponseAnalysis, WSIQuestion

logger = logging.getLogger(__name__)

'''
ranalyzer_content = ranalyzer_imports + '\n'.join(response_analyzer_body) + '\n'
with open(f'{pkg}/response_analyzer.py', 'w') as f:
    f.write(ranalyzer_content)
print(f"response_analyzer.py written: {len(ranalyzer_content.splitlines())} lines")

# ---- score_calculator.py ----
scalc_imports = '''\"""
WSI Score Calculator - Weighted average scoring and percentile ranking.
\"""
import logging

from .models import ResponseAnalysis, WSIResult

logger = logging.getLogger(__name__)

'''
scalc_content = scalc_imports + '\n'.join(score_calc_body) + '\n'
with open(f'{pkg}/score_calculator.py', 'w') as f:
    f.write(scalc_content)
print(f"score_calculator.py written: {len(scalc_content.splitlines())} lines")

# ---- report_generator.py ----
rgen_imports = '''\"""
WSI Report Generator - Structured reports and candidate feedback.
\"""
import logging
from typing import Any, Literal

from .models import (
    CandidateFeedback,
    ResponseAnalysis,
    StructuredReport,
    WSIResult,
    safe_json_parse,
)

logger = logging.getLogger(__name__)

'''
rgen_content = rgen_imports + '\n'.join(report_gen_body) + '\n'
with open(f'{pkg}/report_generator.py', 'w') as f:
    f.write(rgen_content)
print(f"report_generator.py written: {len(rgen_content.splitlines())} lines")

# ---- service.py ----
service_imports = '''\"""
WSI Service - Main orchestrator combining all WSI components.
\"""
import json
import logging
from typing import Any, Literal

from .models import (
    CandidateFeedback,
    Competency,
    CompetencySuggestion,
    ResponseAnalysis,
    StructuredReport,
    WSIQuestion,
    WSIResult,
    normalize_weights,
)
from .question_generator import WSIQuestionGenerator
from .response_analyzer import WSIResponseAnalyzer
from .score_calculator import WSIScoreCalculator
from .report_generator import WSIReportGenerator

from app.services.llm import llm_service

logger = logging.getLogger(__name__)

'''
service_content = service_imports + '\n'.join(wsi_service_body) + '\n\n'
# Append tail (singleton, tool function, factory)
service_content += '\n'.join(tail) + '\n'
with open(f'{pkg}/service.py', 'w') as f:
    f.write(service_content)
print(f"service.py written: {len(service_content.splitlines())} lines")

# ---- __init__.py ----
init_content = '''\"""
WSI (WeDoTalent Skill Index) Service Package.

Re-exports the public API to maintain backward compatibility with all
existing imports of the form:
    from app.domains.cv_screening.services.wsi_service import WSIService
    from app.domains.cv_screening.services.wsi_service import wsi_service
    from app.domains.cv_screening.services.wsi_service import get_wsi_service
\"""
from .models import (
    CandidateFeedback,
    Competency,
    CompetencySuggestion,
    OceanTraitScore,
    ResponseAnalysis,
    SENIORITY_BIGFIVE_TOP_N,
    StructuredReport,
    WSIQuestion,
    WSIResult,
    normalize_weights,
    safe_json_parse,
)
from .question_generator import WSIQuestionGenerator
from .response_analyzer import WSIResponseAnalyzer
from .score_calculator import WSIScoreCalculator
from .report_generator import WSIReportGenerator
from .service import WSIService, wsi_service, get_wsi_service, generate_wsi_questions_tool

__all__ = [
    "WSIService",
    "wsi_service",
    "get_wsi_service",
    "generate_wsi_questions_tool",
    "Competency",
    "CompetencySuggestion",
    "WSIQuestion",
    "ResponseAnalysis",
    "WSIResult",
    "StructuredReport",
    "CandidateFeedback",
    "OceanTraitScore",
    "SENIORITY_BIGFIVE_TOP_N",
    "normalize_weights",
    "safe_json_parse",
    "WSIQuestionGenerator",
    "WSIResponseAnalyzer",
    "WSIScoreCalculator",
    "WSIReportGenerator",
]
'''
with open(f'{pkg}/__init__.py', 'w') as f:
    f.write(init_content)
print(f"__init__.py written: {len(init_content.splitlines())} lines")

print("\nAll files written successfully!")
