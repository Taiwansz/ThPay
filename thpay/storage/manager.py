import os
import uuid
import hashlib
from typing import Any, Dict, Optional, Tuple

STORAGE_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage_data"
)

class StorageManager:
    """
    Gerenciador de armazenamento seguro de documentos e planilhas.
    Calcula SHA-256 real, persiste arquivos de forma isolada e registra metadados.
    """
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.environ.get("STORAGE_DIR", STORAGE_BASE_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    def compute_sha256(self, content_bytes: bytes) -> str:
        return hashlib.sha256(content_bytes).hexdigest()

    def store_file(
        self,
        content_bytes: bytes,
        original_name: str,
        company_id: str,
        entity_type: str,
        entity_id: str,
        document_type: str,
        mime_type: str,
        uploaded_by_user_id: Optional[str] = None,
        db_context: Optional[Any] = None
    ) -> Dict[str, Any]:
        file_id = f"doc-{uuid.uuid4()}"
        sha256_hash = self.compute_sha256(content_bytes)
        file_size = len(content_bytes)
        
        # Subdiretorio por tenant/empresa
        company_dir = os.path.join(self.base_dir, company_id)
        os.makedirs(company_dir, exist_ok=True)
        
        # Nome do arquivo em repouso
        storage_filename = f"{file_id}_{sha256_hash[:12]}_{original_name}"
        storage_path = os.path.join(company_dir, storage_filename)
        
        with open(storage_path, "wb") as f:
            f.write(content_bytes)
            
        doc_record = {
            "id": file_id,
            "company_id": company_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "document_type": document_type,
            "original_name": original_name,
            "storage_path": storage_path,
            "mime_type": mime_type,
            "file_size_bytes": file_size,
            "sha256_hash": sha256_hash,
            "uploaded_by_user_id": uploaded_by_user_id,
            "is_validated": 1
        }
        
        if db_context:
            db_context.execute("""
                INSERT INTO stored_documents (
                    id, company_id, entity_type, entity_id, document_type,
                    original_name, storage_path, mime_type, file_size_bytes,
                    sha256_hash, uploaded_by_user_id, is_validated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                doc_record["id"], doc_record["company_id"], doc_record["entity_type"],
                doc_record["entity_id"], doc_record["document_type"], doc_record["original_name"],
                doc_record["storage_path"], doc_record["mime_type"], doc_record["file_size_bytes"],
                doc_record["sha256_hash"], doc_record["uploaded_by_user_id"], doc_record["is_validated"]
            ))
            
        return doc_record

    def get_file(self, storage_path: str) -> Optional[bytes]:
        if os.path.exists(storage_path):
            with open(storage_path, "rb") as f:
                return f.read()
        return None
