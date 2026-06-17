# Mutation Testing Baseline (UC-P3-11)

**Date:** 2026-05-02
**Tool:** mutmut
**Target modules:** app/shared/compliance/, app/domains/compliance/, app/shared/evaluation/
**Status:** Setup complete; baseline pending first CI run

## Running Locally

Collecting mutmut
  Downloading mutmut-3.5.0-py3-none-any.whl.metadata (10 kB)
Requirement already satisfied: click>=8.0.0 in ./.pythonlibs/lib/python3.11/site-packages (from mutmut) (8.3.1)
Requirement already satisfied: coverage>=7.3.0 in ./.pythonlibs/lib/python3.11/site-packages (from mutmut) (7.13.4)
Collecting libcst>=1.8.5 (from mutmut)
  Downloading libcst-1.8.6-cp311-cp311-manylinux_2_28_x86_64.whl.metadata (15 kB)
Requirement already satisfied: pytest>=6.2.5 in ./.pythonlibs/lib/python3.11/site-packages (from mutmut) (8.3.4)
Collecting setproctitle>=1.1.0 (from mutmut)
  Downloading setproctitle-1.3.7-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (10 kB)
Collecting textual>=1.0.0 (from mutmut)
  Downloading textual-8.2.5-py3-none-any.whl.metadata (9.1 kB)
Requirement already satisfied: pyyaml>=5.2 in ./.pythonlibs/lib/python3.11/site-packages (from libcst>=1.8.5->mutmut) (6.0.3)
Requirement already satisfied: iniconfig in ./.pythonlibs/lib/python3.11/site-packages (from pytest>=6.2.5->mutmut) (2.3.0)
Requirement already satisfied: packaging in ./.pythonlibs/lib/python3.11/site-packages (from pytest>=6.2.5->mutmut) (25.0)
Requirement already satisfied: pluggy<2,>=1.5 in ./.pythonlibs/lib/python3.11/site-packages (from pytest>=6.2.5->mutmut) (1.6.0)
Requirement already satisfied: markdown-it-py>=2.1.0 in ./.pythonlibs/lib/python3.11/site-packages (from markdown-it-py[linkify]>=2.1.0->textual>=1.0.0->mutmut) (4.0.0)
Collecting mdit-py-plugins (from textual>=1.0.0->mutmut)
  Downloading mdit_py_plugins-0.5.0-py3-none-any.whl.metadata (2.8 kB)
Requirement already satisfied: platformdirs<5,>=3.6.0 in ./.pythonlibs/lib/python3.11/site-packages (from textual>=1.0.0->mutmut) (4.9.6)
Requirement already satisfied: pygments<3.0.0,>=2.19.2 in ./.pythonlibs/lib/python3.11/site-packages (from textual>=1.0.0->mutmut) (2.19.2)
Requirement already satisfied: rich>=14.2.0 in ./.pythonlibs/lib/python3.11/site-packages (from textual>=1.0.0->mutmut) (14.3.1)
Requirement already satisfied: typing-extensions<5.0.0,>=4.4.0 in ./.pythonlibs/lib/python3.11/site-packages (from textual>=1.0.0->mutmut) (4.15.0)
Requirement already satisfied: mdurl~=0.1 in ./.pythonlibs/lib/python3.11/site-packages (from markdown-it-py>=2.1.0->markdown-it-py[linkify]>=2.1.0->textual>=1.0.0->mutmut) (0.1.2)
Collecting linkify-it-py<3,>=1 (from markdown-it-py[linkify]>=2.1.0->textual>=1.0.0->mutmut)
  Downloading linkify_it_py-2.1.0-py3-none-any.whl.metadata (8.5 kB)
Collecting uc-micro-py (from linkify-it-py<3,>=1->markdown-it-py[linkify]>=2.1.0->textual>=1.0.0->mutmut)
  Downloading uc_micro_py-2.0.0-py3-none-any.whl.metadata (2.2 kB)
Downloading mutmut-3.5.0-py3-none-any.whl (34 kB)
Downloading libcst-1.8.6-cp311-cp311-manylinux_2_28_x86_64.whl (2.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.3/2.3 MB 27.4 MB/s eta 0:00:00
Downloading setproctitle-1.3.7-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (32 kB)
Downloading textual-8.2.5-py3-none-any.whl (727 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 727.0/727.0 kB 2.7 MB/s eta 0:00:00
Downloading mdit_py_plugins-0.5.0-py3-none-any.whl (57 kB)
Downloading linkify_it_py-2.1.0-py3-none-any.whl (19 kB)
Downloading uc_micro_py-2.0.0-py3-none-any.whl (6.4 kB)
Installing collected packages: uc-micro-py, setproctitle, libcst, mdit-py-plugins, linkify-it-py, textual, mutmut
Successfully installed libcst-1.8.6 linkify-it-py-2.1.0 mdit-py-plugins-0.5.0 mutmut-3.5.0 setproctitle-1.3.7 textual-8.2.5 uc-micro-py-2.0.0

## Configuration

Config file:  at project root.

| Setting | Value |
|---------|-------|
| paths_to_mutate | app/shared/compliance/, app/domains/compliance/, app/shared/evaluation/ |
| runner | python -m pytest tests/unit/ -x -q --no-cov |
| tests_dir | tests/unit/ |

## CI Integration

Mutation testing runs as a non-blocking step on  events to /.
Step: "Mutation Testing (compliance modules)" in .

## Goal

- Current baseline: TBD (first CI run will establish)
- Target: mutation score >= 70% in compliance modules
- Timeline: sprint backlog (P3 — oportunistico)

## Notes

The compliance modules (app/shared/compliance/) already have zero 
comments — they are the strictest in the codebase, making them good mutation
testing candidates with high signal-to-noise.
