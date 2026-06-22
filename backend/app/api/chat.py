"""Chat API - AI conversation with security enforcement."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime
from app.database import get_db
from app.models.chat_session import ChatSession
from app.schemas.agents import ChatMessage, ChatResponse
from app.security.prompt_injection import detect_prompt_injection, get_injection_response
from app.security.input_validator import validate_input
from app.security.output_validator import validate_ai_output
from app.security.audit import log_prompt_injection
from app.agents.orchestrator import Orchestrator

router = APIRouter()
orchestrator = Orchestrator()


@router.post("/message", response_model=ChatResponse)
async def send_message(data: ChatMessage, db: Session = Depends(get_db)):
    """Send a message to the AI system with full security pipeline."""

    # Step 1: Input validation
    is_valid, error, sanitized = validate_input(data.message)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Step 2: Prompt injection detection
    is_injection, findings = detect_prompt_injection(sanitized)
    if is_injection:
        # Log the attempt
        log_prompt_injection(db, findings, data.message)

        # Get/create session
        session = _get_or_create_session(db, data.session_id, data.session_type)
        _add_message(session, "user", sanitized)
        block_response = get_injection_response(findings)
        _add_message(session, "assistant", block_response, agent="security_guard")
        db.commit()

        return ChatResponse(
            response=block_response,
            agent_used="security_guard",
            confidence=0.95,
            session_id=session.id,
            security_validated=False,
            blocked=True,
            block_reason=findings[0]["description"],
        )

    # Step 3: Get/create session
    session = _get_or_create_session(db, data.session_id, data.session_type)
    _add_message(session, "user", sanitized)

    # Step 4: Process through agent orchestrator
    chat_history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in (session.messages[:-1] or [])])
    result = orchestrator.handle_chat_message(sanitized, data.session_type, db, chat_history_str)

    # Step 5: Output validation
    response_text = result.get("response", "")
    is_valid_output, validated_text, warnings = validate_ai_output(
        response_text, response_type=data.session_type
    )

    # Step 6: Save assistant response
    _add_message(session, "assistant", validated_text, agent=result.get("agent_used"))
    db.commit()

    return ChatResponse(
        response=validated_text,
        agent_used=result.get("agent_used", "orchestrator"),
        confidence=result.get("confidence"),
        actions_taken=result.get("actions_taken"),
        session_id=session.id,
        security_validated=is_valid_output,
    )


@router.get("/sessions")
async def list_sessions(db: Session = Depends(get_db)):
    """List all chat sessions."""
    sessions = db.query(ChatSession).filter(ChatSession.is_active == 1).order_by(
        ChatSession.updated_at.desc()
    ).limit(50).all()

    return [
        {
            "id": s.id,
            "title": s.title,
            "session_type": s.session_type,
            "agent_used": s.agent_used,
            "message_count": len(s.messages or []),
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session(session_id: int, db: Session = Depends(get_db)):
    """Get a specific chat session with messages."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": session.id,
        "title": session.title,
        "session_type": session.session_type,
        "messages": session.messages or [],
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


def _get_or_create_session(db: Session, session_id: int = None, session_type: str = "general") -> ChatSession:
    if session_id:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            return session

    session = ChatSession(
        session_type=session_type,
        title=f"{'Security' if session_type == 'security' else 'IT Support' if session_type == 'it_support' else 'General'} Chat",
        messages=[],
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _add_message(session: ChatSession, role: str, content: str, agent: str = None):
    messages = list(session.messages or [])
    messages.append({
        "role": role,
        "content": content,
        "agent": agent,
        "timestamp": datetime.utcnow().isoformat(),
    })
    session.messages = messages
    flag_modified(session, "messages")
    if agent:
        session.agent_used = agent
