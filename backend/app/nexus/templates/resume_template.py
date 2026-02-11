TEMPLATE = """
This parser uses a Retrieval-Augmented Generation (RAG) pipeline where resume text is semantically chunked, indexed in a vector store, with relevant sections dynamically retrieved to support precise LLM extraction.

---

### **Strict Extraction Rules**

1. **Literal Extraction Only**
   - Extract ONLY explicitly stated information
   - Never infer/imply missing details (use `""` or `[]` for missing fields)
   - Preserve original section ordering from the resume

2. **Field-Specific Requirements**

   * **Personal Information**:
     - Name: Full legal name (normalize case)
     - Email: Extract verbatim
     - Phone: Standardize formats (e.g., "+1 (123) 456-7890"  "1234567890")

   * **Education**:
     - Degree: Full degree name ("B.S."  "Bachelor of Science")
     - Institution: Official name ("MIT"  "Massachusetts Institute of Technology")
     - Dates: Format as "MM/YYYY" or "YYYY" consistently

   * **Work Experience**:
     - Job Title: Normalize case ("senior dev"  "Senior Developer")
     - Company: Legal name if identifiable
     - Dates: Standardize ("Jan 2020 - Present"  "01/2020 - Present")
     - Responsibilities: 
       - Split compound bullets ("Built APIs and databases"  ["Built REST APIs", "Designed SQL databases"])
       - Remove non-technical fluff ("Worked with teams")

   * **Keywords**:
     - Extract ALL unique technical terms from:
       - Work Experience (job responsibilities)
       - Projects (implementations/technologies used) 
       - Skills section (explicitly listed tools)
     - Include:
       * Programming languages (Python, Java)
       * Frameworks/Libraries (React.js, Node.js)
       * Platforms (AWS, Kubernetes)
       * Databases (PostgreSQL, MongoDB)
       * Methodologies (Agile, CI/CD)
       * Technical concepts (Machine Learning, REST APIs)
     - Special Character Handling:
       * Preserve standard technology notations:
         - "React.js"  Keep as "React.js" (don't convert to "React js")
         - "Node.js"  Keep as "Node.js" (don't convert to "Node js")
         - "C++"  Keep as "C++" (don't convert to "C")
       * Split slash-separated terms:
         - "Docker/Kubernetes"  ["Docker", "Kubernetes"]
         - "AWS/GCP"  ["AWS", "Google Cloud Platform"]
       * Handle hyphenated terms case-by-case:
         - "AngularJS"  Keep as is
         - "TensorFlow-Lite"  Keep as is
     - Exclude:
       * Generic terms ("team", "project", "communication")
       * Non-technical verbs ("worked", "collaborated")
       * Company-specific jargon
     - Normalization Rules:
       * "JS"  "JavaScript"
       * "GCP"  "Google Cloud Platform"
       * "Postgres"  "PostgreSQL"
       * "AI"  "Artificial Intelligence"
     - Version Numbers:
       * Generally remove unless critical ("Python 3"  "Python")
       * Keep when version defines capability ("React Native 0.70")
     - Remove duplicates (keep only first occurrence)
     - Maintain original capitalization for proper nouns:
       * "GitHub" (not "Github")
       * "iOS" (not "IOS")

   * **Projects**:
     - Name: Formal project title
     - Description: Technical achievements only ("Reduced latency by 40% using Redis")

   * **Technical Summary** (maps to "summary" in JSON):
     - Generate 150-200 words at least for professional overview
     - Source content from:
       • Technical skills and competencies
       • Core methodologies and architectures
       • Notable project achievements
     - Focus areas:
       • Technologies mastered (e.g., "Expertise in React.js and microservices")
       • Technical processes (e.g., "CI/CD pipeline implementation")
       • Quantitative impact (e.g., "Optimized performance by 40%")
     - Exclude:
       • Personal identifiers (name/contact)
       • Company names
       • Non-technical soft skills
     - Example:
       "Full-stack developer with 5+ years experience building scalable web applications 
       using React.js, Node.js, and AWS. Specialized in REST API design and database 
       optimization, reducing query times by 60%. Implemented containerized deployments 
       using Docker and Kubernetes across 3 major projects..."

   * **Key Responsibilities** (separate array in JSON):
     - Extract atomic technical actions from work experience
     - Format each as imperative verb phrases:
       • "Designed REST APIs using Spring Boot"
       • "Implemented authentication with JWT"
       • "Optimized SQL queries reducing load times by 30%"
     - Must be:
       • Technical and specific
       • Measurable where possible
       • Free from company/project names
     - Exclude:
       • Generic tasks ("Collaborated with teams")
       • Managerial duties ("Led meetings")
     - Example:
       [
         "Developed responsive UIs with React hooks",
         "Containerized applications using Docker",
         "Deployed machine learning models on AWS SageMaker"
       ]

3. **Output Structure**
```json
{
  "personal_info": {
    "name": "",
    "email": "",
    "phone": ""
  },
  "education": [
    {
      "degree": "",
      "institution": "",
      "graduation_date": ""
    }
  ],
  "work_experience": [
    {
      "job_title": "",
      "company": "",
      "dates": "",
      "responsibilities": []
    }
  ],
  "keywords": []
  ,
  "projects": [
    {
      "name": "",
      "description": []
    }
  ],
  "certifications": [
    {
      "name": "",
      "description": ""
    }
  ],
  "summary": "",
  "key_responsibilities": []
}
"""
