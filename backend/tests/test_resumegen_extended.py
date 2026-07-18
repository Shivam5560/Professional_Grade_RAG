from app.api.routes.resumegen import GenerateRequest
from app.services.resume_generator import generate_resume_latex


def test_renders_extended_resume_sections() -> None:
    latex = generate_resume_latex(
        {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+1 555 0100",
            "portfolio_url": "https://jane.dev",
            "summary": "Data leader focused on trustworthy systems.",
            "experiences": [
                {
                    "title": "Data Engineer",
                    "company": "Acme",
                    "location": "Remote",
                    "dates": "2022--Present",
                    "responsibilities": ["Built resilient pipelines"],
                }
            ],
            "certifications": [{"name": "AWS Solutions Architect", "issuer": "AWS", "date": "2025"}],
            "awards": [{"name": "Engineering Excellence", "issuer": "Acme", "date": "2024"}],
            "languages": [{"name": "English", "proficiency": "Fluent"}],
            "custom_sections": [{"title": "Community", "items": ["Mentored new engineers"]}],
        }
    )

    assert "+1 555 0100" in latex
    assert "Professional Summary" in latex
    assert "Certifications" in latex
    assert "Awards" in latex
    assert "Languages" in latex
    assert "Community" in latex
    assert "Mentored new engineers" in latex


def test_accepts_the_existing_resume_payload_aliases() -> None:
    request = GenerateRequest.model_validate(
        {
            "data": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "experience": [
                    {
                        "position": "Engineer",
                        "company": "Acme",
                        "duration": "2020-2024",
                        "responsibilities": ["Shipped systems"],
                    }
                ],
                "education": [],
                "projects": [],
                "skills": {"Languages": ["Python", "SQL"]},
            },
            "format": "latex",
        }
    )

    latex = generate_resume_latex(request.data.model_dump())
    assert "Engineer" in latex
    assert "Acme" in latex
    assert "Python, SQL" in latex


def test_resume_links_cannot_break_out_of_latex_href() -> None:
    latex = generate_resume_latex(
        {
            "name": "Jane",
            "email": "jane@example.com",
            "portfolio_url": "https://example.com/}\\input{/tmp/secret}",
            "projects": [
                {
                    "title": "Work",
                    "link": "https://example.com/}\\write18{touch hacked}",
                    "descriptions": [],
                }
            ],
        }
    )

    assert r"}\input{" not in latex
    assert r"}\write18{" not in latex
    assert "%7D" in latex
