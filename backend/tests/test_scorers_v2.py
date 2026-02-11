"""Production-grade tests for scorers_v2."""

from app.services.nexus_ai.core.scorers_v2 import (
    compute_technical_score,
    compute_ats_score,
    compute_grammar_score,
    compute_section_score,
    compute_overall_score,
    skills_match,
    get_canonical_skill,
    calculate_readability_scores,
    validate_contact_info,
    calculate_keyword_density,
    analyze_resume_length,
    SKILL_SYNONYMS,
)


def test_skill_synonyms():
    """Test skill synonym matching."""
    print("\n--- Testing Skill Synonyms ---")
    
    # Test synonym resolution
    assert get_canonical_skill("JS") == "javascript"
    assert get_canonical_skill("React.js") == "react"
    assert get_canonical_skill("Node") == "nodejs"
    assert get_canonical_skill("PostgreSQL") == "postgresql"
    assert get_canonical_skill("K8s") == "kubernetes"
    
    # Test fuzzy matching
    assert skills_match("JavaScript", "JS")
    assert skills_match("React", "ReactJS")
    assert skills_match("Python", "python3")
    assert skills_match("Docker", "containerization")
    
    print("✓ All synonym tests passed")


def test_technical_score_production():
    """Test production-grade technical scoring."""
    print("\n--- Testing Technical Score ---")
    
    result = compute_technical_score(
        candidate_skills=["Python", "React.js", "PostgreSQL", "Docker", "AWS"],
        required_skills=["Python", "JavaScript", "SQL", "React", "Node.js"],
        preferred_skills=["Docker", "AWS", "Kubernetes"],
        jd_text="We need a Python developer with React and Node.js experience. Must know SQL databases."
    )
    
    print(f"Score: {result['score']}")
    print(f"Matched Required: {result['matched_required']}")
    print(f"Missing Required: {result['missing_required']}")
    print(f"Matched Preferred: {result['matched_preferred']}")
    print(f"Categories: {list(result['skill_categories'].keys())}")
    
    assert 0 <= result["score"] <= 100
    assert "Python" in result["matched_required"]
    # React.js should match React
    assert "React" in result["matched_required"] or "react" in str(result["matched_required"]).lower()
    print("✓ Technical score test passed")


def test_ats_score_production():
    """Test comprehensive ATS scoring."""
    print("\n--- Testing ATS Score ---")
    
    resume = """
    John Doe
    john.doe@company.com | 555-123-4567 | linkedin.com/in/johndoe
    
    PROFESSIONAL SUMMARY
    Experienced Python developer with 7 years of experience building scalable applications.
    
    EXPERIENCE
    Senior Software Engineer at Acme Corp (Jan 2020 - Present)
    - Developed microservices using Python and FastAPI
    - Led migration to Kubernetes, reducing deployment time by 60%
    - Managed team of 5 engineers across 3 projects
    
    Software Engineer at Tech Inc (Jun 2017 - Dec 2019)
    - Built REST APIs serving 100K daily requests
    - Implemented CI/CD pipeline with Jenkins
    
    EDUCATION
    BS Computer Science, MIT, 2017
    
    SKILLS
    Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, React, Git
    """
    
    jd = """
    Senior Python Developer - Backend Team
    
    Required:
    - 5+ years Python experience
    - Experience with FastAPI or Django
    - PostgreSQL and SQL databases
    - Docker and Kubernetes
    - REST API development
    
    Preferred:
    - AWS experience
    - CI/CD experience
    - Team leadership
    """
    
    result = compute_ats_score(resume, jd)
    
    print(f"Overall ATS Score: {result['score']}")
    print(f"Components:")
    for comp, data in result["components"].items():
        print(f"  - {comp}: {data['score']} ({data['weight']})")
    print(f"Issues: {result['all_issues']}")
    
    assert 0 <= result["score"] <= 100
    assert result["components"]["contact_info"]["email"] == True
    assert result["components"]["contact_info"]["phone"] == True
    assert result["components"]["contact_info"]["linkedin"] == True
    print("✓ ATS score test passed")


def test_grammar_score_production():
    """Test comprehensive grammar scoring."""
    print("\n--- Testing Grammar Score ---")
    
    resume_text = """
    PROFESSIONAL EXPERIENCE
    
    - Spearheaded development of microservices architecture, reducing latency by 40%
    - Led cross-functional team of 8 engineers, delivering 15 features per quarter
    - Implemented automated testing framework, increasing code coverage from 45% to 92%
    - Optimized database queries, improving response time by 65%
    - Mentored 3 junior developers, resulting in 2 promotions within 6 months
    - Architected real-time data pipeline processing 1M+ events daily
    - Reduced infrastructure costs by $50,000 annually through optimization
    - Developed customer-facing API with 99.9% uptime SLA
    """
    
    result = compute_grammar_score(resume_text)
    
    print(f"Overall Grammar Score: {result['score']}")
    print(f"Components:")
    for comp, data in result["components"].items():
        if isinstance(data, dict) and "score" in data:
            print(f"  - {comp}: {data['score']} ({data.get('weight', '')})")
    print(f"Action Verbs: {result['action_verbs_used']}")
    print(f"Quantified: {result['quantified_achievements']} metrics")
    print(f"Readability: {result['readability_scores']}")
    print(f"Suggestions: {len(result['suggestions'])} items")
    
    assert 0 <= result["score"] <= 100
    assert len(result["action_verbs_used"]) > 0
    assert result["quantified_achievements"] > 0
    print("✓ Grammar score test passed")


def test_readability():
    """Test readability calculations."""
    print("\n--- Testing Readability ---")
    
    # Professional resume text
    text = """
    Led the development of a distributed system handling 100K requests per second.
    Implemented microservices architecture using Docker and Kubernetes.
    Reduced operational costs by 40% through automated infrastructure management.
    """
    
    result = calculate_readability_scores(text)
    
    print(f"Flesch Reading Ease: {result['flesch_reading_ease']}")
    print(f"Flesch-Kincaid Grade: {result['flesch_kincaid_grade']}")
    print(f"Avg Words/Sentence: {result['avg_words_per_sentence']}")
    
    assert 0 <= result["flesch_reading_ease"] <= 100
    assert 0 <= result["flesch_kincaid_grade"] <= 20
    print("✓ Readability test passed")


def test_contact_validation():
    """Test contact info validation."""
    print("\n--- Testing Contact Validation ---")
    
    text = """
    John Doe
    john.doe@example.com
    (555) 123-4567
    linkedin.com/in/johndoe
    """
    
    result = validate_contact_info(text)
    
    print(f"Email: {result['email']}")
    print(f"Phone: {result['phone']}")
    print(f"LinkedIn: {result['linkedin']}")
    
    assert result["email"]["found"] == True
    assert result["email"]["valid"] == True
    assert result["phone"]["found"] == True
    assert result["linkedin"]["found"] == True
    print("✓ Contact validation test passed")


def test_keyword_density():
    """Test keyword density analysis."""
    print("\n--- Testing Keyword Density ---")
    
    resume = "Python developer with React and Node.js experience. Strong in PostgreSQL."
    jd = "Looking for Python Python Python developer with React experience. Node.js preferred. PostgreSQL required."
    
    result = calculate_keyword_density(resume, jd)
    
    print(f"Score: {result['score']}")
    print(f"Matched: {result['matched_keywords']}")
    print(f"Missing: {result['missing_keywords']}")
    
    assert 0 <= result["score"] <= 100
    assert "python" in result["matched_keywords"]
    print("✓ Keyword density test passed")


def test_resume_length():
    """Test resume length analysis."""
    print("\n--- Testing Resume Length ---")
    
    # Short resume
    short = "Python developer. " * 50
    result_short = analyze_resume_length(short)
    print(f"Short: {result_short['word_count']} words - {result_short['assessment']}")
    
    # Optimal resume
    optimal = "Experienced Python developer with strong skills. " * 100
    result_optimal = analyze_resume_length(optimal)
    print(f"Optimal: {result_optimal['word_count']} words - {result_optimal['assessment']}")
    
    # Long resume
    long = "Senior engineer with extensive experience. " * 400
    result_long = analyze_resume_length(long)
    print(f"Long: {result_long['word_count']} words - {result_long['assessment']}")
    
    assert result_short["assessment"] in ["too_short", "optimal"]
    assert result_long["assessment"] == "too_long"
    print("✓ Resume length test passed")


def test_overall_score():
    """Test overall score calculation."""
    print("\n--- Testing Overall Score ---")
    
    result = compute_overall_score(
        technical_score=85,
        ats_score=78,
        grammar_score=82,
        section_score=90
    )
    
    print(f"Overall: {result['overall_score']}")
    print(f"Category: {result['fit_category']}")
    print(f"Description: {result['fit_description']}")
    print(f"Breakdown: {result['breakdown']}")
    
    assert 0 <= result["overall_score"] <= 100
    assert result["fit_category"] in ["Excellent Match", "Strong Match", "Good Match", 
                                      "Moderate Match", "Developing Match", "Not Recommended"]
    print("✓ Overall score test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("PRODUCTION-GRADE SCORER TESTS")
    print("=" * 60)
    
    test_skill_synonyms()
    test_technical_score_production()
    test_ats_score_production()
    test_grammar_score_production()
    test_readability()
    test_contact_validation()
    test_keyword_density()
    test_resume_length()
    test_overall_score()
    
    print("\n" + "=" * 60)
    print("ALL PRODUCTION TESTS PASSED ✓")
    print("=" * 60)
