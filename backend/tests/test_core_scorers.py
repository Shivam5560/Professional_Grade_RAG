"""Quick test for core scorers."""

from app.services.nexus_ai.core.scorers import (
    compute_technical_score,
    compute_ats_score,
    compute_grammar_score,
    compute_section_score,
    compute_overall_score,
)


def test_technical_score():
    result = compute_technical_score(
        candidate_skills=["Python", "JavaScript", "React"],
        required_skills=["Python", "TypeScript", "React", "Node.js"],
        preferred_skills=["Docker", "AWS"]
    )
    print(f"Technical Score: {result['score']}")
    print(f"Matched Required: {result['matched_required']}")
    print(f"Missing Required: {result['missing_required']}")
    assert 0 <= result["score"] <= 100
    assert "Python" in result["matched_required"]
    assert "React" in result["matched_required"]


def test_ats_score():
    resume = """
    John Doe
    john.doe@email.com | 555-123-4567 | LinkedIn
    
    SUMMARY
    Experienced Python developer with 5 years of experience.
    
    EXPERIENCE
    Senior Developer at Acme Corp (2020-Present)
    - Developed scalable applications
    - Led team of 5 engineers
    
    EDUCATION
    BS Computer Science, MIT, 2015
    
    SKILLS
    Python, React, Node.js, PostgreSQL
    """
    
    jd = """
    Looking for a Python Developer with React experience.
    Must have 3+ years experience in backend development.
    Required: Python, PostgreSQL, API development.
    """
    
    result = compute_ats_score(resume, jd)
    print(f"ATS Score: {result['score']}")
    print(f"Keyword Match: {result['keyword_match_score']}")
    print(f"Section Score: {result['section_score']}")
    print(f"Matched Keywords: {result['matched_keywords']}")
    assert 0 <= result["score"] <= 100


def test_grammar_score():
    resume_text = """
    - Developed scalable Python applications serving 50,000 users daily
    - Led cross-functional team of 5 engineers, achieving 20% productivity increase
    - Implemented CI/CD pipeline reducing deployment time by 40%
    - Optimized database queries, improving response time by 65%
    - Mentored 3 junior developers on best practices
    """
    
    result = compute_grammar_score(resume_text)
    print(f"Grammar Score: {result['score']}")
    print(f"Action Verbs Found: {result['action_verbs_used']}")
    print(f"Quantified Achievements: {result['quantified_achievements']}")
    print(f"Suggestions: {result['suggestions']}")
    assert 0 <= result["score"] <= 100
    assert len(result["action_verbs_used"]) > 0


def test_section_score():
    section_assessment = {
        "contact_info": {"present": True, "quality": "good", "feedback": "Complete"},
        "summary": {"present": True, "quality": "good", "feedback": "Well written"},
        "experience": {"present": True, "quality": "good", "feedback": "Strong experience"},
        "education": {"present": True, "quality": "fair", "feedback": "Could add more detail"},
        "skills": {"present": True, "quality": "good", "feedback": "Comprehensive"},
    }
    
    result = compute_section_score(section_assessment)
    print(f"Section Score: {result['score']}")
    assert 0 <= result["score"] <= 100
    assert "sections" in result


def test_overall_score():
    result = compute_overall_score(
        technical_score=75,
        ats_score=80,
        grammar_score=85,
        section_score=90
    )
    print(f"Overall Score: {result['overall_score']}")
    print(f"Fit Category: {result['fit_category']}")
    print(f"Breakdown: {result['breakdown']}")
    assert 0 <= result["overall_score"] <= 100
    assert result["fit_category"] in ["Strong Match", "Good Match", "Moderate Match", "Needs Improvement"]


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Technical Score...")
    test_technical_score()
    print("✓ Technical Score test passed\n")
    
    print("=" * 50)
    print("Testing ATS Score...")
    test_ats_score()
    print("✓ ATS Score test passed\n")
    
    print("=" * 50)
    print("Testing Grammar Score...")
    test_grammar_score()
    print("✓ Grammar Score test passed\n")
    
    print("=" * 50)
    print("Testing Section Score...")
    test_section_score()
    print("✓ Section Score test passed\n")
    
    print("=" * 50)
    print("Testing Overall Score...")
    test_overall_score()
    print("✓ Overall Score test passed\n")
    
    print("=" * 50)
    print("ALL TESTS PASSED ✓")
