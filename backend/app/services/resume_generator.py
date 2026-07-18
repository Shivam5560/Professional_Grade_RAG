"""
Resume Generator Service – LaTeX-based PDF generation.
Adapted from ResumeGen for the Professional_Grade_RAG backend.
"""

import os
import subprocess
import tempfile
import shutil
from typing import Dict, Any, List, Union, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LatexResumeGenerator:
    """Generates LaTeX resumes and compiles them to PDF."""

    # ─── LaTeX escaping ──────────────────────────────────────────

    @staticmethod
    def _escape(text: Union[str, List, None]) -> str:
        if isinstance(text, list):
            text = ", ".join(str(i) for i in text)
        elif not isinstance(text, str):
            text = str(text) if text is not None else ""
        if not text:
            return ""
        
        out = text
        
        # Map common non-ASCII/Unicode characters to their safe LaTeX/ASCII representations
        for uni_char, safe_char in {
            "\u2011": "-",        # Non-breaking hyphen
            "\u202f": " ",        # Narrow no-break space
            "\u00a0": " ",        # No-break space
            "\u2013": "--",       # En dash
            "\u2014": "---",      # Em dash
            "\u201c": "``",       # Left double quote
            "\u201d": "''",       # Right double quote
            "\u2018": "`",        # Left single quote
            "\u2019": "'",        # Right single quote
            "\u2248": "approx. ", # Approximation sign
            "•": "*",             # Bullet point
        }.items():
            out = out.replace(uni_char, safe_char)

        # Normalize remaining accented characters to standard ASCII counterparts
        import unicodedata
        out = unicodedata.normalize('NFKD', out).encode('ascii', 'ignore').decode('ascii')

        out = out.replace("\\", r"\textbackslash{}")
        for char, esc in {
            "{": r"\{", "}": r"\}", "&": r"\&", "%": r"\%",
            "$": r"\$", "#": r"\#", "^": r"\textasciicircum{}",
            "_": r"\_", "~": r"\textasciitilde{}",
        }.items():
            out = out.replace(char, esc)
        return out

    @staticmethod
    def _escape_url(value: Any) -> str:
        url = str(value or "").strip()
        if not url or any(char in url for char in ("\r", "\n", "\x00")):
            return ""
        if not url.startswith(("https://", "http://", "mailto:")):
            url = f"https://{url}"
        url = url.replace("\\", "%5C").replace("{", "%7B").replace("}", "%7D")
        for char, escaped in (("%", r"\%"), ("#", r"\#"), ("&", r"\&"), ("_", r"\_"), ("$", r"\$"), ("^", "%5E"), ("~", "%7E")):
            url = url.replace(char, escaped)
        return url[:2000]

    # ─── Template ────────────────────────────────────────────────

    TEMPLATE = r"""
\documentclass[letterpaper,11pt]{article}
\usepackage{latexsym}
\usepackage[margin=1in]{geometry}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1.2in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.5in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{\vspace{-4pt}\scshape\raggedright\large}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\newcommand{\resumeItem}[1]{\item \small{{#1 \vspace{-2pt}}}}
\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small#4} \\
    \end{tabular*}\vspace{-5pt}
}
\newcommand{\resumeProjectHeading}[2]{
    \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-5pt}
}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}

\begin{center}
    \textbf{\Huge \scshape {{NAME}}} \\ \vspace{1pt}
     {{CONTACT}}
\end{center}

{{RESUME_BODY}}

\end{document}
"""

    # ─── Section builders ────────────────────────────────────────

    def _build_contact(self, data: Dict[str, Any]) -> str:
        email = self._escape(data.get("email", ""))
        phone = self._escape(data.get("phone", ""))
        location = self._escape(data.get("location", ""))
        linkedin = data.get("linkedin_url", "")
        github = data.get("github_url", "")
        portfolio = data.get("portfolio_url", "")
        parts: List[str] = []
        if email:
            parts.append(f"\\href{{mailto:{email}}}{{\\underline{{{email}}}}}")
        if phone:
            parts.append(phone)
        if location:
            parts.append(location)
        first = " $|$ ".join(parts)
        second_parts: List[str] = []
        if linkedin:
            clean = linkedin.replace("https://", "").replace("http://", "").replace("www.", "")
            second_parts.append(f"\\href{{{self._escape_url(linkedin)}}}{{\\underline{{{self._escape(clean)}}}}}")
        if github:
            clean = github.replace("https://", "").replace("http://", "")
            second_parts.append(f"\\href{{{self._escape_url(github)}}}{{\\underline{{{self._escape(clean)}}}}}")
        if portfolio:
            clean = portfolio.replace("https://", "").replace("http://", "").replace("www.", "")
            second_parts.append(f"\\href{{{self._escape_url(portfolio)}}}{{\\underline{{{self._escape(clean)}}}}}")
        if second_parts:
            return f"{first} \\\\ " + " $|$\n    ".join(second_parts)
        return first

    def _build_summary(self, summary: str) -> str:
        if not summary or not summary.strip():
            return ""
        return f"\\section{{Professional Summary}}\n\\small{{{self._escape(summary.strip())}}}"

    def _build_experience(self, exps: List[Dict[str, Any]]) -> str:
        if not exps:
            return ""
        out = "\\section{Professional Experience}\n  \\resumeSubHeadingListStart\n"
        for exp in exps:
            title = self._escape(exp.get("title", ""))
            dates = self._escape(exp.get("dates", ""))
            company = self._escape(exp.get("company", ""))
            location = self._escape(exp.get("location", ""))
            out += f"    \\resumeSubheading\n      {{{title}}}{{{dates}}}\n      {{{company}}}{{{location}}}\n"
            out += "      \\resumeItemListStart\n"
            for resp in exp.get("responsibilities", []):
                r = resp if isinstance(resp, str) else ", ".join(str(i) for i in resp) if isinstance(resp, list) else str(resp or "")
                if r.strip():
                    out += f"        \\resumeItem{{{self._escape(r.strip())}}}\n"
            out += "      \\resumeItemListEnd\n"
        out += "  \\resumeSubHeadingListEnd"
        return out

    def _build_education(self, edus: List[Dict[str, Any]]) -> str:
        if not edus:
            return ""
        out = "\\section{Education}\n  \\resumeSubHeadingListStart\n"
        for edu in edus:
            detail = " --- ".join(
                item for item in (
                    self._escape(edu.get("location", "")),
                    f"GPA {self._escape(edu.get('gpa', ''))}" if edu.get("gpa") else "",
                ) if item
            )
            out += (
                f"    \\resumeSubheading\n"
                f"      {{{self._escape(edu.get('institution', ''))}}}"
                f"{{{self._escape(edu.get('graduation_date', ''))}}}\n"
                f"      {{{self._escape(edu.get('degree', ''))}}}"
                f"{{{detail}}}\n"
            )
        out += "  \\resumeSubHeadingListEnd"
        return out

    def _build_projects(self, projs: List[Dict[str, Any]]) -> str:
        if not projs:
            return ""
        out = "\\section{Projects}\n  \\resumeSubHeadingListStart\n"
        for proj in projs:
            title = self._escape(proj.get("title", ""))
            dates = self._escape(proj.get("dates", ""))
            link = proj.get("link", "")
            heading = f"\\textbf{{{title}}}"
            if link:
                heading = f"\\href{{{self._escape_url(link)}}}{{{heading}}}"
            out += f"      \\resumeProjectHeading\n        {{{heading}}}{{{dates}}} \n      \\resumeItemListStart\n"
            descs = proj.get("descriptions", proj.get("description", []))
            if isinstance(descs, str):
                descs = [descs]
            for d in descs:
                ds = d if isinstance(d, str) else str(d or "")
                if ds.strip():
                    out += f"        \\resumeItem{{{self._escape(ds.strip())}}}\n"
            technologies = self._escape(proj.get("technologies", ""))
            if technologies:
                out += f"        \\resumeItem{{Technologies: {technologies}}}\n"
            out += "      \\resumeItemListEnd\n"
        out += "  \\resumeSubHeadingListEnd"
        return out

    def _build_skills(self, skills: Dict[str, Any]) -> str:
        if not skills:
            return ""
        _names = {
            "languages": "Languages", "tools": "Tools", "technologies": "Technologies",
            "frameworks": "Frameworks", "libraries": "Libraries",
            "frameworks_libraries": "Frameworks \\& Libraries",
            "databases": "Databases", "concepts": "Concepts",
            "soft_skills": "Soft Skills", "operating_systems": "Operating Systems",
            "data_visualization": "Data \\& Visualization",
        }
        items: List[str] = []
        for key, val in skills.items():
            if val and str(val).strip():
                clean = key.lower().replace(" ", "_").replace("-", "_")
                name = _names.get(clean, key.replace("_", " ").replace("-", " ").title())
                items.append(f"  \\item \\textbf{{{name}:}} {self._escape(val)}")
        if not items:
            return ""
        return "\\section{Additional}\n\\begin{itemize}\n" + "\n".join(items) + "\n\\end{itemize}"

    def _build_named_records(self, title: str, records: List[Dict[str, Any]]) -> str:
        items: List[str] = []
        for record in records:
            name = self._escape(record.get("name", ""))
            if not name:
                continue
            link = self._escape_url(record.get("link", ""))
            display_name = f"\\href{{{link}}}{{{name}}}" if link else name
            details = [self._escape(record.get(key, "")) for key in ("issuer", "date", "proficiency")]
            suffix = " --- ".join(item for item in details if item)
            items.append(f"  \\item \\textbf{{{display_name}}}" + (f" --- {suffix}" if suffix else ""))
        if not items:
            return ""
        return f"\\section{{{self._escape(title)}}}\n\\begin{{itemize}}\n" + "\n".join(items) + "\n\\end{itemize}"

    def _build_custom_sections(self, sections: List[Dict[str, Any]]) -> str:
        output: List[str] = []
        for section in sections:
            title = self._escape(section.get("title", ""))
            items = [self._escape(item) for item in section.get("items", []) if str(item).strip()]
            if title and items:
                output.append(f"\\section{{{title}}}\n\\begin{{itemize}}\n" + "\n".join(f"  \\item {item}" for item in items) + "\n\\end{itemize}")
        return "\n\n".join(output)

    # ─── Generate ────────────────────────────────────────────────

    def generate_latex(self, data: Dict[str, Any]) -> str:
        content = self.TEMPLATE
        content = content.replace("{{NAME}}", self._escape(data.get("name", "")))
        content = content.replace("{{CONTACT}}", self._build_contact(data))
        sections = {
            "summary": self._build_summary(data.get("summary", "")),
            "experience": self._build_experience(data.get("experiences", data.get("experience", []))),
            "education": self._build_education(data.get("education", [])),
            "projects": self._build_projects(data.get("projects", [])),
            "skills": self._build_skills(data.get("skills", {})),
            "certifications": self._build_named_records("Certifications", data.get("certifications", [])),
            "awards": self._build_named_records("Awards", data.get("awards", [])),
            "languages": self._build_named_records("Languages", data.get("languages", [])),
            "custom_sections": self._build_custom_sections(data.get("custom_sections", [])),
        }
        default_order = ["summary", "experience", "education", "projects", "skills", "certifications", "awards", "languages", "custom_sections"]
        requested = [item for item in data.get("section_order", []) if item in sections]
        order = requested + [item for item in default_order if item not in requested]
        content = content.replace("{{RESUME_BODY}}", "\n\n".join(sections[item] for item in order if sections[item]))
        return content

    def compile_pdf(self, latex_content: str, output_path: str) -> Dict[str, Any]:
        """Compile LaTeX to PDF using pdflatex."""
        with tempfile.TemporaryDirectory() as tmp:
            tex = os.path.join(tmp, "resume.tex")
            pdf = os.path.join(tmp, "resume.pdf")
            with open(tex, "w", encoding="utf-8") as f:
                f.write(latex_content)
            try:
                last_err = ""
                for _ in range(2):
                    result = subprocess.run(
                        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory", tmp, tex],
                        capture_output=True, text=True, timeout=30,
                    )
                    if result.returncode != 0:
                        last_err = (result.stderr or result.stdout or "").strip()
                        break
                if os.path.exists(pdf):
                    shutil.copy2(pdf, output_path)
                    return {"success": True, "message": "PDF generated", "pdf_path": output_path}
                message = "pdflatex compilation failed"
                if last_err:
                    message = f"{message}: {last_err[-500:]}"
                return {"success": False, "message": message, "pdf_path": None}
            except FileNotFoundError:
                return {"success": False, "message": "pdflatex not installed", "pdf_path": None}
            except Exception as e:
                return {"success": False, "message": str(e), "pdf_path": None}


def check_latex_available() -> bool:
    """Check if pdflatex is available on the system."""
    try:
        result = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def generate_resume_pdf(data: Dict[str, Any], output_path: str) -> Dict[str, Any]:
    """Convenience: generate LaTeX and compile to PDF in one call."""
    gen = LatexResumeGenerator()
    latex = gen.generate_latex(data)
    return gen.compile_pdf(latex, output_path)


def generate_resume_latex(data: Dict[str, Any]) -> str:
    """Return the LaTeX source string without compiling."""
    return LatexResumeGenerator().generate_latex(data)
