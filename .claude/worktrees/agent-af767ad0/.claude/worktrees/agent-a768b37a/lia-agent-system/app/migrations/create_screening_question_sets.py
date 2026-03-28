"""
Migration to create screening_question_sets table.

This migration creates the screening_question_sets table with support for
storing question set versions, snapshots, and metadata for job screening.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def run_migration(db: AsyncSession):
    """
    Create the screening_question_sets table if it doesn't exist.
    
    Args:
        db: AsyncSession database connection
    """
    try:
        # Create the table with IF NOT EXISTS
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS screening_question_sets (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                job_vacancy_id VARCHAR(255) NOT NULL,
                version INTEGER NOT NULL,
                questions_hash VARCHAR(64) NOT NULL,
                questions_snapshot JSONB NOT NULL,
                questions_count INTEGER NOT NULL,
                block_distribution JSONB,
                metadata JSONB,
                source VARCHAR(50) NOT NULL,
                created_by VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                difficulty_coefficient FLOAT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create indexes
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sqs_job_vacancy_id 
            ON screening_question_sets(job_vacancy_id)
        """))
        
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sqs_job_vacancy_version 
            ON screening_question_sets(job_vacancy_id, version)
        """))
        
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sqs_job_vacancy_active 
            ON screening_question_sets(job_vacancy_id, is_active)
        """))
        
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sqs_created_at 
            ON screening_question_sets(created_at)
        """))
        
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        raise e
