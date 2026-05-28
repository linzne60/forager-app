from authlib.integrations.httpx_client import AsyncOAuth2Client

from app.config import settings

PROVIDERS: dict[str, dict] = {
    "google": {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "authorize_url": "https://accounts.google.com/o/oauth2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
        "map": {"id": "sub", "email": "email", "name": "name"}
    },
    "github": {
        "client_id": settings.github_client_id,
        "client_secret": settings.github_client_secret,
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "user:email",
        "map": {"id": "id", "email": "email", "name": "name"}
    },
}

def get_redirect_uri(provider: str) -> str:
    base = settings.frontend_url if settings.debug else settings.backend_url
    return f"{base}/api/auth/oauth/{provider}/callback"

async def get_userinfo(provider: str, code: str) -> dict:
    config = PROVIDERS[provider]
    redirect_uri = get_redirect_uri(provider)

    async with AsyncOAuth2Client(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        redirect_uri=redirect_uri,
    ) as client:
        await client.fetch_token(config["token_url"], code=code)
        response = await client.get(config["userinfo_url"])
        raw_data = response.json()
        
        mapping = config["map"]
        raw_id = raw_data.get(mapping["id"])

        return {
            "oauth_id": str(raw_id) if raw_id else None,
            "email": raw_data.get(mapping["email"]),
            "display_name": raw_data.get(mapping["name"]) or raw_data.get("login") or "User"
        }