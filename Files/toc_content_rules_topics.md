Content Rules for TOC Chapters Generation

1. JSON-only Output
   - The agent must output ONLY valid JSON.
   - No explanations, markdown, or extra text.

2. Structure Requirements
   - Root keys allowed: title, description, chapters.
   - “chapters” MUST contain exactly 15 items.
   - Each chapter item must include:
        - title (string)
        - shortDescription (string)
        - order (integer 1–15)
   - No additional keys allowed.

3. Conciseness Rules
   - chapter title: max 120 characters
   - shortDescription: max 200 characters
   - shortDescription must be 1–2 sentences only.
   - No long paragraphs. No bullet points.

4. Language & Tone
   - Simple, mobile-friendly English.
   - Avoid jargon unless required by chapter.
   - Explanations must be clear and direct.
   - No filler text (“In this chapter we will learn…”).

5. No System Fields
   - Do NOT generate: courseId, chapterId, lessonId, createdAt, version, metadata.
   - These will be added by backend.

6. Content Quality Requirements
   - Titles must reflect distinct subtopics.
   - Avoid repetitive phrasing across chapters.
   - Ensure logical order: foundational chapters first, advanced later.

7. Safety & Compliance
   - Avoid political, medical, legal, or harmful content unless explicitly required by chapter seed.
   - Avoid brand names unless provided.

8. Consistency
   - Keep naming style uniform across chapters.
   - Ensure order numbers 1 to 15 are consecutive with no gaps.

9. No Hallucinations
   - Do NOT invent academic papers, research names, books, or datasets.
   - Stick to general, widely accepted knowledge.
10. Exclusions:
    - Do NOT include chapters related to "build projects", "next steps", "what to learn next", or any roadmap-style content.
    - Do NOT include setup, installation, environment configuration, or tool installation chapters.
    - Only generate strong, core, teachable concepts that can be expanded into actual learning content.
11. Error Handling
   - If unsure about chapter scope, generate universally recognized subtopics.
