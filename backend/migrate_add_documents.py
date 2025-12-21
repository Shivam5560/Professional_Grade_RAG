"""
Database migration to add documents_nexus_rag table for tracking user uploads.

This should be run after updating the models.py file.
"""

from sqlalchemy import create_engine, text
from app.config import settings
from app.db.database import Base, engine
from app.db.models import Document, User, ChatSession, ChatMessage
from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_migration():
    """Create the documents table and update database schema."""
    try:
        logger.info("starting_database_migration")
        
        # Create all tables (will skip existing ones)
        Base.metadata.create_all(bind=engine)
        
        logger.info("database_migration_completed", message="documents_nexus_rag table created")
        print("✅ Migration completed successfully!")
        print("📊 documents_nexus_rag table is ready")
        
    except Exception as e:
        logger.error("migration_failed", error=str(e))
        print(f"❌ Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    print("🚀 Running database migration...")
    print("📝 Creating documents_nexus_rag table...")
    run_migration()
