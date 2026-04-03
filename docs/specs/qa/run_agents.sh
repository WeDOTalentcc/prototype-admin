#!/bin/bash
cd /home/runner/workspace/docs/specs/qa
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxM2NmODJmYi1mMWY2LTQyMDUtOTM3Ny03NThlNTkwNDAxNDgiLCJleHAiOjE3NzUyNDY0NjcsInR5cGUiOiJhY2Nlc3MiLCJyb2xlIjoicmVjcnVpdGVyIiwiaWF0IjoxNzc1MjQ0NjY3fQ.u_NVH7yG1pXYJp3ojAQclhjxNcExHti-CDj4Fx63CPw"
python3 benchmark_agents.py --base-url http://localhost:5000 --token "$TOKEN" --timeout 120 2>&1
