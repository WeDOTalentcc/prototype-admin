#!/usr/bin/env python3
"""Validation script for job templates.

Validates:
- Category and subcategory correctness
- WSI quality gates (technical skills, behavioral competencies, responsibilities)
- Template field validation
- Duplicate detection (same title + seniority)

Exit codes:
- 0: All templates valid
- 1: Validation errors found
"""

import os
import sys
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.data.templates import get_all_system_templates, TEMPLATE_CATEGORIES
from app.domains.job_management.services.job_template_service import validate_wsi_quality, WSI_QUALITY_GATES


class TemplateValidator:
    """Validates templates against quality and correctness criteria."""

    VALID_SENIORITIES = {"junior", "pleno", "senior"}
    VALID_WORK_MODELS = {"remote", "hybrid", "onsite"}
    REQUIRED_SKILL_FIELDS = {"name", "level"}
    VALID_SKILL_LEVELS = {"basic", "intermediate", "advanced"}

    def __init__(self):
        self.valid_templates: List[Dict[str, Any]] = []
        self.invalid_templates: List[Tuple[Dict[str, Any], List[str]]] = []
        self.duplicates: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def validate_all(self) -> bool:
        """
        Validate all system templates.

        Returns:
            True if all templates are valid, False otherwise
        """
        templates = get_all_system_templates()

        if not templates:
            print("No templates found to validate.")
            return True

        # First pass: detect duplicates
        self._detect_duplicates(templates)

        # Second pass: validate each template
        for template in templates:
            errors = self._validate_template(template)

            if errors:
                self.invalid_templates.append((template, errors))
            else:
                self.valid_templates.append(template)

        return len(self.invalid_templates) == 0

    def _detect_duplicates(self, templates: List[Dict[str, Any]]) -> None:
        """Detect templates with same normalized title + seniority."""
        seen: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)

        for template in templates:
            # Use normalized title or default to title if not present
            title_normalized = (
                template.get("title_normalized")
                or template.get("title", "").lower().strip()
            )
            seniority = template.get("seniority", "unknown")
            key = (title_normalized, seniority)
            seen[key].append(template)

        # Collect duplicates (entries with more than one template)
        for key, templates_with_key in seen.items():
            if len(templates_with_key) > 1:
                self.duplicates[str(key)] = templates_with_key

    def _validate_template(self, template: Dict[str, Any]) -> List[str]:
        """
        Validate a single template.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # 1. Validate title
        errors.extend(self._validate_title(template))

        # 2. Validate category and subcategory
        errors.extend(self._validate_category_subcategory(template))

        # 3. Validate seniority
        errors.extend(self._validate_seniority(template))

        # 4. Validate work model
        errors.extend(self._validate_work_model(template))

        # 5. Validate salary range
        errors.extend(self._validate_salary_range(template))

        # 6. Validate default_skills
        errors.extend(self._validate_default_skills(template))

        # 7. Validate WSI quality gates
        errors.extend(self._validate_wsi_quality(template))

        # 8. Check if template is duplicate
        errors.extend(self._validate_no_duplicate(template))

        return errors

    def _validate_title(self, template: Dict[str, Any]) -> List[str]:
        """Validate title field."""
        errors = []
        title = template.get("title")

        if not title:
            errors.append("Missing or empty title")
        elif not isinstance(title, str):
            errors.append(f"Title must be string, got {type(title).__name__}")
        elif len(title.strip()) == 0:
            errors.append("Title is whitespace-only")

        return errors

    def _validate_category_subcategory(self, template: Dict[str, Any]) -> List[str]:
        """Validate category and subcategory."""
        errors = []
        category = template.get("category")
        subcategory = template.get("subcategory")

        # Check category
        if not category:
            errors.append("Missing category")
        elif category not in TEMPLATE_CATEGORIES:
            valid_cats = ", ".join(sorted(TEMPLATE_CATEGORIES.keys()))
            errors.append(f"Invalid category '{category}'. Valid: {valid_cats}")
        else:
            # Check subcategory only if category is valid
            if not subcategory:
                errors.append("Missing subcategory")
            else:
                valid_subcategories = {
                    sc["name"]
                    for sc in TEMPLATE_CATEGORIES[category].get("subcategories", [])
                }
                if subcategory not in valid_subcategories:
                    valid_subs = ", ".join(sorted(valid_subcategories))
                    errors.append(
                        f"Invalid subcategory '{subcategory}' for '{category}'. "
                        f"Valid: {valid_subs}"
                    )

        return errors

    def _validate_seniority(self, template: Dict[str, Any]) -> List[str]:
        """Validate seniority field."""
        errors = []
        seniority = template.get("seniority")

        if not seniority:
            errors.append("Missing seniority")
        elif seniority not in self.VALID_SENIORITIES:
            valid_sen = ", ".join(sorted(self.VALID_SENIORITIES))
            errors.append(f"Invalid seniority '{seniority}'. Must be: {valid_sen}")

        return errors

    def _validate_work_model(self, template: Dict[str, Any]) -> List[str]:
        """Validate work_model field."""
        errors = []
        work_model = template.get("work_model")

        if not work_model:
            errors.append("Missing work_model")
        elif work_model not in self.VALID_WORK_MODELS:
            valid_wm = ", ".join(sorted(self.VALID_WORK_MODELS))
            errors.append(f"Invalid work_model '{work_model}'. Must be: {valid_wm}")

        return errors

    def _validate_salary_range(self, template: Dict[str, Any]) -> List[str]:
        """Validate salary range fields."""
        errors = []
        min_sal = template.get("salary_range_min")
        max_sal = template.get("salary_range_max")

        # Check if values exist
        if min_sal is None:
            errors.append("Missing salary_range_min")
        elif not isinstance(min_sal, (int, float)):
            errors.append(f"salary_range_min must be numeric, got {type(min_sal).__name__}")
        elif min_sal < 0:
            errors.append(f"salary_range_min must be positive, got {min_sal}")

        if max_sal is None:
            errors.append("Missing salary_range_max")
        elif not isinstance(max_sal, (int, float)):
            errors.append(f"salary_range_max must be numeric, got {type(max_sal).__name__}")
        elif max_sal < 0:
            errors.append(f"salary_range_max must be positive, got {max_sal}")

        # Check if min < max only if both are valid
        if min_sal is not None and max_sal is not None:
            if isinstance(min_sal, (int, float)) and isinstance(max_sal, (int, float)):
                if min_sal >= max_sal:
                    errors.append(
                        f"salary_range_min ({min_sal}) must be < salary_range_max ({max_sal})"
                    )

        return errors

    def _validate_default_skills(self, template: Dict[str, Any]) -> List[str]:
        """Validate default_skills field."""
        errors = []
        skills = template.get("default_skills", [])

        if not isinstance(skills, list):
            errors.append(f"default_skills must be a list, got {type(skills).__name__}")
            return errors

        for idx, skill in enumerate(skills):
            if not isinstance(skill, dict):
                errors.append(f"Skill at index {idx} is not a dict: {type(skill).__name__}")
                continue

            # Check required fields
            if "name" not in skill or not skill["name"]:
                errors.append(f"Skill at index {idx} missing or empty 'name'")

            if "level" not in skill:
                errors.append(f"Skill at index {idx} missing 'level'")
            elif skill["level"] not in self.VALID_SKILL_LEVELS:
                skill_name = skill.get("name", "unknown")
                valid_lvl = ", ".join(sorted(self.VALID_SKILL_LEVELS))
                errors.append(
                    f"Skill '{skill_name}' has invalid level '{skill['level']}'. "
                    f"Valid: {valid_lvl}"
                )

        return errors

    def _validate_wsi_quality(self, template: Dict[str, Any]) -> List[str]:
        """Validate WSI quality gates."""
        errors = []

        result = validate_wsi_quality(template, strict=False)

        if result["warnings"]:
            for warning in result["warnings"]:
                errors.append(f"WSI Quality: {warning}")

        return errors

    def _validate_no_duplicate(self, template: Dict[str, Any]) -> List[str]:
        """Check if template is a duplicate."""
        errors = []
        title_normalized = (
            template.get("title_normalized") or template.get("title", "").lower().strip()
        )
        seniority = template.get("seniority", "unknown")
        key = (title_normalized, seniority)

        if str(key) in self.duplicates:
            errors.append(f"Duplicate: same title '{title_normalized}' + seniority '{seniority}'")

        return errors

    def print_report(self) -> None:
        """Print validation report."""
        total = len(self.valid_templates) + len(self.invalid_templates)

        print("\n" + "=" * 80)
        print("TEMPLATE VALIDATION REPORT")
        print("=" * 80)

        # Summary
        print(f"\nSummary:")
        print(f"  Total templates:    {total}")
        print(f"  Valid:              {len(self.valid_templates)}")
        print(f"  Invalid:            {len(self.invalid_templates)}")
        print(f"  Duplicates found:   {len(self.duplicates)}")

        # Invalid templates details
        if self.invalid_templates:
            print(f"\n{'-' * 80}")
            print(f"INVALID TEMPLATES ({len(self.invalid_templates)}):")
            print(f"{'-' * 80}")

            for template, errors in self.invalid_templates:
                title = template.get("title", "unknown")
                category = template.get("category", "unknown")
                seniority = template.get("seniority", "unknown")
                subcategory = template.get("subcategory", "unknown")

                print(f"\n  Template: {title}")
                print(f"  Category: {category} / {subcategory}")
                print(f"  Seniority: {seniority}")
                print(f"  Errors:")
                for error in errors:
                    print(f"    - {error}")

        # Duplicates details
        if self.duplicates:
            print(f"\n{'-' * 80}")
            print(f"DUPLICATES FOUND ({len(self.duplicates)}):")
            print(f"{'-' * 80}")

            for key, templates_list in self.duplicates.items():
                print(f"\n  Key: {key}")
                for idx, tpl in enumerate(templates_list, 1):
                    print(
                        f"    {idx}. {tpl.get('title', 'unknown')} "
                        f"({tpl.get('category', '?')}/{tpl.get('subcategory', '?')})"
                    )

        print("\n" + "=" * 80)

        # Exit code message
        if len(self.invalid_templates) == 0 and len(self.duplicates) == 0:
            print("\n✓ All templates are valid!")
        else:
            errors_count = len(self.invalid_templates) + sum(
                len(t) - 1 for t in self.duplicates.values()
            )
            print(f"\n✗ Found {errors_count} validation issues!")

        print("=" * 80 + "\n")


def main():
    """Main entry point."""
    validator = TemplateValidator()
    is_valid = validator.validate_all()
    validator.print_report()

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
