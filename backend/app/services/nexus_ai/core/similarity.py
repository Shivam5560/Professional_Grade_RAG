"""
Production-grade similarity scoring for resume-JD matching.
Combines multiple algorithms for robust matching:
- BM25 (term frequency with document length normalization)
- TF-IDF (term frequency-inverse document frequency)
- Jaccard Similarity (set overlap)
- Cosine Similarity (vector space)
- Skill-level semantic matching (domain-aware)
"""

import re
import math
from typing import Dict, List, Any, Tuple, Set, Optional
from collections import Counter


# =============================================================================
# TEXT PREPROCESSING
# =============================================================================

def preprocess_text(text: str, remove_stopwords: bool = True) -> List[str]:
    """
    Preprocess text for similarity calculations.
    Returns list of normalized tokens.
    """
    # Lowercase and extract words
    text = text.lower()
    tokens = re.findall(r'\b[a-z]+(?:[a-z0-9]*)\b', text)
    
    if remove_stopwords:
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their',
            'we', 'us', 'our', 'you', 'your', 'i', 'me', 'my', 'he', 'him', 'his',
            'she', 'her', 'about', 'after', 'before', 'between', 'into', 'through',
            'during', 'above', 'below', 'up', 'down', 'out', 'over', 'under',
            'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
            'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
            'very', 'just', 'also', 'now', 'any', 'both', 'being', 'who', 'which',
        }
        tokens = [t for t in tokens if t not in stopwords and len(t) > 2]
    
    return tokens


def extract_technical_terms(text: str) -> List[str]:
    """
    Extract technical terms (skills, technologies, methodologies).
    Handles multi-word terms and acronyms.
    """
    text_lower = text.lower()
    
    # Common multi-word technical terms
    multi_word_terms = [
        "machine learning", "deep learning", "natural language processing",
        "computer vision", "data science", "data engineering", "data analysis",
        "artificial intelligence", "neural network", "neural networks",
        "reinforcement learning", "transfer learning", "feature engineering",
        "model training", "model deployment", "model optimization", "model evaluation",
        "data preprocessing", "data pipeline", "data warehouse", "data lake",
        "cloud computing", "distributed systems", "microservices",
        "rest api", "restful api", "graphql api",
        "ci cd", "continuous integration", "continuous deployment",
        "version control", "source control",
        "unit testing", "integration testing", "test automation",
        "agile methodology", "scrum master", "product owner",
        "full stack", "front end", "back end", "backend", "frontend",
        "spring boot", "spring framework",
        "react native", "react js", "vue js", "angular js", "next js",
        "node js", "express js",
        "power bi", "data visualization",
        "time series", "anomaly detection", "recommendation system",
        "object detection", "image classification", "text classification",
        "sentiment analysis", "entity extraction", "named entity recognition",
        "llm", "large language model", "generative ai", "gen ai",
        "prompt engineering", "rag", "retrieval augmented generation",
    ]
    
    found_terms = []
    for term in multi_word_terms:
        if term in text_lower:
            found_terms.append(term)
            # Remove from text to avoid double counting
            text_lower = text_lower.replace(term, " ")
    
    # Single word technical terms (after removing multi-word)
    single_tokens = preprocess_text(text_lower, remove_stopwords=True)
    
    # Filter for technical-looking terms (3+ chars, not common words)
    common_words = {
        'work', 'team', 'project', 'experience', 'years', 'develop', 
        'create', 'build', 'manage', 'lead', 'implement', 'design',
        'support', 'maintain', 'improve', 'optimize', 'analyze', 'review',
        'strong', 'excellent', 'good', 'great', 'must', 'required',
        'preferred', 'ability', 'skills', 'knowledge', 'understanding',
    }
    
    technical_tokens = [t for t in single_tokens if t not in common_words and len(t) >= 3]
    
    return found_terms + technical_tokens


# =============================================================================
# BM25 SIMILARITY
# =============================================================================

class BM25:
    """
    BM25 (Best Matching 25) algorithm for document similarity.
    Better than TF-IDF for ranking and handles document length normalization.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: Term saturation parameter (1.2-2.0 typical)
            b: Length normalization (0=no normalization, 1=full normalization)
        """
        self.k1 = k1
        self.b = b
    
    def score(self, query_tokens: List[str], doc_tokens: List[str], 
              corpus_stats: Optional[Dict] = None) -> float:
        """
        Calculate BM25 score for a document given a query.
        
        Args:
            query_tokens: Tokenized query (JD)
            doc_tokens: Tokenized document (Resume)
            corpus_stats: Optional IDF statistics from a corpus
        
        Returns:
            BM25 score (higher = better match)
        """
        # Document term frequencies
        doc_tf = Counter(doc_tokens)
        doc_len = len(doc_tokens)
        
        # If no corpus stats, use single document as corpus
        if corpus_stats is None:
            # Approximate IDF using query and document
            all_terms = set(query_tokens) | set(doc_tokens)
            N = 2  # Two "documents": query and doc
            corpus_stats = {}
            for term in all_terms:
                df = sum(1 for _ in [query_tokens, doc_tokens] if term in _)
                corpus_stats[term] = {
                    'df': df,
                    'idf': math.log((N - df + 0.5) / (df + 0.5) + 1)
                }
        
        # Average document length (approximate)
        avg_dl = (len(query_tokens) + doc_len) / 2
        
        score = 0.0
        for term in query_tokens:
            if term not in doc_tf:
                continue
            
            tf = doc_tf[term]
            idf = corpus_stats.get(term, {}).get('idf', 1.0)
            
            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / avg_dl))
            score += idf * (numerator / denominator)
        
        return score
    
    def similarity(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        """
        Calculate normalized BM25 similarity (0-100 scale).
        """
        if not query_tokens or not doc_tokens:
            return 0.0
        
        raw_score = self.score(query_tokens, doc_tokens)
        
        # Normalize: max possible score if all query terms appear
        max_score = self.score(query_tokens, query_tokens)
        
        if max_score == 0:
            return 0.0
        
        normalized = (raw_score / max_score) * 100
        return min(100, max(0, normalized))


# =============================================================================
# TF-IDF SIMILARITY
# =============================================================================

def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """Compute term frequency (normalized by document length)."""
    tf = Counter(tokens)
    total = len(tokens)
    if total == 0:
        return {}
    return {term: count / total for term, count in tf.items()}


def compute_idf(doc_tokens_list: List[List[str]]) -> Dict[str, float]:
    """Compute inverse document frequency."""
    N = len(doc_tokens_list)
    if N == 0:
        return {}
    
    # Document frequency
    df = Counter()
    for tokens in doc_tokens_list:
        unique_terms = set(tokens)
        df.update(unique_terms)
    
    # IDF with smoothing
    idf = {}
    for term, freq in df.items():
        idf[term] = math.log((N + 1) / (freq + 1)) + 1
    
    return idf


def tfidf_similarity(query_tokens: List[str], doc_tokens: List[str]) -> float:
    """
    Calculate TF-IDF cosine similarity between query and document.
    Returns score 0-100.
    """
    if not query_tokens or not doc_tokens:
        return 0.0
    
    # Compute TF for both
    query_tf = compute_tf(query_tokens)
    doc_tf = compute_tf(doc_tokens)
    
    # Compute IDF using both as corpus
    idf = compute_idf([query_tokens, doc_tokens])
    
    # TF-IDF vectors
    all_terms = set(query_tf.keys()) | set(doc_tf.keys())
    
    query_vec = []
    doc_vec = []
    
    for term in all_terms:
        q_tfidf = query_tf.get(term, 0) * idf.get(term, 0)
        d_tfidf = doc_tf.get(term, 0) * idf.get(term, 0)
        query_vec.append(q_tfidf)
        doc_vec.append(d_tfidf)
    
    # Cosine similarity
    dot_product = sum(q * d for q, d in zip(query_vec, doc_vec))
    query_norm = math.sqrt(sum(q ** 2 for q in query_vec))
    doc_norm = math.sqrt(sum(d ** 2 for d in doc_vec))
    
    if query_norm == 0 or doc_norm == 0:
        return 0.0
    
    similarity = dot_product / (query_norm * doc_norm)
    return min(100, max(0, similarity * 100))


# =============================================================================
# JACCARD SIMILARITY
# =============================================================================

def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Calculate Jaccard similarity coefficient.
    |A ∩ B| / |A ∪ B|
    Returns score 0-100.
    """
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
    
    return (intersection / union) * 100


def weighted_jaccard(query_terms: List[str], doc_terms: List[str], 
                     weights: Optional[Dict[str, float]] = None) -> float:
    """
    Weighted Jaccard similarity - terms can have different importance.
    """
    if not query_terms or not doc_terms:
        return 0.0
    
    query_set = set(query_terms)
    doc_set = set(doc_terms)
    
    if weights is None:
        weights = {t: 1.0 for t in query_set}
    
    intersection_weight = sum(weights.get(t, 1.0) for t in query_set & doc_set)
    union_weight = sum(weights.get(t, 1.0) for t in query_set | doc_set)
    
    if union_weight == 0:
        return 0.0
    
    return (intersection_weight / union_weight) * 100


# =============================================================================
# COSINE SIMILARITY (Bag of Words)
# =============================================================================

def cosine_similarity_bow(tokens1: List[str], tokens2: List[str]) -> float:
    """
    Calculate cosine similarity using bag-of-words representation.
    Returns score 0-100.
    """
    if not tokens1 or not tokens2:
        return 0.0
    
    # Create frequency vectors
    tf1 = Counter(tokens1)
    tf2 = Counter(tokens2)
    
    # All terms
    all_terms = set(tf1.keys()) | set(tf2.keys())
    
    # Vectors
    vec1 = [tf1.get(t, 0) for t in all_terms]
    vec2 = [tf2.get(t, 0) for t in all_terms]
    
    # Cosine similarity
    dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
    norm1 = math.sqrt(sum(v ** 2 for v in vec1))
    norm2 = math.sqrt(sum(v ** 2 for v in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    return min(100, max(0, similarity * 100))


# =============================================================================
# SKILL-LEVEL MATCHING
# =============================================================================

# Import skill utilities from scorers_v2
try:
    from app.services.nexus_ai.core.scorers_v2 import (
        skills_match,
        get_canonical_skill,
        get_skill_category,
        SKILL_SYNONYMS,
        SKILL_CATEGORIES,
    )
except ImportError:
    # Fallback for testing
    def skills_match(s1, s2, threshold=0.85):
        return s1.lower() == s2.lower()
    
    def get_canonical_skill(skill):
        return skill.lower()
    
    def get_skill_category(skill):
        return "other", 0.7
    
    SKILL_SYNONYMS = {}
    SKILL_CATEGORIES = {}


def skill_overlap_similarity(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Calculate skill-based similarity with category weighting.
    Uses synonym matching and fuzzy matching.
    
    Returns detailed breakdown of matched/missing skills.
    """
    preferred_skills = preferred_skills or []
    
    if not required_skills:
        return {
            "overall_score": 100,
            "required_score": 100,
            "preferred_score": 100,
            "matched_required": [],
            "missing_required": [],
            "matched_preferred": [],
            "category_scores": {},
        }
    
    # Match required skills
    matched_required = []
    missing_required = []
    category_matches = {}
    
    for req in required_skills:
        req_canonical = get_canonical_skill(req)
        category, weight = get_skill_category(req)
        
        if category not in category_matches:
            category_matches[category] = {"required": 0, "matched": 0, "weight": weight}
        category_matches[category]["required"] += 1
        
        matched = False
        matched_by = None
        for cand in candidate_skills:
            if skills_match(cand, req):
                matched = True
                matched_by = cand
                break
        
        if matched:
            matched_required.append({
                "skill": req,
                "matched_by": matched_by,
                "category": category
            })
            category_matches[category]["matched"] += 1
        else:
            missing_required.append({
                "skill": req,
                "category": category,
                "canonical": req_canonical
            })
    
    # Match preferred skills
    matched_preferred = []
    for pref in preferred_skills:
        for cand in candidate_skills:
            if skills_match(cand, pref):
                matched_preferred.append({"skill": pref, "matched_by": cand})
                break
    
    # Calculate scores
    required_score = (len(matched_required) / len(required_skills) * 100) if required_skills else 100
    preferred_score = (len(matched_preferred) / len(preferred_skills) * 100) if preferred_skills else 100
    
    # Category scores
    category_scores = {}
    for cat, data in category_matches.items():
        if data["required"] > 0:
            category_scores[cat] = {
                "score": round(data["matched"] / data["required"] * 100, 1),
                "matched": data["matched"],
                "required": data["required"],
            }
    
    # Overall weighted score
    overall_score = required_score * 0.75 + preferred_score * 0.25
    
    return {
        "overall_score": round(overall_score, 1),
        "required_score": round(required_score, 1),
        "preferred_score": round(preferred_score, 1),
        "matched_required": matched_required,
        "missing_required": missing_required,
        "matched_preferred": matched_preferred,
        "category_scores": category_scores,
        "summary": f"{len(matched_required)}/{len(required_skills)} required, {len(matched_preferred)}/{len(preferred_skills)} preferred"
    }


# =============================================================================
# ENSEMBLE SIMILARITY
# =============================================================================

def compute_ensemble_similarity(
    resume_text: str,
    jd_text: str,
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Compute ensemble similarity using multiple algorithms.
    
    Default weights:
    - Skill matching: 40% (most important for job fit)
    - BM25: 25% (handles term frequency well)
    - TF-IDF: 15% (classic IR approach)
    - Jaccard: 10% (set overlap)
    - Cosine: 10% (vector similarity)
    
    Returns detailed breakdown of all similarity scores.
    """
    if weights is None:
        weights = {
            "skill_match": 0.40,
            "bm25": 0.25,
            "tfidf": 0.15,
            "jaccard": 0.10,
            "cosine": 0.10,
        }
    
    # Preprocess texts
    resume_tokens = preprocess_text(resume_text)
    jd_tokens = preprocess_text(jd_text)
    
    # Technical terms for Jaccard
    resume_tech = extract_technical_terms(resume_text)
    jd_tech = extract_technical_terms(jd_text)
    
    # Calculate individual similarities
    bm25 = BM25()
    bm25_score = bm25.similarity(jd_tokens, resume_tokens)
    
    tfidf_score = tfidf_similarity(jd_tokens, resume_tokens)
    
    jaccard_score = jaccard_similarity(set(resume_tech), set(jd_tech))
    
    cosine_score = cosine_similarity_bow(jd_tokens, resume_tokens)
    
    # Skill-level matching
    skill_result = skill_overlap_similarity(
        candidate_skills, required_skills, preferred_skills
    )
    skill_score = skill_result["overall_score"]
    
    # Weighted ensemble
    ensemble_score = (
        skill_score * weights["skill_match"] +
        bm25_score * weights["bm25"] +
        tfidf_score * weights["tfidf"] +
        jaccard_score * weights["jaccard"] +
        cosine_score * weights["cosine"]
    )
    
    return {
        "similarity_score": round(ensemble_score, 1),
        "breakdown": {
            "skill_match": {
                "score": round(skill_score, 1),
                "weight": f"{int(weights['skill_match'] * 100)}%",
                "details": skill_result,
            },
            "bm25": {
                "score": round(bm25_score, 1),
                "weight": f"{int(weights['bm25'] * 100)}%",
                "description": "Term frequency with length normalization"
            },
            "tfidf": {
                "score": round(tfidf_score, 1),
                "weight": f"{int(weights['tfidf'] * 100)}%",
                "description": "Term importance weighting"
            },
            "jaccard": {
                "score": round(jaccard_score, 1),
                "weight": f"{int(weights['jaccard'] * 100)}%",
                "description": "Technical term overlap"
            },
            "cosine": {
                "score": round(cosine_score, 1),
                "weight": f"{int(weights['cosine'] * 100)}%",
                "description": "Vector space similarity"
            },
        },
        "matched_skills": skill_result["matched_required"],
        "missing_skills": skill_result["missing_required"],
        "matched_preferred": skill_result["matched_preferred"],
        "category_scores": skill_result["category_scores"],
        "text_stats": {
            "resume_tokens": len(resume_tokens),
            "jd_tokens": len(jd_tokens),
            "resume_tech_terms": len(resume_tech),
            "jd_tech_terms": len(jd_tech),
        }
    }


# =============================================================================
# GAP ANALYSIS
# =============================================================================

# Learning resources for skills
SKILL_LEARNING_PATHS = {
    "python": {
        "resources": ["Python.org tutorial", "Automate the Boring Stuff", "LeetCode Python"],
        "time_estimate": "2-4 weeks",
        "difficulty": "beginner"
    },
    "aws": {
        "resources": ["AWS Free Tier", "AWS Certified Cloud Practitioner", "A Cloud Guru"],
        "time_estimate": "4-8 weeks",
        "difficulty": "intermediate"
    },
    "azure": {
        "resources": ["Microsoft Learn", "Azure Fundamentals (AZ-900)", "Azure Free Account"],
        "time_estimate": "4-6 weeks",
        "difficulty": "intermediate"
    },
    "gcp": {
        "resources": ["Google Cloud Skills Boost", "GCP Free Tier", "Coursera GCP courses"],
        "time_estimate": "4-6 weeks",
        "difficulty": "intermediate"
    },
    "kubernetes": {
        "resources": ["Kubernetes.io docs", "KodeKloud", "CKA Certification"],
        "time_estimate": "6-8 weeks",
        "difficulty": "advanced"
    },
    "docker": {
        "resources": ["Docker Get Started", "Docker Hub tutorials", "Play with Docker"],
        "time_estimate": "1-2 weeks",
        "difficulty": "beginner"
    },
    "machine learning": {
        "resources": ["Andrew Ng's ML Course", "Fast.ai", "Kaggle Learn"],
        "time_estimate": "8-12 weeks",
        "difficulty": "intermediate"
    },
    "deep learning": {
        "resources": ["Deep Learning Specialization", "Fast.ai v2", "PyTorch tutorials"],
        "time_estimate": "10-16 weeks",
        "difficulty": "advanced"
    },
    "tensorflow": {
        "resources": ["TensorFlow tutorials", "TF Developer Certificate", "Keras documentation"],
        "time_estimate": "4-6 weeks",
        "difficulty": "intermediate"
    },
    "pytorch": {
        "resources": ["PyTorch.org tutorials", "Deep Learning with PyTorch", "Lightning AI"],
        "time_estimate": "4-6 weeks",
        "difficulty": "intermediate"
    },
    "computer vision": {
        "resources": ["OpenCV tutorials", "CS231n Stanford", "PyImageSearch"],
        "time_estimate": "8-12 weeks",
        "difficulty": "advanced"
    },
    "nlp": {
        "resources": ["Hugging Face Course", "CS224N Stanford", "spaCy tutorials"],
        "time_estimate": "8-12 weeks",
        "difficulty": "advanced"
    },
    "data preprocessing": {
        "resources": ["Pandas documentation", "Kaggle Data Cleaning", "Feature Engineering book"],
        "time_estimate": "2-4 weeks",
        "difficulty": "beginner"
    },
    "feature engineering": {
        "resources": ["Feature Engineering for ML book", "Kaggle feature engineering", "Feast tutorials"],
        "time_estimate": "3-4 weeks",
        "difficulty": "intermediate"
    },
    "model deployment": {
        "resources": ["MLflow tutorials", "BentoML", "TensorFlow Serving", "FastAPI ML deployment"],
        "time_estimate": "3-4 weeks",
        "difficulty": "intermediate"
    },
    "react": {
        "resources": ["React.dev tutorial", "Scrimba React", "React patterns"],
        "time_estimate": "3-4 weeks",
        "difficulty": "beginner"
    },
    "nodejs": {
        "resources": ["Node.js docs", "The Odin Project", "Node.js Design Patterns"],
        "time_estimate": "3-4 weeks",
        "difficulty": "beginner"
    },
    "sql": {
        "resources": ["SQLZoo", "Mode SQL Tutorial", "LeetCode SQL"],
        "time_estimate": "2-3 weeks",
        "difficulty": "beginner"
    },
    "postgresql": {
        "resources": ["PostgreSQL Tutorial", "Postgres Guide", "pgExercises"],
        "time_estimate": "2-3 weeks",
        "difficulty": "beginner"
    },
    "git": {
        "resources": ["Git documentation", "Learn Git Branching", "Atlassian Git tutorial"],
        "time_estimate": "1 week",
        "difficulty": "beginner"
    },
}

# Seniority level skill expectations
SENIORITY_REQUIREMENTS = {
    "junior": {
        "years": "0-2",
        "core_skills_expected": 3,
        "preferred_skills_expected": 0,
        "leadership_expected": False,
        "description": "Entry-level, learning fundamentals"
    },
    "mid": {
        "years": "2-5",
        "core_skills_expected": 6,
        "preferred_skills_expected": 2,
        "leadership_expected": False,
        "description": "Independent contributor, some mentoring"
    },
    "senior": {
        "years": "5-8",
        "core_skills_expected": 8,
        "preferred_skills_expected": 4,
        "leadership_expected": True,
        "description": "Technical leader, architecture decisions"
    },
    "lead": {
        "years": "8+",
        "core_skills_expected": 10,
        "preferred_skills_expected": 5,
        "leadership_expected": True,
        "description": "Team leadership, cross-functional work"
    },
}


def analyze_technical_gaps(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None,
    candidate_experience_years: float = 0,
    job_title: str = ""
) -> Dict[str, Any]:
    """
    Comprehensive technical gap analysis with:
    - Category-based gaps (skills by domain)
    - Seniority-based assessment
    - Actionable learning paths
    
    Returns detailed gap analysis with recommendations.
    """
    preferred_skills = preferred_skills or []
    
    # Determine target seniority from job title
    job_lower = job_title.lower()
    if any(x in job_lower for x in ["senior", "sr.", "lead", "principal", "staff"]):
        target_seniority = "senior" if "lead" not in job_lower else "lead"
    elif any(x in job_lower for x in ["junior", "jr.", "entry", "associate", "trainee"]):
        target_seniority = "junior"
    else:
        target_seniority = "mid"
    
    seniority_req = SENIORITY_REQUIREMENTS[target_seniority]
    
    # Find missing skills with details
    missing_required = []
    missing_by_category = {}
    
    for req in required_skills:
        matched = any(skills_match(cand, req) for cand in candidate_skills)
        if not matched:
            canonical = get_canonical_skill(req)
            category, weight = get_skill_category(req)
            
            # Get learning path if available
            learning_path = SKILL_LEARNING_PATHS.get(canonical, {})
            
            gap_info = {
                "skill": req,
                "canonical": canonical,
                "category": category,
                "priority": "high",  # Required skills are high priority
                "learning_path": learning_path,
            }
            missing_required.append(gap_info)
            
            if category not in missing_by_category:
                missing_by_category[category] = []
            missing_by_category[category].append(gap_info)
    
    # Missing preferred skills
    missing_preferred = []
    for pref in preferred_skills:
        matched = any(skills_match(cand, pref) for cand in candidate_skills)
        if not matched:
            canonical = get_canonical_skill(pref)
            category, _ = get_skill_category(pref)
            learning_path = SKILL_LEARNING_PATHS.get(canonical, {})
            
            missing_preferred.append({
                "skill": pref,
                "canonical": canonical,
                "category": category,
                "priority": "medium",
                "learning_path": learning_path,
            })
    
    # Seniority assessment
    matched_count = len(required_skills) - len(missing_required)
    matched_preferred_count = len(preferred_skills) - len(missing_preferred)
    
    seniority_assessment = {
        "target_level": target_seniority,
        "target_requirements": seniority_req,
        "candidate_experience": candidate_experience_years,
        "experience_match": candidate_experience_years >= float(seniority_req["years"].split("-")[0]),
        "core_skills_match": matched_count >= seniority_req["core_skills_expected"],
        "skills_matched": matched_count,
        "skills_expected": seniority_req["core_skills_expected"],
    }
    
    # Calculate gap severity
    total_gaps = len(missing_required) + len(missing_preferred)
    gap_severity = (
        "critical" if len(missing_required) > 5 else
        "significant" if len(missing_required) > 3 else
        "moderate" if len(missing_required) > 1 else
        "minimal" if len(missing_required) == 1 else
        "none"
    )
    
    # Prioritized action items
    action_items = []
    
    # Sort missing by category importance
    for gap in missing_required[:5]:  # Top 5 gaps
        action = {
            "priority": "high",
            "skill": gap["skill"],
            "category": gap["category"],
            "action": f"Learn {gap['skill']}",
            "resources": gap.get("learning_path", {}).get("resources", ["Self-study", "Online courses"]),
            "time_estimate": gap.get("learning_path", {}).get("time_estimate", "2-4 weeks"),
            "difficulty": gap.get("learning_path", {}).get("difficulty", "intermediate"),
        }
        action_items.append(action)
    
    for gap in missing_preferred[:3]:  # Top 3 preferred
        action = {
            "priority": "medium",
            "skill": gap["skill"],
            "category": gap["category"],
            "action": f"Consider learning {gap['skill']}",
            "resources": gap.get("learning_path", {}).get("resources", ["Self-study"]),
            "time_estimate": gap.get("learning_path", {}).get("time_estimate", "2-4 weeks"),
            "difficulty": gap.get("learning_path", {}).get("difficulty", "intermediate"),
        }
        action_items.append(action)
    
    return {
        "gap_severity": gap_severity,
        "total_gaps": total_gaps,
        "missing_required": missing_required,
        "missing_required_count": len(missing_required),
        "missing_preferred": missing_preferred,
        "missing_preferred_count": len(missing_preferred),
        "gaps_by_category": missing_by_category,
        "seniority_assessment": seniority_assessment,
        "action_items": action_items,
        "summary": f"{len(missing_required)} required skills gap, {len(missing_preferred)} preferred skills gap. Severity: {gap_severity}",
    }
