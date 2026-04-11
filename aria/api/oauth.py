# filename: api/oauth.py
# purpose: OAuth connect and callback API endpoints.
# dependencies: fastapi, services.oauth

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from services.oauth import OAuthService

router = APIRouter()


@router.get("/connect")
async def oauth_connect(request: Request, platform: str = Query(...), company_id: str = Query(...)):
    service: OAuthService = request.app.state.oauth_service
    try:
        url = await service.get_authorization_url(company_id=company_id, platform=platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(url=url, status_code=307)


@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    platform: str = Query(...),
) -> dict[str, str]:
    service: OAuthService = request.app.state.oauth_service
    try:
        return await service.handle_callback(code=code, state=state, platform=platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
