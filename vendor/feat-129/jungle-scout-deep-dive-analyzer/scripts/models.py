"""
Data models for the jungle-scout-deep-dive-analyzer skill.

Defines the core data structures for the pipeline:
SubQuestion/SubQuestionList (Step 4), SubQuestionAnswer/SubQuestionAnswerList (Step 5),
SkillError (error handling), and language detection utilities for bilingual support.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any


def detect_language(text: str) -> str:
    """Detect whether the input text is primarily Chinese or English.

    Uses a simple heuristic: if the text contains any CJK Unified Ideograph
    characters (Unicode range U+4E00–U+9FFF), it is classified as Chinese.
    Otherwise, it defaults to English.

    Args:
        text: The input text to classify.

    Returns:
        ``"zh"`` for Chinese, ``"en"`` for English.
    """
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'zh'
    return 'en'


@dataclass
class SubQuestion:
    """A targeted analysis question generated from indicator data.

    Attributes:
        question_id: Unique identifier, e.g. "1", "2", "3"
        question_text: The actual question text
        target_dimension: Analysis dimension, e.g. "search_volume_trend"
        expected_answer_format: Expected format, e.g. "trend_chart + growth_rate"
        source_indicators: Which indicators inform this question
    """

    question_id: str
    question_text: str
    target_dimension: str
    expected_answer_format: str
    source_indicators: list[str] = field(default_factory=list)


@dataclass
class SubQuestionList:
    """Collection of sub-questions with metadata.

    Attributes:
        question_type: Detected question type (e.g. "Market Opportunity")
        user_query: Original user query string
        questions: List of generated sub-questions
        language: Detected language code ("zh" or "en")
    """

    question_type: str
    user_query: str
    questions: list[SubQuestion] = field(default_factory=list)
    language: str = field(default='en')

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> SubQuestionList:
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        questions = [SubQuestion(**q) for q in data.get('questions', [])]
        return cls(
            question_type=data['question_type'],
            user_query=data['user_query'],
            questions=questions,
            language=data.get('language', 'en'),
        )



@dataclass
class SubQuestionAnswer:
    """Structured answer to a sub-question.

    Attributes:
        question_id: Matches SubQuestion.question_id
        answer_text: Human-readable answer narrative
        data_points: List of key-value quantitative estimates
        confidence_level: "high", "medium", or "low"
        analysis_reasoning: Step-by-step reasoning
        conclusion: One-line conclusion
        citations: Data source references
        presentation_format: How to present the answer — "table", "text", "chart", or "mixed"
        chart_suggestion: Optional chart description (for "chart" or "mixed" formats)
        recommended_asins: Optional list of ASINs the analysis points to.
            Each entry: {"asin": "B0XXX", "reason": "short reason from this dimension"}.
            Not every dimension will have product-level conclusions — only include
            when the analysis naturally identifies specific products (e.g. competition,
            entry barrier, pain-points dimensions). Leave empty for dimensions like
            seasonality or search volume trends where product-level mapping is forced.
    """

    question_id: str
    answer_text: str
    data_points: list[dict[str, str]]
    confidence_level: str
    analysis_reasoning: str
    conclusion: str
    citations: list[str] = field(default_factory=list)
    presentation_format: str = field(default='table')
    chart_suggestion: str = field(default='')
    recommended_asins: list[dict[str, str]] = field(default_factory=list)



@dataclass
class SubQuestionAnswerList:
    """Collection of sub-question answers.

    Attributes:
        answers: List of structured answers
    """

    answers: list[SubQuestionAnswer] = field(default_factory=list)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> SubQuestionAnswerList:
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        answers = [SubQuestionAnswer(**a) for a in data.get('answers', [])]
        return cls(answers=answers)


@dataclass
class SkillError:
    """Structured error response for skill pipeline failures.

    Attributes:
        step_name: Which step failed, e.g. "step_1", "step_2", "step_3"
        error_type: Error category, e.g. "validation_error", "llm_error", "parse_error"
        error_description: Human-readable error description
        recoverable: Whether the pipeline can continue past this error
    """

    step_name: str
    error_type: str
    error_description: str
    recoverable: bool

