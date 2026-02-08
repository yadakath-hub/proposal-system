"""
AI Persona CRUD endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.ai_persona import AiPersona
from app.models.user import User
from app.schemas.ai import PersonaCreate, PersonaResponse, PersonaUpdate
from app.services.auth_service import get_current_user

router = APIRouter()


async def _get_persona_or_404(persona_id: uuid.UUID, db: AsyncSession) -> AiPersona:
    result = await db.execute(select(AiPersona).where(AiPersona.id == persona_id))
    persona = result.scalar_one_or_none()
    if persona is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "角色不存在")
    return persona


@router.get("/", response_model=list[PersonaResponse])
async def list_personas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AiPersona)
        .where(AiPersona.is_active == True)
        .order_by(AiPersona.is_system.desc(), AiPersona.name)
    )
    return [PersonaResponse.model_validate(p) for p in result.scalars().all()]


@router.post("/", response_model=PersonaResponse, status_code=201)
async def create_persona(
    body: PersonaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    persona = AiPersona(
        name=body.name,
        description=body.description,
        system_prompt=body.system_prompt,
        preferred_model=body.preferred_model,
        parameters=body.parameters or {},
        default_max_tokens=body.default_max_tokens,
        is_active=body.is_active,
        created_by=current_user.id,
    )
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    return PersonaResponse.model_validate(persona)


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    persona = await _get_persona_or_404(persona_id, db)
    return PersonaResponse.model_validate(persona)


@router.put("/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: uuid.UUID,
    body: PersonaUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    persona = await _get_persona_or_404(persona_id, db)
    if persona.is_system and current_user.role != "Admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "系統角色只有管理員可修改")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(persona, field, value)
    await db.commit()
    await db.refresh(persona)
    return PersonaResponse.model_validate(persona)


@router.delete("/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    persona = await _get_persona_or_404(persona_id, db)
    if persona.is_system:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "系統角色無法刪除")
    await db.delete(persona)
    await db.commit()
