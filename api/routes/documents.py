# api/routes/documents.py
from fastapi import APIRouter, HTTPException
from api.models import DocumentResponse
from datetime import datetime, timezone

router = APIRouter()

@router.get("/{case_id}", tags=["Documents"])
async def get_documents(case_id: str):
    """Get all generated documents for a case."""
    from api.routes.cases import _case_store
    case = _case_store.get(case_id.upper())
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return [
        DocumentResponse(
            doc_type=d.doc_type, title=d.title,
            content=d.content, citations=d.citations,
            generated_at=d.generated_at,
        ) for d in case.generated_documents
    ]

@router.get("/{case_id}/{doc_type}", tags=["Documents"])
async def get_document_by_type(case_id: str, doc_type: str):
    """Get a specific document type for a case."""
    from api.routes.cases import _case_store
    case = _case_store.get(case_id.upper())
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    doc = next((d for d in case.generated_documents if d.doc_type == doc_type), None)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document type {doc_type} not found for case {case_id}")
    return DocumentResponse(
        doc_type=doc.doc_type, title=doc.title,
        content=doc.content, citations=doc.citations,
        generated_at=doc.generated_at,
    )
