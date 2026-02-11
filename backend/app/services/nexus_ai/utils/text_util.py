import json
import re
import string
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from rank_bm25 import BM25Okapi

# --- Flask and LlamaIndex related imports ---
# Assuming these are correctly set up in your environment
# from flask import Flask, request, jsonify, current_app
from sklearn.metrics.pairwise import cosine_similarity
from llama_index.core.base.embeddings.base import BaseEmbedding
from app.config import settings
from .file_util import load_from_json
from app.utils.logger import get_logger

logger = get_logger(__name__)
# --- Constants ---
# TECHNICAL_KEYWORDS_SEED = set([
#     'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'swift', 'kotlin', 'typescript', 'sql', 'nosql',
#     'scala', 'perl', 'r',
#     'react', 'angular', 'vue', 'django', 'flask', 'spring', 'springboot', 'nodejs', 'express', 'rubyonrails', 'laravel',
#     'jquery', 'bootstrap',
#     'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'oracle', 'sqlserver', 'elasticsearch', 'dynamodb',
#     'aws', 'azure', 'gcp', 'amazonwebservices', 'googlecloudplatform', 'microsoftazure', 'heroku', 'kubernetes',
#     'docker', 'terraform', 'lambda', 'ec2', 's3', 'rds',
#     'linux', 'unix', 'windows', 'macos', 'bash', 'shell', 'nginx', 'apache',
#     'pandas', 'numpy', 'scipy', 'sklearn', 'scikitlearn', 'tensorflow', 'pytorch', 'keras', 'machinelearning',
#     'deeplearning', 'dataanalysis', 'nlp', 'computervision', 'statistics',
#     'git', 'svn', 'jenkins', 'cicd', 'ci/cd', 'devops', 'agile', 'scrum', 'rest', 'graphql', 'api', 'microservices',
#     'oop', 'testing', 'debugging', 'jira',
#     'architecture', 'scalability', 'performance', 'security', 'algorithms', 'datastructures', 'ux', 'ui',
#     'android', 'ios', 'reactnative', 'flutter', 'api', 'sdk', 'ide', 'automation', 'bigdata', 'hadoop', 'spark'
# ])
TECHNICAL_KEYWORDS_SEED = load_from_json("resources", "technical_keywords.json")
SKILL_SIMILARITY_THRESHOLD = 0.75
RESPONSIBILITY_SIMILARITY_THRESHOLD = 0.50  # Keeping the lower threshold based on previous feedback
PASS_THRESHOLD = 70.0
RESPONSIBILITY_BONUS_FACTOR = 0.25
HYBRID_VECTOR_WEIGHT = 0.70
HYBRID_BM25_WEIGHT = 0.30

# Skill normalization dictionary for semantic equivalents
SKILL_NORMALIZATIONS = {
    "nlp": "natural language processing",
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "k8s": "kubernetes",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "db": "database",
    "api": "application programming interface",
    "ci/cd": "continuous integration continuous deployment",
    "devops": "development operations",
    "rdbms": "relational database management system",
    "nosql": "non-relational database",
    "rest": "representational state transfer",
    "graphql": "graph query language",
    "oop": "object oriented programming",
    "crud": "create read update delete",
    "etl": "extract transform load",
    "bi": "business intelligence",
    "cv": "computer vision",
    "nn": "neural network",
    "cnn": "convolutional neural network",
    "rnn": "recurrent neural network",
    "gan": "generative adversarial network",
    "bert": "bidirectional encoder representations from transformers",
    "gpt": "generative pre-trained transformer",
    "llm": "large language model",
    "rag": "retrieval augmented generation",
}


# --- Helper Functions ---
def clean_text(s):
    if '```toon' in s:
        start_index = s.index('```toon') + 7
        end_index = s.rindex('```')
        return s[start_index:end_index]
    if '```json' in s:
        start_index = s.index('```json') + 7
        end_index = s.rindex('```')
        return s[start_index:end_index]
    return s

# Global cache for embed model (singleton pattern)
_cached_embed_model = None

def get_embed_model() -> BaseEmbedding:
    """Retrieve the configured embedding model (remote, cohere, or ollama). Cached for reuse."""
    global _cached_embed_model
    
    # Return cached instance if available
    if _cached_embed_model is not None:
        logger.debug("Reusing cached embed model")
        return _cached_embed_model
    
    logger.info("Initializing new embed model instance")
    provider = settings.embedding_provider
    if provider == "remote" or settings.use_remote_embedding_service:
        from app.services.remote_embedding_service import RemoteEmbeddingService

        _cached_embed_model = RemoteEmbeddingService(
            base_url=settings.remote_embedding_service_url,
            model_name=settings.ollama_embedding_model,
        )
    elif provider == "cohere":
        from app.services.cohere_service import get_cohere_service

        _cached_embed_model = get_cohere_service().get_embed_model()
    else:
        from app.services.ollama_service import get_ollama_service

        _cached_embed_model = get_ollama_service().get_embed_model()
    
    logger.info(f"Embed model initialized: {type(_cached_embed_model).__name__}")
    return _cached_embed_model


def _get_text_embeddings(
    embed_model: BaseEmbedding,
    texts: List[str],
    input_type: str,
) -> List[List[float]]:
    if hasattr(embed_model, "get_text_embedding_batch"):
        try:
            return embed_model.get_text_embedding_batch(
                texts,
                input_type=input_type,
                show_progress=False,
            )
        except TypeError:
            return embed_model.get_text_embedding_batch(texts)
    if hasattr(embed_model, "get_text_embeddings"):
        return embed_model.get_text_embeddings(texts)
    if hasattr(embed_model, "_get_text_embeddings"):
        return embed_model._get_text_embeddings(texts)
    if hasattr(embed_model, "get_text_embedding"):
        return [embed_model.get_text_embedding(text) for text in texts]
    raise ValueError("Embedding model does not support batch embeddings")


def preprocess_text(text: Any) -> str:
    """Cleans text: lowercase, removes most punctuation, strips extra whitespace."""
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'[^\w\s\-/]', '', text)  # Keep words, spaces, hyphen, slash
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def normalize_skill(skill: str) -> str:
    """Normalize skill to catch semantic equivalents (e.g., 'NLP' -> 'natural language processing')."""
    skill_lower = skill.lower().strip()
    # Check direct normalization
    if skill_lower in SKILL_NORMALIZATIONS:
        return SKILL_NORMALIZATIONS[skill_lower]
    return skill_lower


def fuzzy_skill_match(skill1: str, skill2: str) -> bool:
    """Check if two skills are semantically equivalent using normalization and BM25."""
    norm1 = normalize_skill(skill1)
    norm2 = normalize_skill(skill2)
    
    # Direct match after normalization
    if norm1 == norm2:
        return True
    
    # Check if either contains the other (handles "Python" vs "Python Programming")
    if norm1 in norm2 or norm2 in norm1:
        return True
    
    # Check if acronym expansion matches
    # "NLP" -> "natural language processing" vs "Natural Language Processing"
    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())
    
    # If significant token overlap (>= 50% of smaller set)
    if tokens1 and tokens2:
        overlap = len(tokens1 & tokens2)
        min_tokens = min(len(tokens1), len(tokens2))
        if overlap >= min_tokens * 0.5:
            return True
    
    return False


def _tokenize_for_bm25(text: str) -> List[str]:
    return preprocess_text(text).split()


def _collect_resume_texts(resume_dict: Dict[str, Any]) -> List[str]:
    texts: List[str] = []

    summary = resume_dict.get("summary")
    if isinstance(summary, str) and summary.strip():
        texts.append(summary)

    keywords = resume_dict.get("keywords", [])
    if isinstance(keywords, list):
        keyword_text = " ".join([k for k in keywords if isinstance(k, str)])
        if keyword_text.strip():
            texts.append(keyword_text)

    key_responsibilities = resume_dict.get("key_responsibilities", [])
    if isinstance(key_responsibilities, list):
        texts.extend([r for r in key_responsibilities if isinstance(r, str) and r.strip()])

    work_experience = resume_dict.get("work_experience", [])
    if isinstance(work_experience, list):
        for item in work_experience:
            if not isinstance(item, dict):
                continue
            responsibilities = item.get("responsibilities", [])
            if isinstance(responsibilities, list):
                texts.extend([r for r in responsibilities if isinstance(r, str) and r.strip()])

    projects = resume_dict.get("projects", [])
    if isinstance(projects, list):
        for item in projects:
            if not isinstance(item, dict):
                continue
            description = item.get("description", [])
            if isinstance(description, list):
                texts.extend([d for d in description if isinstance(d, str) and d.strip()])
            elif isinstance(description, str) and description.strip():
                texts.append(description)

    return texts


def _collect_jd_texts(job_description_dict: Dict[str, Any]) -> List[str]:
    texts: List[str] = []

    job_title = job_description_dict.get("job_title")
    if isinstance(job_title, str) and job_title.strip():
        texts.append(job_title)

    summary = job_description_dict.get("summary")
    if isinstance(summary, str) and summary.strip():
        texts.append(summary)

    required_skills = job_description_dict.get("required_skills", [])
    if isinstance(required_skills, list):
        texts.extend([s for s in required_skills if isinstance(s, str) and s.strip()])

    key_responsibilities = job_description_dict.get("key_responsibilities", [])
    if isinstance(key_responsibilities, list):
        texts.extend([r for r in key_responsibilities if isinstance(r, str) and r.strip()])

    other_qualifications = job_description_dict.get("other_qualifications", [])
    if isinstance(other_qualifications, list):
        texts.extend([q for q in other_qualifications if isinstance(q, str) and q.strip()])

    return texts


def _bm25_similarity_score(resume_dict: Dict[str, Any], job_description_dict: Dict[str, Any]) -> float:
    resume_texts = _collect_resume_texts(resume_dict)
    jd_texts = _collect_jd_texts(job_description_dict)

    if not resume_texts or not jd_texts:
        return 0.0

    tokenized_corpus = [
        _tokenize_for_bm25(text)
        for text in resume_texts
        if isinstance(text, str) and text.strip()
    ]
    tokenized_query = _tokenize_for_bm25(" ".join(jd_texts))

    if not tokenized_corpus or not tokenized_query:
        return 0.0

    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(tokenized_query)
    if scores is None or len(scores) == 0:
        return 0.0

    top_score = float(max(scores))
    normalized = (top_score / (top_score + 5.0)) * 100.0
    return round(normalized, 2)


def calculate_batch_similarity(embeddings1: np.ndarray, embeddings2: np.ndarray) -> np.ndarray:
    """Calculates cosine similarity between two batches of embeddings."""
    if embeddings1.ndim == 1: embeddings1 = embeddings1.reshape(1, -1)
    if embeddings2.ndim == 1: embeddings2 = embeddings2.reshape(1, -1)
    if embeddings1.shape[0] == 0 or embeddings2.shape[0] == 0 or embeddings1.shape[1] == 0 or embeddings2.shape[1] == 0:
        return np.empty((embeddings1.shape[0], embeddings2.shape[0]))

    norm1 = np.linalg.norm(embeddings1, axis=1, keepdims=True)
    norm2 = np.linalg.norm(embeddings2, axis=1, keepdims=True)
    normalized1 = np.divide(embeddings1, norm1, out=np.zeros_like(embeddings1), where=norm1 != 0)
    normalized2 = np.divide(embeddings2, norm2, out=np.zeros_like(embeddings2), where=norm2 != 0)
    similarity_matrix = cosine_similarity(normalized1, normalized2)
    return np.clip(similarity_matrix, 0.0, 1.0)


def _get_qualitative_assessment(score_percent: float, thresholds: List[Tuple[float, str]]) -> str:
    """Helper to get qualitative string based on score."""
    for threshold, assessment in thresholds:
        if score_percent >= threshold:
            return assessment
    return thresholds[-1][1]  # Return the lowest assessment if none match


# --- Skill Matching (Revamped Justifications) ---
def find_skill_matches_with_embeddings(
    resume_skills: List[str],
    jd_skills: List[str],
    embed_model: BaseEmbedding,
    threshold: float
) -> Tuple[List[str], List[str], Dict[str, Tuple[str, float]], str, str]:
    """
    Finds semantic matches for skills.
    Returns: Tuple[found_skills, missing_skills, match_details, internal_justification, user_justification]
    """
    internal_notes = []
    user_insight = ""

    # --- Initial checks ---
    if not jd_skills:
        user_insight = "No required skills listed in the job description to compare against."
        internal_notes.append("No JD skills.")
        return [], [], {}, " ".join(internal_notes), user_insight
    if not resume_skills:
        missing_skills_list = sorted(list(set(jd_skills)))
        num_missing = len(missing_skills_list)
        user_insight = f"No relevant skills identified in the resume to match the {num_missing} required job skills."
        internal_notes.append("No resume skills.")
        return [], missing_skills_list, {}, " ".join(internal_notes), user_insight

    # --- Preprocessing ---
    original_jd_skills_map = {preprocess_text(s): s for s in jd_skills if isinstance(s, str)}
    unique_resume_skills = sorted(list(set(filter(None, [preprocess_text(s) for s in resume_skills]))))
    unique_jd_skills = sorted(list(set(filter(None, [preprocess_text(s) for s in jd_skills]))))
    total_jd_skills_unique = len(unique_jd_skills)
    internal_notes.append(
        f"Compared {total_jd_skills_unique} unique JD skills vs {len(unique_resume_skills)} resume skills. Threshold={threshold}.")

    if not unique_jd_skills or not unique_resume_skills:
        # Handle cases where lists become empty after processing
        missing_list = [original_jd_skills_map.get(s, s) for s in unique_jd_skills]
        user_insight = "Could not perform skill comparison due to lack of valid skills in JD or resume after processing."
        internal_notes.append("One list empty post-processing.")
        return [], sorted(missing_list), {}, " ".join(internal_notes), user_insight

    # --- Phase 1: Fuzzy/BM25 Pre-Matching (catches semantic equivalents) ---
    found_skills_pp = []
    remaining_jd_skills = []
    match_details_pp = {}
    bm25_matches = 0
    
    logger.info(f"Starting Phase 1: BM25/Fuzzy matching for {len(unique_jd_skills)} JD skills")
    
    for jd_skill_pp in unique_jd_skills:
        matched = False
        for resume_skill_pp in unique_resume_skills:
            if fuzzy_skill_match(jd_skill_pp, resume_skill_pp):
                found_skills_pp.append(jd_skill_pp)
                match_details_pp[jd_skill_pp] = (resume_skill_pp, 1.0)  # Perfect match
                matched = True
                bm25_matches += 1
                logger.debug(f"BM25 match: '{jd_skill_pp}' <-> '{resume_skill_pp}'")
                break
        if not matched:
            remaining_jd_skills.append(jd_skill_pp)
    
    logger.info(f"Phase 1 complete: {bm25_matches} BM25 matches, {len(remaining_jd_skills)} skills need embedding")
    internal_notes.append(f"BM25/Fuzzy matched {bm25_matches} skills directly.")
    
    # If all skills matched via BM25, skip embeddings entirely
    if not remaining_jd_skills:
        final_found = sorted([original_jd_skills_map.get(s, s) for s in found_skills_pp])
        final_match_details = {original_jd_skills_map.get(k, k): (v, score) for k, (v, score) in match_details_pp.items()}
        
        match_percentage = 100.0
        internal_notes.append(f"All skills matched via BM25/fuzzy logic. No embeddings needed.")
        logger.info("All skills matched via BM25 - skipping embeddings")
        user_insight = f"Skill Check: Excellent alignment. Covers {len(final_found)}/{total_jd_skills_unique} required skills via exact/semantic matches."
        return final_found, [], final_match_details, " ".join(internal_notes), user_insight

    # --- Phase 2: Embedding for Remaining Skills Only ---
    logger.info(f"Starting Phase 2: Embedding {len(remaining_jd_skills)} remaining JD skills + {len(unique_resume_skills)} resume skills")
    # --- Phase 2: Embedding for Remaining Skills Only ---
    try:
        all_unique_skills = unique_resume_skills + remaining_jd_skills
        internal_notes.append(f"Embedding {len(remaining_jd_skills)} remaining JD skills + {len(unique_resume_skills)} resume skills.")
        
        all_embeddings_list = _get_text_embeddings(
            embed_model,
            all_unique_skills,
            input_type="search_document",
        )
        if all_embeddings_list is None or len(all_embeddings_list) != len(all_unique_skills): raise ValueError(
            "Embedding failed")
        all_embeddings = np.array(all_embeddings_list, dtype=np.float32)
        num_resume_skills = len(unique_resume_skills)
        resume_embeddings = all_embeddings[:num_resume_skills]
        jd_embeddings = all_embeddings[num_resume_skills:]
        if resume_embeddings.shape[0] == 0 or jd_embeddings.shape[0] == 0: raise ValueError("Empty embeddings")
        similarity_matrix = calculate_batch_similarity(jd_embeddings, resume_embeddings)
        if similarity_matrix.shape[0] != len(remaining_jd_skills) or similarity_matrix.shape[1] != len(
            unique_resume_skills): raise ValueError("Matrix shape mismatch")
    except Exception as e:
        internal_notes.append(f"Embedding/Similarity Error: {e}.")
        user_insight = "An internal error prevented skill comparison."
        # Return BM25 matches + mark remaining as missing
        final_found = sorted([original_jd_skills_map.get(s, s) for s in found_skills_pp])
        final_missing = sorted([original_jd_skills_map.get(s, s) for s in remaining_jd_skills])
        final_match_details = {original_jd_skills_map.get(k, k): v for k, v in match_details_pp.items()}
        return final_found, final_missing, final_match_details, " ".join(internal_notes), user_insight

    # --- Matching Logic for Remaining Skills ---
    missing_skills_pp = []

    for i, jd_skill_pp in enumerate(remaining_jd_skills):
        if similarity_matrix.shape[1] > 0:
            best_match_score = np.max(similarity_matrix[i, :])
            best_match_index = np.argmax(similarity_matrix[i, :])
        else:
            best_match_score = 0.0; best_match_index = -1

        if best_match_score >= threshold and best_match_index != -1 and best_match_index < len(unique_resume_skills):
            found_skills_pp.append(jd_skill_pp)
            match_details_pp[jd_skill_pp] = (unique_resume_skills[best_match_index], round(float(best_match_score), 4))
        else:
            missing_skills_pp.append(jd_skill_pp)

    # --- Map back ---
    final_found = sorted([original_jd_skills_map.get(s, s) for s in found_skills_pp])
    final_missing = sorted([original_jd_skills_map.get(s, s) for s in missing_skills_pp])
    final_match_details = {original_jd_skills_map.get(k, k): v for k, v in match_details_pp.items()}

    # --- Generate Justifications ---
    found_count = len(final_found)
    match_percentage = round((found_count / total_jd_skills_unique) * 100, 1) if total_jd_skills_unique > 0 else 100.0
    internal_notes.append(f"Match Percentage: {match_percentage}%.")

    # User Insight Generation
    assessment_levels = [
        (85.0, "Excellent alignment."),
        (65.0, "Good alignment."),
        (40.0, "Moderate alignment."),
        (0.0, "Low alignment.")]
    assessment = _get_qualitative_assessment(match_percentage, assessment_levels)

    user_insight_parts = [f"Skill Check: {assessment}"]
    if final_found:
        # Mention types or key examples if possible - simplified: mention count
        user_insight_parts.append(f"Covers {found_count}/{total_jd_skills_unique} required skills.")
        # Example: Check for a common tech skill presence
        if any(f.lower() == 'python' for f in final_found):
            user_insight_parts.append("Core skills like Python appear present.")
    if final_missing:
        user_insight_parts.append(
            f"Potential gaps in skills like: {', '.join(final_missing[:2])}{'...' if len(final_missing) > 2 else ''}.")
    if not final_found and not final_missing and total_jd_skills_unique > 0:
        user_insight_parts.append("No skills matched the criteria.")

    user_insight = " ".join(user_insight_parts)

    return final_found, final_missing, final_match_details, " ".join(internal_notes), user_insight


# --- Responsibility Comparison (Revamped Justifications) ---
def compare_responsibility_lists(
    resume_responsibilities: List[str],
    jd_responsibilities: List[str],
    embed_model: BaseEmbedding,
    threshold: float
) -> Tuple[List[str], List[str], List[str], Dict[str, Tuple[str, float]], float, str, str]:
    """
    Compares responsibilities (JD as queries, Resume as docs).
    Returns: Tuple[matched_resp, possibly_matched_resp, missing_resp, match_details,
                   match_percentage, internal_justification, user_justification]
    """
    internal_notes = []
    user_insight = ""
    partial_match_threshold = threshold * 0.7  # 70% of main threshold for partial matches

    # --- Initial checks ---
    if not jd_responsibilities:
        user_insight = "No key responsibilities listed in the job description."
        internal_notes.append("No JD responsibilities.")
        return [], [], [], {}, 0.0, " ".join(internal_notes), user_insight

    # --- Preprocessing ---
    original_jd_resp_map = {preprocess_text(r): r for r in jd_responsibilities if isinstance(r, str)}
    original_resume_resp_map = {preprocess_text(r): r for r in resume_responsibilities if isinstance(r, str)}
    pp_jd_resp = sorted(list(set(filter(None, [preprocess_text(r) for r in jd_responsibilities]))))
    pp_resume_resp = sorted(list(set(filter(None, [preprocess_text(r) for r in resume_responsibilities]))))
    total_jd_resp_unique = len(pp_jd_resp)
    internal_notes.append(
        f"Compared {total_jd_resp_unique} JD resp (query) vs {len(pp_resume_resp)} resume resp (doc). Threshold={threshold} (Partial={partial_match_threshold:.2f}).")

    if not pp_jd_resp or not pp_resume_resp:
        missing_list = [original_jd_resp_map.get(r, r) for r in pp_jd_resp]
        user_insight = "Could not compare responsibilities due to lack of valid entries in JD or resume after processing."
        internal_notes.append("One list empty post-processing.")
        match_percentage = 0.0 if not pp_resume_resp else 100.0
        return [], [], sorted(missing_list), {}, match_percentage, " ".join(internal_notes), user_insight

    # --- Embedding and Similarity ---
    try:
        jd_embeddings_list = _get_text_embeddings(
            embed_model,
            pp_jd_resp,
            input_type="search_query",
        )
        if not jd_embeddings_list or len(jd_embeddings_list) != len(pp_jd_resp): raise ValueError("JD embedding failed")
        jd_embeddings = np.array(jd_embeddings_list, dtype=np.float32)

        resume_embeddings_list = _get_text_embeddings(
            embed_model,
            pp_resume_resp,
            input_type="search_document",
        )
        if not resume_embeddings_list or len(resume_embeddings_list) != len(pp_resume_resp): raise ValueError(
            "Resume embedding failed")
        resume_embeddings = np.array(resume_embeddings_list, dtype=np.float32)

        if resume_embeddings.shape[0] == 0 or jd_embeddings.shape[0] == 0: raise ValueError("Empty embeddings")
        similarity_matrix = calculate_batch_similarity(jd_embeddings, resume_embeddings)
        if similarity_matrix.shape[0] != total_jd_resp_unique or similarity_matrix.shape[1] != len(
            pp_resume_resp): raise ValueError("Matrix shape mismatch")
    except Exception as e:
        internal_notes.append(f"Embedding/Similarity Error: {e}.")
        user_insight = "An internal error prevented responsibility comparison."
        missing_list = sorted([original_jd_resp_map.get(r, r) for r in pp_jd_resp])
        return [], [], missing_list, {}, 0.0, " ".join(internal_notes), user_insight

    # --- Matching Logic ---
    matched_jd_resp_pp = []
    possibly_matched_jd_resp_pp = []  # New: partial matches
    missing_jd_resp_pp = []
    match_details_pp = {}

    for i, jd_resp_pp in enumerate(pp_jd_resp):
        if similarity_matrix.shape[1] > 0:
            best_match_score = np.max(similarity_matrix[i, :])
            best_match_index = np.argmax(similarity_matrix[i, :])
        else:
            best_match_score = 0.0
            best_match_index = -1

        if best_match_score >= threshold and best_match_index != -1 and best_match_index < len(pp_resume_resp):
            matched_jd_resp_pp.append(jd_resp_pp)
            match_details_pp[jd_resp_pp] = (pp_resume_resp[best_match_index], round(float(best_match_score), 4))
        elif best_match_score >= partial_match_threshold and best_match_index != -1 and best_match_index < len(
                pp_resume_resp):
            possibly_matched_jd_resp_pp.append(jd_resp_pp)
            match_details_pp[jd_resp_pp] = (pp_resume_resp[best_match_index], round(float(best_match_score), 4))
        else:
            missing_jd_resp_pp.append(jd_resp_pp)

    # --- Calculate Match Percentage (with partial matches counting as 0.5) ---
    full_match_value = len(matched_jd_resp_pp)
    partial_match_value = len(possibly_matched_jd_resp_pp) * 0.5
    effective_match_count = full_match_value + partial_match_value
    match_percentage = round((effective_match_count / total_jd_resp_unique) * 100,
                             1) if total_jd_resp_unique > 0 else 100.0

    internal_notes.append(
        f"Match Percentage: {match_percentage}% "
        f"(Full: {len(matched_jd_resp_pp)}, Partial: {len(possibly_matched_jd_resp_pp)})."
    )

    # --- Map back to original text ---
    final_matched = sorted([original_jd_resp_map.get(r, r) for r in matched_jd_resp_pp])
    final_possibly_matched = sorted([original_jd_resp_map.get(r, r) for r in possibly_matched_jd_resp_pp])
    final_missing = sorted([original_jd_resp_map.get(r, r) for r in missing_jd_resp_pp])
    final_match_details = {
        original_jd_resp_map.get(jd_r, jd_r): (original_resume_resp_map.get(res_r, res_r), score)
        for jd_r, (res_r, score) in match_details_pp.items()
    }

    # --- Generate User Justification ---
    user_insight_parts = [f"Duty Alignment Check:"]
    if matched_jd_resp_pp or possibly_matched_jd_resp_pp:
        user_insight_parts.append(
            f"Resume shows experience related to {len(matched_jd_resp_pp)}/{total_jd_resp_unique} "
            f"listed duties, with potential partial matches on {len(possibly_matched_jd_resp_pp)} more."
        )
        # Show examples of full matches first, then partial
        examples = []
        if matched_jd_resp_pp:
            examples.append(
                f"clear matches like '{original_jd_resp_map.get(matched_jd_resp_pp[0], matched_jd_resp_pp[0])[:50]}...'")
        if possibly_matched_jd_resp_pp:
            examples.append(
                f"possible matches like '{original_jd_resp_map.get(possibly_matched_jd_resp_pp[0], possibly_matched_jd_resp_pp[0])[:50]}...'")
        if examples:
            user_insight_parts.append(f"Examples include {', '.join(examples)}.")
    else:
        user_insight_parts.append(
            f"Limited direct connection found between specific resume examples and the {total_jd_resp_unique} general duties listed.")

    assessment_levels = [
        (65.0, "Suggests good coverage of related duties."),
        (40.0, "Suggests moderate coverage with some gaps."),
        (20.0, "Suggests partial coverage of duties."),
        (0.0, "Suggests limited connection to listed duties.")]
    assessment = _get_qualitative_assessment(match_percentage, assessment_levels)
    user_insight_parts.append(assessment)
    user_insight_parts.append("Partial matches receive half credit in scoring.")

    user_insight = " ".join(user_insight_parts)

    return (
        final_matched,
        final_possibly_matched,
        final_missing,
        final_match_details,
        match_percentage,
        " ".join(internal_notes),
        user_insight
    )


# --- Main ATS Logic (Revamped Justifications) ---
def advanced_ats_similarity(resume_dict: Dict[str, Any], job_description_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates ATS score based on Skills and Summary match, with a bonus for Responsibility alignment.
    Provides revamped, concise, insightful justifications.
    """
    try:
        embed_model: BaseEmbedding = get_embed_model()
    except (ValueError, RuntimeError) as e:
        return {  # User-friendly error
            "error": f"Initialization failed: {e}", "similarity_score": 0.0, "pass": False,
            "user_justification": {"overall": f"Analysis failed due to setup error.", "skills": "-",
                                   "responsibilities": "-", "work_experience_projects": "-"},
            "internal_justification": {"overall": f"Init Error: {e}", "skills": "-", "responsibilities": "-",
                                       "work_experience_projects": "-"}
        }

    # --- Initialize Results Structure ---
    results = {
        "similarity_score": 0.0, "pass": False,
        "required_skills_missing": [], "required_skills_found": [], "required_skills_found_count": 0,
        "total_required_skills_in_jd": 0, "required_skill_match_percentage": 0.0, "skill_match_details": {},
        "key_responsibilities_comparison": {"matched_responsibilities": [], "missing_responsibilities": [],
                                            "match_details": {}, "match_percentage": 0.0},
        "summary_comparison_score": 0.0,
        "section_scores": {"skills": 0.0, "work_experience_projects": 0.0},
        # Revamped Justification Keys
        "internal_justification": {"skills": "", "responsibilities": "", "work_experience_projects": "", "overall": ""},
        "user_justification": {"skills": "", "responsibilities": "", "work_experience_projects": "", "overall": ""},
        "notes": "", "job_description_required_skills": [], "job_description_key_responsibilities": [],
        "job_description_summary": "", "resume_summary": "",
    }

    # --- 1. Extract Original Data ---
    jd_req_skills_list_orig = job_description_dict.get("required_skills", [])
    jd_key_resp_list_orig = job_description_dict.get("key_responsibilities", [])
    jd_summary_orig = job_description_dict.get("summary", "")
    resume_summary_orig = resume_dict.get("summary", "")
    results["job_description_required_skills"] = jd_req_skills_list_orig
    results["job_description_key_responsibilities"] = jd_key_resp_list_orig
    results["job_description_summary"] = jd_summary_orig
    results["resume_summary"] = resume_summary_orig

    # --- 2. Skills Comparison ---
    resume_skills_list = resume_dict.get("keywords", [])
    if not isinstance(resume_skills_list, list): resume_skills_list = []
    req_found, req_missing, req_match_details, skill_int_just, skill_user_just = find_skill_matches_with_embeddings(
        resume_skills_list, jd_req_skills_list_orig, embed_model, SKILL_SIMILARITY_THRESHOLD
    )
    results["required_skills_found"] = req_found
    results["required_skills_missing"] = req_missing
    results["required_skills_found_count"] = len(req_found)
    results["skill_match_details"] = req_match_details
    unique_jd_req_skills_count = len(
        set(filter(None, [preprocess_text(s) for s in jd_req_skills_list_orig if isinstance(s, str)])))
    results["total_required_skills_in_jd"] = unique_jd_req_skills_count
    results["required_skill_match_percentage"] = round((len(req_found) / unique_jd_req_skills_count) * 100,
                                                       2) if unique_jd_req_skills_count > 0 else 100.0
    results["section_scores"]["skills"] = results["required_skill_match_percentage"]
    results["internal_justification"]["skills"] = skill_int_just
    results["user_justification"]["skills"] = skill_user_just

    # --- 3. Work Experience / Projects (Summary Comparison) ---
    summary_int_parts = []
    summary_user_insight = ""
    summary_similarity_score = 0.0

    pp_jd_summary = preprocess_text(jd_summary_orig)
    pp_resume_summary = preprocess_text(resume_summary_orig)
    summary_int_parts.append(f"Summary vs Summary comparison.")

    if not pp_jd_summary or not pp_resume_summary:
        summary_int_parts.append("Empty summary found.")
        summary_user_insight = "Resume or Job summary missing, high-level alignment not assessed."
        results["section_scores"]["work_experience_projects"] = 0.0
    else:
        try:
            jd_sum_emb = _get_text_embeddings(embed_model, [pp_jd_summary], input_type="search_query")[0]
            res_sum_emb = _get_text_embeddings(embed_model, [pp_resume_summary], input_type="search_document")[0]
            if jd_sum_emb is not None and res_sum_emb is not None:
                similarity_matrix = calculate_batch_similarity(np.array([jd_sum_emb]), np.array([res_sum_emb]))
                if similarity_matrix.size > 0:
                    summary_similarity_score = float(similarity_matrix[0, 0])
                    results["summary_comparison_score"] = round(summary_similarity_score, 4)
                    summary_score_100 = round(summary_similarity_score * 100, 2)
                    results["section_scores"]["work_experience_projects"] = summary_score_100
                    summary_int_parts.append(f"Raw similarity: {results['summary_comparison_score']:.3f}.")

                    assessment_levels = [
                        (80.0, "Strong alignment suggests good high-level relevance."),
                        (60.0, "Good alignment suggests reasonable high-level relevance."),
                        (40.0, "Moderate alignment suggests some potential relevance."),
                        (0.0, "Low alignment suggests potential divergence in focus.")]
                    summary_user_insight = f"Summary Check: {_get_qualitative_assessment(summary_score_100, assessment_levels)}"

                else:
                    raise ValueError("Summary similarity calc failed.")
            else:
                raise ValueError("Summary embedding failed.")
        except Exception as e:
            summary_int_parts.append(f"Error: {e}.")
            summary_user_insight = "Could not assess summary alignment due to an error."
            results["section_scores"]["work_experience_projects"] = 0.0

    results["internal_justification"]["work_experience_projects"] = " ".join(summary_int_parts)
    results["user_justification"]["work_experience_projects"] = summary_user_insight

    # --- 4. Key Responsibilities Comparison (for Bonus) ---
    resume_resp_list = []
    resume_resp_list = resume_dict.get('key_responsibilities', [])

    matched_resp, possibly_matched_resp, missing_resp, resp_match_details, resp_match_percentage, resp_int_just, resp_user_just = compare_responsibility_lists(
        resume_resp_list, jd_key_resp_list_orig, embed_model, RESPONSIBILITY_SIMILARITY_THRESHOLD
    )
    results["key_responsibilities_comparison"]["matched_responsibilities"] = matched_resp
    results["key_responsibilities_comparison"]["possibly_matched_responsibilities"] = possibly_matched_resp  # New field
    results["key_responsibilities_comparison"]["missing_responsibilities"] = missing_resp
    results["key_responsibilities_comparison"]["match_details"] = resp_match_details
    results["key_responsibilities_comparison"]["match_percentage"] = resp_match_percentage
    results["internal_justification"]["responsibilities"] = resp_int_just
    results["user_justification"]["responsibilities"] = resp_user_just

    # --- 5. Calculate Final Score (Weighted Base + Responsibility Bonus) ---
    internal_overall_parts = []

    weight_skills = 0.50
    weight_summary = 0.50
    internal_overall_parts.append(f"Base weights: Skills={weight_skills:.2f}, Summary={weight_summary:.2f}.")

    skills_score_100 = results["section_scores"]["skills"]
    summary_score_100 = results["section_scores"]["work_experience_projects"]

    # Modified scoring with partial matches
    full_match_value = len(matched_resp)
    partial_match_value = len(possibly_matched_resp) * 0.5
    effective_match_count = full_match_value + partial_match_value
    resp_match_perc_for_bonus = (effective_match_count / len(
        jd_key_resp_list_orig)) * 100 if jd_key_resp_list_orig else 0

    base_score_100 = (skills_score_100 * weight_skills) + (summary_score_100 * weight_summary)
    bonus_amount = (base_score_100 / 100.0) * RESPONSIBILITY_BONUS_FACTOR * (resp_match_perc_for_bonus / 100.0)
    bonus_percent = round(bonus_amount * 100, 2)
    internal_overall_parts.append(
        f"Base: {base_score_100:.2f}. Bonus: +{bonus_percent:.2f} (Factor:{RESPONSIBILITY_BONUS_FACTOR}, Resp%:{resp_match_perc_for_bonus:.1f}).")

    final_score_combined = base_score_100 + bonus_percent
    vector_score = round(max(0.0, min(100.0, final_score_combined)), 2)
    bm25_score = _bm25_similarity_score(resume_dict, job_description_dict)
    hybrid_score = round(
        (vector_score * HYBRID_VECTOR_WEIGHT) + (bm25_score * HYBRID_BM25_WEIGHT),
        2,
    )

    results["vector_similarity_score"] = vector_score
    results["bm25_similarity_score"] = bm25_score
    results["hybrid_weights"] = {
        "vector": HYBRID_VECTOR_WEIGHT,
        "bm25": HYBRID_BM25_WEIGHT,
    }
    results["similarity_score"] = hybrid_score
    results["pass"] = hybrid_score >= PASS_THRESHOLD
    internal_overall_parts.append(
        f"Vector: {vector_score:.2f}. BM25: {bm25_score:.2f}. Hybrid: {hybrid_score:.2f}."
    )
    internal_overall_parts.append(f"Pass: {results['pass']} (Thresh:{PASS_THRESHOLD}).")

    # Rest remains exactly the same
    jd_skills_combined_set = set(filter(None, [preprocess_text(s) for s in jd_req_skills_list_orig]))
    jd_title_lower = str(job_description_dict.get('job_title', '')).lower()
    is_technical_job = any(skill in TECHNICAL_KEYWORDS_SEED for skill in jd_skills_combined_set) or \
                       any(indicator in jd_title_lower for indicator in
                           ['engineer', 'developer', 'programmer', 'scientist', 'technical', 'analyst', 'architect',
                            'data', 'software', 'ml', 'ai', 'backend', 'frontend'])
    results["notes"] = f"Tech job profile: {is_technical_job}."
    results["internal_justification"]["overall"] = " ".join(internal_overall_parts)

    # --- 6. Generate User-Friendly Overall Justification ---
    user_overall_parts = []
    assessment_levels = [
        (85.0, "Very Strong Match."),
        (PASS_THRESHOLD, f"Good Match (meets threshold of {PASS_THRESHOLD}%)."),
        (50.0, "Partial Match (below threshold)."),
        (0.0, "Low Match (below threshold).")]
    overall_assessment = _get_qualitative_assessment(hybrid_score, assessment_levels)

    user_overall_parts.append(f"Overall Assessment: {overall_assessment}")
    user_overall_parts.append("Key factors influencing the score:")
    user_overall_parts.append(f"- Skills: {results['user_justification']['skills']}")
    user_overall_parts.append(f"- Summary Relevance: {results['user_justification']['work_experience_projects']}")
    user_overall_parts.append(
        f"- Duty Alignment: {results['user_justification']['responsibilities']}")  # Already includes bonus context

    # Concise recommendation / next step hint
    if results["pass"]:
        user_overall_parts.append(
            "Recommendation: Profile shows strong potential based on key areas. Recommended for review.")
    else:
        user_overall_parts.append(
            "Recommendation: Profile may have gaps in key areas relative to requirements. Review details or consider other candidates.")

    results["user_justification"]["overall"] = " ".join(user_overall_parts)

    return results

# Note: The driver code (if __name__ == '__main__': ...) has been removed as requested.
# You would call advanced_ats_similarity(resume_dict, jd_dict) elsewhere in your application.