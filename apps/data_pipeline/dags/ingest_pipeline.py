"""
Airflow DAG – Data Ingestion Pipeline.

Flow:
  Raw data (MinIO) → chunk_documents → embed_chunks → store_in_qdrant

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from chunks.chunker import chunk_texts
from embeddings.embedder import embed_chunks
from storage.minio_client import list_raw_objects, read_object
from storage.qdrant_uploader import upload_to_qdrant

default_args = {
    "owner": "tranquydat",
    "email": ["tranquydat.work@gmail.com"],
    "email_on_failure": True,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="chatopsllm_ingest_pipeline",
    default_args=default_args,
    description="Ingest raw documents from MinIO → chunk → embed → store in Qdrant",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["chatopsllm", "rag", "ingestion"],
) as dag:

    def _load_raw(**context):
        """Load raw document paths from MinIO and push to XCom."""
        objects = list_raw_objects()
        context["ti"].xcom_push(key="raw_objects", value=objects)

    def _chunk(**context):
        """Read objects from MinIO and split into overlapping chunks."""
        objects = context["ti"].xcom_pull(key="raw_objects", task_ids="load_raw_data")
        all_chunks = []
        all_meta = []
        for obj_key in objects:
            text = read_object(obj_key)
            chunks, meta = chunk_texts(text, source=obj_key)
            all_chunks.extend(chunks)
            all_meta.extend(meta)
        context["ti"].xcom_push(key="chunks", value=all_chunks)
        context["ti"].xcom_push(key="chunk_meta", value=all_meta)

    def _embed(**context):
        """Embed document chunks and push vectors to XCom."""
        chunks = context["ti"].xcom_pull(key="chunks", task_ids="chunk_documents")
        vectors = embed_chunks(chunks)
        context["ti"].xcom_push(key="vectors", value=vectors)

    def _store(**context):
        """Upsert embeddings + metadata into Qdrant."""
        vectors = context["ti"].xcom_pull(key="vectors", task_ids="embed_chunks")
        meta = context["ti"].xcom_pull(key="chunk_meta", task_ids="chunk_documents")
        upload_to_qdrant(vectors=vectors, payloads=meta)

    load_raw = PythonOperator(task_id="load_raw_data", python_callable=_load_raw)
    chunk = PythonOperator(task_id="chunk_documents", python_callable=_chunk)
    embed = PythonOperator(task_id="embed_chunks", python_callable=_embed)
    store = PythonOperator(task_id="store_in_qdrant", python_callable=_store)

    load_raw >> chunk >> embed >> store
