{%- if cookiecutter.enable_rag and cookiecutter.use_celery and cookiecutter.enable_conversation_persistence %}
"""RAG ingestion Celery task — processes documents asynchronously."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, soft_time_limit=300, time_limit=360)
def ingest_document_task(
    self,
    rag_document_id: str,
    collection_name: str,
    filepath: str,
    source_path: str,
    replace: bool = False,
) -> dict[str, Any]:
    """Process a document: parse, chunk, embed, store in vector DB."""
    logger.info(f"Starting ingestion: {source_path} -> {collection_name}")

    try:
        result = asyncio.run(
            _run_ingestion(rag_document_id, collection_name, filepath, source_path, replace)
        )
        return result
    except Exception as exc:
        logger.error(f"Ingestion failed: {exc}")
        asyncio.run(_update_status(rag_document_id, "error", error_message=str(exc)))
        raise self.retry(exc=exc, countdown=30)


async def _run_ingestion(
    rag_document_id: str,
    collection_name: str,
    filepath: str,
    source_path: str,
    replace: bool,
) -> dict[str, Any]:
    from datetime import UTC, datetime
    from uuid import UUID

    from app.core.config import settings
    from app.db.session import get_db_context
    from app.db.models.rag_document import RAGDocument
    from app.rag.documents import DocumentProcessor
    from app.rag.embeddings import EmbeddingService
    from app.rag.ingestion import IngestionService
{%- if cookiecutter.use_milvus %}
    from app.rag.vectorstore import MilvusVectorStore as VectorStore
{%- elif cookiecutter.use_qdrant %}
    from app.rag.vectorstore import QdrantVectorStore as VectorStore
{%- elif cookiecutter.use_chromadb %}
    from app.rag.vectorstore import ChromaVectorStore as VectorStore
{%- elif cookiecutter.use_pgvector %}
    from app.rag.vectorstore import PgVectorStore as VectorStore
{%- endif %}

    rag_settings = settings.rag
    embed_service = EmbeddingService(settings=rag_settings)
    vector_store = VectorStore(settings=rag_settings, embedding_service=embed_service)
    processor = DocumentProcessor(settings=rag_settings)
    ingestion_service = IngestionService(processor=processor, vector_store=vector_store)

    file_path = Path(filepath)

    try:
        result = await ingestion_service.ingest_file(
            filepath=file_path, collection_name=collection_name, replace=replace, source_path=source_path,
        )

        async with get_db_context() as db:
            rag_doc = await db.get(RAGDocument, UUID(rag_document_id))
            if rag_doc:
                rag_doc.status = "done"
                rag_doc.vector_document_id = result.document_id
                rag_doc.completed_at = datetime.now(UTC)
                await db.commit()

        await _notify_ws(rag_document_id, "done", source_path)
        logger.info(f"Ingestion complete: {source_path}")
        return {"status": "done", "document_id": result.document_id, "filename": source_path}

    except Exception as e:
        await _update_status(rag_document_id, "error", error_message=str(e))
        raise


async def _update_status(rag_document_id: str, status: str, error_message: str | None = None):
    from datetime import UTC, datetime
    from uuid import UUID
    from app.db.session import get_db_context
    from app.db.models.rag_document import RAGDocument

    try:
        async with get_db_context() as db:
            rag_doc = await db.get(RAGDocument, UUID(rag_document_id))
            if rag_doc:
                rag_doc.status = status
                rag_doc.error_message = error_message
                if status in ("done", "error"):
                    rag_doc.completed_at = datetime.now(UTC)
                await db.commit()
    except Exception as e:
        logger.warning(f"Failed to update RAGDocument status: {e}")


async def _notify_ws(rag_document_id: str, status: str, filename: str):
    try:
        import json
        import redis.asyncio as aioredis
        from app.core.config import settings
        r = aioredis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
        await r.publish("rag_status", json.dumps({
            "document_id": rag_document_id, "status": status, "filename": filename,
        }))
        await r.aclose()
    except Exception as e:
        logger.warning(f"Failed to send WS notification: {e}")


@shared_task(bind=True, max_retries=1, soft_time_limit=600, time_limit=720)
def sync_collection_task(self, sync_log_id: str, source: str, collection_name: str, mode: str, path: str) -> dict[str, Any]:
    """Sync a collection from a local directory. Respects sync mode."""
    logger.info(f"Starting sync: {source} -> {collection_name} (mode={mode})")
    try:
        result = asyncio.run(_run_sync(sync_log_id, source, collection_name, mode, path))
        return result
    except Exception as exc:
        logger.error(f"Sync failed: {exc}")
        asyncio.run(_update_sync_log(sync_log_id, "error", error_message=str(exc)))
        raise self.retry(exc=exc, countdown=60)


async def _run_sync(sync_log_id: str, source: str, collection_name: str, mode: str, path: str) -> dict[str, Any]:
    import hashlib
    from datetime import UTC, datetime
    from uuid import UUID
    from app.core.config import settings
    from app.db.session import get_db_context
    from app.db.models.sync_log import SyncLog
    from app.db.models.rag_document import RAGDocument
    from app.rag.documents import DocumentProcessor
    from app.rag.embeddings import EmbeddingService
    from app.rag.ingestion import IngestionService
    from app.rag.config import DocumentExtensions
{%- if cookiecutter.use_milvus %}
    from app.rag.vectorstore import MilvusVectorStore as VectorStore
{%- elif cookiecutter.use_qdrant %}
    from app.rag.vectorstore import QdrantVectorStore as VectorStore
{%- elif cookiecutter.use_chromadb %}
    from app.rag.vectorstore import ChromaVectorStore as VectorStore
{%- elif cookiecutter.use_pgvector %}
    from app.rag.vectorstore import PgVectorStore as VectorStore
{%- endif %}

    rag_settings = settings.rag
    embed_service = EmbeddingService(settings=rag_settings)
    vector_store = VectorStore(settings=rag_settings, embedding_service=embed_service)
    processor = DocumentProcessor(settings=rag_settings)
    ingestion_service = IngestionService(processor=processor, vector_store=vector_store)

    target_path = Path(path).resolve()
    if not target_path.exists():
        await _update_sync_log(sync_log_id, "error", error_message=f"Path not found: {path}")
        return {"status": "error", "message": f"Path not found: {path}"}

    if target_path.is_file():
        files = [target_path]
    else:
        files = [f for f in target_path.rglob("*") if f.is_file() and not f.name.startswith(".")]

    allowed = {ext.value for ext in DocumentExtensions}
    files = [f for f in files if f.suffix.lower() in allowed]

    ingested = updated = skipped = failed = 0

    for filepath in files:
        source_path = str(filepath.resolve())
        if mode in ("new_only", "update_only"):
            existing_id = await ingestion_service.find_existing(collection_name, source_path)
            if mode == "new_only" and existing_id:
                skipped += 1
                continue
            if mode == "update_only":
                if not existing_id:
                    skipped += 1
                    continue
                file_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
                existing_hash = await ingestion_service.get_existing_hash(collection_name, source_path)
                if existing_hash and file_hash == existing_hash:
                    skipped += 1
                    continue

        try:
            result = await ingestion_service.ingest_file(filepath=filepath, collection_name=collection_name, replace=True)
            if result.status.value == "done":
                if result.message and "replaced" in result.message:
                    updated += 1
                else:
                    ingested += 1
                async with get_db_context() as db:
                    rag_doc = RAGDocument(collection_name=collection_name, filename=filepath.name,
                        filesize=filepath.stat().st_size, filetype=filepath.suffix.lstrip(".").lower(),
                        status="done", vector_document_id=result.document_id, completed_at=datetime.now(UTC))
                    db.add(rag_doc)
                    await db.commit()
            else:
                failed += 1
        except Exception as e:
            logger.warning(f"Sync file error {filepath.name}: {e}")
            failed += 1

    async with get_db_context() as db:
        sync_log = await db.get(SyncLog, UUID(sync_log_id))
        if sync_log:
            sync_log.status = "done" if failed == 0 else "error"
            sync_log.total_files = len(files)
            sync_log.ingested = ingested
            sync_log.updated = updated
            sync_log.skipped = skipped
            sync_log.failed = failed
            sync_log.completed_at = datetime.now(UTC)
            await db.commit()

    return {"status": "done", "ingested": ingested, "updated": updated, "skipped": skipped, "failed": failed}


async def _update_sync_log(sync_log_id: str, status: str, error_message: str | None = None):
    from datetime import UTC, datetime
    from uuid import UUID
    from app.db.session import get_db_context
    from app.db.models.sync_log import SyncLog
    try:
        async with get_db_context() as db:
            sync_log = await db.get(SyncLog, UUID(sync_log_id))
            if sync_log:
                sync_log.status = status
                sync_log.error_message = error_message
                if status in ("done", "error"):
                    sync_log.completed_at = datetime.now(UTC)
                await db.commit()
    except Exception as e:
        logger.warning(f"Failed to update SyncLog: {e}")
{%- endif %}
