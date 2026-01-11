import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from app.schemas.course_schemas import CourseTOC, ChapterContent
from pydantic import ValidationError

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def generate_course_toc(topic: str, difficulty: str, course_type: str, length: str) -> CourseTOC:
    """
    Generates a Table of Contents using OpenAI with Pydantic validation.
    """
    schema = json.dumps(CourseTOC.model_json_schema(), indent=2)
    
    system_prompt = f"""
    You are a curriculum designer for a micro-learning mobile app.
    Generate a Table of Contents (TOC) for a course on "{topic}" .
    
    Settings:
    - Difficulty: {difficulty}
    - Type: {course_type} (e.g., Interview Prep, Deep Dive)
    - Length: {length}

    Requirements:
    1. STRICTLY 15 chapters.
    2. Each chapter must have a clear, descriptive title focused on a single concept.
    3. 'order' must be sequential (1-15).
    4. Output must match the required JSON schema below.

    Pedagogical constraints: 
    - The TOC must be **theoretical and concept-driven** 
    - Each chapter should represent a **core concept or principle** 
    - Chapters must be suitable for **content explanation**, not projects 
    - Avoid: 
    - Hands-on projects 
    - Setup or installation topics 
    - "Next steps", "What to learn next", or roadmap-style chapters

    REQUIRED JSON SCHEMA:
    {schema}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate TOC for '{topic}'"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        # Validate with Pydantic
        toc_data = json.loads(content)
        return CourseTOC(**toc_data)

    except Exception as e:
        print(f"Error in generate_course_toc: {e}")
        raise e

async def generate_chapter_content(course_title: str, chapter_title: str, course_length: str, difficulty: str, course_type: str) -> ChapterContent:
    """
    Generates slides and quiz for a chapter.
    """
    schema = json.dumps(ChapterContent.model_json_schema(), indent=2)

    system_prompt = f"""
    You are an expert educational content creator for a mobile micro-learning app.
    Course: "{course_title}"
    Chapter: "{chapter_title}"
    

    Content configuration:
    - Course length: {course_length}
    - small → 4-5 slides
    - medium → 6-7 slides
    - long → 9-10 slides
    - Difficulty level: {difficulty}
    - Course type: {course_type}

    Course type behavior:
    - Basics → focus on clear definitions, intuition, and foundational understanding
    - Deep Concepts → explain internal mechanisms, edge cases, and deeper reasoning
    - Interview → focus on conceptual clarity, common questions, pitfalls, and crisp explanations

    Slide design rules:
    - Each slide must explain **one core concept**
    - Content must be **theoretical and concept-driven**
    - Avoid implementation steps, setup, or framework-specific details
    - Keep explanations concise and suitable for mobile reading

    Each slide must include:
    - title
    - content (main theoretical explanation)
    - explainMore (simple clarification or elaboration)
    - deeperConcepts (advanced details or edge cases)
    - quickExamples (conceptual, not code-heavy)
    - analogy (real-world analogy)

    Quiz rules:
    - Generate exactly 5 questions
    - Questions must test **conceptual understanding**
    - Quiz difficulty must align with course difficulty and course type
    - Each question must include:
        - question
        - options (list of 4 strings)
        - correctAnswer (string, must match one of the options)
        - explanation (why the answer is correct)
    
    Output rules:
    - Output **valid JSON only**
    - Output must strictly match the ChapterContent schema

    REQUIRED JSON SCHEMA:
    {schema}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate content for chapter: {chapter_title}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        chapter_data = json.loads(content)
        return ChapterContent(**chapter_data)
        
    except Exception as e:
        print(f"Error in generate_chapter_content: {e}")
        raise e

async def chat_with_ai(message: str, context: str = "") -> dict:
    """
    Handles Doubt Clarification chat.
    """
    system_prompt = f"""
    You are a friendly and encouraging AI Tutor for a micro-learning app.
    
    Context:
    {context}
    
    Rules:
    - Keep answers concise (mobile-friendly).
    - Use analogies where possible.
    - End with a thought-provoking followup question to check understanding.
    
    Output JSON:
    {{
        "answer": "string",
        "suggested_followup": "string"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            response_format={"type": "json_object"},
            temperature=0.7 # Slight creativity for chat
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in chat_with_ai: {e}")
        raise e
