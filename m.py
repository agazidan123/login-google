from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security.oauth2 import OAuth2PasswordBearer
from starlette.requests import Request
from starlette.config import Config
from urllib.parse import urlencode
import httpx
import os

app = FastAPI()

# Load environment variables
config = Config(".env")
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/auth/google/callback"

@app.get("/auth/google")
def auth_google():
    # Google OAuth 2.0 endpoint for requesting an authorization code
    google_auth_endpoint = "https://accounts.google.com/o/oauth2/auth"

    # Query parameters for the request
    query_params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": REDIRECT_URI,
        "access_type": "offline",
        "prompt": "consent"
    }

    # Redirect the user to the Google OAuth 2.0 authorization endpoint
    return RedirectResponse(url=f"{google_auth_endpoint}?{urlencode(query_params)}")

@app.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not found")

    token_url = "https://oauth2.googleapis.com/token"

    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        token_json = token_response.json()

    if "error" in token_json:
        raise HTTPException(status_code=400, detail=token_json["error"])

    access_token = token_json.get("access_token")

    # Use the access token to get user info from Google
    user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(user_info_url, headers=headers)
        user_info = user_info_response.json()

    return user_info  # Return user info obtained from Google


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
