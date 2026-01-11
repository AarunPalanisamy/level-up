from fastapi import APIRouter, HTTPException, Header, Depends
from app.schemas.user_schemas import ProfileCreate, ProfileResponse, ProfileUpdate
from app.utils.supabase import supabase
from uuid import UUID

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/", response_model=ProfileResponse)
async def get_profile(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    token = authorization.replace("Bearer ", "")
    try:
        user_response = supabase.auth.get_user(token)
        user_id = user_response.user.id
    except Exception:
         raise HTTPException(status_code=401, detail="Invalid Authentication Token")
         
    try:
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        
        if not response.data:
            # If profile doesn't exist (unlikely with triggers, but possible), return 404 or create?
            # API flow says "create profile else go to home page".
            # If trigger failed, we might want to return 404.
            raise HTTPException(status_code=404, detail="Profile not found")
            
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/", response_model=ProfileResponse)
async def update_profile(profile_update: ProfileUpdate, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    token = authorization.replace("Bearer ", "")
    try:
        user_response = supabase.auth.get_user(token)
        user_id = user_response.user.id
    except Exception:
         raise HTTPException(status_code=401, detail="Invalid Authentication Token")
    
    # Filter out None values
    update_data = {k: v for k, v in profile_update.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        response = supabase.table("profiles").update(update_data).eq("id", user_id).execute()
        
        if not response.data:
             raise HTTPException(status_code=500, detail="Failed to update profile")
             
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
