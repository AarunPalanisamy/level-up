from fastapi import APIRouter, HTTPException, Header, Depends
from app.schemas.course_schemas import CourseGenerateRequest, CourseResponse
from app.services.llm_service import generate_course_toc
from app.utils.supabase import supabase
from uuid import UUID

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("/generate", response_model=CourseResponse)
async def generate_course(request: CourseGenerateRequest, authorization: str = Header(None)):
    """
    Generates a generic Course TOC via LLM, then saves it to DB.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    token = authorization.replace("Bearer ", "")
    
    # 1. Verify User
    try:
        user_response = supabase.auth.get_user(token)
        user_id = user_response.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Authentication Token")

    # 2. Generate TOC via LLM
    try:
        toc = await generate_course_toc(
            request.topic,
            request.difficulty,
            request.course_type,
            request.length
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation Failed: {str(e)}")

    # 3. Save to Supabase
    course_data = {
        "user_id": user_id,
        "title": toc.title,
        "description": toc.description,
        "difficulty": request.difficulty,
        "course_type": request.course_type,
        "length": request.length,
        "toc": toc.model_dump(mode='json') 
    }

    try:
        # Note: We insert into 'courses' table. 
        # RLS is enabled, but since we are using the admin client (supabase), 
        # we can insert for any user if we set the ID manually, 
        # OR we should ideally create a scoped client.
        # For this MVP, we insert with the admin client but strictly use the verified user_id.
        response = supabase.table("courses").insert(course_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Database Insert Failed")
            
        return response.data[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: UUID, authorization: str = Header(None)):
    """
    Fetches course details by ID.
    Enforces RLS via Policy (or manual check if using admin client).
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        user_response = supabase.auth.get_user(token)
        user_id = user_response.user.id
    except Exception:
         raise HTTPException(status_code=401, detail="Invalid Authentication Token")

    try:
        response = supabase.table("courses").select("*").eq("id", str(course_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Course not found")
            
        course = response.data[0]
        
        # Security Check: Ensure user owns the course (If RLS wasn't enough)
        if course["user_id"] != user_id:
             raise HTTPException(status_code=403, detail="Not authorized to view this course")
             
        return course

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
