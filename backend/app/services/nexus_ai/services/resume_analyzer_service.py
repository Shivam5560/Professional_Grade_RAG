import spacy
import numpy as np
import re
import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer  # Kept, but still not actively used for scoring
from thefuzz import process as fuzzy_process
import language_tool_python
import math  # For ceiling function

from ..utils.file_util import load_from_json

# --- Configuration ---
ACTION_VERBS_FILE = 'action_verbs.json'
INDUSTRY_SKILLS_FILE = 'industry_skills.json'
FUZZY_MATCH_THRESHOLD = 85
GRAMMAR_CHECK_LANG = 'en-US'
ABSOLUTE_MATCH_THRESHOLD_HIGH = 30  # Min absolute matches for at least "High"
ABSOLUTE_MATCH_THRESHOLD_MEDIUM = 15  # Min absolute matches for at least "Medium"

# --- New Categorical Scoring Definition ---
SCORE_CATEGORIES = {
    "Very Low": 20,
    "Low": 45,
    "Medium": 70,  # Adjusted center point slightly
    "High": 85,
    "Very High": 100
}


class PracticalResumeAnalyzer:
    # action_verbs_data = load_from_json("resources", "action_verbs.json")
    #
    # industry_skills = load_from_json("resources","industry_skills.json")

    def __init__(self):
        self.nlp = self._load_spacy_model()
        # Load JSON data here
        action_verbs_data = load_from_json("resources", "action_verbs.json")
        self.all_action_verbs = self._compile_action_verbs(action_verbs_data)  # pass dict, not path
        self.industry_skills = load_from_json("resources", "industry_skills.json")


        # Define weights (these remain crucial)
        self.weights = {
            "length": 0.05,
            "action_verbs": 0.15,
            "bullet_points": 0.10,
            "quantifiable": 0.15,
            "sentence_structure": 0.05,
            "active_voice": 0.10,
            "completeness": 0.10,
            "skills_format": 0.05,
            "industry_fit": 0.15,
            "grammar_spelling": 0.10,
        }
        # Normalize weights to sum to 1 (good practice)
        total_weight = sum(self.weights.values())
        if total_weight > 0 and abs(total_weight - 1.0) > 1e-6:
            print(f"Normalizing weights from sum {total_weight} to 1.0")
            self.weights = {k: v / total_weight for k, v in self.weights.items()}

    # --- Loading Functions (modified slightly) ---

    def _load_spacy_model(self):
        # (Same as before - loads spaCy model with fallbacks)
        try:
            return spacy.load("en_core_web_md")
        except OSError:
            print("Warning: en_core_web_md not found. Trying en_core_web_sm.")
            try:
                return spacy.load("en_core_web_sm")
            except OSError:
                print("ERROR: No spaCy language models found.")
                print("Install one: python -m spacy download en_core_web_sm")
                raise

    def _load_json_data(self, file_path):
        # (Same as before - loads JSON)
        if not os.path.exists(file_path):
            print(f"ERROR: Data file not found at {file_path}")
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to load or parse JSON from {file_path}. Error: {e}")
            return None

    def _load_action_verbs_data(self, file_path):
        """Loads the raw action verbs dictionary (with impact categories)."""
        return self._load_json_data(file_path) or {}

    def _compile_action_verbs(self, verbs_data):
        """Creates a single dictionary mapping verbs to numeric impact scores (0-1)."""
        all_verbs = {}

        # Add score based on old hardcoded dict values if provided
        if 'high_impact' in verbs_data and isinstance(verbs_data['high_impact'], dict):
            all_verbs.update(
                {k.lower(): v for k, v in verbs_data['high_impact'].items() if isinstance(v, (float, int))})
        if 'medium_impact' in verbs_data and isinstance(verbs_data['medium_impact'], dict):
            all_verbs.update(
                {k.lower(): v for k, v in verbs_data['medium_impact'].items() if isinstance(v, (float, int))})
        if 'low_impact' in verbs_data and isinstance(verbs_data['low_impact'], dict):
            all_verbs.update({k.lower(): v for k, v in verbs_data['low_impact'].items() if isinstance(v, (float, int))})

        return all_verbs

    def _load_industry_skills(self, file_path):
        # (Same as before - loads skills, converts to sets)
        data = self._load_json_data(file_path)
        if data:
            return {industry: set(skill.lower() for skill in skills)
                    for industry, skills in data.items()}
        return {}

    # --- Core Analysis Function (Orchestrator) ---

    def analyze_resume(self, resume_text, resume_dict, industry="default"):
        """
        Main analysis function using categorical scoring internally.

        Returns:
            tuple: (overall_score_ B{0-100},
                    recommendations_list,
                    section_results_dict, # Contains {'category': str, 'details': dict, 'score': int} for each section
                    detailed_justification_string)
        """
        if not resume_text or not isinstance(resume_dict, dict):
            return 0, ["Invalid input: Resume text or dictionary is missing/empty."], {}, "Invalid input provided."

        doc = self.nlp(resume_text)
        sentences = [sent.text for sent in doc.sents if sent.text.strip()]

        work_experience = resume_dict.get('work_experience', [])
        projects = resume_dict.get('projects', [])
        all_bullets = []
        # Safely extract bullets
        if isinstance(work_experience, list):
            for exp in work_experience:
                if isinstance(exp, dict):
                    resp = exp.get('responsibilities', [])
                    if isinstance(resp, list):
                        all_bullets.extend([b for b in resp if isinstance(b, str) and b.strip()])
        if isinstance(projects, list):
            for desc in projects:
                if isinstance(desc, dict):
                    resp = desc.get('description', [])
                    if isinstance(resp, list):
                        all_bullets.extend([b for b in resp if isinstance(b, str) and b.strip()])
        # if isinstance(projects, str):
        #     for desc in projects:
        #         if isinstance(desc, dict):
        #             resp = desc.get('description', '')
        #             if isinstance(resp, str):
        #                 sentences = resp.split('.')
        #                 all_bullets.extend(sentences)

        section_results = {}
        all_recommendations = []

        # --- Define Analysis Tasks ---
        # Each tuple: (analysis_function, args_tuple, section_key_string)
        analysis_tasks = [
            (self._analyze_length, (all_bullets,), "length"),
            (self.analyze_action_verbs, (all_bullets,), "action_verbs"),
            (self._analyze_bullet_points, (all_bullets, work_experience), "bullet_points"),
            (self.analyze_quantifiable, (all_bullets,), "quantifiable"),
            (self._analyze_sentence_structure, (all_bullets,), "sentence_structure"),
            (self.analyze_passive_voice, (sentences,), "active_voice"),
            (self._analyze_completeness, (resume_dict,), "completeness"),
            (self._analyze_skills_format, (resume_dict.get('keywords', []),), "skills_format"),
            (self.analyze_industry_fit, (resume_text, resume_dict.get('keywords', []), industry), "industry_fit"),
        ]

        # --- Execute Analyses ---
        for func, args, key in analysis_tasks:
            category = "Medium"  # Default category if analysis fails
            details = {"error": "Analysis execution failed."}
            recommendations = []
            numerical_score = SCORE_CATEGORIES[category]  # Default score

            try:
                # *** Expecting (category_str, details_dict, recommendations_list) from helpers ***
                cat, det, recs = func(*args)
                category = cat  # String like "High"
                details = det  # Dictionary with specific findings
                recommendations = recs if isinstance(recs, list) else ([recs] if recs else [])
                numerical_score = SCORE_CATEGORIES.get(category, SCORE_CATEGORIES["Medium"])  # Get score from map

            except Exception as e:
                print(f"ERROR during analysis section '{key}': {e}")
                recommendations.append(f"Could not complete '{key}' analysis due to an error.")
                details['error'] = str(e)  # Add specific error to details

            # Store results
            section_results[key] = {
                'category': category,
                'score': numerical_score,  # Store the mapped numerical score (0-100)
                'details': details
            }
            all_recommendations.extend(recommendations)

        # Non-weighted check (recommendations only) - Contact Info
        _, contact_rec = self._analyze_contact_info(resume_dict.get('personal_info', {}))
        if contact_rec:
            # Ensure it's a list before extending
            contact_recs_list = contact_rec if isinstance(contact_rec, list) else [contact_rec]
            all_recommendations.extend(contact_recs_list)  # Add contact recommendations

        # --- Calculate Overall Score ---
        overall_score = 0.0
        for key, weight in self.weights.items():
            if key in section_results:
                overall_score += section_results[key]['score'] * weight
            # else: # Section analysis might have failed catastrophically
            #     overall_score += SCORE_CATEGORIES["Low"] * weight # Penalize if section is missing

        final_score = max(0, min(100, round(overall_score)))  # Clamp score 0-100

        # --- Generate Detailed Justification ---
        detailed_justification = self._generate_dynamic_justification(final_score, section_results)

        return final_score, all_recommendations, section_results, detailed_justification

    # --- Analysis Helper Methods (MUST be refactored) ---
    # Each method below needs to:
    # 1. Perform its analysis.
    # 2. Determine the category ("Very Low" to "Very High") based on criteria.
    # 3. Compile a 'details' dictionary with specific findings.
    # 4. Return (category, details, recommendations).

    def _get_category_from_score(self, score_0_to_1):
        """Maps a 0-1 score to a category name."""
        score_100 = score_0_to_1 * 100
        if score_100 >= 95: return "Very High"
        if score_100 >= 80: return "High"
        if score_100 >= 55: return "Medium"  # Adjusted threshold
        if score_100 >= 30: return "Low"  # Adjusted threshold
        return "Very Low"

    def _analyze_length(self, all_bullets):
        """
        Analyzes the total meaningful word count across all provided bullet points (from work exp/projects).
        Returns category, details, and recommendations based on bullet point verbosity/conciseness.
        Requires self.nlp to be initialized.
        """
        total_meaningful_words = 0

        # Ensure input is a list
        if not isinstance(all_bullets, list):
            # Return an error state if the input isn't as expected
            return "Error", {'issue': 'Invalid input: Expected a list of bullets.'}, [
                "Could not analyze bullet verbosity due to invalid input format."]

        # Process each bullet string
        for bullet in all_bullets:
            # Ensure the item in the list is a non-empty string
            if isinstance(bullet, str) and bullet.strip():
                total_meaningful_words += len(bullet.split(' '))

        details = {'total_bullet_meaningful_word_count': total_meaningful_words}
        recs = []

        # --- Adjusted Thresholds for Total Meaningful Words in Bullets ---
        # Centered around an ideal of ~325-475 words

        if total_meaningful_words < 75:
            category = "Very Low"
            recs.append(
                "Bullet points critically lack detail. Significantly expand on actions, context, tools used, and quantifiable outcomes. Aim for 325-475 total meaningful words across all bullets.")
            details['issue'] = 'Insufficient bullet point detail'
        elif total_meaningful_words < 120:
            category = "Low"
            recs.append(
                "Bullet points are sparse. Elaborate further on your contributions, methods, and results. Quantify achievements wherever possible (aim for 325-475 total words).")
        elif total_meaningful_words < 200:
            category = "Medium"
            recs.append(
                "Bullet points show some substance but can be more impactful. Focus on using stronger action verbs and adding specific, quantified results (aim for 325-475 total words).")
        elif total_meaningful_words <= 280:
            category = "Very High"
            # Optional positive feedback:
            # recs.append("The level of detail in your bullet points appears optimal, balancing description and conciseness.")
        elif total_meaningful_words <= 320:
            category = "High"
            recs.append(
                "Your bullet points are detailed. Ensure they remain concise and focused; check if any descriptions can be tightened without losing impact.")
        elif total_meaningful_words <= 350:
            category = "Medium"
            recs.append(
                "Bullet points seem quite verbose. Review carefully to remove redundant phrases or less critical information. Focus on conciseness for better readability.")
            details['issue'] = 'Potentially verbose bullets'
        else:  # > 350
            category = "Low"  # Penalize excessive length even in bullets
            recs.append(
                "Bullet points are excessively wordy, potentially hiding key achievements. Drastically shorten descriptions, focusing only on the most critical actions and quantifiable results.")
            details['issue'] = 'Excessive bullet point verbosity'

        # Add the count to details regardless of category
        details['total_bullet_meaningful_word_count'] = total_meaningful_words

        return category, details, recs

    def analyze_action_verbs(self, bullet_points):
        """Analyzes action verbs, returns category, details (with examples), recommendations."""
        # ... (Initial setup remains the same) ...
        verb_scores = []
        weak_verbs_found = {}  # Store verb and example bullet
        missing_verb_bullets = []
        first_verbs_list = []
        details = {}
        for bullet in bullet_points:
            bullet_clean = bullet.strip()
            if not bullet_clean:
                continue
            # Truncate long bullets early for examples
            bullet_example = bullet_clean[:80] + ("..." if len(bullet_clean) > 80 else "")
            doc = self.nlp(bullet_clean)
            if not doc or len(doc) == 0: continue

            first_token = doc[0]
            first_lemma = str(doc).split(' ')[0].lower()

            if first_lemma in self.all_action_verbs:
                score = self.all_action_verbs[first_lemma]
                verb_scores.append(score)
                first_verbs_list.append(first_lemma)
                if score < 0.5:  # Weak verb threshold
                    # Store first example found for each weak verb
                    if first_lemma not in weak_verbs_found:
                        weak_verbs_found[first_lemma] = bullet_example
            else:
                if len(missing_verb_bullets) < 3:  # Limit examples
                    missing_verb_bullets.append(bullet_example)

        # ... (Calculate ratios: missing_ratio, avg_verb_strength, diversity_ratio - same as before) ...
        num_bullets = len(bullet_points)
        missing_ratio = len(missing_verb_bullets) / num_bullets if num_bullets else 0
        avg_verb_strength = np.mean(verb_scores) if verb_scores else 0
        unique_verbs = set(first_verbs_list)
        diversity_ratio = len(unique_verbs) / len(first_verbs_list) if first_verbs_list else 0

        # *** MODIFIED DETAILS ***
        details = {
            'bullet_count': num_bullets,
            'missing_verb_ratio': round(missing_ratio, 2),
            'avg_verb_strength_score': round(avg_verb_strength, 2),
            'diversity_ratio': round(diversity_ratio, 2),
            'weak_verb_examples': weak_verbs_found,  # Dict: {'verb': 'example bullet...'}
            'missing_verb_bullet_examples': missing_verb_bullets  # List: ['bullet example...']
        }
        recs = []

        # ... (Determine category based on scores - same logic as before) ...
        final_score_component = 0.0
        if missing_ratio > 0.5:
            final_score_component -= 0.5
        elif missing_ratio > 0.2:
            final_score_component -= 0.25
        final_score_component += avg_verb_strength
        if len(first_verbs_list) > 5 and diversity_ratio < 0.5: final_score_component -= 0.15
        final_score_0_to_1 = max(0, min(1, final_score_component))
        category = self._get_category_from_score(final_score_0_to_1)

        # ... (Generate recommendations, potentially using examples - same logic as before) ...
        # Add examples to recommendations if needed, e.g.:
        if avg_verb_strength < 0.5 and weak_verbs_found:
            example_verb, example_bullet = next(iter(weak_verbs_found.items()))  # Get first example
            recs.append(
                f"Weak verbs identified (e.g., '{example_verb}' in \"{example_bullet}\"). Replace with stronger alternatives.")
        if missing_verb_bullets and (missing_ratio > 0.15):
            recs.append(
                f"Some bullets don't start with action verbs (e.g., \"{missing_verb_bullets[0]}\"). Ensure all start with a verb.")

        # ... (Handle special case for no verbs - same logic) ...
        if not verb_scores and missing_ratio == 1.0:
            category = "Very Low"
            recs = ["No bullet points appear to start with recognized action verbs."]
            details['issue'] = 'No action verbs identified at start of bullets.'

        return category, details, recs

    def _analyze_bullet_points(self, all_bullets, work_experience):
        """Analyzes bullet points, returns category, details (with examples), recommendations."""
        # ... (Initial setup and calculations - same as before) ...
        details = {}
        recs = []
        long_bullet_examples = []
        short_bullet_examples = []

        if not work_experience or not all_bullets:
            return "Low", {'issue': 'Missing work experience or bullets'}, [
                "Work experience section missing or lacks bullet points."]

        # ... (Calculate avg_bullets_per_job, bullet_lengths, verb_start_ratio - same as before) ...
        bullets_per_job = []
        jobs_with_zero_bullets = 0
        total_jobs = len(work_experience)
        for exp in work_experience:
            count = len(exp.get('responsibilities', []))
            bullets_per_job.append(count)
            if count == 0: jobs_with_zero_bullets += 1
        avg_bullets_per_job = np.mean(bullets_per_job) if bullets_per_job else 0

        bullet_lengths = []
        verb_start_count = 0
        for bullet in all_bullets:
            if not bullet: continue
            words = bullet.split()
            length = len(words)
            bullet_lengths.append(length)
            # Capture examples
            if length > 30 and len(long_bullet_examples) < 2:
                long_bullet_examples.append(f"\"{bullet[:80]}...\" ({length} words)")
            if length < 8 and len(short_bullet_examples) < 2:
                short_bullet_examples.append(f"\"{bullet}\" ({length} words)")
            # Check verb start
            doc = self.nlp(bullet.strip())
            # print("Doc in bullet",doc)
            if doc and str(doc).split(' ')[0].lower() in list(self.all_action_verbs.keys()): verb_start_count += 1

        avg_bullet_length = np.mean(bullet_lengths) if bullet_lengths else 0
        verb_start_ratio = verb_start_count / len(all_bullets) if all_bullets else 0

        #
        # print(all_bullets)
        # *** MODIFIED DETAILS ***
        details = {
            'total_bullets': len(all_bullets),
            'total_jobs_analyzed': total_jobs,
            'jobs_with_zero_bullets': jobs_with_zero_bullets,
            'avg_bullets_per_job': round(avg_bullets_per_job, 1),
            'avg_bullet_word_length': round(avg_bullet_length, 1),
            'percent_bullets_starting_verb': round(verb_start_ratio * 100),
            'long_bullet_examples': long_bullet_examples,  # List of examples
            'short_bullet_examples': short_bullet_examples  # List of examples
        }

        # ... (Determine category - same logic as before) ...
        score_components = []
        if jobs_with_zero_bullets > 0:
            score_components.append(0.5)
        else:
            score_components.append(1.0)
        if avg_bullets_per_job < 2:
            score_components.append(0.45)
        else:
            score_components.append(1.0)
        if avg_bullet_length < 8:
            score_components.append(0.6)
        elif avg_bullet_length > 30:
            score_components.append(0.6)
        else:
            score_components.append(1.0)
        score_components.append(verb_start_ratio)
        final_score_0_to_1 = np.mean(score_components) if score_components else 0.5
        category = self._get_category_from_score(final_score_0_to_1)

        # ... (Generate recommendations - same logic as before, examples already in details) ...
        # Recommendations can now implicitly rely on the justification using the examples

        return category, details, recs

    def analyze_quantifiable(self, bullet_points):
        """Analyzes quantifiable achievements, returns category, details (with examples), recommendations."""
        # *** MODIFIED DETAILS COLLECTION ***
        details = {'quantified_bullet_examples': [], 'non_quantified_impact_examples': []}
        recs = []
        if not bullet_points:
            return "Low", {'issue': 'Missing bullet points'}, ["Work experience section lacks bullets to quantify."]

        # ... (Patterns and impact indicators - same as before) ...
        number_pattern = re.compile(r'\b\d[\d,.]*%?\b|\$\s?\d[\d,.]*([kKmMbB])?\b')
        impact_indicators = {"increase", "decrease", "reduce", "improve", "generate", "save", "exceed", "grow",
                             "optimize", "achieve", "deliver", "complete", "launch", "drive"}

        quantifiable_count = 0
        impact_linked_count = 0
        non_quantified_impact_count = 0

        for bullet in bullet_points:
            bullet_clean = bullet.strip()
            if not bullet_clean: continue
            bullet_example = bullet_clean[:80] + ("..." if len(bullet_clean) > 80 else "")
            bullet_lower = bullet_clean.lower()
            has_number = bool(number_pattern.search(bullet_clean))
            has_impact = any(indicator in bullet_lower for indicator in impact_indicators)

            if has_number:
                quantifiable_count += 1
                if len(details['quantified_bullet_examples']) < 2:
                    details['quantified_bullet_examples'].append(bullet_example)
                if has_impact:
                    impact_linked_count += 1
            elif has_impact:  # Has impact word but no number
                non_quantified_impact_count += 1
                if len(details['non_quantified_impact_examples']) < 2:
                    details['non_quantified_impact_examples'].append(bullet_example)

        # ... (Calculate ratios and determine category - same logic as before) ...
        total_bullets = len(bullet_points)
        quant_ratio = quantifiable_count / total_bullets if total_bullets else 0
        final_score_0_to_1 = min(1.0, quant_ratio * 2.5)
        category = self._get_category_from_score(final_score_0_to_1)

        # Update details dictionary
        details.update({
            'total_bullets': total_bullets,
            'quantified_bullet_count': quantifiable_count,
            'quantified_ratio': round(quant_ratio, 2),
            'impact_keywords_without_metrics_count': non_quantified_impact_count
            # Examples already added above
        })

        # ... (Generate recommendations - same logic as before) ...
        if quant_ratio == 0: category = "Very Low"
        if 0.3 <= quant_ratio < 0.4 and category == "Medium": category = "High"
        if quant_ratio >= 0.4: category = "Very High"

        return category, details, recs

    def _analyze_sentence_structure(self, all_bullets):
        """Analyzes sentence structure within bullet points using word count, returns category, details, recommendations."""
        details = {'long_sentence_examples': [], 'short_sentence_examples': []}
        recs = []
        sentences_from_bullets = []

        if not all_bullets:
            return "Low", {'issue': 'No bullet points found'}, ["No bullet points to analyze for sentence structure."]

        # Extract sentences from each bullet point
        for bullet in all_bullets:
            if isinstance(bullet, str) and bullet.strip():
                doc = self.nlp(bullet)
                for sent in doc.sents:
                    sentences_from_bullets.append(sent.text)

        if not sentences_from_bullets:
            return "Low", {'issue': 'No complete sentences found in bullet points'}, [
                "Review bullet points to ensure they form complete sentences where appropriate."]

        sentence_lengths_words = []
        sentence_texts = []  # Store original text for examples

        for sentence in sentences_from_bullets:
            text = sentence.strip()
            if not text:
                continue
            sentence_texts.append(text)
            # Count words by splitting on whitespace (simple but effective for this purpose)
            word_count = len(text.split())
            sentence_lengths_words.append(word_count)

        if not sentence_lengths_words:
            return "Low", {'issue': 'No valid sentences extracted from bullets'}, [
                "Ensure bullet points contain valid sentences for analysis."]

        avg_len = np.mean(sentence_lengths_words)
        std_dev_len = np.std(sentence_lengths_words)
        long_sentences_count = 0
        short_sentences_count = 0

        # Collect examples while counting
        for i, length in enumerate(sentence_lengths_words):
            text_example = sentence_texts[i][:80] + ("..." if len(sentence_texts[i]) > 80 else "")

            # Adjusted thresholds for word count (instead of tokens)
            if length > 30:  # Long sentence threshold in words
                long_sentences_count += 1
                if len(details['long_sentence_examples']) < 2:
                    details['long_sentence_examples'].append(f"\"{text_example}\" ({length} words)")

            if length < 5:  # Short sentence threshold in words
                short_sentences_count += 1
                if len(details['short_sentence_examples']) < 2:
                    details['short_sentence_examples'].append(f"\"{text_example}\" ({length} words)")

        details.update({
            'sentence_count': len(sentences_from_bullets),
            'avg_sentence_length_words': round(avg_len, 1),
            'std_dev_sentence_length': round(std_dev_len, 1),
            'long_sentence_count (>30 words)': long_sentences_count,
            'short_sentence_count (<5 words)': short_sentences_count,
        })

        # Determine category and recommendations
        score_0_to_1 = 1
        sentence_count = len(sentences_from_bullets)
        long_ratio = long_sentences_count / sentence_count if sentence_count else 0
        short_ratio = short_sentences_count / sentence_count if sentence_count else 0
        if long_ratio > 0.2 or avg_len > 20:  # Adjusted thresholds for words
            score_0_to_1 -= 0.3
            recs.append("Consider breaking down long bullet points into shorter, more digestible sentences.")
            if details['long_sentence_examples']:
                recs.append(f"Examples of long sentences: {', '.join(details['long_sentence_examples'])}")

        if short_ratio > 0.5 and avg_len < 10:  # Adjusted thresholds for words
            score_0_to_1 -= 0.3
            recs.append(
                "Ensure bullet points are sufficiently detailed. Some appear to be very short and might lack impact.")
            if details['short_sentence_examples']:
                recs.append(f"Examples of short sentences: {', '.join(details['short_sentence_examples'])}")

        if std_dev_len < 3 and 8 < avg_len < 18:  # Adjusted thresholds for words
            score_0_to_1 -= 0.1
            recs.append("Sentence length variation is good. Maintain a mix of sentence lengths for readability.")
        elif std_dev_len > 7:
            recs.append("Consider varying sentence lengths more to improve rhythm and engagement.")
        final_score_0_to_1 = max(0, min(1, score_0_to_1))
        category = self._get_category_from_score(final_score_0_to_1)

        return category, details, recs

    def analyze_passive_voice(self, sentences):
        """Analyzes passive voice, returns category, details (with examples), recommendations."""
        # *** MODIFIED DETAILS COLLECTION ***
        details = {'passive_sentence_examples': []}
        recs = []
        if not sentences:
            return "Very High", {'issue': 'No sentences found'}, []

        passive_count = 0
        for sent in sentences:
            sent_text = sent.strip()
            if not sent_text: continue
            doc = self.nlp(sent_text)
            is_passive = False
            # ... (passive detection logic - same as before) ...
            for token in doc:
                if "pass" in token.dep_: is_passive = True; break
                if token.lemma_ == "be" and token.head.pos_ == "VERB" and token.head.tag_ == "VBN":
                    if any(
                        child.dep_ in ("nsubjpass", "agent") for child in token.head.children): is_passive = True; break
            if is_passive:
                passive_count += 1
                if len(details['passive_sentence_examples']) < 2:  # Capture examples
                    details['passive_sentence_examples'].append(sent_text[:80] + ("..." if len(sent_text) > 80 else ""))

        # ... (Calculate ratio, determine category, generate recommendations - same as before) ...
        total_sentences = len(sentences)
        passive_ratio = passive_count / total_sentences if total_sentences else 0

        details.update({
            'sentence_count': total_sentences,
            'passive_sentence_count': passive_count,
            'passive_ratio': round(passive_ratio, 2)
            # Examples added above
        })

        if passive_ratio == 0:
            category = "Very High"
        elif passive_ratio <= 0.05:
            category = "High"
        elif passive_ratio <= 0.15:
            category = "Medium"
        elif passive_ratio <= 0.30:
            category = "Low"
        else:
            category = "Very Low"

        if category in ["Low", "Very Low"] and details['passive_sentence_examples']:
            recs.append(
                f"High use of passive voice ({passive_ratio:.0%}). Rewrite passive sentences (e.g., \"{details['passive_sentence_examples'][0]}\") into active voice.")
        elif category == "Medium":
            recs.append(f"Some passive voice ({passive_ratio:.0%}) detected. Review to ensure active voice is used.")

        return category, details, recs

    def _analyze_completeness(self, resume_dict):
        """Analyzes section completeness, returns category, details, recommendations."""
        # (No specific text examples needed, details already include missing sections)
        # (Logic remains the same as previous version)
        essential = {'personal_info', 'education', 'work_experience', 'keywords'}
        recommended = {'summary', 'projects', 'certifications', }
        details = {}
        recs = []
        # ... (logic for missing_essential, missing_recommended, present_recommended_count) ...
        present_sections = {key for key, value in resume_dict.items() if value}
        missing_essential = sorted(list(essential - present_sections))
        missing_recommended = sorted(list(recommended - present_sections))
        present_recommended_count = len(recommended.intersection(present_sections))

        details = {
            'present_sections': sorted(list(present_sections)),
            'missing_essential_sections': missing_essential,
            'missing_recommended_sections': missing_recommended,
            'present_recommended_count': present_recommended_count
        }

        if missing_essential:
            category = "Very Low"
            recs.append(
                f"CRITICAL: Missing essential sections: {', '.join(s.replace('_', ' ').title() for s in missing_essential)}. These must be included.")
        else:
            category = "High"
            if present_recommended_count == 0:
                category = "Medium"
                recs.append("Consider adding optional sections like Summary, Projects, or Certifications.")
            elif present_recommended_count >= 1:
                category = "Very High"
        # Ensure category is defined
        if 'category' not in locals(): category = "Medium"

        return category, details, recs

    def _analyze_skills_format(self, skills):
        """Analyzes skills format, returns category, details (with examples), recommendations."""
        # (Keeps verbose_skill_examples from previous version, logic is the same)
        details = {}
        recs = []
        if not skills or not isinstance(skills, list):
            return "Low", {'issue': 'Skills section missing or invalid'}, ["Skills section missing or empty."]

        num_skills = len(skills)
        long_skills_examples = [s for s in skills if isinstance(s, str) and len(s.split()) > 5][:3]  # Limit examples
        categorized_heuristically = any(':' in s for s in skills if isinstance(s, str))

        details = {
            'skill_count': num_skills,
            'verbose_skill_examples': long_skills_examples,
            'detected_categorization_heuristic': categorized_heuristically
        }

        # ... (Determine category and recs - same logic as before) ...
        score_0_to_1 = 0.9
        if num_skills < 5: score_0_to_1 = 0.4
        if len(long_skills_examples) / max(1, num_skills) > 0.2: score_0_to_1 = max(0.2, score_0_to_1 - 0.4)
        if categorized_heuristically and num_skills > 10: score_0_to_1 = min(1.0, score_0_to_1 + 0.1)
        category = self._get_category_from_score(score_0_to_1)
        if score_0_to_1 >= 0.95: category = "Very High"

        if long_skills_examples:
            recs.append(
                f"Found {len(long_skills_examples)} verbose skills entries. Keep skills concise (1-3 words). Example: '{long_skills_examples[0]}'")

        if not skills: category = "Very Low"

        return category, details, recs

    def analyze_industry_fit(self, resume_text, skills_list, industry="default"):
        """
        Analyzes industry fit based on keyword matching (ratio and absolute count).
        Returns category, details (excluding some previous fields), and recommendations.
        """
        details = {}
        recs = []  # Keep recommendations list, but population logic changes

        target_industry = industry.lower() if isinstance(industry, str) else "default"

        # --- Initial Checks ---
        if target_industry == "default" or target_industry not in self.industry_skills:
            details = {'issue': 'No specific or valid industry provided for analysis.'}
            recs = ["Industry fit not assessed: Target industry missing or invalid."]
            return "Not Assessed", details, recs  # Use a specific category like "Not Assessed"

        industry_keywords = set(self.industry_skills[target_industry])  # Use a set for efficiency
        total_kw = len(industry_keywords)

        if not industry_keywords:
            details = {'issue': f"No keywords defined for industry '{target_industry}'."}
            recs = [f"Industry fit not assessed: No keywords defined for '{target_industry}'."]
            return "Not Assessed", details, recs

        # --- Keyword Matching ---
        explicit_skills = {skill.lower() for skill in skills_list if isinstance(skill, str)}
        resume_lower = resume_text.lower() if isinstance(resume_text, str) else ""
        matched_keywords = set()
        keywords_in_skills = set()
        # Removed: keywords_in_text set, as it's no longer needed for output

        # 1. Fuzzy match keywords found in the explicit skills list
        # Use process.extract instead of extractOne to handle potential multiple good matches if needed,
        # but extractOne is usually fine if industry_keywords are distinct.
        temp_industry_list = list(industry_keywords)  # fuzzywuzzy needs a list
        for skill in explicit_skills:
            # Find the best match for this skill within the industry list
            match = fuzzy_process.extractOne(skill, temp_industry_list, score_cutoff=FUZZY_MATCH_THRESHOLD)
            if match:
                matched_keyword = match[0]
                matched_keywords.add(matched_keyword)
                keywords_in_skills.add(matched_keyword)

        # 2. Substring match keywords found directly in resume text (for those not already matched)
        remaining_kw = industry_keywords - matched_keywords
        for kw in remaining_kw:
            # Use word boundaries to avoid partial matches like 'fin' in 'finance' matching 'fintech'
            # This requires careful thought - simple substring `kw in resume_lower` might be too broad.
            # Let's stick to the simpler substring match for now as per original logic,
            # but be aware of its limitations.
            if kw in resume_lower:
                matched_keywords.add(kw)
                # We don't need to track keywords_in_text separately anymore

        # --- Calculate Metrics ---
        absolute_matches = len(matched_keywords)
        match_ratio = absolute_matches / total_kw if total_kw else 0

        # --- Determine Category based on Ratio AND Absolute Count ---
        category = "Very Low"  # Default lowest category
        if match_ratio >= 0.60:
            category = "Very High"
        elif match_ratio >= 0.40:
            category = "High"
        elif match_ratio >= 0.20:
            category = "Medium"
        elif match_ratio >= 0.05:
            category = "Low"
        # else remains "Very Low"

        # **Apply Absolute Threshold Boost**
        # If absolute matches are high, boost the category if it's currently low/medium
        if absolute_matches >= 40:
            category = "Very High"
            details['boost_reason'] = f"Boosted to High based on absolute match count ({absolute_matches})"
        elif absolute_matches >= ABSOLUTE_MATCH_THRESHOLD_HIGH and category in ["Medium", "Low", "Very Low"]:
            category = "High"
            details['boost_reason'] = f"Boosted to High based on absolute match count ({absolute_matches})"
        elif absolute_matches >= ABSOLUTE_MATCH_THRESHOLD_MEDIUM and category in ["Low", "Very Low"]:
            category = "Medium"
            details['boost_reason'] = f"Boosted to Medium based on absolute match count ({absolute_matches})"

        # --- Populate Details (Removed specified keys) ---
        details.update({
            'target_industry': target_industry,
            'total_industry_keywords': total_kw,
            'matched_keyword_count': absolute_matches,
            'match_ratio': round(match_ratio, 2),
            'keywords_found_in_skills': sorted(list(keywords_in_skills)),
            # 'keywords_found_only_in_text': REMOVED
            # 'missing_keyword_examples': REMOVED
        })

        # --- Generate Recommendations (Revised) ---
        # Since missing keywords are removed, make recommendations more general
        if category in ["Low", "Very Low"]:
            recs.append(
                f"Consider enhancing your profile with more keywords relevant to the '{target_industry}' industry to improve fit.")
        elif category == "Medium":
            recs.append(
                f"You have a moderate keyword match for the '{target_industry}' industry. Adding more specific keywords could strengthen your profile.")
        # No specific recommendation needed for High/Very High unless desired

        return category, details, recs

    def _analyze_contact_info(self, personal_info):
        """Checks contact info, provides recommendations only."""
        # This function doesn't return a category/score, just recommendations
        if not personal_info or not isinstance(personal_info, dict):
            return None, ["Missing personal information section with contact details."]

        required = {'name', 'email', 'phone'}
        recommended = {'linkedin', 'location', 'portfolio', 'website'}
        present = {k for k, v in personal_info.items() if v}
        missing_required = sorted(list(required - present))
        missing_recommended = sorted(list(recommended - present))  # Check common recommended ones
        recs = []

        if missing_required:
            recs.append(
                f"CRITICAL: Missing essential contact info: {', '.join(missing_required)}. Add these immediately.")

        email = personal_info.get('email')
        if email and ('@' not in email or '.' not in email.split('@')[-1]):
            recs.append("Warning: Email address format seems invalid. Please double-check.")
        phone = personal_info.get('phone')
        if phone and not re.search(r'^[\d\s\-\+\(\)ext.]+$', phone,
                                   re.IGNORECASE):  # Slightly more permissive phone check
            recs.append("Warning: Phone number format seems potentially unusual. Please verify.")

        if not any(k in present for k in ['linkedin', 'linkedin_url']):
            recs.append("Consider adding your LinkedIn profile URL.")
        if 'location' not in present:
            recs.append("Consider adding your general location (e.g., 'City, State').")
        if not any(k in present for k in ['portfolio', 'website', 'github', 'personal_website']):
            recs.append("Consider adding a link to your Portfolio/GitHub/Personal Website if applicable.")

        return None, recs  # Return None for score/details, only recommendations

    def _generate_dynamic_justification(self, overall_score, section_results):
        """Generates detailed justification using section categories and specific examples from details."""

        justification = [f"Overall Score: {overall_score}/100."]
        # ... (Overall assessment statement based on score - same as before) ...
        score_level_desc = ""
        if overall_score >= 90:
            score_level_desc = "Excellent"
        elif overall_score >= 80:
            score_level_desc = "Strong"
        elif overall_score >= 65:
            score_level_desc = "Fair"
        elif overall_score >= 50:
            score_level_desc = "Needs Significant Revision"
        else:
            score_level_desc = "Requires Major Overhaul"
        justification.append(
            f"Assessment: {score_level_desc}. This reflects the analysis across key resume components:")

        justification.append("\n--- Detailed Analysis ---")

        # --- Helper to format section feedback (NOW includes examples) ---
        def format_section_feedback(key, data):
            feedback = []
            name = key.replace("_", " ").title()
            category = data.get('category', 'Medium')  # Default if missing
            details = data.get('details', {})
            score = data.get('score', SCORE_CATEGORIES['Medium'])

            feedback.append(f"\n* {name} (Category: {category}, Score: {score}/100):")

            # Base explanation based on category
            if category == "Very High":
                feedback.append("  - Outcome: Exceptionally strong performance.")
            elif category == "High":
                feedback.append("  - Outcome: Strong performance, meets high standards.")
            elif category == "Medium":
                feedback.append("  - Outcome: Adequate, meets baseline expectations but could be improved.")
            elif category == "Low":
                feedback.append("  - Outcome: Below expectations; improvement recommended.")
            elif category == "Very Low":
                feedback.append("  - Outcome: Significantly below expectations; requires major attention.")

            # *** ADD DYNAMIC EXAMPLES BASED ON DETAILS ***
            # Grammar/Spelling
            if key == "grammar_spelling" and details.get('error_examples'):
                feedback.append(f"  - Detail: Errors identified, e.g., {details['error_examples'][0]}")
            # Passive Voice
            elif key == "active_voice" and details.get(
                    'passive_sentence_examples'):  # Note: Key is "Active Voice", check "passive_sentence_examples"
                feedback.append(f"  - Detail: Passive voice used, e.g., \"{details['passive_sentence_examples'][0]}\"")
            # Action Verbs - Weakness Examples
            elif key == "action_verbs":
                if details.get('weak_verb_examples'):
                    verb, example = next(iter(details['weak_verb_examples'].items()))  # Get first example pair
                    feedback.append(f"  - Detail: Weak verbs noted, e.g., '{verb}' in \"{example}\"")
                elif details.get('missing_verb_bullet_examples'):
                    feedback.append(
                        f"  - Detail: Bullets lacking action verbs, e.g., \"{details['missing_verb_bullet_examples'][0]}\"")
            # Quantifiable - Missing Examples
            elif key == "quantifiable" and details.get('non_quantified_impact_examples'):
                feedback.append(
                    f"  - Detail: Impact statements lack metrics, e.g., \"{details['non_quantified_impact_examples'][0]}\"")
            # Skills - Verbose Examples
            elif key == "skills_format" and details.get('verbose_skill_examples'):
                feedback.append(
                    f"  - Detail: Overly verbose skill entries found, e.g., '{details['verbose_skill_examples'][0]}'")
            # Sentence Structure - Length Examples
            elif key == "sentence_structure":
                if details.get('long_sentence_examples'):
                    feedback.append(
                        f"  - Detail: Overly long sentences found, e.g., {details['long_sentence_examples'][0]}")
                elif details.get('short_sentence_examples'):
                    feedback.append(
                        f"  - Detail: Very short/choppy sentences found, e.g., {details['short_sentence_examples'][0]}")
            # Bullet Points - Length Examples
            elif key == "bullet_points":
                if details.get('long_bullet_examples'):
                    feedback.append(
                        f"  - Detail: Overly long bullet points found, e.g., {details['long_bullet_examples'][0]}")
                elif details.get('short_bullet_examples'):
                    feedback.append(
                        f"  - Detail: Very brief bullet points found, e.g., {details['short_bullet_examples'][0]}")
            # Industry Fit - Missing Keywords
            elif key == "industry_fit" and details.get('missing_keyword_examples') and category in ["Low", "Very Low",
                                                                                                    "Medium"]:
                kw_list = ", ".join(details['missing_keyword_examples'])
                feedback.append(f"  - Detail: Missing relevant industry keywords (e.g., {kw_list}).")
            # Completeness - Missing Sections
            elif key == "completeness" and details.get('missing_essential_sections'):
                missing_str = ', '.join(s.replace('_', ' ').title() for s in details['missing_essential_sections'])
                feedback.append(f"  - Detail: CRITICAL - Missing essential sections: {missing_str}.")
            # Add fallback for general issues if no specific example fits
            elif 'issue' in details and category in ["Low", "Very Low"]:
                feedback.append(f"  - Issue: {details['issue']}")

            return "".join(feedback)

        # --- End Helper ---

        # ... (Iterate through sections and call helper - same as before) ...
        for key in sorted(section_results.keys()):
            if key in self.weights:
                # print(key,section_results[key])
                justification.append(format_section_feedback(key, section_results[key]))

        # ... (Concluding thought based on score - same as before) ...
        justification.append("\n--- Overall Recommendation ---")
        if overall_score >= 80:
            justification.append("Focus on minor refinements suggested.")
        elif overall_score >= 60:
            justification.append("Prioritize addressing sections categorized as 'Low' or 'Very Low'.")
        else:
            justification.append(
                "A comprehensive revision focusing on 'Very Low' and 'Low' rated sections is necessary.")

        return "\n".join(justification)

    def generate_summary_report(self, score, recommendations, section_results, justification):
        """Generates a readable summary report including the detailed justification."""
        report = []

        # 1. Use the detailed justification generated previously
        report.append(justification)  # This now contains score, assessment, and detailed breakdown
        report.append("\n" + "=" * 40 + "\n")  # Separator

        # 2. Key Recommendations (Prioritized as before)
        critical_keywords = ["CRITICAL:", "Missing essential"]
        priority_recs = [rec for rec in recommendations if any(kw in rec for kw in critical_keywords)]
        other_recs = [rec for rec in recommendations if not any(kw in rec for kw in critical_keywords)]
        display_recs = priority_recs + other_recs
        max_display_recs = 10  # Show a few more recommendations maybe

        if display_recs:
            report.append("Actionable Recommendations:")
            for i, rec in enumerate(display_recs[:max_display_recs], 1):
                report.append(f"{i}. {rec}")
            if len(display_recs) > max_display_recs:
                report.append(f"\n(...plus {len(display_recs) - max_display_recs} more suggestions.)")
        else:
            report.append("No specific recommendations generated.")

        # Optional: Add back section scores/categories if desired
        # report.append("\n" + "="*40 + "\n")
        # report.append("Section Performance Summary:")
        # for key in sorted(section_results.keys()):
        #      if key in self.weights:
        #          name = key.replace("_", " ").title()
        #          category = section_results[key]['category']
        #          score_val = section_results[key]['score']
        #          report.append(f"- {name:<25}: {category:<12} ({score_val}/100)")

        return "\n".join(report)