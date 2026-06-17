"""Mint a JWT for smoke testing — uses a real user from the DB.

Outputs the JWT to stdout, plus the company_id, on separate lines for shell
parsing.
"""
import asyncio
import sys
from app.core.database import AsyncSessionLocal
from app.auth.security import create_access_token
from sqlalchemy import text


async def go():
    async with AsyncSessionLocal() as db:
        # Try to find an active user with non-null company_id
        result = await db.execute(text(
            "SELECT id::text, company_id::text, role "
            "FROM users WHERE is_active = true AND company_id IS NOT NULL "
            "ORDER BY created_at DESC LIMIT 1"
        ))
        row = result.fetchone()
        if not row:
            print("ERROR: no active user with company_id found", file=sys.stderr)
            sys.exit(2)
        user_id, company_id, role = row
        token = create_access_token(
            subject=user_id,
            role=role or "recruiter",
            company_id=company_id,
        )
        print(token)
        print(f"USER_ID={user_id}", file=sys.stderr)
        print(f"COMPANY_ID={company_id}", file=sys.stderr)
        print(f"ROLE={role}", file=sys.stderr)

asyncio.run(go())
