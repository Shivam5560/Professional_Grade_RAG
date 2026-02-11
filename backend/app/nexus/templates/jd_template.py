JD_TEMPLATE = """
Given a plain text job description (JD) and optional context documents, extract structured information with maximum accuracy. Follow these rules strictly:

1. **Literal Extraction Only**  
   - Use ONLY explicitly stated information from the JD  
   - Never infer/imply missing details (return `""` or `[]` for unspecified fields)  
   - Use context docs ONLY for:  
     * Acronym expansion ("AWS"  "Amazon Web Services")  
     * Term standardization ("Javascript"  "JavaScript")  
     * Location disambiguation ("NY"  "New York")  

2. **Field-Specific Rules**  
   - **Job Title**: Exact role name, normalize case ("senior data ENGINEER"  "Senior Data Engineer")  
   - **Company Name**: Full legal name if available ("Microsoft"  "Microsoft Corporation")  
   - **Location**: Format as `"[City, State/Country] | [Work Model]"` ("Remote in US"  "United States | Remote")  
   * **Required Skills**:
     - Extract ALL technical competencies with strict normalization:
       ```python
       {
         "required_skills": [
           # Base terms only (2-3 words max)
           "Python",  # Not "Python programming skills"
           "PyTorch", 
           "TensorFlow",
           # Expanded acronyms
           "Google Cloud Vertex AI",  # From "GCP Vertex AI"
           "Amazon Web Services",  # From "AWS"
           # Split compound terms
           "Spark",  # From "Distributed computing (Spark, Dask)"
           "Dask",
           # Individual practices
           "Unit testing",  # From "Software engineering best practices (unit testing, CI/CD)"
           "CI/CD"
         ]
       }
       ```
     - Normalization Rules:
       1. **Phrase Cleaning**:
          - Remove proficiency indicators ("Expertise in", "Knowledge of")
          - Keep only tool/technology names
       2. **Special Cases**:
          - Slash-separated: "Docker/K8s"  ["Docker", "Kubernetes"]
          - Parentheticals: "Cloud (AWS, GCP)"  ["AWS", "Google Cloud"]
          - Version numbers: "Python 3.8"  "Python"
       3. **Exclusions**:
          - Generic terms: "Team player", "Problem solving"
          - Non-technical verbs: "Develop", "Implement"
   - **Experience**: Extract ONLY numerals ("5+ years"  "5", "Minimum 3 yrs"  "3")  
   - **Key Responsibilities**:  
     * Split compound items ("Design APIs and DBs"  ["Design REST APIs", "Optimize SQL databases"])  
     * Remove fluff ("Collaborate with teams"  SKIP)  
     * Keep technical ("Implement CI/CD pipelines")  
   - **Industry**: Auto-detect using keywords:  
      * any one in ("tech","finance","healthcare","marketing") based on summary of the overall responsibility.
      * Default: `"tech"`  

3. **Summary Generation**  
   - **150-200 words at least** combining Skills/Responsibilities/Qualifications  
   - **Technical Focus**: Tools, systems, methodologies  
   - **Exclude**: Company name, job title, location  
   - **Example**:  
     "Requires Python and SQL for ETL pipeline development... Kubernetes for container orchestration... BS in Computer Science or equivalent..."  

4. **Output Format (JSON)**  
```json
{
  "job_title": "",               // Normalized title
  "company_name": "",            // Legal name if available
  "location": "",                // Standardized format
  "required_skills": [],         // Cleaned, categorized skills
  "required_experience_years": "", // Only numerals
  "key_responsibilities": [],    // Atomic technical items
  "other_qualifications": [],    // Degrees/certifications
  "industry": "tech",            // Auto-detected
  "summary": ""                  // Technical-only summary
}
"""
