"""
WSI Question Service for Skill-Specific Screening Question Generation.

Integrates skills into the WSI (Workforce Skills Index) methodology by:
1. Mapping skills to WSI blocks based on skill categories
2. Generating skill-specific screening questions tailored to each required skill
3. Creating depth assessment questions for technical skills
4. Creating behavioral fit questions for competencies

WSI Block Mapping:
- Block 2 (Technical Depth): Language skills, database skills
- Block 3 (Practical Experience): Framework skills, tool skills
- Block 4 (Problem Solving): General skills, methodologies
- Block 5 (Behavioral Fit): Behavioral competencies, soft skills
"""

from typing import List, Dict, Optional, Literal, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
import logging

from app.schemas.screening import ScreeningQuestion, ScreeningQuestionRequest
from app.models.job_draft import JobDraft

logger = logging.getLogger(__name__)


class SkillCategory(str, Enum):
    """Classification of skill types for WSI block mapping."""
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    TOOL = "tool"
    GENERAL = "general"
    BEHAVIORAL = "behavioral"


class WSIBlock(str, Enum):
    """WSI screening blocks corresponding to different assessment dimensions."""
    TECHNICAL_DEPTH = "technical_depth"
    PRACTICAL_EXPERIENCE = "practical_experience"
    PROBLEM_SOLVING = "problem_solving"
    BEHAVIORAL_FIT = "behavioral_fit"


@dataclass
class SkillClassification:
    """Classification metadata for a skill."""
    skill: str
    category: SkillCategory
    wsi_block: WSIBlock
    seniority_requirement: str = "pleno"
    is_critical: bool = False
    description: Optional[str] = None


@dataclass
class SkillSpecificContext:
    """Context for generating skill-specific questions."""
    skill: str
    category: SkillCategory
    wsi_block: WSIBlock
    seniority: str
    role: str
    company_context: Optional[str] = None
    is_critical: bool = False
    related_skills: List[str] = field(default_factory=list)


SKILL_CATEGORY_MAPPING = {
    "language_skills": [
        "python", "javascript", "typescript", "java", "go", "rust", "c#", ".net",
        "php", "ruby", "scala", "kotlin", "swift", "objective-c", "r", "matlab",
        "sql", "plsql", "tsql", "vb", "perl", "groovy", "clojure", "haskell",
        "erlang", "elixir", "julia", "lua", "pascal", "delphi", "cobol"
    ],
    "framework_skills": [
        "react", "vue.js", "angular", "next.js", "nuxt.js", "svelte", "ember",
        "spring", "spring boot", "django", "flask", "fastapi", "laravel",
        "symfony", "rails", "sinatra", "express.js", "nest.js", "koa",
        "asp.net", "asp.net core", "play framework", "grails", "quarkus",
        "micronaut", "thymeleaf", "freemarker", "mustache", "pug", "ejs"
    ],
    "database_skills": [
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb",
        "cassandra", "couchdb", "firestore", "sql server", "oracle", "mariadb",
        "sqlite", "neo4j", "memcached", "rabbitmq", "kafka", "graphdb",
        "cockroachdb", "timescaledb", "influxdb", "prometheus", "mongodb atlas"
    ],
    "tool_skills": [
        "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ansible",
        "jenkins", "gitlab ci", "github actions", "circleci", "travis ci",
        "git", "svn", "jira", "confluence", "slack", "gitlab", "github",
        "bitbucket", "datadog", "newrelic", "splunk", "cloudflare", "nginx",
        "apache", "linux", "windows", "macos", "vim", "vscode", "intellij",
        "postman", "insomnia", "swagger", "figma", "sketch", "adobe xd"
    ],
    "general_skills": [
        "agile", "scrum", "kanban", "waterfall", "design patterns", "microservices",
        "rest api", "graphql", "grpc", "websockets", "testing", "tdd", "bdd",
        "ci/cd", "devops", "cloud native", "serverless", "infrastructure as code",
        "data structures", "algorithms", "system design", "performance optimization",
        "security", "encryption", "authentication", "authorization"
    ]
}

BEHAVIORAL_COMPETENCIES_MAPPING = {
    "leadership": ["team leadership", "strategic thinking", "decision making"],
    "communication": ["verbal communication", "written communication", "presentation"],
    "collaboration": ["teamwork", "partnership", "conflict resolution"],
    "problem_solving": ["analytical thinking", "critical thinking", "creativity"],
    "adaptability": ["flexibility", "resilience", "learning agility"],
    "results_orientation": ["goal focus", "accountability", "execution"],
    "customer_focus": ["empathy", "service orientation", "user experience"],
    "ethics": ["integrity", "transparency", "compliance"]
}

SKILL_SPECIFIC_QUESTION_TEMPLATES = {
    "language": {
        "junior": [
            {
                "template": "You mentioned experience with {skill}. Describe a specific project where you used {skill} and what you learned.",
                "bloom_level": 2,
                "expected_signals": ["basic understanding", "practical application", "learning mindset"],
                "wsi_block": "technical_depth"
            },
            {
                "template": "What was the most challenging aspect of learning {skill}? How did you overcome it?",
                "bloom_level": 3,
                "expected_signals": ["problem solving", "resourcefulness", "persistence"],
                "wsi_block": "technical_depth"
            }
        ],
        "pleno": [
            {
                "template": "Tell me about a complex project where {skill} was core to the solution. What architectural decisions did you make?",
                "bloom_level": 4,
                "expected_signals": ["technical depth", "architectural thinking", "design expertise"],
                "wsi_block": "technical_depth"
            },
            {
                "template": "How would you compare {skill} with alternative approaches for solving the same problem? When would you use each?",
                "bloom_level": 5,
                "expected_signals": ["comparative analysis", "trade-off thinking", "best practices"],
                "wsi_block": "technical_depth"
            }
        ],
        "senior": [
            {
                "template": "Describe your most significant technical contribution using {skill}. What made it complex and how did you approach it?",
                "bloom_level": 5,
                "expected_signals": ["technical mastery", "complex problem solving", "innovation"],
                "wsi_block": "technical_depth"
            },
            {
                "template": "How do you approach mentoring others in {skill}? Describe a specific example.",
                "bloom_level": 6,
                "expected_signals": ["teaching ability", "knowledge transfer", "leadership"],
                "wsi_block": "technical_depth"
            }
        ],
        "lead": [
            {
                "template": "How have you established technical standards or best practices around {skill} in your team or company?",
                "bloom_level": 6,
                "expected_signals": ["technical leadership", "standard setting", "team development"],
                "wsi_block": "technical_depth"
            }
        ]
    },
    "framework": {
        "junior": [
            {
                "template": "Describe your experience building projects with {skill}. What features of {skill} do you find most useful?",
                "bloom_level": 2,
                "expected_signals": ["framework knowledge", "practical experience", "feature understanding"],
                "wsi_block": "practical_experience"
            },
            {
                "template": "What challenges have you faced when using {skill}? How did you resolve them?",
                "bloom_level": 3,
                "expected_signals": ["problem solving", "framework understanding", "debugging skills"],
                "wsi_block": "practical_experience"
            }
        ],
        "pleno": [
            {
                "template": "Tell me about a production application you built with {skill}. How did you structure components and manage state?",
                "bloom_level": 4,
                "expected_signals": ["architecture understanding", "production experience", "best practices"],
                "wsi_block": "practical_experience"
            },
            {
                "template": "Compare {skill} with other similar frameworks. What are the trade-offs in different scenarios?",
                "bloom_level": 5,
                "expected_signals": ["framework comparison", "architectural knowledge", "informed decisions"],
                "wsi_block": "practical_experience"
            }
        ],
        "senior": [
            {
                "template": "Describe a scalability challenge in {skill} that you solved. What optimizations did you implement?",
                "bloom_level": 5,
                "expected_signals": ["performance optimization", "scalability expertise", "advanced techniques"],
                "wsi_block": "practical_experience"
            },
            {
                "template": "How have you contributed to {skill} development or community? Share examples of your impact.",
                "bloom_level": 6,
                "expected_signals": ["community involvement", "thought leadership", "expertise sharing"],
                "wsi_block": "practical_experience"
            }
        ]
    },
    "database": {
        "junior": [
            {
                "template": "Describe a project where you designed or worked with {skill} databases. What was the schema like?",
                "bloom_level": 2,
                "expected_signals": ["database concepts", "practical experience", "design understanding"],
                "wsi_block": "technical_depth"
            },
            {
                "template": "When would you choose {skill} over other database options? What are its strengths?",
                "bloom_level": 3,
                "expected_signals": ["database knowledge", "comparative thinking", "use case understanding"],
                "wsi_block": "technical_depth"
            }
        ],
        "pleno": [
            {
                "template": "Tell me about optimizing query performance in {skill}. What indexing strategies did you use?",
                "bloom_level": 4,
                "expected_signals": ["optimization knowledge", "query expertise", "performance tuning"],
                "wsi_block": "technical_depth"
            },
            {
                "template": "How do you approach {skill} schema design for scalability? Describe a complex schema you designed.",
                "bloom_level": 5,
                "expected_signals": ["database architecture", "scalability thinking", "design patterns"],
                "wsi_block": "technical_depth"
            }
        ],
        "senior": [
            {
                "template": "Describe your experience with {skill} at scale. What optimization and scaling challenges did you face?",
                "bloom_level": 5,
                "expected_signals": ["enterprise experience", "scaling expertise", "advanced optimization"],
                "wsi_block": "technical_depth"
            },
            {
                "template": "How do you decide database architecture for large systems? Walk me through your decision-making process.",
                "bloom_level": 6,
                "expected_signals": ["strategic thinking", "architectural expertise", "system design"],
                "wsi_block": "technical_depth"
            }
        ]
    },
    "tool": {
        "junior": [
            {
                "template": "Describe your experience using {skill}. What are the key features you use regularly?",
                "bloom_level": 2,
                "expected_signals": ["tool knowledge", "practical application", "workflow understanding"],
                "wsi_block": "practical_experience"
            },
            {
                "template": "How has {skill} helped improve your development workflow or productivity?",
                "bloom_level": 3,
                "expected_signals": ["tool proficiency", "productivity awareness", "process improvement"],
                "wsi_block": "practical_experience"
            }
        ],
        "pleno": [
            {
                "template": "Tell me about implementing {skill} in a team or company context. What challenges did you face?",
                "bloom_level": 4,
                "expected_signals": ["tool mastery", "team implementation", "problem solving"],
                "wsi_block": "practical_experience"
            },
            {
                "template": "How do you configure and optimize {skill} for different scenarios or team sizes?",
                "bloom_level": 5,
                "expected_signals": ["advanced configuration", "optimization", "best practices"],
                "wsi_block": "practical_experience"
            }
        ],
        "senior": [
            {
                "template": "Describe establishing {skill} practices or standards in your organization. What was the adoption process?",
                "bloom_level": 5,
                "expected_signals": ["leadership", "change management", "organizational impact"],
                "wsi_block": "practical_experience"
            }
        ]
    },
    "general": {
        "junior": [
            {
                "template": "How do you apply {skill} in your daily development work? Give a concrete example.",
                "bloom_level": 2,
                "expected_signals": ["concept understanding", "practical application", "experience"],
                "wsi_block": "problem_solving"
            }
        ],
        "pleno": [
            {
                "template": "Describe a complex problem you solved using {skill}. What was your approach?",
                "bloom_level": 4,
                "expected_signals": ["problem solving", "analytical thinking", "solution design"],
                "wsi_block": "problem_solving"
            }
        ],
        "senior": [
            {
                "template": "How do you mentor others in {skill}? What framework do you use to teach this concept?",
                "bloom_level": 5,
                "expected_signals": ["teaching ability", "deep knowledge", "communication"],
                "wsi_block": "problem_solving"
            }
        ]
    }
}

BEHAVIORAL_QUESTION_TEMPLATES = {
    "leadership": [
        {
            "template": "Tell me about a time you led a team through a challenging project. How did you motivate and guide them?",
            "expected_signals": ["team motivation", "clear direction", "decision making"],
            "bloom_level": 5
        },
        {
            "template": "Describe a situation where you developed a team member's skills or career. What was your approach?",
            "expected_signals": ["mentoring", "people development", "investment in others"],
            "bloom_level": 5
        }
    ],
    "communication": [
        {
            "template": "Share an example of explaining a complex technical concept to non-technical stakeholders.",
            "expected_signals": ["clarity", "audience awareness", "explanation skills"],
            "bloom_level": 4
        },
        {
            "template": "Tell me about presenting your ideas to leadership. How do you structure your communication?",
            "expected_signals": ["presentation skills", "persuasion", "preparation"],
            "bloom_level": 4
        }
    ],
    "collaboration": [
        {
            "template": "Describe a time you worked effectively across different teams or departments. How did you build alignment?",
            "expected_signals": ["cross-functional work", "relationship building", "compromise"],
            "bloom_level": 4
        },
        {
            "template": "Tell me about resolving a conflict with a colleague. What was your approach?",
            "expected_signals": ["conflict resolution", "empathy", "problem solving"],
            "bloom_level": 4
        }
    ],
    "problem_solving": [
        {
            "template": "Describe your approach to solving an ambiguous or poorly defined problem.",
            "expected_signals": ["analytical thinking", "clarity seeking", "systematic approach"],
            "bloom_level": 5
        },
        {
            "template": "Tell me about a time you needed to think creatively to solve a problem. What was the result?",
            "expected_signals": ["creativity", "innovation", "resourcefulness"],
            "bloom_level": 5
        }
    ],
    "adaptability": [
        {
            "template": "Share an example of adapting to a significant change in technology or methodology.",
            "expected_signals": ["learning agility", "flexibility", "resilience"],
            "bloom_level": 4
        },
        {
            "template": "Tell me about a time you worked in an ambiguous situation. How did you handle the uncertainty?",
            "expected_signals": ["comfort with ambiguity", "adaptability", "proactivity"],
            "bloom_level": 4
        }
    ],
    "results_orientation": [
        {
            "template": "Describe a project where you had to deliver results under tight deadlines. How did you ensure quality?",
            "expected_signals": ["deadline management", "quality focus", "accountability"],
            "bloom_level": 4
        },
        {
            "template": "Tell me about a goal you exceeded. What drove you to go beyond expectations?",
            "expected_signals": ["motivation", "initiative", "ownership"],
            "bloom_level": 4
        }
    ]
}


class SkillClassifier:
    """Classifies skills into categories and maps them to WSI blocks."""
    
    @staticmethod
    def classify_skill(skill: str) -> SkillClassification:
        """
        Classify a skill and map it to appropriate WSI block.
        
        Args:
            skill: Skill name to classify
            
        Returns:
            SkillClassification with category and WSI block mapping
        """
        skill_lower = skill.lower().strip()
        
        for category_key, skills_list in SKILL_CATEGORY_MAPPING.items():
            if any(s in skill_lower for s in skills_list):
                if category_key == "language_skills":
                    category = SkillCategory.LANGUAGE
                    wsi_block = WSIBlock.TECHNICAL_DEPTH
                elif category_key == "framework_skills":
                    category = SkillCategory.FRAMEWORK
                    wsi_block = WSIBlock.PRACTICAL_EXPERIENCE
                elif category_key == "database_skills":
                    category = SkillCategory.DATABASE
                    wsi_block = WSIBlock.TECHNICAL_DEPTH
                elif category_key == "tool_skills":
                    category = SkillCategory.TOOL
                    wsi_block = WSIBlock.PRACTICAL_EXPERIENCE
                else:
                    category = SkillCategory.GENERAL
                    wsi_block = WSIBlock.PROBLEM_SOLVING
                
                return SkillClassification(
                    skill=skill,
                    category=category,
                    wsi_block=wsi_block,
                    description=None
                )
        
        return SkillClassification(
            skill=skill,
            category=SkillCategory.GENERAL,
            wsi_block=WSIBlock.PROBLEM_SOLVING,
            description="Unclassified skill"
        )
    
    @staticmethod
    def classify_competency(competency: str) -> Tuple[str, WSIBlock]:
        """
        Classify a behavioral competency.
        
        Args:
            competency: Competency name
            
        Returns:
            Tuple of (competency_key, WSI block)
        """
        competency_lower = competency.lower().strip()
        
        for comp_key in BEHAVIORAL_COMPETENCIES_MAPPING.keys():
            if comp_key in competency_lower or competency_lower in comp_key:
                return (comp_key, WSIBlock.BEHAVIORAL_FIT)
        
        return (competency_lower, WSIBlock.BEHAVIORAL_FIT)
    
    @staticmethod
    def classify_skills(skills: List[str]) -> Dict[str, List[SkillClassification]]:
        """
        Classify multiple skills and group by WSI block.
        
        Args:
            skills: List of skill names
            
        Returns:
            Dictionary mapping WSI blocks to classified skills
        """
        classified_by_block: Dict[str, List[SkillClassification]] = {
            block.value: [] for block in WSIBlock
        }
        
        for skill in skills:
            classification = SkillClassifier.classify_skill(skill)
            classified_by_block[classification.wsi_block.value].append(classification)
        
        return classified_by_block


class WSIQuestionService:
    """
    Main service for generating skill-specific WSI screening questions.
    
    Integrates skills into the WSI methodology by:
    1. Classifying skills to appropriate WSI blocks
    2. Generating skill-depth assessment questions
    3. Generating behavioral fit questions
    4. Creating comprehensive screening assessments
    """
    
    def __init__(self):
        self.classifier = SkillClassifier()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_skill_specific_questions(
        self,
        skills: List[str],
        behavioral_competencies: Optional[List[str]] = None,
        seniority: str = "pleno",
        job_title: Optional[str] = None,
        company_context: Optional[str] = None,
        critical_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate WSI screening questions tailored to each required skill.
        
        Creates skill-specific questions mapped to appropriate WSI blocks:
        - Block 2 (Technical Depth): Language & database skills
        - Block 3 (Practical Experience): Framework & tool skills
        - Block 4 (Problem Solving): General skills & methodologies
        - Block 5 (Behavioral Fit): Behavioral competencies
        
        Args:
            skills: List of required technical skills
            behavioral_competencies: Optional list of required behavioral competencies
            seniority: Seniority level (junior, pleno, senior, lead, executive)
            job_title: Job title for context
            company_context: Company-specific context for questions
            critical_skills: List of critical/must-have skills
            
        Returns:
            Dictionary with categorized questions organized by WSI block
        """
        critical_skills = critical_skills or []
        behavioral_competencies = behavioral_competencies or []
        
        classified_skills = self.classifier.classify_skills(skills)
        
        results = {
            "technical_depth_questions": [],
            "practical_experience_questions": [],
            "problem_solving_questions": [],
            "behavioral_fit_questions": [],
            "all_questions": [],
            "metadata": {
                "seniority": seniority,
                "job_title": job_title,
                "total_skills": len(skills),
                "total_competencies": len(behavioral_competencies),
                "total_questions": 0,
                "blocks_covered": []
            }
        }
        
        for skill_classification in classified_skills[WSIBlock.TECHNICAL_DEPTH.value]:
            questions = self._generate_skill_specific_questions(
                skill_classification,
                seniority,
                is_critical=skill_classification.skill in critical_skills,
                context=company_context
            )
            results["technical_depth_questions"].extend(questions)
        
        for skill_classification in classified_skills[WSIBlock.PRACTICAL_EXPERIENCE.value]:
            questions = self._generate_skill_specific_questions(
                skill_classification,
                seniority,
                is_critical=skill_classification.skill in critical_skills,
                context=company_context
            )
            results["practical_experience_questions"].extend(questions)
        
        for skill_classification in classified_skills[WSIBlock.PROBLEM_SOLVING.value]:
            questions = self._generate_skill_specific_questions(
                skill_classification,
                seniority,
                is_critical=skill_classification.skill in critical_skills,
                context=company_context
            )
            results["problem_solving_questions"].extend(questions)
        
        for competency in behavioral_competencies:
            comp_key, _ = self.classifier.classify_competency(competency)
            questions = self._generate_behavioral_questions(comp_key, seniority)
            results["behavioral_fit_questions"].extend(questions)
        
        all_questions = (
            results["technical_depth_questions"] +
            results["practical_experience_questions"] +
            results["problem_solving_questions"] +
            results["behavioral_fit_questions"]
        )
        
        for i, q in enumerate(all_questions):
            q.order = i
        
        results["all_questions"] = all_questions
        results["metadata"]["total_questions"] = len(all_questions)
        
        blocks_with_questions = []
        if results["technical_depth_questions"]:
            blocks_with_questions.append("technical_depth")
        if results["practical_experience_questions"]:
            blocks_with_questions.append("practical_experience")
        if results["problem_solving_questions"]:
            blocks_with_questions.append("problem_solving")
        if results["behavioral_fit_questions"]:
            blocks_with_questions.append("behavioral_fit")
        
        results["metadata"]["blocks_covered"] = blocks_with_questions
        
        return results
    
    def get_questions_for_skills(
        self,
        job_draft: JobDraft
    ) -> Dict[str, Any]:
        """
        Generate screening questions based on job draft's selected skills.
        
        Receives a JobDraft object with selected technical skills and behavioral
        competencies, then generates appropriate WSI screening questions for
        depth assessment and behavioral fit evaluation.
        
        Args:
            job_draft: JobDraft model instance with selected skills and competencies
            
        Returns:
            Dictionary with structured screening questions and metadata
        """
        skills = job_draft.skills or []
        behavioral_competencies = job_draft.behavioral_competencies or []
        
        critical_skills = []
        if job_draft.inferred_fields and "critical_skills" in job_draft.inferred_fields:
            critical_skills = job_draft.inferred_fields.get("critical_skills", [])
        
        return self.generate_skill_specific_questions(
            skills=skills,
            behavioral_competencies=behavioral_competencies,
            seniority=job_draft.seniority or "pleno",
            job_title=job_draft.job_title,
            company_context=None,
            critical_skills=critical_skills
        )
    
    def _generate_skill_specific_questions(
        self,
        skill_classification: SkillClassification,
        seniority: str,
        is_critical: bool = False,
        context: Optional[str] = None
    ) -> List[ScreeningQuestion]:
        """
        Generate questions for a specific skill.
        
        Args:
            skill_classification: Classified skill with category and block mapping
            seniority: Seniority level
            is_critical: Whether this is a critical skill
            context: Optional company/role context
            
        Returns:
            List of ScreeningQuestion objects
        """
        questions = []
        category = skill_classification.category.value
        templates = SKILL_SPECIFIC_QUESTION_TEMPLATES.get(category, {})
        
        seniority_templates = templates.get(seniority, templates.get("pleno", []))
        
        for template_dict in seniority_templates:
            question_text = template_dict["template"].format(skill=skill_classification.skill)
            
            if context:
                question_text += f" (Context: {context})"
            
            question = ScreeningQuestion(
                id=str(uuid.uuid4()),
                text=question_text,
                category="technical",
                skill=skill_classification.skill,
                bloom_level=template_dict.get("bloom_level", 3),
                bloom_label=self._get_bloom_label(template_dict.get("bloom_level", 3)),
                dreyfus_stage=self._get_dreyfus_stage(seniority),
                dreyfus_label=self._get_dreyfus_label(self._get_dreyfus_stage(seniority)),
                framework="CBI",
                weight=2.0 if is_critical else 1.0,
                expected_signals=template_dict.get("expected_signals", []),
                scoring_criteria=self._create_scoring_criteria(template_dict.get("bloom_level", 3)),
                is_selected=True,
                order=0
            )
            
            questions.append(question)
        
        return questions
    
    def _generate_behavioral_questions(
        self,
        competency_key: str,
        seniority: str
    ) -> List[ScreeningQuestion]:
        """
        Generate behavioral assessment questions for a competency.
        
        Args:
            competency_key: Key of the behavioral competency
            seniority: Seniority level
            
        Returns:
            List of ScreeningQuestion objects
        """
        questions = []
        templates = BEHAVIORAL_QUESTION_TEMPLATES.get(competency_key, [])
        
        for template_dict in templates:
            question = ScreeningQuestion(
                id=str(uuid.uuid4()),
                text=template_dict["template"],
                category="behavioral",
                trait=competency_key,
                bloom_level=template_dict.get("bloom_level", 4),
                bloom_label=self._get_bloom_label(template_dict.get("bloom_level", 4)),
                dreyfus_stage=self._get_dreyfus_stage(seniority),
                dreyfus_label=self._get_dreyfus_label(self._get_dreyfus_stage(seniority)),
                framework="BigFive",
                weight=1.0,
                expected_signals=template_dict.get("expected_signals", []),
                scoring_criteria=self._create_scoring_criteria(template_dict.get("bloom_level", 4)),
                is_selected=True,
                order=0
            )
            
            questions.append(question)
        
        return questions
    
    @staticmethod
    def _get_bloom_label(level: int) -> str:
        """Get Bloom's Taxonomy level label."""
        labels = {
            1: "Lembrar",
            2: "Compreender",
            3: "Aplicar",
            4: "Analisar",
            5: "Avaliar",
            6: "Criar"
        }
        return labels.get(level, "Aplicar")
    
    @staticmethod
    def _get_dreyfus_stage(seniority: str) -> int:
        """Map seniority to Dreyfus model stage."""
        mapping = {
            "junior": 2,
            "pleno": 3,
            "senior": 4,
            "lead": 5,
            "executive": 5
        }
        return mapping.get(seniority.lower(), 3)
    
    @staticmethod
    def _get_dreyfus_label(stage: int) -> str:
        """Get Dreyfus model stage label."""
        labels = {
            1: "Novato",
            2: "Iniciante Avançado",
            3: "Competente",
            4: "Proficiente",
            5: "Especialista"
        }
        return labels.get(stage, "Competente")
    
    @staticmethod
    def _create_scoring_criteria(bloom_level: int) -> Dict[str, str]:
        """Create scoring criteria based on Bloom's level."""
        criteria_map = {
            1: {
                "poor": "No recall of the concept or skill",
                "fair": "Partial recall with some inaccuracies",
                "good": "Accurate recall with minor gaps",
                "excellent": "Perfect recall with relevant examples"
            },
            2: {
                "poor": "Cannot explain the concept",
                "fair": "Superficial explanation with gaps",
                "good": "Clear explanation with minor gaps",
                "excellent": "Comprehensive explanation with examples"
            },
            3: {
                "poor": "Cannot apply the skill",
                "fair": "Applies with significant errors",
                "good": "Applies correctly with minor issues",
                "excellent": "Applies correctly in various contexts"
            },
            4: {
                "poor": "Cannot analyze or compare",
                "fair": "Superficial analysis with gaps",
                "good": "Thoughtful analysis with clear reasoning",
                "excellent": "In-depth analysis with insightful comparisons"
            },
            5: {
                "poor": "Cannot evaluate or judge",
                "fair": "Surface-level evaluation",
                "good": "Reasonable evaluation with clear criteria",
                "excellent": "Sophisticated evaluation with deep insight"
            },
            6: {
                "poor": "Cannot create or design",
                "fair": "Limited creative output",
                "good": "Solid creative output with some innovation",
                "excellent": "Highly innovative and well-structured creation"
            }
        }
        
        return criteria_map.get(bloom_level, criteria_map[3])
    
    def generate_skill_depth_summary(
        self,
        skills: List[str],
        seniority: str = "pleno"
    ) -> Dict[str, Any]:
        """
        Generate a summary of skill depth assessment approach for the given skills.
        
        Args:
            skills: List of skills
            seniority: Seniority level
            
        Returns:
            Dictionary with skill assessment approach and recommended focus areas
        """
        classified = self.classifier.classify_skills(skills)
        
        summary = {
            "assessment_approach": {},
            "skill_count_by_block": {},
            "recommended_focus": []
        }
        
        for block_name, skills_list in classified.items():
            if skills_list:
                summary["skill_count_by_block"][block_name] = len(skills_list)
                summary["assessment_approach"][block_name] = self._get_block_assessment_approach(
                    block_name, seniority
                )
        
        if classified.get(WSIBlock.TECHNICAL_DEPTH.value):
            summary["recommended_focus"].append(
                "Deep technical knowledge assessment via architecture and design questions"
            )
        
        if classified.get(WSIBlock.PRACTICAL_EXPERIENCE.value):
            summary["recommended_focus"].append(
                "Practical application assessment via production scenarios and implementation challenges"
            )
        
        if classified.get(WSIBlock.PROBLEM_SOLVING.value):
            summary["recommended_focus"].append(
                "Problem-solving approach assessment via methodology and thinking process"
            )
        
        return summary
    
    @staticmethod
    def _get_block_assessment_approach(block_name: str, seniority: str) -> str:
        """Get assessment approach description for a WSI block."""
        approaches = {
            "technical_depth": "Assess deep technical knowledge through architecture decisions, optimization, and advanced problem-solving",
            "practical_experience": "Assess hands-on experience through production scenarios, implementation challenges, and real-world application",
            "problem_solving": "Assess problem-solving approach through methodology, analysis, and critical thinking",
            "behavioral_fit": "Assess cultural and behavioral fit through situational questions and competency indicators"
        }
        return approaches.get(block_name, "Standard assessment")
