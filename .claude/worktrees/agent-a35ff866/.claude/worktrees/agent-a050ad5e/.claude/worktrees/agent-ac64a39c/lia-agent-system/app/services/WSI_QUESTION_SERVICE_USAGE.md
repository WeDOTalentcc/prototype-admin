# WSI Question Service - Usage Guide

## Overview

The `WSIQuestionService` is a specialized service for generating skill-specific screening questions that integrate technical skills and behavioral competencies into the WSI (Workforce Skills Index) methodology.

## Key Features

1. **Skill Classification**: Automatically classifies skills into categories and maps them to WSI assessment blocks
2. **Skill-Specific Questions**: Generates tailored screening questions for each technical skill
3. **Behavioral Assessment**: Creates behavioral fit questions for competencies
4. **WSI Block Mapping**: Ensures questions are organized by assessment dimension

## WSI Block Mapping

The service maps skills to five assessment blocks:

| Block | Description | Skills | Seniority Levels |
|-------|-------------|--------|-----------------|
| **Technical Depth** (Block 2) | Deep technical knowledge | Languages: Python, Java, Go; Databases: PostgreSQL, MongoDB, etc. | All levels |
| **Practical Experience** (Block 3) | Hands-on application | Frameworks: React, Vue, Django; Tools: Docker, Kubernetes, AWS | All levels |
| **Problem Solving** (Block 4) | Methodology & thinking | Design Patterns, Microservices, System Design, Algorithms | All levels |
| **Behavioral Fit** (Block 5) | Soft skills & culture | Leadership, Communication, Collaboration, Problem-solving | All levels |

## Skill Categories

Skills are automatically classified into these categories:

- **Language Skills**: Python, JavaScript, Java, Go, Rust, C#, etc.
- **Framework Skills**: React, Vue.js, Angular, Django, Spring Boot, etc.
- **Database Skills**: PostgreSQL, MongoDB, Redis, Elasticsearch, etc.
- **Tool Skills**: Docker, Kubernetes, AWS, Git, Jenkins, etc.
- **General Skills**: Agile, Microservices, API Design, Testing, etc.
- **Behavioral Competencies**: Leadership, Communication, Collaboration, etc.

## Basic Usage

### 1. Generate Skill-Specific Questions

```python
from app.services.wsi_question_service import WSIQuestionService

service = WSIQuestionService()

# Generate questions for specific skills
result = service.generate_skill_specific_questions(
    skills=["Python", "React", "PostgreSQL", "Docker"],
    behavioral_competencies=["leadership", "communication"],
    seniority="pleno",
    job_title="Senior Full Stack Engineer",
    critical_skills=["Python", "PostgreSQL"]
)

# Access the results
print(f"Total questions: {result['metadata']['total_questions']}")
print(f"Blocks covered: {result['metadata']['blocks_covered']}")

# Questions organized by WSI block
print(f"Technical Depth: {len(result['technical_depth_questions'])}")
print(f"Practical Experience: {len(result['practical_experience_questions'])}")
print(f"Problem Solving: {len(result['problem_solving_questions'])}")
print(f"Behavioral Fit: {len(result['behavioral_fit_questions'])}")

# All questions combined and ordered
for question in result['all_questions']:
    print(f"Q{question.order + 1}: {question.text[:60]}...")
```

### 2. Generate Questions from Job Draft

```python
from app.services.wsi_question_service import WSIQuestionService
from app.models.job_draft import JobDraft

service = WSIQuestionService()

# Assuming you have a JobDraft instance with skills
job_draft = JobDraft(
    job_title="Backend Engineer",
    skills=["Python", "PostgreSQL", "Docker"],
    behavioral_competencies=["problem_solving", "collaboration"],
    seniority="senior"
)

# Generate questions based on draft
result = service.get_questions_for_skills(job_draft)
```

### 3. Classify Skills

```python
from app.services.wsi_question_service import SkillClassifier

classifier = SkillClassifier()

# Classify a single skill
classification = classifier.classify_skill("Python")
print(f"Skill: {classification.skill}")
print(f"Category: {classification.category.value}")  # 'language'
print(f"WSI Block: {classification.wsi_block.value}")  # 'technical_depth'

# Classify multiple skills
classifications = classifier.classify_skills([
    "Python", "React", "PostgreSQL", "Docker"
])

for block_name, skills_list in classifications.items():
    if skills_list:
        print(f"\n{block_name.upper()}:")
        for skill_class in skills_list:
            print(f"  - {skill_class.skill} ({skill_class.category.value})")
```

### 4. Get Assessment Approach Summary

```python
from app.services.wsi_question_service import WSIQuestionService

service = WSIQuestionService()

summary = service.generate_skill_depth_summary(
    skills=["Python", "React", "PostgreSQL"],
    seniority="pleno"
)

print("Assessment Approach by Block:")
for block, approach in summary["assessment_approach"].items():
    print(f"  {block}: {approach}")

print("\nRecommended Focus Areas:")
for focus in summary["recommended_focus"]:
    print(f"  • {focus}")
```

## API Integration Example

To integrate the service with FastAPI endpoints:

```python
from fastapi import APIRouter, HTTPException, Depends
from app.services.wsi_question_service import WSIQuestionService
from app.auth.dependencies import get_current_active_user

router = APIRouter()
service = WSIQuestionService()

@router.post("/skill-based-questions")
async def generate_skill_based_questions(
    skills: list[str],
    behavioral_competencies: list[str] = None,
    seniority: str = "pleno",
    job_title: str = None,
    current_user = Depends(get_current_active_user)
):
    """Generate screening questions based on selected skills."""
    try:
        result = service.generate_skill_specific_questions(
            skills=skills,
            behavioral_competencies=behavioral_competencies,
            seniority=seniority,
            job_title=job_title
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job-draft-questions")
async def generate_job_draft_questions(
    job_draft_id: str,
    db = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Generate questions from a job draft."""
    try:
        job_draft = await db.get(JobDraft, job_draft_id)
        if not job_draft:
            raise HTTPException(status_code=404, detail="Job draft not found")
        
        result = service.get_questions_for_skills(job_draft)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Question Structure

Each generated question includes:

```python
class ScreeningQuestion(BaseModel):
    id: str  # Unique identifier
    text: str  # Question text
    category: str  # "technical" or "behavioral"
    skill: Optional[str]  # Associated technical skill
    trait: Optional[str]  # Associated behavioral trait
    
    # Bloom's Taxonomy (1-6)
    bloom_level: int  # 1=Remember, 2=Understand, 3=Apply, 4=Analyze, 5=Evaluate, 6=Create
    bloom_label: str  # Human-readable label
    
    # Dreyfus Model (1-5)
    dreyfus_stage: int  # 1=Novice, 2=Advanced Beginner, 3=Competent, 4=Proficient, 5=Expert
    dreyfus_label: str  # Human-readable label
    
    # Assessment Framework
    framework: str  # "CBI", "Bloom", "Dreyfus", or "BigFive"
    
    # Scoring
    weight: float  # Question importance (2.0 for critical, 1.0 for normal)
    expected_signals: List[str]  # What to listen for in answer
    scoring_criteria: Dict[str, str]  # Scoring rubric by level
    
    # Metadata
    is_selected: bool  # Whether question is active
    order: int  # Display order
```

## Seniority-Based Differentiation

Questions adapt based on seniority level:

| Seniority | Dreyfus | Bloom Focus | Question Depth |
|-----------|---------|-------------|-----------------|
| Junior | 2 (Advanced Beginner) | 1-3 (Remember-Apply) | Basic concepts, first experiences |
| Pleno | 3 (Competent) | 3-4 (Apply-Analyze) | Practical projects, decision-making |
| Senior | 4 (Proficient) | 4-5 (Analyze-Evaluate) | Complex solutions, trade-offs |
| Lead | 5 (Expert) | 5-6 (Evaluate-Create) | Architecture, mentoring, standards |

## Skill Weight & Criticality

Critical skills are weighted at 2.0, giving them higher importance in assessment:

```python
result = service.generate_skill_specific_questions(
    skills=["Python", "React", "Docker", "AWS"],
    critical_skills=["Python", "Docker"],  # These get weight 2.0
    seniority="senior"
)
```

## Behavioral Competencies Supported

- **Leadership**: Team leadership, strategic thinking, decision making
- **Communication**: Verbal, written, presentations, negotiation
- **Collaboration**: Teamwork, partnership, conflict resolution
- **Problem Solving**: Analytical thinking, creativity, innovation
- **Adaptability**: Flexibility, resilience, learning agility
- **Results Orientation**: Goal focus, accountability, execution
- **Customer Focus**: Empathy, service orientation, user experience
- **Ethics**: Integrity, transparency, compliance

## Best Practices

1. **Use Critical Skills**: Mark essential skills to ensure deeper assessment
2. **Combine with Behavioral**: Always include behavioral competencies for holistic evaluation
3. **Match Seniority**: Ensure seniority level is accurate for appropriate Bloom/Dreyfus levels
4. **Limit Skill Count**: 5-8 technical skills + 2-3 competencies works best
5. **Review Questions**: Always review generated questions for context appropriateness

## Advanced Features

### Get Skill Classification

```python
classifier = SkillClassifier()
classifications_by_block = classifier.classify_skills(skill_list)
```

### Classify Competencies

```python
competency_key, wsi_block = classifier.classify_competency("Leadership")
# Returns: ("leadership", WSIBlock.BEHAVIORAL_FIT)
```

## Error Handling

```python
try:
    result = service.generate_skill_specific_questions(skills=[])
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Service error: {e}")
```

## Performance Considerations

- Question generation is synchronous and completes in milliseconds
- Suitable for real-time API endpoints
- No external API calls required
- Minimal memory footprint

## Future Enhancements

- LLM-enhanced question personalization
- Industry-specific question templates
- Multi-language support
- Custom skill category mapping
- Machine learning-based skill weight optimization
