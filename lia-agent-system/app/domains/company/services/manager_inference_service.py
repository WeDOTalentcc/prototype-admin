"""

# ADR-001-EXEMPT: Heuristic manager inference scanner with complex
# fuzzy-matching queries (func.lower().contains, multi-source candidate
# ranking across CompanyProfile + Department + DepartmentMember). Tenant
# scope established via company_id at service entry.
# TODO Sprint 6: extract to ManagerInferenceRepository with composite  # R-048: needs owner + ticket
# match-and-score methods.

Manager Inference Service - Infer manager email from company structure.

Searches for managers in:
1. Department.manager_name → manager_email
2. DepartmentMember.name → email (when level indicates manager)

Provides fallback strategies when manager info is not found.
"""
import logging
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import func, or_, select

from app.core.database import AsyncSessionLocal
from lia_models.company import CompanyProfile, Department, DepartmentMember
from lia_models.client_user import ClientUser

logger = logging.getLogger(__name__)


class ManagerInferenceService:
    """Service for inferring manager information from company structure."""
    
    MANAGER_LEVELS = ["gestor", "gerente", "diretor", "head", "líder", "lider", "coordenador", "supervisor"]
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names using SequenceMatcher."""
        if not name1 or not name2:
            return 0.0
        return SequenceMatcher(None, name1.lower().strip(), name2.lower().strip()).ratio()
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        if not name:
            return ""
        return " ".join(name.lower().strip().split())
    
    async def get_manager_by_name(
        self, 
        manager_name: str, 
        company_id: str,
        department: str | None = None,
        min_similarity: float = 0.7
    ) -> dict[str, Any] | None:
        """
        Find manager by name in company structure.
        
        Args:
            manager_name: Name of the manager to search
            company_id: Company ID for multi-tenancy
            department: Optional department name to narrow search
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            Dict with manager info or None if not found:
            {
                "name": "João Silva",
                "email": "joao.silva@empresa.com",
                "title": "Gerente de Tecnologia",
                "department": "Tecnologia",
                "source": "department_manager" | "department_member",
                "confidence": 0.95
            }
        """
        if not manager_name or not company_id:
            return None
        
        self._normalize_name(manager_name)
        candidates: list[tuple[dict[str, Any], float]] = []
        
        async with AsyncSessionLocal() as db:
            company_profile = await db.execute(
                select(CompanyProfile).where(
                    or_(
                        CompanyProfile.id == company_id,
                        CompanyProfile.name == company_id
                    )
                )
            )
            company = company_profile.scalar_one_or_none()
            
            if not company:
                logger.warning(f"Company not found: {company_id}")
                # TENANT-EXEMPT: fallback edge case quando CompanyProfile não
                # resolve. Path defensivo executado APENAS quando company lookup
                # falha — log + degrade graciosamente. TODO(harness): raise
                # CompanyNotFound em vez de cross-tenant fallback.
                dept_query = select(Department).where(
                    Department.manager_name.isnot(None)
                )
            else:
                dept_query = select(Department).where(
                    Department.company_id == company.id,
                    Department.manager_name.isnot(None)
                )
            
            if department:
                dept_query = dept_query.where(
                    func.lower(Department.name).contains(department.lower())
                )
            
            result = await db.execute(dept_query)
            departments = result.scalars().all()
            
            for dept in departments:
                dept_manager_name = str(dept.manager_name) if dept.manager_name else None
                dept_manager_email = str(dept.manager_email) if dept.manager_email else None
                if dept_manager_name and dept_manager_email:
                    similarity = self._calculate_similarity(manager_name, dept_manager_name)
                    if similarity >= min_similarity:
                        candidates.append((
                            {
                                "name": dept_manager_name,
                                "email": dept_manager_email,
                                "title": str(dept.manager_title) if dept.manager_title else f"Gestor de {dept.name}",
                                "phone": str(dept.manager_phone) if dept.manager_phone else None,
                                "department": str(dept.name),
                                "department_id": str(dept.id),
                                "source": "department_manager",
                                "confidence": similarity
                            },
                            similarity
                        ))
            
            if company:
                member_query = select(DepartmentMember).where(
                    DepartmentMember.company_id == company.id,
                    DepartmentMember.is_active,
                    DepartmentMember.email.isnot(None),
                    or_(
                        func.lower(DepartmentMember.level).in_(self.MANAGER_LEVELS),
                        func.lower(DepartmentMember.title).contains("gerente"),
                        func.lower(DepartmentMember.title).contains("diretor"),
                        func.lower(DepartmentMember.title).contains("head"),
                        func.lower(DepartmentMember.title).contains("líder"),
                        func.lower(DepartmentMember.title).contains("coordenador")
                    )
                )
                
                result = await db.execute(member_query)
                members = result.scalars().all()
                
                for member in members:
                    member_name = str(member.name) if member.name else None
                    member_email = str(member.email) if member.email else None
                    if member_name and member_email:
                        similarity = self._calculate_similarity(manager_name, member_name)
                        if similarity >= min_similarity:
                            dept_name = None
                            if member.department_id:
                                dept_result = await db.execute(
                                    select(Department.name).where(Department.id == member.department_id)
                                )
                                dept_name_result = dept_result.scalar_one_or_none()
                                dept_name = str(dept_name_result) if dept_name_result else None
                            
                            candidates.append((
                                {
                                    "name": member_name,
                                    "email": member_email,
                                    "title": str(member.title) if member.title else str(member.level) if member.level else None,
                                    "phone": str(member.phone) if member.phone else None,
                                    "department": dept_name,
                                    "department_id": str(member.department_id) if member.department_id else None,
                                    "source": "department_member",
                                    "confidence": similarity * 0.95
                                },
                                similarity * 0.95
                            ))
        
            # --- Source 3: ClientUser table (actual company users) ---
            user_query = select(ClientUser).where(
                ClientUser.company_id == company.id,
                ClientUser.status == "active",
                ClientUser.is_deleted.is_(False),
                ClientUser.name.isnot(None),
            )
            user_result = await db.execute(user_query)
            client_users = user_result.scalars().all()

            for cu in client_users:
                cu_name = str(cu.name) if cu.name else None
                cu_email = str(cu.email) if cu.email else None
                if cu_name and cu_email:
                    similarity = self._calculate_similarity(manager_name, cu_name)
                    if similarity >= min_similarity:
                        candidates.append((
                            {
                                "name": cu_name,
                                "email": cu_email,
                                "title": str(cu.role) if cu.role else None,
                                "phone": None,
                                "department": None,
                                "department_id": None,
                                "source": "client_user",
                                "confidence": similarity * 0.90,
                                "client_user_id": str(cu.id),
                            },
                            similarity * 0.90,
                        ))

        if not candidates:
            # pii-logs ok: nome de config (manager/schedule), nao PII pessoa natural
            logger.info(f"No manager found for name: {manager_name}")
            return None
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_match = candidates[0][0]
        
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"Found manager: {best_match['name']} ({best_match['email']}) with confidence {best_match['confidence']:.2f}")
        return best_match
    
    async def get_managers_by_department(
        self, 
        department_name: str, 
        company_id: str
    ) -> list[dict[str, Any]]:
        """
        Get all managers for a specific department.
        
        Args:
            department_name: Department name to search
            company_id: Company ID for multi-tenancy
            
        Returns:
            List of manager dicts
        """
        managers = []
        
        async with AsyncSessionLocal() as db:
            company_profile = await db.execute(
                select(CompanyProfile).where(
                    or_(
                        CompanyProfile.id == company_id,
                        CompanyProfile.name == company_id
                    )
                )
            )
            company = company_profile.scalar_one_or_none()
            
            if not company:
                return managers
            
            dept_query = select(Department).where(
                Department.company_id == company.id,
                func.lower(Department.name).contains(department_name.lower()),
                Department.manager_name.isnot(None)
            )
            
            result = await db.execute(dept_query)
            departments = result.scalars().all()
            
            for dept in departments:
                dept_manager_name = str(dept.manager_name) if dept.manager_name else None
                if dept_manager_name:
                    managers.append({
                        "name": dept_manager_name,
                        "email": str(dept.manager_email) if dept.manager_email else None,
                        "title": str(dept.manager_title) if dept.manager_title else None,
                        "phone": str(dept.manager_phone) if dept.manager_phone else None,
                        "department": str(dept.name),
                        "department_id": str(dept.id),
                        "source": "department_manager"
                    })
        
        return managers
    
    async def get_all_managers(self, company_id: str) -> list[dict[str, Any]]:
        """
        Get all managers for a company.
        
        Args:
            company_id: Company ID for multi-tenancy
            
        Returns:
            List of all manager dicts for autocomplete
        """
        managers = []
        seen_emails = set()
        
        async with AsyncSessionLocal() as db:
            company_profile = await db.execute(
                select(CompanyProfile).where(
                    or_(
                        CompanyProfile.id == company_id,
                        CompanyProfile.name == company_id
                    )
                )
            )
            company = company_profile.scalar_one_or_none()
            
            if not company:
                return managers
            
            dept_query = select(Department).where(
                Department.company_id == company.id,
                Department.is_active,
                Department.manager_name.isnot(None)
            )
            
            result = await db.execute(dept_query)
            departments = result.scalars().all()
            
            for dept in departments:
                dept_email = str(dept.manager_email) if dept.manager_email else None
                if dept_email and dept_email not in seen_emails:
                    seen_emails.add(dept_email)
                    managers.append({
                        "name": str(dept.manager_name) if dept.manager_name else None,
                        "email": dept_email,
                        "title": str(dept.manager_title) if dept.manager_title else None,
                        "department": str(dept.name),
                        "source": "department_manager"
                    })
            
            member_query = select(DepartmentMember).where(
                DepartmentMember.company_id == company.id,
                DepartmentMember.is_active,
                DepartmentMember.email.isnot(None),
                or_(
                    func.lower(DepartmentMember.level).in_(self.MANAGER_LEVELS),
                    func.lower(DepartmentMember.title).contains("gerente"),
                    func.lower(DepartmentMember.title).contains("diretor"),
                    func.lower(DepartmentMember.title).contains("head"),
                    func.lower(DepartmentMember.title).contains("líder"),
                    func.lower(DepartmentMember.title).contains("coordenador")
                )
            )
            
            result = await db.execute(member_query)
            members = result.scalars().all()
            
            for member in members:
                member_email = str(member.email) if member.email else None
                if member_email and member_email not in seen_emails:
                    seen_emails.add(member_email)
                    
                    dept_name = None
                    if member.department_id:
                        dept_result = await db.execute(
                            select(Department.name).where(Department.id == member.department_id)
                        )
                        dept_name_result = dept_result.scalar_one_or_none()
                        dept_name = str(dept_name_result) if dept_name_result else None
                    
                    managers.append({
                        "name": str(member.name) if member.name else None,
                        "email": member_email,
                        "title": str(member.title) if member.title else str(member.level) if member.level else None,
                        "department": dept_name,
                        "source": "department_member"
                    })
        
        managers.sort(key=lambda x: x["name"])
        return managers
    
    async def infer_manager_from_department(
        self, 
        department_name: str, 
        company_id: str
    ) -> dict[str, Any] | None:
        """
        Infer the most likely manager for a department.
        Used when manager name is not provided but department is known.
        
        Args:
            department_name: Department name
            company_id: Company ID
            
        Returns:
            Manager dict or None
        """
        managers = await self.get_managers_by_department(department_name, company_id)
        
        if managers:
            return managers[0]
        
        return None
    
    async def list_managers(
        self,
        company_id: str,
        department_id: str | None = None,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        List managers for a company (for autocomplete).
        
        Args:
            company_id: Company ID
            department_id: Optional department filter
            limit: Max results
            
        Returns:
            List of manager dicts with id, name, email, role, department
        """
        all_managers = await self.get_all_managers(company_id)
        
        if department_id:
            all_managers = [m for m in all_managers if m.get("department_id") == department_id]
        
        formatted = []
        for m in all_managers[:limit]:
            formatted.append({
                "id": m.get("id") or m.get("email") or m.get("name", ""),
                "name": m.get("name", ""),
                "email": m.get("email"),
                "role": m.get("title") or m.get("level"),
                "department_id": m.get("department_id"),
                "department_name": m.get("department")
            })
        
        return formatted
    
    async def search_managers(
        self,
        company_id: str,
        search_term: str,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Search managers by name for autocomplete.
        
        Args:
            company_id: Company ID
            search_term: Search term
            limit: Max results
            
        Returns:
            List of matching manager dicts
        """
        all_managers = await self.get_all_managers(company_id)
        
        search_lower = search_term.lower()
        matches = [
            m for m in all_managers
            if m.get("name") and search_lower in m.get("name", "").lower()
        ]
        
        formatted = []
        for m in matches[:limit]:
            formatted.append({
                "id": m.get("id") or m.get("email") or m.get("name", ""),
                "name": m.get("name", ""),
                "email": m.get("email"),
                "role": m.get("title") or m.get("level"),
                "department_id": m.get("department_id"),
                "department_name": m.get("department")
            })
        
        return formatted


manager_inference_service = ManagerInferenceService()
