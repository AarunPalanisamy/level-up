import json
import os
import sys

# Configuration: File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(BASE_DIR, "course_toc_schema.json")
CONTENT_RULES_PATH = os.path.join(BASE_DIR, "toc_content_rules_topics.md")
STYLE_GUIDELINES_PATH = os.path.join(BASE_DIR, "toc_style_guidelines.md")

def load_file_content(path):
    """Reads content from a file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {path}")
        sys.exit(1)

def validate_toc(toc_data):
    """
    Validates the generated TOC against the schema and specific business rules.
    Raises ValueError if validation fails.
    """
    
    # 1. Validate Root Fields
    required_root = ["title", "description", "chapters"]
    for field in required_root:
        if field not in toc_data:
            raise ValueError(f"Missing root field: {field}")
            
    # 2. Validate Root Types and Constraints
    if not isinstance(toc_data["title"], str) or len(toc_data["title"]) > 80:
        raise ValueError("Root 'title' must be a string <= 80 chars.")
    if not isinstance(toc_data["description"], str) or len(toc_data["description"]) > 200:
        raise ValueError("Root 'description' must be a string <= 200 chars.")
    if not isinstance(toc_data["chapters"], list):
        raise ValueError("Root 'chapters' must be a list.")
        
    # 3. Validate Chapter Count
    if len(toc_data["chapters"]) != 15:
        raise ValueError(f"Expected exactly 15 chapters, found {len(toc_data['chapters'])}.")
        
    # 4. Validate Individual Chapters
    for index, topic in enumerate(toc_data["chapters"]):
        if not isinstance(topic, dict):
             raise ValueError(f"Chapter at index {index} is not an object.")
        
        # Required fields
        if "title" not in topic or "shortDescription" not in topic or "order" not in topic:
             raise ValueError(f"Chapter {index+1} is missing required fields.")
             
        # Type and Content checks
        if not isinstance(topic["title"], str) or len(topic["title"]) > 80:
             raise ValueError(f"Chapter {index+1} title exceeds 80 chars.")
             
        if not isinstance(topic["shortDescription"], str) or len(topic["shortDescription"]) > 200:
             raise ValueError(f"Chapter {index+1} shortDescription exceeds 200 chars.")
             
        if topic["order"] != index + 1:
             raise ValueError(f"Chapter {index+1} has incorrect order value: {topic.get('order')}. Expected {index+1}.")

    return True

def generate_system_prompt(content_rules, style_guidelines, schema):
    """Constructs the system prompt."""
    prompt = f"""
You are a Table of Contents (TOC) generation engine for a micro-learning app.
You MUST follow the strict rules below to generate a JSON Table of Contents (list of chapters).

---
### 1. JSON Schema
{schema}

### 2. Content Rules
{content_rules}

### 3. Style Guidelines
{style_guidelines}

---
### Output format
Return ONLY valid JSON. No markdown formatting (no ```json ... ```), no code blocks, no explanations.
"""
    return prompt

def call_openai_chat(messages):
    """
    Calls the OpenAI API with a list of messages.
    """
    try:
        from openai import OpenAI
        from openai import OpenAIError
    except ImportError:
        print("\nError: The 'openai' library is not installed.")
        print("Please install it using: pip install openai")
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("\nError: OPENAI_API_KEY environment variable is not set.")
        print("Please set it in your environment.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return response.choices[0].message.content
    except OpenAIError as e:
        print(f"\nOpenAI API Error: {e}")
        sys.exit(1)

def generate_with_retries(course_title, system_prompt):
    """
    Generates TOC with a feedback loop.
    If validation fails, feeds the error back to the LLM to fix it.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Generate 15 Chapters for the course: {course_title}"}
    ]
    
    max_retries = 3
    print(f"Generating Chapters for '{course_title}'...")

    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            print(f"Attempt {attempt}/{max_retries}: Retrying with feedback...")
            
        content = call_openai_chat(messages)
        
        try:
            # 1. Parse JSON
            data = json.loads(content)
            
            # 2. Validate content
            validate_toc(data)
            
            # Success
            return data
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON Parse Error: {str(e)}"
            print(f"  > {error_msg}")
            # Feed back
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Your output was not valid JSON. Error: {error_msg}. Please fix and return ONLY valid JSON."})
            
        except ValueError as e:
            error_msg = f"Validation Error: {str(e)}"
            print(f"  > {error_msg}")
            # Feed back
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Your output failed validation rules. Error: {error_msg}. Please fix this specific error."})
    
    print("\nFailed to generate a valid TOC after multiple attempts.")
    sys.exit(1)

def main():
    # Strict Input Check
    if len(sys.argv) < 2:
        print("Error: No course title provided.")
        print("Usage: python toc_generator.py \"Your Course Title\"")
        sys.exit(1)
        
    course_title = " ".join(sys.argv[1:])
    
    # 1. Load Context
    try:
        schema_content = load_file_content(SCHEMA_PATH)
        content_rules = load_file_content(CONTENT_RULES_PATH)
        style_guidelines = load_file_content(STYLE_GUIDELINES_PATH)
    except Exception as e:
        print(f"Error loading files: {e}")
        sys.exit(1)
    
    # 2. Build System Prompt
    system_prompt = generate_system_prompt(content_rules, style_guidelines, schema_content)
    
    # 3. Generate with Loop
    final_toc = generate_with_retries(course_title, system_prompt)
    
    # 4. Output
    print("\n--- GENERATED TOC ---")
    print(json.dumps(final_toc, indent=4))

if __name__ == "__main__":
    main()
