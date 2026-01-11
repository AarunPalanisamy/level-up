from fastapi import APIRouter, HTTPException, Header, Depends
from app.schemas.chat_schemas import ChatRequest, ChatResponse
from app.services.llm_service import chat_with_ai
from app.utils.supabase import supabase

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    # Authenticate (Just to be safe, though chat doesn't access DB directly, 
    # we usually want only logged-in users to use LLM quota)
    token = authorization.replace("Bearer ", "")
    try:
        supabase.auth.get_user(token)
    except Exception:
         raise HTTPException(status_code=401, detail="Invalid Authentication Token")
    
    # Build Context
    context_parts = []
    
    if request.course_id:
        try:
            course = supabase.table("courses").select("title, description, difficulty").eq("id", request.course_id).execute()
            if course.data:
                c = course.data[0]
                context_parts.append(f"Course: {c['title']} ({c['difficulty']}) - {c['description']}")
        except:
            pass # Ignore context errors
            
    if request.chapter_id:
        try:
            # We assume chapter_id matches the chapters table
            # But wait, request.chapter_id might be the ID, or index? 
            # In schemas we defined it as string (Optional[str]), likely the UUID.
            chapter = supabase.table("chapters").select("title, content").eq("id", request.chapter_id).execute()
            if chapter.data:
                ch = chapter.data[0]
                context_parts.append(f"Current Chapter: {ch['title']}")
                # We could add content summary, but 'content' JSON might be huge. 
                # Let's just add title for now to save tokens.
        except:
            pass

    full_context = "\n".join(context_parts)
    
    try:
        response = await chat_with_ai(request.message, full_context)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
