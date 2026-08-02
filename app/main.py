from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from .schemas import UserCreate, UserLogin
from .database import supabase, frontend_url

app = FastAPI(title="FastAPI Project with Supabase")

@app.get("/")
def root():
    return {"message": "Hello FastAPI"}

@app.post("/register", tags=["Auth"])
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

@app.post("/login", tags=["Auth"])
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

@app.get("/auth/google", tags=["Auth"])
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

@app.post("/logout", tags=["Auth"])
def logout():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        supabase.auth.sign_out()
        return {"message": "Logout successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from .schemas import TrustedContactCreate

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_response.user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token or " + str(e))

@app.get("/trusted-contacts", tags=["Trusted Contacts"])
def get_trusted_contacts(current_user = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
        
    try:
        response = supabase.table("trusted_contacts").select("*").eq("user_id", current_user.id).execute()
        return {"data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/trusted-contacts", status_code=status.HTTP_201_CREATED, tags=["Trusted Contacts"])
def add_trusted_contact(contact: TrustedContactCreate, current_user = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        data = {
            "user_id": current_user.id,
            "name": contact.name,
            "phone_number": contact.phone_number
        }
        response = supabase.table("trusted_contacts").insert(data).execute()
        return {"message": "Trusted contact added successfully", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/trusted-contacts/{contact_id}", tags=["Trusted Contacts"])
def remove_trusted_contact(contact_id: int, current_user = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
        
    try:
        response = supabase.table("trusted_contacts").delete().eq("id", contact_id).eq("user_id", current_user.id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Trusted contact not found or not authorized to delete")
            
        return {"message": "Trusted contact removed successfully", "data": response.data}
    except Exception as e:
        if type(e) is HTTPException:
            raise e
        raise HTTPException(status_code=400, detail=str(e))