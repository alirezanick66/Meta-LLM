import sys
from pathlib import Path

# اضافه کردن مسیر پروژه
sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent.parent ) )

from backend.app.api.dependencies import get_qdrant_manager
from backend.app.core.database import SessionLocal
from backend.app.db.postgres import PostgresManager

with SessionLocal() as db:
    pg = PostgresManager( db )
    doc = pg.get_document_by_filename( "enghelab.md" )
    qdrant = get_qdrant_manager()
    if qdrant.client is not None:
        qdrant.client.delete_collection( qdrant.collection_name )
    print( "✅ کل collection حذف شد" )
