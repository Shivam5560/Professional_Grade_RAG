"""
Production-grade algorithmic scorers for resume analysis.
All scoring is done without LLM calls - pure computation.

Features:
- Skill synonym mapping & fuzzy matching
- Skill taxonomy with categories
- Hybrid weighting (JD frequency + category importance)
- Full grammar analysis with readability scores
- Comprehensive ATS compatibility checks
- Contact validation, date consistency, keyword density
"""

import re
import math
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import Counter
from difflib import SequenceMatcher


# =============================================================================
# SKILL TAXONOMY & SYNONYMS
# =============================================================================

SKILL_SYNONYMS: Dict[str, Set[str]] = {
    # Programming Languages
    "javascript": {"js", "ecmascript", "es6", "es2015", "es2020", "es2021", "es2022"},
    "typescript": {"ts"},
    "python": {"py", "python3", "python2"},
    "java": {"jdk", "jre", "j2ee", "jakarta"},
    "csharp": {"c#", "c-sharp", ".net", "dotnet"},
    "cplusplus": {"c++", "cpp"},
    "golang": {"go"},
    "ruby": {"rb"},
    "php": {"php7", "php8"},
    "swift": {"swiftui"},
    "kotlin": {"kt"},
    "rust": {"rs"},
    "scala": {"sbt"},
    "r": {"rlang", "r-lang"},
    
    # Frontend Frameworks
    "react": {"reactjs", "react.js", "react js", "react-native", "react native"},
    "angular": {"angularjs", "angular.js", "angular2", "angular 2"},
    "vue": {"vuejs", "vue.js", "vue3", "vue 3", "nuxt", "nuxtjs"},
    "nextjs": {"next.js", "next js", "next"},
    "svelte": {"sveltekit", "svelte-kit"},
    "jquery": {"jq"},
    
    # Backend Frameworks
    "nodejs": {"node.js", "node js", "node", "express", "expressjs", "express.js"},
    "django": {"drf", "django rest", "django-rest-framework"},
    "flask": {"flask-restful", "flask-restx"},
    "fastapi": {"fast-api", "fast api"},
    "spring": {"spring boot", "springboot", "spring-boot", "spring framework"},
    "rails": {"ruby on rails", "ror"},
    "laravel": {"lumen"},
    "aspnet": {"asp.net", "asp net", ".net core", "dotnet core"},
    
    # Databases
    "postgresql": {"postgres", "psql", "pg"},
    "mysql": {"mariadb", "maria db"},
    "mongodb": {"mongo", "mongoose"},
    "redis": {"redis cache"},
    "elasticsearch": {"elastic", "es", "elk"},
    "cassandra": {"apache cassandra"},
    "dynamodb": {"dynamo db", "dynamo"},
    "sqlite": {"sqlite3"},
    "oracle": {"oracle db", "plsql", "pl/sql"},
    "sqlserver": {"sql server", "mssql", "t-sql", "tsql"},
    
    # Cloud & DevOps
    "aws": {"amazon web services", "ec2", "s3", "lambda", "ecs", "eks", "rds", "cloudfront"},
    "gcp": {"google cloud", "google cloud platform", "bigquery", "gke"},
    "azure": {"microsoft azure", "azure devops", "aks"},
    "docker": {"dockerfile", "docker-compose", "docker compose", "containerization"},
    "kubernetes": {"k8s", "kubectl", "helm", "kube"},
    "terraform": {"tf", "iac", "infrastructure as code"},
    "ansible": {"ansible playbook"},
    "jenkins": {"jenkins pipeline", "ci/cd"},
    "github actions": {"github-actions", "gh actions"},
    "gitlab": {"gitlab ci", "gitlab-ci"},
    "circleci": {"circle ci", "circle-ci"},
    
    # Data & ML
    "machine learning": {"ml", "deep learning", "dl", "ai", "artificial intelligence"},
    "tensorflow": {"tf", "keras"},
    "pytorch": {"torch"},
    "pandas": {"pd"},
    "numpy": {"np"},
    "scikit-learn": {"sklearn", "scikit learn"},
    "spark": {"apache spark", "pyspark", "spark sql"},
    "hadoop": {"hdfs", "mapreduce", "hive"},
    "tableau": {"power bi", "looker", "data visualization"},
    
    # Tools & Practices
    "git": {"github", "gitlab", "bitbucket", "version control", "vcs"},
    "agile": {"scrum", "kanban", "sprint", "jira"},
    "rest api": {"restful", "rest-api", "api development"},
    "graphql": {"apollo", "gql"},
    "testing": {"unit testing", "integration testing", "e2e", "jest", "pytest", "junit"},
    "linux": {"unix", "bash", "shell", "cli", "command line"},
    
    # Soft Skills
    "leadership": {"team lead", "tech lead", "team leadership", "leading"},
    "communication": {"interpersonal", "verbal", "written communication"},
    "problem solving": {"problem-solving", "analytical", "troubleshooting"},
    "teamwork": {"collaboration", "cross-functional", "team player"},
}

SKILL_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "languages": {
        "skills": {"python", "javascript", "typescript", "java", "csharp", "cplusplus", 
                   "golang", "ruby", "php", "swift", "kotlin", "rust", "scala", "r"},
        "weight": 1.0,
        "label": "Programming Languages"
    },
    "frontend": {
        "skills": {"react", "angular", "vue", "nextjs", "svelte", "jquery", "html", "css", 
                   "sass", "tailwind", "bootstrap"},
        "weight": 0.9,
        "label": "Frontend Frameworks"
    },
    "backend": {
        "skills": {"nodejs", "django", "flask", "fastapi", "spring", "rails", "laravel", "aspnet"},
        "weight": 0.95,
        "label": "Backend Frameworks"
    },
    "database": {
        "skills": {"postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
                   "dynamodb", "sqlite", "oracle", "sqlserver", "sql"},
        "weight": 0.9,
        "label": "Databases"
    },
    "cloud": {
        "skills": {"aws", "gcp", "azure", "heroku", "vercel", "netlify"},
        "weight": 0.85,
        "label": "Cloud Platforms"
    },
    "devops": {
        "skills": {"docker", "kubernetes", "terraform", "ansible", "jenkins", "github actions",
                   "gitlab", "circleci", "ci/cd", "linux"},
        "weight": 0.85,
        "label": "DevOps & Infrastructure"
    },
    "data_ml": {
        "skills": {"machine learning", "tensorflow", "pytorch", "pandas", "numpy", 
                   "scikit-learn", "spark", "hadoop", "tableau", "data science"},
        "weight": 0.9,
        "label": "Data & Machine Learning"
    },
    "tools": {
        "skills": {"git", "agile", "rest api", "graphql", "testing", "jira", "figma"},
        "weight": 0.7,
        "label": "Tools & Practices"
    },
    "soft_skills": {
        "skills": {"leadership", "communication", "problem solving", "teamwork", "mentoring"},
        "weight": 0.5,
        "label": "Soft Skills"
    },
}

# Strong action verbs for resume writing
STRONG_ACTION_VERBS = {
    # Leadership & Management
    "led", "managed", "directed", "supervised", "coordinated", "oversaw", "headed",
    "orchestrated", "spearheaded", "championed", "mentored", "coached", "guided",
    
    # Achievement & Results
    "achieved", "accomplished", "delivered", "exceeded", "surpassed", "attained",
    "completed", "earned", "generated", "produced", "won",
    
    # Creation & Innovation
    "created", "designed", "developed", "built", "established", "founded", "launched",
    "initiated", "introduced", "pioneered", "invented", "innovated", "architected",
    
    # Improvement & Optimization
    "improved", "enhanced", "optimized", "streamlined", "revamped", "transformed",
    "modernized", "upgraded", "accelerated", "maximized", "minimized", "reduced",
    
    # Technical
    "implemented", "engineered", "programmed", "coded", "debugged", "automated",
    "integrated", "deployed", "configured", "migrated", "refactored", "scaled",
    
    # Analysis & Problem Solving
    "analyzed", "evaluated", "assessed", "diagnosed", "investigated", "researched",
    "resolved", "troubleshot", "identified", "discovered", "solved",
    
    # Communication & Presentation
    "presented", "communicated", "negotiated", "collaborated", "facilitated",
    "documented", "reported", "trained", "educated", "persuaded",
}

# Weak/passive phrases to avoid
WEAK_PHRASES = [
    "was responsible for",
    "responsibilities included",
    "duties included",
    "tasked with",
    "worked on",
    "helped with",
    "assisted with",
    "participated in",
    "involved in",
    "in charge of",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def normalize_skill(skill: str) -> str:
    """Normalize a skill string for comparison."""
    return skill.lower().strip().replace("-", " ").replace("_", " ").replace(".", " ")


def get_canonical_skill(skill: str) -> str:
    """Get the canonical (normalized) name for a skill, resolving synonyms."""
    normalized = normalize_skill(skill)
    
    # Check if it matches any canonical skill directly
    for canonical, synonyms in SKILL_SYNONYMS.items():
        if normalized == canonical or normalized in synonyms:
            return canonical
    
    return normalized


def get_skill_category(skill: str) -> Tuple[str, float]:
    """Get the category and weight for a skill."""
    canonical = get_canonical_skill(skill)
    
    for category, data in SKILL_CATEGORIES.items():
        if canonical in data["skills"]:
            return category, data["weight"]
    
    # Default category for unknown skills
    return "other", 0.6


def fuzzy_match_score(str1: str, str2: str) -> float:
    """Calculate fuzzy match score between two strings (0-1)."""
    return SequenceMatcher(None, normalize_skill(str1), normalize_skill(str2)).ratio()


def skills_match(candidate_skill: str, required_skill: str, threshold: float = 0.85) -> bool:
    """
    Check if candidate skill matches required skill using:
    1. Exact match (after normalization)
    2. Synonym matching
    3. Fuzzy matching with threshold
    """
    # Normalize both
    cand_norm = normalize_skill(candidate_skill)
    req_norm = normalize_skill(required_skill)
    
    # Direct match
    if cand_norm == req_norm:
        return True
    
    # Substring match (for compound skills)
    if cand_norm in req_norm or req_norm in cand_norm:
        return True
    
    # Synonym matching
    cand_canonical = get_canonical_skill(candidate_skill)
    req_canonical = get_canonical_skill(required_skill)
    
    if cand_canonical == req_canonical:
        return True
    
    # Fuzzy matching
    if fuzzy_match_score(cand_norm, req_norm) >= threshold:
        return True
    
    return False


def calculate_readability_scores(text: str) -> Dict[str, float]:
    """
    Calculate multiple readability scores.
    - Flesch Reading Ease (0-100, higher = easier)
    - Flesch-Kincaid Grade Level
    - Average words per sentence
    - Average syllables per word
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 2]
    
    if not sentences:
        return {
            "flesch_reading_ease": 50,
            "flesch_kincaid_grade": 10,
            "avg_words_per_sentence": 0,
            "avg_syllables_per_word": 0
        }
    
    # Count words and syllables
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    total_words = len(words)
    total_sentences = len(sentences)
    
    def count_syllables(word: str) -> int:
        word = word.lower()
        vowels = "aeiouy"
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        # Adjust for silent e
        if word.endswith('e') and count > 1:
            count -= 1
        return max(1, count)
    
    total_syllables = sum(count_syllables(w) for w in words)
    
    if total_words == 0 or total_sentences == 0:
        return {
            "flesch_reading_ease": 50,
            "flesch_kincaid_grade": 10,
            "avg_words_per_sentence": 0,
            "avg_syllables_per_word": 0
        }
    
    avg_words_per_sentence = total_words / total_sentences
    avg_syllables_per_word = total_syllables / total_words
    
    # Flesch Reading Ease: 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)
    flesch_ease = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
    flesch_ease = max(0, min(100, flesch_ease))
    
    # Flesch-Kincaid Grade: 0.39*(words/sentences) + 11.8*(syllables/words) - 15.59
    fk_grade = (0.39 * avg_words_per_sentence) + (11.8 * avg_syllables_per_word) - 15.59
    fk_grade = max(0, min(20, fk_grade))
    
    return {
        "flesch_reading_ease": round(flesch_ease, 1),
        "flesch_kincaid_grade": round(fk_grade, 1),
        "avg_words_per_sentence": round(avg_words_per_sentence, 1),
        "avg_syllables_per_word": round(avg_syllables_per_word, 2)
    }


def detect_spelling_issues(text: str) -> List[str]:
    """
    Detect common spelling mistakes and typos in resumes.
    Returns list of potential issues found.
    """
    common_typos = {
        # Common resume typos
        "recieve": "receive",
        "acheive": "achieve",
        "occured": "occurred",
        "seperate": "separate",
        "definately": "definitely",
        "occassion": "occasion",
        "recomend": "recommend",
        "accomodate": "accommodate",
        "liason": "liaison",
        "priviledge": "privilege",
        "managment": "management",
        "enviroment": "environment",
        "developement": "development",
        "maintainance": "maintenance",
        "experiance": "experience",
        "profesional": "professional",
        "responsibilites": "responsibilities",
        "sucess": "success",
        "successfull": "successful",
        "refered": "referred",
        "occuring": "occurring",
        "beleive": "believe",
        "calender": "calendar",
        "comittee": "committee",
        "independant": "independent",
        "knowlege": "knowledge",
        "neccessary": "necessary",
        "occurence": "occurrence",
        "persue": "pursue",
        "sincerly": "sincerely",
        "strenght": "strength",
        "wich": "which",
        "writting": "writing",
    }
    
    issues = []
    text_lower = text.lower()
    
    for typo, correct in common_typos.items():
        if typo in text_lower:
            issues.append(f"'{typo}' should be '{correct}'")
    
    # Check for double spaces
    if "  " in text:
        issues.append("Multiple consecutive spaces detected")
    
    # Check for inconsistent capitalization patterns
    sentences = re.split(r'[.!?]\s+', text)
    for sent in sentences:
        if sent and sent[0].islower() and len(sent) > 10:
            issues.append("Sentence starting with lowercase letter")
            break
    
    return issues


def validate_contact_info(text: str) -> Dict[str, Any]:
    """
    Validate contact information in resume.
    Returns validation results for email, phone, LinkedIn.
    """
    results = {
        "email": {"found": False, "valid": False, "value": None, "issues": []},
        "phone": {"found": False, "valid": False, "value": None, "issues": []},
        "linkedin": {"found": False, "valid": False, "value": None, "issues": []},
    }
    
    # Email validation
    email_pattern = r'[\w.+-]+@[\w-]+\.[\w.-]+'
    email_matches = re.findall(email_pattern, text)
    if email_matches:
        email = email_matches[0]
        results["email"]["found"] = True
        results["email"]["value"] = email
        
        # Validate email format
        if re.match(r'^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$', email):
            results["email"]["valid"] = True
        else:
            results["email"]["issues"].append("Email format may be invalid")
        
        # Check for professional domain
        personal_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
        domain = email.split("@")[1].lower() if "@" in email else ""
        if domain in personal_domains:
            results["email"]["issues"].append("Consider using professional email domain")
    
    # Phone validation
    phone_patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
        r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}',  # International
    ]
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            results["phone"]["found"] = True
            results["phone"]["value"] = phone_match.group()
            results["phone"]["valid"] = True
            break
    
    # LinkedIn validation
    linkedin_pattern = r'linkedin\.com/in/[\w-]+'
    linkedin_match = re.search(linkedin_pattern, text.lower())
    if linkedin_match:
        results["linkedin"]["found"] = True
        results["linkedin"]["value"] = linkedin_match.group()
        results["linkedin"]["valid"] = True
    
    return results


def check_date_consistency(text: str) -> Dict[str, Any]:
    """
    Check for date format consistency in resume.
    """
    date_patterns = {
        "month_year": r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}\b',
        "mm_yyyy": r'\b\d{1,2}/\d{4}\b',
        "yyyy_mm": r'\b\d{4}/\d{1,2}\b',
        "year_only": r'\b(?:19|20)\d{2}\b',
        "range": r'(?:19|20)\d{2}\s*[-–—]\s*(?:19|20)?\d{2,4}|(?:19|20)\d{2}\s*[-–—]\s*(?:Present|Current)',
    }
    
    found_formats = {}
    for format_name, pattern in date_patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found_formats[format_name] = matches
    
    # Determine consistency
    is_consistent = len(found_formats) <= 2  # Allow year_only + one format
    
    issues = []
    if len(found_formats) > 2:
        issues.append(f"Multiple date formats detected: {', '.join(found_formats.keys())}")
    
    return {
        "is_consistent": is_consistent,
        "formats_found": list(found_formats.keys()),
        "issues": issues,
        "date_count": sum(len(v) for v in found_formats.values())
    }


def calculate_keyword_density(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Calculate detailed keyword density analysis.
    """
    # Extract meaningful keywords from JD
    stop_words = {
        'the', 'and', 'or', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'for', 'with',
        'about', 'against', 'between', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'from', 'up', 'down', 'this', 'that', 'what',
        'which', 'who', 'whom', 'work', 'team', 'role', 'position', 'company',
        'looking', 'join', 'ability', 'strong', 'excellent', 'good', 'great',
        'required', 'preferred', 'plus', 'bonus', 'years', 'year', 'experience',
        'responsibilities', 'including', 'also', 'such', 'our', 'you', 'your',
        'their', 'they', 'them', 'we', 'us', 'will', 'must', 'should',
    }
    
    # Extended stop words: common English gerunds, vague verbs, filler words
    # that are NOT meaningful ATS keywords
    generic_words = {
        # Common gerunds / present participles used as filler
        'working', 'building', 'making', 'using', 'doing', 'getting', 'going',
        'having', 'being', 'coming', 'taking', 'keeping', 'giving', 'finding',
        'putting', 'running', 'moving', 'living', 'bringing', 'thinking',
        'becoming', 'leaving', 'feeling', 'trying', 'helping', 'providing',
        'following', 'showing', 'starting', 'creating', 'growing', 'opening',
        'playing', 'turning', 'setting', 'offering', 'holding', 'learning',
        # Vague / non-technical verbs & adjectives
        'ensure', 'ensuring', 'various', 'within', 'across', 'well', 'like',
        'based', 'related', 'knowledge', 'understanding', 'skills', 'apply',
        'environment', 'environments', 'support', 'supporting', 'level',
        'include', 'includes', 'opportunity', 'ideal', 'candidate', 'part',
        'time', 'full', 'high', 'best', 'other', 'more', 'most', 'some',
        'many', 'very', 'just', 'only', 'also', 'well', 'much', 'even',
        'each', 'both', 'make', 'take', 'come', 'keep', 'give', 'find',
        'help', 'show', 'know', 'want', 'seem', 'feel', 'tell', 'call',
        'every', 'same', 'different', 'first', 'last', 'long', 'little',
        'when', 'where', 'then', 'than', 'them', 'these', 'those', 'over',
        'under', 'back', 'still', 'here', 'there', 'through', 'right',
        'effectively', 'efficiently', 'actively', 'closely', 'directly',
        'currently', 'especially', 'primarily', 'responsible', 'minimum',
        'qualifications', 'requirements', 'description', 'overview',
        'benefits', 'apply', 'equal', 'employer', 'location',
    }
    stop_words |= generic_words
    
    # Extract n-grams from JD
    jd_lower = jd_text.lower()
    resume_lower = resume_text.lower()
    
    # Single words (4+ chars)
    jd_words = re.findall(r'\b[a-z]{4,}\b', jd_lower)
    jd_words = [w for w in jd_words if w not in stop_words]
    
    # Get top keywords by frequency
    word_counts = Counter(jd_words)
    top_keywords = [word for word, count in word_counts.most_common(25)]
    
    # Check which appear in resume
    matched = []
    missing = []
    keyword_stats = []
    
    for kw in top_keywords:
        jd_count = word_counts[kw]
        resume_count = resume_lower.count(kw)
        
        keyword_stats.append({
            "keyword": kw,
            "jd_count": jd_count,
            "resume_count": resume_count,
            "match": resume_count > 0
        })
        
        if resume_count > 0:
            matched.append(kw)
        else:
            missing.append(kw)
    
    # Calculate density score
    match_rate = len(matched) / len(top_keywords) if top_keywords else 1.0
    
    return {
        "score": round(match_rate * 100, 1),
        "matched_keywords": matched,
        "missing_keywords": missing[:10],  # Top 10 missing
        "keyword_details": keyword_stats[:15],  # Top 15 with details
        "total_jd_keywords": len(top_keywords),
        "total_matched": len(matched)
    }


def analyze_resume_length(text: str) -> Dict[str, Any]:
    """
    Analyze resume length and provide recommendations.
    Optimal: 400-800 words for 1 page, 800-1200 for 2 pages.
    """
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    
    # Estimate pages (approx 500 words per page)
    estimated_pages = word_count / 500
    
    # Determine if length is optimal
    if 350 <= word_count <= 600:
        assessment = "optimal"
        recommendation = "Good length for a concise 1-page resume"
    elif 600 < word_count <= 900:
        assessment = "good"
        recommendation = "Appropriate length for an experienced professional"
    elif 900 < word_count <= 1200:
        assessment = "acceptable"
        recommendation = "Consider condensing for better readability"
    elif word_count < 350:
        assessment = "too_short"
        recommendation = "Resume may lack sufficient detail - consider adding more achievements"
    else:
        assessment = "too_long"
        recommendation = "Consider reducing to 2 pages maximum - focus on most relevant experience"
    
    return {
        "word_count": word_count,
        "estimated_pages": round(estimated_pages, 1),
        "assessment": assessment,
        "recommendation": recommendation,
        "optimal_range": "400-800 words" if word_count < 900 else "800-1200 words"
    }


# =============================================================================
# MAIN SCORING FUNCTIONS
# =============================================================================

def compute_technical_score(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None,
    jd_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute technical match score with:
    - Synonym resolution
    - Fuzzy matching
    - Category-based weighting
    - JD frequency weighting (if jd_text provided)
    
    Score breakdown:
    - 70% weight on required skills match
    - 30% weight on preferred skills match
    """
    preferred_skills = preferred_skills or []
    
    if not required_skills:
        return {
            "score": 100,
            "matched_required": [],
            "missing_required": [],
            "matched_preferred": [],
            "skill_categories": {},
            "details": "No specific skills required"
        }
    
    # Calculate JD keyword frequency for weighting
    jd_keyword_freq = {}
    if jd_text:
        jd_lower = jd_text.lower()
        all_req_skills = required_skills + (preferred_skills or [])
        for skill in all_req_skills:
            freq = jd_lower.count(normalize_skill(skill))
            jd_keyword_freq[skill.lower()] = max(1, freq)
    
    # Match required skills with weighting
    matched_required = []
    missing_required = []
    required_score_weighted = 0
    max_required_score = 0
    
    for req in required_skills:
        # Calculate weight for this skill
        category, cat_weight = get_skill_category(req)
        jd_freq_weight = jd_keyword_freq.get(req.lower(), 1)
        combined_weight = cat_weight * (1 + 0.2 * min(jd_freq_weight, 3))
        
        max_required_score += combined_weight
        
        # Check if candidate has this skill
        matched = False
        for cand in candidate_skills:
            if skills_match(cand, req):
                matched = True
                matched_required.append({"skill": req, "matched_by": cand, "category": category})
                required_score_weighted += combined_weight
                break
        
        if not matched:
            missing_required.append({"skill": req, "category": category, "weight": round(combined_weight, 2)})
    
    # Match preferred skills
    matched_preferred = []
    preferred_score_weighted = 0
    max_preferred_score = 0
    
    for pref in preferred_skills:
        category, cat_weight = get_skill_category(pref)
        combined_weight = cat_weight * 0.8  # Preferred skills have lower base weight
        
        max_preferred_score += combined_weight
        
        for cand in candidate_skills:
            if skills_match(cand, pref):
                matched_preferred.append({"skill": pref, "matched_by": cand, "category": category})
                preferred_score_weighted += combined_weight
                break
    
    # Calculate scores
    required_score = (required_score_weighted / max_required_score * 100) if max_required_score > 0 else 100
    preferred_score = (preferred_score_weighted / max_preferred_score * 100) if max_preferred_score > 0 else 100
    
    # Weighted average (70% required, 30% preferred)
    total_score = required_score * 0.7 + preferred_score * 0.3
    
    # Categorize matched/missing skills
    category_breakdown = {}
    for match in matched_required:
        cat = match["category"]
        if cat not in category_breakdown:
            category_breakdown[cat] = {"matched": [], "missing": []}
        category_breakdown[cat]["matched"].append(match["skill"])
    
    for miss in missing_required:
        cat = miss["category"]
        if cat not in category_breakdown:
            category_breakdown[cat] = {"matched": [], "missing": []}
        category_breakdown[cat]["missing"].append(miss["skill"])
    
    return {
        "score": round(total_score, 1),
        "matched_required": [m["skill"] for m in matched_required],
        "matched_required_details": matched_required,
        "missing_required": [m["skill"] for m in missing_required],
        "missing_required_details": missing_required,
        "matched_preferred": [m["skill"] for m in matched_preferred],
        "required_match_pct": round(required_score, 1),
        "preferred_match_pct": round(preferred_score, 1),
        "skill_categories": category_breakdown,
        "match_summary": f"{len(matched_required)}/{len(required_skills)} required, {len(matched_preferred)}/{len(preferred_skills)} preferred"
    }


def compute_ats_score(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Comprehensive ATS (Applicant Tracking System) compatibility score.
    
    Factors:
    - Keyword density from JD (40%)
    - Standard section headers (20%)
    - Contact info presence & validation (15%)
    - Resume length optimization (10%)
    - Date consistency (10%)
    - Formatting quality (5%)
    """
    # Keyword density analysis
    keyword_analysis = calculate_keyword_density(resume_text, job_description)
    keyword_score = keyword_analysis["score"]
    
    # Check for standard section headers
    resume_lower = resume_text.lower()
    section_headers = {
        'experience': ['experience', 'employment', 'work history', 'professional experience', 'career'],
        'education': ['education', 'academic', 'qualifications', 'degree'],
        'skills': ['skills', 'technical skills', 'competencies', 'expertise', 'technologies'],
        'summary': ['summary', 'objective', 'profile', 'about me', 'professional summary'],
        'projects': ['projects', 'portfolio', 'key projects'],
    }
    
    sections_found = []
    sections_missing = []
    for section, keywords in section_headers.items():
        if any(kw in resume_lower for kw in keywords):
            sections_found.append(section)
        else:
            sections_missing.append(section)
    
    section_score = (len(sections_found) / len(section_headers)) * 100
    
    # Contact info validation
    contact_validation = validate_contact_info(resume_text)
    contact_score = 0
    contact_issues = []
    
    for field in ["email", "phone", "linkedin"]:
        if contact_validation[field]["found"]:
            contact_score += 25 if field != "linkedin" else 15
            if contact_validation[field]["valid"]:
                contact_score += 10
        contact_issues.extend(contact_validation[field].get("issues", []))
    
    contact_score = min(100, contact_score)
    
    # Resume length analysis
    length_analysis = analyze_resume_length(resume_text)
    length_score = {
        "optimal": 100, "good": 90, "acceptable": 75,
        "too_short": 50, "too_long": 60
    }.get(length_analysis["assessment"], 70)
    
    # Date consistency check
    date_check = check_date_consistency(resume_text)
    date_score = 100 if date_check["is_consistent"] else 60
    
    # Formatting checks
    formatting_issues = []
    if resume_text.count('|') > 10:
        formatting_issues.append("Heavy pipe character usage - may cause parsing issues")
    if len(re.findall(r'\t{2,}', resume_text)) > 5:
        formatting_issues.append("Excessive tab usage detected")
    special_chars = len(re.findall(r'[■●►▪▸◆★☆✓✔✗✘]', resume_text))
    if special_chars > 15:
        formatting_issues.append("Many special bullet characters - use standard bullets")
    
    formatting_score = max(0, 100 - len(formatting_issues) * 20)
    
    # Calculate weighted total
    total_score = (
        keyword_score * 0.40 +
        section_score * 0.20 +
        contact_score * 0.15 +
        length_score * 0.10 +
        date_score * 0.10 +
        formatting_score * 0.05
    )
    
    return {
        "score": round(total_score, 1),
        "components": {
            "keyword_density": {
                "score": round(keyword_score, 1),
                "weight": "40%",
                "matched": keyword_analysis["matched_keywords"][:10],
                "missing": keyword_analysis["missing_keywords"][:10],
            },
            "section_structure": {
                "score": round(section_score, 1),
                "weight": "20%",
                "found": sections_found,
                "missing": sections_missing,
            },
            "contact_info": {
                "score": round(contact_score, 1),
                "weight": "15%",
                "email": contact_validation["email"]["found"],
                "phone": contact_validation["phone"]["found"],
                "linkedin": contact_validation["linkedin"]["found"],
                "issues": contact_issues[:3],
            },
            "resume_length": {
                "score": round(length_score, 1),
                "weight": "10%",
                "word_count": length_analysis["word_count"],
                "pages": length_analysis["estimated_pages"],
                "assessment": length_analysis["assessment"],
            },
            "date_consistency": {
                "score": round(date_score, 1),
                "weight": "10%",
                "is_consistent": date_check["is_consistent"],
                "formats_found": date_check["formats_found"],
            },
            "formatting": {
                "score": round(formatting_score, 1),
                "weight": "5%",
                "issues": formatting_issues,
            }
        },
        "keyword_match_score": round(keyword_score, 1),
        "section_score": round(section_score, 1),
        "formatting_score": round(formatting_score, 1),
        "contact_score": round(contact_score, 1),
        "matched_keywords": keyword_analysis["matched_keywords"][:10],
        "sections_missing": sections_missing,
        "formatting_issues": formatting_issues,
        "all_issues": formatting_issues + contact_issues + date_check.get("issues", [])
    }


def compute_grammar_score(resume_text: str) -> Dict[str, Any]:
    """
    Comprehensive grammar and writing quality score.
    
    Factors:
    - Action verb usage (25%)
    - Quantified achievements (25%)
    - Readability scores (20%)
    - Sentence structure variety (15%)
    - Spelling/typos (10%)
    - Weak phrases penalty (5%)
    """
    lines = [l.strip() for l in resume_text.split('\n') if l.strip()]
    text_lower = resume_text.lower()
    
    # Action verb analysis
    action_verbs_found = [v for v in STRONG_ACTION_VERBS if v in text_lower]
    action_verb_score = min(100, len(action_verbs_found) * 8)  # ~12 verbs = 100%
    
    # Quantified achievements
    percentages = re.findall(r'\d+%', resume_text)
    numbers = re.findall(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?[KMB]?\b', resume_text)
    dollar_amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?[KMB]?', resume_text)
    
    quantification_count = len(percentages) + len(numbers) // 2 + len(dollar_amounts) * 2
    quantification_score = min(100, quantification_count * 10)
    
    # Readability analysis
    readability = calculate_readability_scores(resume_text)
    # Ideal Flesch score for resume: 50-70 (professional but accessible)
    flesch = readability["flesch_reading_ease"]
    if 45 <= flesch <= 75:
        readability_score = 100
    elif 30 <= flesch < 45 or 75 < flesch <= 85:
        readability_score = 80
    else:
        readability_score = 60
    
    # Sentence variety
    sentence_starts = []
    for line in lines:
        words = line.split()
        if words and len(words) > 3:
            first_word = re.sub(r'^[\-•*●]\s*', '', words[0]).lower()
            if first_word:
                sentence_starts.append(first_word)
    
    unique_starts = len(set(sentence_starts))
    total_starts = len(sentence_starts)
    variety_score = (unique_starts / total_starts * 100) if total_starts > 0 else 70
    variety_score = min(100, variety_score * 1.2)  # Boost slightly
    
    # Spelling issues
    spelling_issues = detect_spelling_issues(resume_text)
    spelling_score = max(0, 100 - len(spelling_issues) * 15)
    
    # Weak phrases check
    weak_phrase_count = sum(1 for phrase in WEAK_PHRASES if phrase in text_lower)
    weak_phrase_penalty = weak_phrase_count * 10
    
    # Calculate bullet point quality
    bullet_points = [l for l in lines if l.startswith(('-', '•', '*', '–', '●')) or 
                    (l and l[0].isdigit() and '.' in l[:3])]
    bullets_with_verbs = sum(1 for b in bullet_points 
                            if any(v in b.lower().split()[:2] for v in STRONG_ACTION_VERBS))
    bullets_with_numbers = sum(1 for b in bullet_points if re.search(r'\d', b))
    
    # Weighted total
    total_score = max(0, min(100, (
        action_verb_score * 0.25 +
        quantification_score * 0.25 +
        readability_score * 0.20 +
        variety_score * 0.15 +
        spelling_score * 0.10 +
        100 * 0.05 - weak_phrase_penalty  # 5% base minus penalty
    )))
    
    # Generate suggestions
    suggestions = _generate_writing_suggestions(
        action_verbs_found, quantification_count, weak_phrase_count,
        readability, bullets_with_verbs, len(bullet_points), spelling_issues
    )
    
    return {
        "score": round(total_score, 1),
        "components": {
            "action_verbs": {
                "score": round(action_verb_score, 1),
                "weight": "25%",
                "found": action_verbs_found[:10],
                "count": len(action_verbs_found),
            },
            "quantification": {
                "score": round(quantification_score, 1),
                "weight": "25%",
                "count": quantification_count,
                "percentages": len(percentages),
                "numbers": len(numbers),
                "dollars": len(dollar_amounts),
            },
            "readability": {
                "score": round(readability_score, 1),
                "weight": "20%",
                "flesch_reading_ease": readability["flesch_reading_ease"],
                "flesch_kincaid_grade": readability["flesch_kincaid_grade"],
                "avg_words_per_sentence": readability["avg_words_per_sentence"],
            },
            "variety": {
                "score": round(variety_score, 1),
                "weight": "15%",
                "unique_sentence_starts": unique_starts,
            },
            "spelling": {
                "score": round(spelling_score, 1),
                "weight": "10%",
                "issues": spelling_issues[:5],
            },
            "weak_phrases": {
                "penalty": weak_phrase_penalty,
                "count": weak_phrase_count,
            }
        },
        "action_verbs_used": action_verbs_found[:10],
        "action_verb_count": len(action_verbs_found),
        "quantified_achievements": quantification_count,
        "clarity_score": round(readability_score, 1),
        "variety_score": round(variety_score, 1),
        "passive_voice_issues": weak_phrase_count,
        "spelling_issues": spelling_issues,
        "readability_scores": readability,
        "bullet_analysis": {
            "total_bullets": len(bullet_points),
            "bullets_with_action_verbs": bullets_with_verbs,
            "bullets_with_numbers": bullets_with_numbers,
        },
        "suggestions": suggestions
    }


def _generate_writing_suggestions(
    action_verbs: List[str],
    quant_count: int,
    weak_count: int,
    readability: Dict,
    bullets_with_verbs: int,
    total_bullets: int,
    spelling_issues: List[str]
) -> List[Dict[str, str]]:
    """Generate prioritized writing improvement suggestions."""
    suggestions = []
    
    if len(action_verbs) < 8:
        suggestions.append({
            "priority": "high",
            "category": "action_verbs",
            "issue": f"Only {len(action_verbs)} strong action verbs found",
            "fix": "Start more bullet points with action verbs like: Developed, Led, Implemented, Achieved, Optimized"
        })
    
    if quant_count < 5:
        suggestions.append({
            "priority": "high",
            "category": "quantification",
            "issue": "Resume lacks quantified achievements",
            "fix": "Add numbers, percentages, or metrics. E.g., 'Reduced costs by 25%' or 'Managed team of 8'"
        })
    
    if weak_count > 0:
        suggestions.append({
            "priority": "medium",
            "category": "language",
            "issue": f"Found {weak_count} weak/passive phrases",
            "fix": "Replace 'was responsible for' → 'Led', 'worked on' → 'Developed'"
        })
    
    flesch = readability.get("flesch_reading_ease", 50)
    if flesch < 40:
        suggestions.append({
            "priority": "medium",
            "category": "readability",
            "issue": "Text may be too complex to read quickly",
            "fix": "Use shorter sentences and simpler words. Aim for quick skimmability."
        })
    elif flesch > 80:
        suggestions.append({
            "priority": "low",
            "category": "readability",
            "issue": "Language may be too simple for professional context",
            "fix": "Consider using more industry-specific terminology"
        })
    
    if total_bullets > 0 and bullets_with_verbs / total_bullets < 0.5:
        suggestions.append({
            "priority": "high",
            "category": "bullets",
            "issue": "Many bullets don't start with action verbs",
            "fix": "Lead each bullet point with a strong action verb"
        })
    
    if spelling_issues:
        suggestions.append({
            "priority": "high",
            "category": "spelling",
            "issue": f"Found {len(spelling_issues)} potential spelling issues",
            "fix": f"Review: {', '.join(spelling_issues[:3])}"
        })
    
    if not suggestions:
        suggestions.append({
            "priority": "low",
            "category": "general",
            "issue": "Writing quality is strong",
            "fix": "Maintain consistent style and continue quantifying achievements"
        })
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda x: priority_order.get(x["priority"], 1))
    
    return suggestions


def compute_section_score(section_assessment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute section completeness score based on LLM's section assessment.
    
    This takes the section_assessment from LLM and converts to numerical score.
    """
    quality_scores = {'good': 100, 'fair': 70, 'poor': 40}
    
    sections = ['contact_info', 'summary', 'experience', 'education', 'skills']
    weights = {
        'contact_info': 0.15,
        'summary': 0.15,
        'experience': 0.35,
        'education': 0.15,
        'skills': 0.20
    }
    
    total_score = 0
    section_scores = {}
    
    for section in sections:
        section_data = section_assessment.get(section, {})
        present = section_data.get('present', False)
        quality = section_data.get('quality', 'poor').lower()
        
        if present:
            score = quality_scores.get(quality, 50)
        else:
            score = 0
        
        section_scores[section] = {
            "present": present,
            "quality": quality,
            "score": score,
            "feedback": section_data.get('feedback', ''),
            "weight": f"{int(weights.get(section, 0.15) * 100)}%"
        }
        
        total_score += score * weights.get(section, 0.15)
    
    return {
        "score": round(total_score, 1),
        "sections": section_scores,
        "summary": f"{sum(1 for s in section_scores.values() if s['present'])}/{len(sections)} sections present"
    }


def compute_overall_score(
    technical_score: float,
    ats_score: float,
    grammar_score: float,
    section_score: float
) -> Dict[str, Any]:
    """
    Compute weighted overall score from all components.
    
    Weights:
    - Technical Match: 35% (most important for job fit)
    - ATS Compatibility: 25% (critical for getting past screening)
    - Writing Quality: 15% (important for impression)
    - Section Completeness: 25% (structural requirements)
    """
    weights = {
        'technical': 0.35,
        'ats': 0.25,
        'grammar': 0.15,
        'section': 0.25
    }
    
    overall = (
        technical_score * weights['technical'] +
        ats_score * weights['ats'] +
        grammar_score * weights['grammar'] +
        section_score * weights['section']
    )
    
    # Determine fit category with more granular levels
    if overall >= 85:
        fit = "Excellent Match"
        description = "Strong candidate - highly aligned with requirements"
    elif overall >= 75:
        fit = "Strong Match"
        description = "Good candidate - meets most requirements"
    elif overall >= 65:
        fit = "Good Match"
        description = "Solid candidate - some gaps to address"
    elif overall >= 50:
        fit = "Moderate Match"
        description = "Potential candidate - significant improvements needed"
    elif overall >= 35:
        fit = "Developing Match"
        description = "Needs work - major gaps in requirements"
    else:
        fit = "Not Recommended"
        description = "Does not meet minimum requirements"
    
    return {
        "overall_score": round(overall, 1),
        "fit_category": fit,
        "fit_description": description,
        "breakdown": {
            "technical_match": round(technical_score, 1),
            "ats_compatibility": round(ats_score, 1),
            "writing_quality": round(grammar_score, 1),
            "section_completeness": round(section_score, 1)
        },
        "weights": weights,
        "interpretation": {
            "85-100": "Excellent Match - prioritize for interview",
            "75-84": "Strong Match - recommend for interview",
            "65-74": "Good Match - consider with notes",
            "50-64": "Moderate Match - backup candidate",
            "0-49": "Below threshold - do not proceed"
        }
    }
