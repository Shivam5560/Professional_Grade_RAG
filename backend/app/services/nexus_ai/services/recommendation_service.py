from app.services.groq_service import get_groq_service
from ..utils.toon_util import decode_toon
from app.utils.logger import get_logger

logger = get_logger(__name__)


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


def getRecommendations(analysis_dict):
    llm = get_groq_service().get_llm()

    prompt = f"""
    You are an expert resume analysis assistant. Given comprehensive analysis data, produce a concise, professional summary in structured TOON format with TWO CRITICAL sections: 'refined_recommendations' and 'refined_justifications'.

    **CRITICAL REQUIREMENTS**:
    - You MUST provide AT LEAST 7 items in EACH section
    - Each item must be on a NEW LINE starting with the array index
    - DO NOT skip any important details from the analysis
    - Be specific and actionable, not generic

    Instructions:

    1. **refined_recommendations** (Minimum 7 items):
        - Extract ALL clear, actionable suggestions for improvement from the analysis
        - Cover EVERY gap identified (skills missing, responsibilities not matching, etc.)
        - Use concise bullet points with strong action verbs
        - Be specific: "Add AWS SageMaker experience" NOT "Improve cloud skills"
        - Prioritize technical gaps first, then grammar/formatting issues
        - Examples:
          * "Acquire hands-on experience with Apache Beam for data pipeline development"
          * "Add quantifiable metrics to project descriptions (e.g., performance improvements, scale)"
          * "Include AWS SageMaker model deployment experience in projects section"

    2. **refined_justifications** (Minimum 7 items):
    - Provide COMPLETE factual summary of evaluation rationale
    - **NEVER use "the candidate," "they," or "their"** - use impersonal phrasing
    - Include SPECIFIC numbers and facts:
      * Exact skill match counts ("Covers 8 of 15 required skills")
      * List key matched skills ("Strong in Python, TensorFlow, Docker")
      * List ALL missing critical skills ("Gaps in AWS SageMaker, Apache Beam, Vertex AI")
      * Responsibility alignment percentage
      * Grammar score breakdown
    - Use objective, data-driven language:
      * "Skills cover 5 of 12 job requirements, with strengths in Python but gaps in AWS SageMaker and Apache Beam."
      * "Experience aligns with machine learning model development, data preprocessing, and feature engineering."
      * "Grammar score of 75% reflects strong action verb usage but needs improved quantifiable metrics."
    - DO NOT omit any gaps or weaknesses identified in the analysis
    - Avoid generic statements - be specific and factual

    Output Format (TOON only - NO markdown code blocks, NO ```toon wrapper):
    refined_recommendations[0]: First specific recommendation
    refined_recommendations[1]: Second specific recommendation
    refined_recommendations[2]: Third specific recommendation
    refined_recommendations[3]: Fourth specific recommendation
    refined_recommendations[4]: Fifth specific recommendation
    refined_recommendations[5]: Sixth specific recommendation
    refined_recommendations[6]: Seventh specific recommendation
    refined_justifications[0]: First factual justification with numbers
    refined_justifications[1]: Second factual justification with specifics
    refined_justifications[2]: Third factual justification
    refined_justifications[3]: Fourth factual justification
    refined_justifications[4]: Fifth factual justification
    refined_justifications[5]: Sixth factual justification
    refined_justifications[6]: Seventh factual justification

    Analysis Data to Summarize:
    {analysis_dict}
    """

    try:
        logger.info("Generating recommendations via LLM")
        response = llm.complete(prompt)
        refined_data = response.text
        logger.info(f"LLM response length: {len(refined_data)} chars")
        
        refined_data = clean_text(refined_data)
        logger.info(f"Cleaned TOON data length: {len(refined_data)} chars")
        
        decoded = decode_toon(refined_data)
        logger.info(f"Decoded TOON keys: {list(decoded.keys())}")
        
        # Ensure arrays are properly formatted
        if "refined_recommendations" in decoded:
            if isinstance(decoded["refined_recommendations"], dict):
                logger.info(f"Converting recommendations dict to list ({len(decoded['refined_recommendations'])} items)")
                decoded["refined_recommendations"] = list(decoded["refined_recommendations"].values())
            elif not isinstance(decoded["refined_recommendations"], list):
                decoded["refined_recommendations"] = [decoded["refined_recommendations"]]
            logger.info(f"Final recommendations count: {len(decoded['refined_recommendations'])}")
        else:
            logger.warning("No refined_recommendations found in decoded TOON")
            decoded["refined_recommendations"] = []
            
        if "refined_justifications" in decoded:
            if isinstance(decoded["refined_justifications"], dict):
                logger.info(f"Converting justifications dict to list ({len(decoded['refined_justifications'])} items)")
                decoded["refined_justifications"] = list(decoded["refined_justifications"].values())
            elif not isinstance(decoded["refined_justifications"], list):
                decoded["refined_justifications"] = [decoded["refined_justifications"]]
            logger.info(f"Final justifications count: {len(decoded['refined_justifications'])}")
        else:
            logger.warning("No refined_justifications found in decoded TOON")
            decoded["refined_justifications"] = []
        
        logger.info("Successfully generated and formatted recommendations")
        return decoded
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}", exc_info=True)
        # Return error dict instead of JSONResponse
        return {
            "error": "Failed to generate recommendations",
            "details": str(e),
            "refined_recommendations": [],
            "refined_justifications": []
        }