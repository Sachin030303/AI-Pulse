"""Read-only task planning preview endpoint."""

import httpx

from fastapi import APIRouter, HTTPException

from app.db.session import SessionLocal
from app.schemas.task_planning import (
    TaskPlanRequest,
    TaskPlanResponse,
)
from app.services.task_planning_service import generate_task_plan


router = APIRouter()


@router.post("/preview", response_model=TaskPlanResponse)
def preview_task_plan(payload: TaskPlanRequest):
    try:
        with SessionLocal() as db:
            return generate_task_plan(db, payload)

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        ) from error

    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=503,
            detail="Task planning generation failed",
        ) from error

# Explicit task approval endpoint.
from fastapi import Request
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.task_plan_approval import (
    TaskPlanApplyRequest,
    TaskPlanApplyResponse,
)
from app.services.task_plan_approval_service import (
    DuplicateTaskError,
    apply_task_plan,
)


@router.post("/apply", response_model=TaskPlanApplyResponse)
def apply_approved_task_plan(
    payload: TaskPlanApplyRequest,
    request: Request,
):
    # Development-only restriction.
    # Production requires real authentication and authorization.
    if request.client is None or request.client.host not in (
        "127.0.0.1",
        "::1",
    ):
        raise HTTPException(
            status_code=403,
            detail="Local development access only",
        )

    try:
        with SessionLocal() as db:
            return apply_task_plan(db, payload)

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        ) from error

    except DuplicateTaskError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="Database task creation failed",
        ) from error
