from fastapi import APIRouter, HTTPException, Header, Depends
from app.schemas.course_schemas import ChapterGenerateRequest, ChapterResponse
from app.services.llm_service import generate_chapter_content
from app.utils.supabase import supabase
from uuid import UUID

router = APIRouter(prefix="/chapters", tags=["Chapters"])

@router.post("/generate", response_model=ChapterResponse)
async def generate_chapter(request: ChapterGenerateRequest, authorization: str = Header(None)):
    """
    Generates content for a specific chapter.
    Fetches context (Title, Difficulty, etc.) from the parent Course first.
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

    # 2. Fetch Parent Course (Need Title, Difficulty, Type, TOC)
    try:
        course_response = supabase.table("courses").select("*").eq("id", str(request.course_id)).execute()
        if not course_response.data:
            raise HTTPException(status_code=404, detail="Course not found")
        
        course = course_response.data[0]
        
        # Verify Ownership
        if course["user_id"] != user_id:
             raise HTTPException(status_code=403, detail="Not authorized")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

    # 3. Extract Chapter Title from TOC
    # TOC is stored as check if it's string or dict
    toc = course["toc"] 
    # If using correct supabase client, JSONB comes back as dict.
    
    target_chapter = next((ch for ch in toc["chapters"] if ch["order"] == request.chapter_index), None)
    
    if not target_chapter:
        raise HTTPException(status_code=404, detail=f"Chapter {request.chapter_index} not found in TOC")

    chapter_title = target_chapter["title"]

    # 4. Generate Content via LLM
    try:
        content = await generate_chapter_content(
            course_title=course["title"],
            chapter_title=chapter_title,
            course_length=course.get("length", "Medium"),
            difficulty=course["difficulty"],
            course_type=course["course_type"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    # 5. Save/Update Chapter in DB
    # We might need to UPSERT if it already exists? 
    # The requirement imply lazy generation, so usually an Insert.
    # But if user regenerates?
    # Let's check if it exists first or use upsert.
    
    chapter_data = {
        "course_id": str(request.course_id),
        "chapter_index": request.chapter_index,
        "title": chapter_title,
        "content": content.model_dump(mode='json'),
        "is_generated": True
    }
    
    try:
        # Check if exists
        existing = supabase.table("chapters").select("id").eq("course_id", str(request.course_id)).eq("chapter_index", request.chapter_index).execute()
        
        if existing.data:
            # Update
            response = supabase.table("chapters").update(chapter_data).eq("id", existing.data[0]['id']).execute()
        else:
            # Insert
            response = supabase.table("chapters").insert(chapter_data).execute()
            
        if not response.data:
             raise HTTPException(status_code=500, detail="Failed to save chapter")
             
        return response.data[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Save Error: {str(e)}")

@router.get("/{course_id}/{chapter_index}", response_model=ChapterResponse)
async def get_chapter(course_id: UUID, chapter_index: int, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    token = authorization.replace("Bearer ", "")
    try:
        user_response = supabase.auth.get_user(token)
        user_id = user_response.user.id
    except Exception:
         raise HTTPException(status_code=401, detail="Invalid Authentication Token")

    try:
        # Fetch Chapter
        response = supabase.table("chapters").select("*").eq("course_id", str(course_id)).eq("chapter_index", chapter_index).execute()
        
        if not response.data:
             raise HTTPException(status_code=404, detail="Chapter not found (or not generated yet)")
        
        chapter = response.data[0]
        
        # Verify Course Ownership (Implicitly handled by RLS on 'chapters' table via 'using ( auth.uid() in (select user_id from courses...))')
        # BUT, since we are using admin client potentially? No, we need to be careful.
        # If RLS is strictly enforcing "auth.uid()", and we are using `supabase` client initialized with service key?
        # Creating a client with the user token is better.
        # For this MVP, we are reusing the global client.
        # We should manually verify ownership if we are not 100% sure the client is scoped.
        
        # Verify via course fetch
        course_check = supabase.table("courses").select("user_id").eq("id", str(course_id)).execute()
        if not course_check.data or course_check.data[0]["user_id"] != user_id:
             raise HTTPException(status_code=403, detail="Not authorized")

        return chapter

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
