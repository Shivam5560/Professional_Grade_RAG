#!/usr/bin/env python3
"""Clear Nexus embedding cache to force re-indexing with new chunk size."""

import os
import sys

# Set minimal env to allow imports
os.environ.setdefault('GROQ_API_KEY', 'temp')

try:
    from sqlalchemy import create_engine, text
    from app.config import settings
    
    # Build connection URL
    url = f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    
    engine = create_engine(url)
    
    with engine.connect() as conn:
        # Clear specific resume from logs
        result = conn.execute(
            text("DELETE FROM nexus_resume_embeddings WHERE metadata_->>'resume_id' = 'SHIVAM-20260210-GUBM'")
        )
        conn.commit()
        print(f"✅ Cleared {result.rowcount} embedding nodes for SHIVAM-20260210-GUBM")
        
        # Check total count
        count = conn.execute(text("SELECT COUNT(*) FROM nexus_resume_embeddings")).scalar()
        print(f"📊 Total nexus embeddings remaining: {count}")
        print("\n✅ Done! Restart backend and try analysis again.")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nAlternative: Delete the resume in Nexus UI and re-upload.")
    sys.exit(1)
