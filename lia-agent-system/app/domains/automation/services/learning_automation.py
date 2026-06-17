"""
Learning Automation Service - Automates pattern detection and skill promotion.

Runs periodically to:
1. Detect correction patterns and success profiles per company
2. Promote skills that have been confirmed enough times
3. Cache results for efficient retrieval
"""
import logging

from sqlalchemy import and_, update

from app.core.database import async_session_factory

logger = logging.getLogger(__name__)


class LearningAutomationService:
    """
    Automates learning tasks across all companies.
    
    Tasks:
    - Pattern detection (correction patterns, success profiles)
    - Skill promotion (CompanySkills with times_confirmed >= 5)
    """

    SKILL_PROMOTION_THRESHOLD = 5

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._pattern_detector = None

    def _get_pattern_detector(self):
        if self._pattern_detector is None:
            from app.shared.services.pattern_detector_service import PatternDetectorService
            self._pattern_detector = PatternDetectorService()
        return self._pattern_detector

    async def run_pattern_detection(self, company_id: str) -> dict:
        """
        Run pattern detection for a specific company.
        
        Detects correction patterns and success profiles,
        then caches the results for efficient retrieval.
        """
        detector = self._get_pattern_detector()
        results = {
            "company_id": company_id,
            "correction_patterns": 0,
            "success_profiles": 0,
            "cached": 0,
        }

        try:
            async with async_session_factory() as db:
                correction_patterns = await detector.detect_correction_patterns(
                    db=db,
                    company_id=company_id,
                )

                if correction_patterns:
                    await detector.save_correction_patterns(db, company_id, correction_patterns)
                    await detector.cache_patterns(db, company_id, correction_patterns, "correction")
                    results["correction_patterns"] = len(correction_patterns)
                    self.logger.info(
                        f"Detected {len(correction_patterns)} correction patterns for {company_id}"
                    )

                success_profiles = await detector.detect_success_profiles(
                    db=db,
                    company_id=company_id,
                )

                if success_profiles:
                    for profile in success_profiles:
                        db.add(profile)
                    await db.flush()
                    results["success_profiles"] = len(success_profiles)
                    self.logger.info(
                        f"Detected {len(success_profiles)} success profiles for {company_id}"
                    )

                results["cached"] = results["correction_patterns"] + results["success_profiles"]
                await db.commit()

        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            self.logger.error(f"Error running pattern detection for {company_id}: {e}")

        return results

    async def run_skill_promotion(self, company_id: str) -> dict:
        """
        Promote CompanySkills that have times_confirmed >= threshold.
        
        Sets is_promoted = True for skills meeting the threshold
        that haven't been promoted yet.
        """
        results = {
            "company_id": company_id,
            "skills_promoted": 0,
        }

        try:
            from lia_models.company_learning import CompanySkill

            async with async_session_factory() as db:
                stmt = (
                    update(CompanySkill)
                    .where(
                        and_(
                            CompanySkill.company_id == company_id,
                            CompanySkill.times_confirmed >= self.SKILL_PROMOTION_THRESHOLD,
                            not CompanySkill.is_promoted,
                        )
                    )
                    .values(is_promoted=True)
                )

                result = await db.execute(stmt)
                promoted_count = result.rowcount
                await db.commit()

                results["skills_promoted"] = promoted_count

                if promoted_count > 0:
                    self.logger.info(
                        f"Promoted {promoted_count} skills for company {company_id}"
                    )

        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            self.logger.error(f"Error running skill promotion for {company_id}: {e}")

        return results

    async def run_all_companies(self) -> dict:
        """
        Scan all companies and run pattern detection + skill promotion for each.
        """
        summary = {
            "companies_processed": 0,
            "total_correction_patterns": 0,
            "total_success_profiles": 0,
            "total_skills_promoted": 0,
            "errors": 0,
        }

        try:
            from sqlalchemy import text

            async with async_session_factory() as db:
                result = await db.execute(
                    text("SELECT id FROM companies WHERE is_active = TRUE")
                )
                companies = [row[0] for row in result.fetchall()]

            self.logger.info(f"Running learning automation for {len(companies)} companies")

            for company_id in companies:
                try:
                    detection_result = await self.run_pattern_detection(company_id)
                    promotion_result = await self.run_skill_promotion(company_id)

                    summary["companies_processed"] += 1
                    summary["total_correction_patterns"] += detection_result.get("correction_patterns", 0)
                    summary["total_success_profiles"] += detection_result.get("success_profiles", 0)
                    summary["total_skills_promoted"] += promotion_result.get("skills_promoted", 0)

                except Exception as e:
                    self.logger.error(f"Error processing company {company_id}: {e}")
                    summary["errors"] += 1

            self.logger.info(
                f"Learning automation complete: "
                f"{summary['companies_processed']} companies, "
                f"{summary['total_correction_patterns']} correction patterns, "
                f"{summary['total_success_profiles']} success profiles, "
                f"{summary['total_skills_promoted']} skills promoted, "
                f"{summary['errors']} errors"
            )

        except Exception as e:
            self.logger.error(f"Error in run_all_companies: {e}")

        return summary


learning_automation_service = LearningAutomationService()


def get_learning_automation_service() -> "LearningAutomationService":
    return learning_automation_service
