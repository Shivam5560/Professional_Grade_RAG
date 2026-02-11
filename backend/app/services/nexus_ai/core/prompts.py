"""
Single comprehensive prompt for resume analysis.
One LLM call returns everything we need in JSON format.
Optimized for accurate extraction and detailed recommendations.
"""

ANALYSIS_PROMPT = """You are an expert resume analyst, ATS specialist, and senior technical recruiter with 15+ years of experience. Analyze the resume against the job description with meticulous attention to detail.

## RESUME:
{resume_text}

## JOB DESCRIPTION:
{job_description}

## EXTRACTION INSTRUCTIONS:
1. **Skills Extraction**: Extract ALL technical skills, tools, frameworks, languages, and platforms. Include:
   - Programming languages (Python, JavaScript, Java, C++, etc.)
   - Frameworks & libraries (React, Django, TensorFlow, etc.)
   - Cloud platforms (AWS, GCP, Azure, etc.)
   - Databases (PostgreSQL, MongoDB, Redis, etc.)
   - DevOps tools (Docker, Kubernetes, Jenkins, etc.)
   - Methodologies (Agile, Scrum, TDD, etc.)
   - Soft skills mentioned explicitly (Leadership, Communication, etc.)

2. **Experience Parsing**: For each position, extract:
   - Exact job title as written
   - Company name
   - Duration in format "Month Year - Month Year" or "Month Year - Present"
   - 3-5 key achievements with metrics when available

3. **JD Analysis**: Extract skills as they appear in the JD, categorizing into:
   - Required: Skills explicitly marked as required/must-have
   - Preferred: Skills marked as nice-to-have/preferred/bonus

Return ONLY valid JSON matching this exact structure (no markdown, no explanations outside JSON):

{{
  "resume_analysis": {{
    "name": "Full name exactly as written or null",
    "email": "email@example.com or null",
    "phone": "phone number or null",
    "location": "City, State/Country or null",
    "linkedin": "LinkedIn URL if present or null",
    "github": "GitHub URL if present or null",
    "portfolio": "Portfolio/website URL if present or null",
    "summary": "2-3 sentence professional summary capturing core competencies and career trajectory",
    "skills": ["Python", "React", "AWS", "Docker"],
    "skills_by_category": {{
      "programming_languages": ["Python", "JavaScript"],
      "frameworks": ["React", "Django"],
      "databases": ["PostgreSQL", "MongoDB"],
      "cloud_platforms": ["AWS", "GCP"],
      "devops_tools": ["Docker", "Kubernetes"],
      "other_technical": ["Git", "REST APIs"],
      "soft_skills": ["Leadership", "Communication"]
    }},
    "experience_years": 5.5,
    "seniority_level": "junior/mid/senior/lead/principal",
    "education": [
      {{
        "degree": "Bachelor of Science in Computer Science",
        "institution": "University Name",
        "year": "2020",
        "gpa": "3.8" 
      }}
    ],
    "experience": [
      {{
        "title": "Senior Software Engineer",
        "company": "Company Name",
        "duration": "Jan 2022 - Present",
        "is_current": true,
        "highlights": [
          "Led team of 5 engineers to deliver microservices platform reducing latency by 40%",
          "Architected real-time data pipeline processing 10M+ events/day",
          "Mentored 3 junior developers and conducted technical interviews"
        ]
      }}
    ],
    "certifications": ["AWS Solutions Architect", "Kubernetes CKAD"],
    "projects": [
      {{
        "name": "Project Name",
        "description": "Brief description",
        "technologies": ["Python", "React", "AWS"]
      }}
    ]
  }},
  
  "job_analysis": {{
    "title": "Job title as written",
    "company": "Company name or null",
    "department": "Department if mentioned or null",
    "required_skills": ["Python", "AWS", "Docker"],
    "preferred_skills": ["Kubernetes", "Go"],
    "experience_required": "5+ years of software engineering experience",
    "experience_years_min": 5,
    "education_required": "Bachelor's in CS or related field",
    "key_responsibilities": [
      "Design and implement scalable microservices",
      "Lead technical design reviews",
      "Mentor junior engineers"
    ],
    "seniority_level": "senior",
    "industry": "Technology/Finance/Healthcare/etc"
  }},
  
  "match_analysis": {{
    "matched_required": ["Python", "AWS"],
    "matched_preferred": ["Kubernetes"],
    "missing_required": ["Go"],
    "missing_preferred": ["GraphQL"],
    "experience_match": {{
      "status": "exceeds/meets/below",
      "candidate_years": 6,
      "required_years": 5,
      "explanation": "6 years of relevant experience exceeds the 5-year requirement"
    }},
    "education_match": {{
      "status": "meets/exceeds/below",
      "explanation": "MS in CS exceeds BS requirement"
    }},
    "seniority_match": {{
      "candidate_level": "senior",
      "required_level": "senior",
      "status": "match/overqualified/underqualified"
    }},
    "overall_fit": {{
      "category": "strong/moderate/weak",
      "score_estimate": 75,
      "explanation": "Strong technical match with 85% required skills coverage. Minor gaps in Go experience can be quickly addressed."
    }}
  }},
  
  "section_assessment": {{
    "contact_info": {{"present": true, "quality": "good", "feedback": "Complete with email, phone, and LinkedIn"}},
    "summary": {{"present": true, "quality": "good", "feedback": "Clear and targeted to the role"}},
    "experience": {{"present": true, "quality": "good", "feedback": "Strong bullet points with metrics"}},
    "education": {{"present": true, "quality": "good", "feedback": "Relevant degree clearly listed"}},
    "skills": {{"present": true, "quality": "fair", "feedback": "Could be better organized by category"}},
    "certifications": {{"present": false, "quality": "poor", "feedback": "Consider adding relevant certifications"}},
    "projects": {{"present": true, "quality": "good", "feedback": "Demonstrates practical application of skills"}}
  }},
  
  "recommendations": [
    {{
      "priority": "high",
      "category": "skills",
      "action": "Add experience with Go programming language",
      "reason": "Listed as required skill - consider taking a course or contributing to Go open source projects",
      "impact": "Would significantly improve match score and ATS ranking",
      "effort": "medium",
      "timeframe": "2-4 weeks for basic proficiency"
    }},
    {{
      "priority": "high",
      "category": "content",
      "action": "Add more quantified achievements in current role",
      "reason": "Metrics like 'increased performance by X%' are highly valued by recruiters",
      "impact": "Makes achievements concrete and memorable",
      "effort": "low",
      "timeframe": "1-2 hours to revise"
    }},
    {{
      "priority": "medium",
      "category": "formatting",
      "action": "Organize skills section by category (Languages, Frameworks, Cloud, etc.)",
      "reason": "Easier for recruiters and ATS to parse",
      "impact": "Improved readability and ATS compatibility",
      "effort": "low",
      "timeframe": "30 minutes"
    }}
  ],
  
  "ats_feedback": {{
    "keyword_optimization": {{
      "status": "good/needs_improvement",
      "matched_keywords": ["Python", "AWS", "microservices"],
      "missing_keywords": ["Go", "gRPC"],
      "suggestions": ["Include 'Go' in skills section", "Mention 'gRPC' experience if applicable"]
    }},
    "formatting_issues": [],
    "contact_completeness": "complete/partial/missing",
    "section_headers": "standard/non-standard",
    "overall_ats_readiness": "high/medium/low"
  }},
  
  "writing_feedback": {{
    "action_verbs_used": ["Led", "Developed", "Architected", "Optimized"],
    "weak_verbs_to_replace": [{{"original": "Worked on", "suggested": "Implemented/Developed"}}],
    "quantified_achievements": true,
    "achievement_count": 8,
    "clarity_score": "excellent",
    "passive_voice_instances": 2,
    "suggestions": [
      "Replace 'was responsible for' with active verbs like 'managed' or 'led'",
      "Add specific metrics to the database optimization achievement"
    ]
  }}
}}

CRITICAL INSTRUCTIONS:
- Extract ALL skills visible in the resume - be thorough
- Skills arrays must be flat lists of strings
- Return ONLY valid JSON, no markdown code blocks, no explanations
- Ensure valid JSON syntax - check all brackets and quotes
- For experience_years, calculate from work history, use decimals (e.g., 5.5 years)
- Mark skills as required/preferred based on JD language ("must have" vs "nice to have")
- Recommendations should be specific, actionable, and tailored to THIS job
"""


def build_analysis_prompt(resume_text: str, job_description: str) -> str:
    """Build the complete analysis prompt with resume and JD."""
    # Generous limits for thorough extraction
    return ANALYSIS_PROMPT.format(
        resume_text=resume_text[:60000],  # Allow more content
        job_description=job_description[:15000]
    )
