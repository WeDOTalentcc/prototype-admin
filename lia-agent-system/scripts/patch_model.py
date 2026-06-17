"""Add education_snapshot to main Candidate model in candidates.py."""
path = "/home/runner/workspace/lia-agent-system/libs/models/lia_models/candidate.py"

with open(path, "r") as f:
    content = f.read()

# Find the work_history line and add education_snapshot after it
old = "    # Work History (JSON snapshot for fast access - denormalized from candidate_experiences)\n    work_history = Column(JSON, default=[])"
new = ("    # Work History (JSON snapshot for fast access - denormalized from candidate_experiences)\n"
       "    work_history = Column(JSON, default=[])\n"
       "    # Education snapshot (denormalized from candidate_education; populated by PUT /candidates/{id}/education)\n"
       "    education_snapshot = Column(JSON, nullable=True)")

# Only patch inside the main Candidate class (before CandidateSearch)
main_class = content.split("class CandidateSearch")[0]
if "education_snapshot" in main_class.split("class Candidate(")[1]:
    print("education_snapshot already exists in Candidate model — no change needed")
elif old not in content:
    print("ERROR: could not find anchor string in file")
    exit(1)
else:
    new_content = content.replace(old, new, 1)  # only first occurrence (in Candidate class)
    with open(path, "w") as f:
        f.write(new_content)
    print("Added education_snapshot to Candidate model")
