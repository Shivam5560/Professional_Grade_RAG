JD_TEMPLATE = """
Given a plain text job description (JD) and optional context documents, extract structured information with maximum accuracy. Follow these rules strictly:

**CRITICAL: EXTRACT ALL INFORMATION - DO NOT SKIP ANY REQUIREMENTS**

1. **Literal Extraction Only**  
   - Use ONLY explicitly stated information from the JD  
   - Never infer/imply missing details (return "" or [] for unspecified fields)  
   - Use context docs ONLY for:  
     * Acronym expansion ("AWS" to "Amazon Web Services")  
     * Term standardization ("Javascript" to "JavaScript")  
     * Location disambiguation ("NY" to "New York")  
   - **EXTRACT EVERY SINGLE skill, tool, technology, and qualification mentioned**

2. **Field-Specific Rules**  
   - **Job Title**: Exact role name, normalize case ("senior data ENGINEER" to "Senior Data Engineer")  
   - **Company Name**: Full legal name if available ("Microsoft" to "Microsoft Corporation")  
   - **Location**: Format as "[City, State/Country] | [Work Model]" ("Remote in US" to "United States | Remote")  
   
   * **Required Skills** (CRITICAL - DO NOT MISS ANY):
     - **Extract EVERY SINGLE technical competency mentioned with strict normalization**
     - Normalization Rules (MUST APPLY):
       1. **Phrase Cleaning**:
          - Remove proficiency indicators ("Expertise in", "Knowledge of", "Proficiency with", "Experience in")
          - Remove qualifiers ("Strong", "Good", "Deep understanding of")
          - Keep only tool/technology names
       2. **Acronym Expansion** (always expand):
          - "AWS" to "Amazon Web Services" (and keep specific services like "AWS SageMaker", "AWS Lambda")
          - "GCP" to "Google Cloud Platform" (and keep "Google Cloud Vertex AI", "Google Cloud BigQuery")
          - "NLP" to "Natural Language Processing"
          - "ML" to "Machine Learning"
          - "AI" to "Artificial Intelligence"
          - "K8s" to "Kubernetes"
          - "JS" to "JavaScript"
          - "TS" to "TypeScript"
       3. **Special Cases**:
          - Slash-separated: "Docker/K8s" becomes ["Docker", "Kubernetes"]
          - Parentheticals: "Cloud (AWS, GCP)" becomes ["Amazon Web Services", "Google Cloud Platform"]
          - Comma lists: "Python, Java, C++" becomes ["Python", "Java", "C++"]
          - Version numbers: "Python 3.8" becomes "Python"
       4. **Exclusions**:
          - Generic soft skills: "Team player", "Problem solving", "Communication", "Leadership"
          - Non-technical verbs: "Develop", "Implement", "Build" (unless part of tool name)
          - Years of experience (handled separately)
     - **DO NOT skip any technical requirement - aim for 15+ skills minimum**
     
   - **Experience**: Extract ONLY numerals ("5+ years" to "5", "Minimum 3 yrs" to "3")  
   
   - **Key Responsibilities** (CRITICAL - EXTRACT ALL):  
     * **Extract EVERY responsibility mentioned - do not summarize**
     * Split compound items:
       - "Design APIs and DBs" becomes ["Design REST APIs", "Optimize SQL databases"]
       - "Implement ML pipelines and deploy models" becomes ["Implement ML pipelines", "Deploy models to production"]
     * Remove generic fluff:
       - "Collaborate with teams" (SKIP)
       - "Work in fast-paced environment" (SKIP)
     * Keep ALL technical responsibilities:
       - "Implement CI/CD pipelines"
       - "Design microservices architecture"
       - "Optimize database performance"
       - "Build data processing pipelines"
     * Include quantifiable expectations:
       - "Handle 1M+ requests per day"
       - "Reduce latency to sub-100ms"
     * **Aim for 10-20 responsibilities minimum to capture full scope**
     
   - **Other Qualifications**:
     * Include ALL mentioned:
       - Educational requirements ("BS in Computer Science")
       - Certifications ("AWS Certified Solutions Architect")
       - Nice-to-have skills
       - Domain knowledge ("Healthcare experience", "Financial systems")
       
   - **Industry**: Auto-detect using keywords:  
      * "tech" - Software, technology, SaaS companies
      * "finance" - Banking, fintech, trading
      * "healthcare" - Medical, biotech, pharma
      * "marketing" - Advertising, digital marketing
      * Default: "tech"

3. **Summary Generation**  
   - **200-300 words minimum** combining Skills/Responsibilities/Qualifications comprehensively
   - **Technical Focus**: ALL tools, systems, methodologies, technologies
   - **Include**:
     * Every skill and tool mentioned
     * Key responsibilities with technical details
     * Required experience and qualifications
     * Domain knowledge requirements
     * Performance expectations
   - **Exclude**: Company name, job title, location, generic soft skills
   - **Example**:  
     "Requires extensive Python programming for ETL pipeline development and data processing at scale. 
     Experience with PyTorch and TensorFlow for machine learning model development and deployment. 
     Proficiency in Apache Beam for distributed data processing and Apache Kafka for real-time streaming. 
     Strong knowledge of Google Cloud Platform services including Vertex AI, BigQuery, and Cloud Storage. 
     Experience deploying models on AWS SageMaker with auto-scaling and monitoring. SQL expertise for 
     database optimization (PostgreSQL, MySQL). Containerization with Docker and orchestration using 
     Kubernetes for production deployments. CI/CD pipeline implementation with Jenkins and GitHub Actions. 
     Unit testing, integration testing, and TDD practices. Agile/Scrum methodology. BS in Computer Science 
     or equivalent with 5+ years of production ML experience..."  

4. **Output Format (TOON only, no JSON)**  
```toon
job_title:
company_name:
location:
required_skills[0]:
required_experience_years:
key_responsibilities[0]:
other_qualifications[0]:
industry: tech
summary:
```

**FINAL REMINDER: DO NOT SKIP ANY SKILLS, TOOLS, OR RESPONSIBILITIES - EXTRACT EVERYTHING**
"""
