from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import ApiEnvelope, AuthProvider, AuthSession, LoginRequest, LogoutBody, RefreshSession, UserProfile
from app.services.api import ApiError, created, success
from app.services.auth_service import (
    auth_providers,
    build_auth_session,
    build_user_profile,
    clear_session_cookies,
    create_session,
    get_or_create_user,
    logout_session,
    refresh_session,
    resolve_session,
)
from app.services.seed_service import ensure_seed_data

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=ApiEnvelope[AuthSession],
    summary="Login",
    description="Validate credentials, create a backend session, and return the auth session payload used by the frontend.",
)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    await ensure_seed_data(db)
    user = await get_or_create_user(db, payload.username, payload.password)
    session = await create_session(db, user)
    auth_session = build_auth_session(user, session)
    clear_session_cookies(response)
    response = success(auth_session.model_dump(), message="success")
    response.set_cookie("fluid_access_token", session.access_token, httponly=True, samesite="lax", secure=False)
    response.set_cookie("fluid_refresh_token", session.refresh_token, httponly=True, samesite="lax", secure=False)
    return response


@router.post(
    "/logout",
    response_model=ApiEnvelope[LogoutBody],
    summary="Logout",
    description="Invalidate the current session if present and clear auth cookies.",
)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    await logout_session(db, request)
    response = success({"loggedOut": True}, message="success")
    clear_session_cookies(response)
    return response


@router.get(
    "/me",
    response_model=ApiEnvelope[UserProfile],
    summary="Current User",
    description="Return the current authenticated user profile.",
)
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    return success(build_user_profile(context.user).model_dump(), message="success")


@router.api_route(
    "/refresh",
    methods=["GET", "POST"],
    response_model=ApiEnvelope[RefreshSession],
    summary="Refresh Session",
    description="Rotate the active access and refresh tokens and return the updated token pair.",
)
async def refresh(request: Request, db: AsyncSession = Depends(get_db)):
    context = await resolve_session(db, request, allow_compatibility_fallback=True)
    session = await refresh_session(db, context.session)
    response = success(
        {
            "accessToken": session.access_token,
            "refreshToken": session.refresh_token,
            "expiresInSeconds": 3600,
        },
        message="session refreshed",
    )
    response.set_cookie("fluid_access_token", session.access_token, httponly=True, samesite="lax", secure=False)
    response.set_cookie("fluid_refresh_token", session.refresh_token, httponly=True, samesite="lax", secure=False)
    return response


@router.get(
    "/providers",
    response_model=ApiEnvelope[list[AuthProvider]],
    summary="Auth Providers",
    description="Return available sign-in providers for login and profile settings screens.",
)
async def providers(request: Request, db: AsyncSession = Depends(get_db)):
    await ensure_seed_data(db)
    user = None
    try:
        context = await resolve_session(db, request, allow_compatibility_fallback=True)
        user = context.user
    except ApiError:
        user = None
    return success(await auth_providers(db, user), message="success")
