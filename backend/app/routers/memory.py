"""
Memory router — exposes long-term memory for the Memory Viewer UI.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/")
async def get_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all memories AroMi has built about this user.
    Includes confidence-decayed values for transparency.
    """
    return {
        "memories": MemoryService.get_all_memories(db, current_user.id),
        "context": MemoryService.get_user_memory_context(db, current_user.id)
    }


@router.post("/extract")
async def trigger_memory_extraction(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger behavioral memory extraction from workout history.
    Normally runs automatically after each workout completion.
    """
    count = MemoryService.extract_memories_from_behavior(db, current_user.id)
    return {
        "message": f"Extracted {count} memory entries from behavior patterns",
        "count": count
    }


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allow user to remove a specific memory (GDPR-style control)."""
    from app.models.memory import UserMemory
    memory = db.query(UserMemory).filter(
        UserMemory.id == memory_id,
        UserMemory.user_id == current_user.id
    ).first()
    if not memory:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Memory not found")
    db.delete(memory)
    db.commit()
    return {"message": "Memory deleted"}
