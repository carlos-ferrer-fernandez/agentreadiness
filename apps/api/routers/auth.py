"""
Auth Router

API endpoints for authentication and user management.
Supports GitHub OAuth and JWT token-based auth.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import logging

from database import get_db
from models import User, Organization
from auth import create_access_token, get_current_user
from config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


class GitHubAuthRequest(BaseModel):
    code: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    github_id: Optional[str] = None
    organization_id: str

    model_config = {"from_attributes": True}


class OrganizationResponse(BaseModel):
    id: str
    name: str
    github_id: Optional[str] = None
    tier: str

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserResponse
    organization: Optional[OrganizationResponse] = None
    token: str
    is_new_user: bool


@router.post("/github", response_model=AuthResponse)
async def github_auth(request: GitHubAuthRequest, db: AsyncSession = Depends(get_db)):
    """Handle GitHub OAuth callback. Exchange code for token, create/get user."""

    github_user = await _get_github_user(request.code)
    github_id = str(github_user["id"])
    email = github_user.get("email") or f"{github_user['login']}@users.noreply.github.com"
    name = github_user.get("name") or github_user["login"]

    # Check if user already exists
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if user:
        result = await db.execute(
            select(Organization).where(Organization.id == user.organization_id)
        )
        org = result.scalar_one_or_none()
        token = create_access_token(user.id, user.email)
        return AuthResponse(
            user=UserResponse.model_validate(user),
            organization=OrganizationResponse.model_validate(org) if org else None,
            token=token,
            is_new_user=False,
        )

    # New user: create organization + user
    org = Organization(name=f"{name}'s Org", github_id=github_id, tier="free")
    db.add(org)
    await db.flush()

    user = User(
        email=email,
        name=name,
        github_id=github_id,
        organization_id=org.id,
    )
    db.add(user)
    await db.flush()

    token = create_access_token(user.id, user.email)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        organization=OrganizationResponse.model_validate(org),
        token=token,
        is_new_user=True,
    )


@router.get("/me")
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current authenticated user and their organization."""
    result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = result.scalar_one_or_none()

    return {
        "user": UserResponse.model_validate(user),
        "organization": OrganizationResponse.model_validate(org) if org else None,
    }


@router.post("/logout")
async def logout():
    """Logout. Client should discard the JWT token."""
    return {"message": "Logged out successfully"}


async def _get_github_user(code: str) -> dict:
    """Exchange GitHub OAuth code for access token, then fetch user profile."""
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.",
        )

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            logger.error(f"GitHub token exchange failed: {token_response.text}")
            raise HTTPException(status_code=400, detail="GitHub authentication failed")

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            error = token_data.get("error_description", "Unknown error")
            raise HTTPException(status_code=400, detail=f"GitHub auth error: {error}")

        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )

        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub user profile")

        return user_response.json()
