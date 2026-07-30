from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from .schemas import UserCreate, UserLogin
from .database import supabase, frontend_url

app = FastAPI(title="FastAPI Project with Supabase")

@app.get("/")
def root():
    return {"message": "Hello FastAPI"}

@app.post("/register")
def register(user: UserCreate):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    # Sign up using Supabase Auth
    try:
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "full_name": user.full_name
                }
            }
        })
        return {
            "message": "User registered successfully.",
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "full_name": response.user.user_metadata.get("full_name") if response.user.user_metadata else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
def login(user: UserLogin):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
        return {
            "message": "Login successful",
            "session": {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token
            },
            "user": {
                "id": response.session.user.id if response.session.user else None,
                "email": response.session.user.email if response.session.user else None,
                "full_name": response.session.user.user_metadata.get("full_name") if response.session.user and response.session.user.user_metadata else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid credentials or " + str(e))

@app.get("/auth/google")
def login_google():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": frontend_url
            }
        })
        # The response usually contains a url to redirect the user to
        if hasattr(response, 'url'):
            return {"authorization_url": response.url}
        else:
            return {"message": "Google Login initiated", "data": response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/logout")
def logout():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        supabase.auth.sign_out()
        return {"message": "Logout successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))