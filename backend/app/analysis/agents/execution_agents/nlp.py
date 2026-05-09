"""
NLP Agent — text column analysis.

Detects text columns, computes word frequency, sentiment,
and named entity extraction (LLM-assisted).
Only runs when config.include_nlp is True and text columns exist.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.analysis.base import BaseAnalysisAgent
from app.analysis.events import AgentFinding, AgentResult
from app.analysis.validation import DataQualityReport
from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    from textblob import TextBlob

    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False

try:
    from sklearn.feature_extraction.text import CountVectorizer

    HAS_SKLEARN_TEXT = True
except ImportError:
    HAS_SKLEARN_TEXT = False


class NLPAgent(BaseAnalysisAgent):
    """Text analysis: word frequency, sentiment, entity extraction."""

    def __init__(self):
        super().__init__(agent_name="nlp", use_structured_llm=True)

    async def run(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any],
        profile: Dict[str, Any],
        quality: DataQualityReport,
    ) -> AgentResult:
        findings: List[AgentFinding] = []
        errors = False

        # Detect text columns
        text_cols = quality.text_columns
        if not text_cols:
            # Also scan object columns with reasonable text length
            for col in quality.categorical_columns:
                sample = df[col].dropna().head(100)
                if len(sample) == 0:
                    continue
                avg_len = sample.astype(str).str.len().mean()
                if avg_len > 20:
                    text_cols.append(col)

        if not text_cols:
            findings.append(AgentFinding(
                metric="no_text_detected",
                value="No text columns found",
                description="NLP analysis requires text columns (average string length > 20 chars). No suitable columns detected.",
                significance=0.1,
            ))
            return AgentResult(agent_name="nlp", task_id=params.get("task_id", ""), findings=findings, confidence=0.1)

        text_col = text_cols[0]  # Analyze primary text column
        text_series = df[text_col].dropna().astype(str)
        if len(text_series) < 5:
            findings.append(AgentFinding(metric="too_few_texts", value={"count": len(text_series)}, description=f"Only {len(text_series)} non-null texts in '{text_col}'. Need ≥5.", significance=0.1))
            return AgentResult(agent_name="nlp", task_id=params.get("task_id", ""), findings=findings, confidence=0.1)

        # 1. Text statistics
        text_lengths = text_series.str.len()
        avg_length = float(text_lengths.mean())
        findings.append(AgentFinding(
            metric="text_statistics",
            value={
                "column": text_col,
                "document_count": int(len(text_series)),
                "avg_length_chars": round(avg_length, 1),
                "min_length": int(text_lengths.min()),
                "max_length": int(text_lengths.max()),
                "total_chars": int(text_lengths.sum()),
            },
            description=f"'{text_col}': {len(text_series):,} documents, avg {avg_length:.0f} chars each.",
            significance=0.55,
        ))

        # 2. Word frequency (unigrams + bigrams)
        if HAS_SKLEARN_TEXT and len(text_series) >= 10:
            try:
                # Unigrams
                vec = CountVectorizer(stop_words="english", max_features=20, ngram_range=(1, 1))
                vec.fit(text_series)
                unigrams = dict(sorted(
                    zip(vec.get_feature_names_out(), vec.transform(text_series).sum(axis=0).A1),
                    key=lambda x: x[1], reverse=True
                ))

                # Bigrams
                vec2 = CountVectorizer(stop_words="english", max_features=15, ngram_range=(2, 2))
                vec2.fit(text_series)
                bigrams = dict(sorted(
                    zip(vec2.get_feature_names_out(), vec2.transform(text_series).sum(axis=0).A1),
                    key=lambda x: x[1], reverse=True
                ))

                findings.append(AgentFinding(
                    metric="word_frequency",
                    value={"top_unigrams": {str(k): int(v) for k, v in list(unigrams.items())[:10]}, "top_bigrams": {str(k): int(v) for k, v in list(bigrams.items())[:10]}},
                    description=f"Top unigrams: {', '.join(list(unigrams.keys())[:5])}. Top bigrams: {', '.join(list(bigrams.keys())[:3])}.",
                    significance=0.65,
                ))
            except Exception as exc:
                logger.log_error("Word frequency extraction failed", exc)

        # 3. Sentiment analysis
        if HAS_TEXTBLOB and len(text_series) >= 5:
            try:
                sentiments = text_series.head(500).apply(lambda t: TextBlob(t).sentiment.polarity)
                avg_sentiment = float(sentiments.mean())
                sentiment_dist = {
                    "positive_pct": round(float((sentiments > 0.1).mean()) * 100, 1),
                    "neutral_pct": round(float(((sentiments >= -0.1) & (sentiments <= 0.1)).mean()) * 100, 1),
                    "negative_pct": round(float((sentiments < -0.1).mean()) * 100, 1),
                }
                findings.append(AgentFinding(
                    metric="sentiment_analysis",
                    value={"column": text_col, "avg_polarity": round(avg_sentiment, 4), "distribution": sentiment_dist},
                    description=f"Sentiment: {sentiment_dist['positive_pct']}% positive, {sentiment_dist['neutral_pct']}% neutral, {sentiment_dist['negative_pct']}% negative. Avg polarity: {avg_sentiment:.3f}.",
                    significance=0.7,
                ))
            except Exception as exc:
                logger.log_error("Sentiment analysis failed", exc)
        elif not HAS_TEXTBLOB:
            findings.append(AgentFinding(metric="textblob_unavailable", value="textblob not installed", description="Install textblob for sentiment analysis: pip install textblob", significance=0.0))

        # 4. Topic/keyword extraction via LLM (sample only)
        if len(text_series) >= 5:
            try:
                samples = text_series.sample(min(5, len(text_series)), random_state=42).tolist()
                sample_text = "\n---\n".join(f"{i + 1}. {t[:300]}" for i, t in enumerate(samples))

                prompt = f"""Analyze these text samples from column '{text_col}':

{sample_text}

Summarize in JSON format what these texts are about."""
                system_prompt = "You are a text analyst. Return a JSON object with 'topics' (list of 3-5 key topics) and 'domain' (e.g., 'customer feedback', 'product reviews', 'support tickets', 'legal documents')."

                result = await self._call_llm(prompt, system_prompt, max_retries=2)
                topics = result.get("topics", [])
                domain = result.get("domain", "unknown")

                findings.append(AgentFinding(
                    metric="text_topic_analysis",
                    value={"column": text_col, "topics": topics, "domain": domain},
                    description=f"Text domain: {domain}. Key topics: {', '.join(topics[:5])}.",
                    significance=0.75,
                ))
            except Exception as exc:
                logger.log_error("Topic extraction via LLM failed", exc)
                errors = True

        confidence = self.compute_confidence(len(findings), errors, quality.overall_score)
        return AgentResult(agent_name="nlp", task_id=params.get("task_id", ""), findings=findings, confidence=confidence)
