We are planning to use supabase postgres sql database for our application and supabase auth for authentication. We are planning to use python + Fast API for our backend.

Below is our API sequential flow:
1.Auth: Login/Signup 
2.Profile: Create/Update/Get(if new user create profile else go to home page)
3.Home: Get all relevant information courses and recommendations
4.Course: Get course details of already created course
5.Create Course: Create new course course topic is sent to LLM and Table of contents (15 chapters title) is generated and stored in DB which will be fetched by frontend.
After user enters the topic  and while entering all other course information like difficulty , type, length. we will generate the TOC and store it in DB and fetch it by frontend.
6. Chapter Creation: User reaarange the TOC shown to to him and click create course. now we send the 1st chapter title to LLM and get the chapter content and store it in DB, abract image to be shown is also stored for each topic/slides and fetch it by frontend. From here on frontend can use this to create chapters by sendinf the chapterid. chapter content will have all the content / quiz / answers / summary.
7.Course tracking incuding completion of chapters/courses/quizs
8.Chat query - where user query is sent to LLM and answers is sent forward
9.Daily Recommendation: Daily falshcard / course recommendations