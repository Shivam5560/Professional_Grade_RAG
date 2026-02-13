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
        out = out.replace("\\", r"\textbackslash{}")
        for char, esc in {
            "{": r"\{", "}": r"\}", "&": r"\&", "%": r"\%",
            "$": r"\$", "#": r"\#", "^": r"\textasciicircum{}",
            "_": r"\_", "~": r"\textasciitilde{}",
        }.items():
            out = out.replace(char, esc)
        return out

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

{{EXPERIENCE_SECTION}}

{{EDUCATION_SECTION}}

{{PROJECTS_SECTION}}

{{SKILLS_SECTION}}

\end{document}
"""

    # ─── Section builders ────────────────────────────────────────

    def _build_contact(self, data: Dict[str, Any]) -> str:
        email = self._escape(data.get("email", ""))
        location = self._escape(data.get("location", ""))
        linkedin = data.get("linkedin_url", "")
        github = data.get("github_url", "")
        parts: List[str] = []
        if email:
            parts.append(f"\\href{{mailto:{email}}}{{\\underline{{{email}}}}}")
        if location:
            parts.append(location)
        first = " $|$ ".join(parts)
        second_parts: List[str] = []
        if linkedin:
            clean = linkedin.replace("https://", "").replace("http://", "").replace("www.", "")
            second_parts.append(f"\\href{{{linkedin}}}{{\\underline{{{clean}}}}}")
        if github:
            clean = github.replace("https://", "").replace("http://", "")
            second_parts.append(f"\\href{{{github}}}{{\\underline{{{clean}}}}}")
        if second_parts:
            return f"{first} \\\\ " + " $|$\n    ".join(second_parts)
        return first

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
            out += (
                f"    \\resumeSubheading\n"
                f"      {{{self._escape(edu.get('institution', ''))}}}"
                f"{{{self._escape(edu.get('graduation_date', ''))}}}\n"
                f"      {{{self._escape(edu.get('degree', ''))}}}"
                f"{{{self._escape(edu.get('gpa', ''))}}}\n"
            )
        out += "  \\resumeSubHeadingListEnd"
        return out

    def _build_projects(self, projs: List[Dict[str, Any]]) -> str:
        if not projs:
            return ""
        out = "\\section{Projects}\n  \\resumeSubHeadingListStart\n"
        for proj in projs:
            title = self._escape(proj.get("title", ""))
            out += f"      \\resumeProjectHeading\n        {{\\textbf{{{title}}}}}{{}} \n      \\resumeItemListStart\n"
            descs = proj.get("descriptions", proj.get("description", []))
            if isinstance(descs, str):
                descs = [descs]
            for d in descs:
                ds = d if isinstance(d, str) else str(d or "")
                if ds.strip():
                    out += f"        \\resumeItem{{{self._escape(ds.strip())}}}\n"
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

    # ─── Generate ────────────────────────────────────────────────

    def generate_latex(self, data: Dict[str, Any]) -> str:
        content = self.TEMPLATE
        content = content.replace("{{NAME}}", self._escape(data.get("name", "")))
        content = content.replace("{{CONTACT}}", self._build_contact(data))
        content = content.replace("{{EXPERIENCE_SECTION}}", self._build_experience(data.get("experiences", [])))
        content = content.replace("{{EDUCATION_SECTION}}", self._build_education(data.get("education", [])))
        content = content.replace("{{PROJECTS_SECTION}}", self._build_projects(data.get("projects", [])))
        content = content.replace("{{SKILLS_SECTION}}", self._build_skills(data.get("skills", {})))
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
