"""Q-A pair generation from KoGovDoc-Bench using OpenAI structured outputs."""

from wigtnocr_radp.qa_generation.generator import (
    QAGenerator,
    generate_for_config,
)
from wigtnocr_radp.qa_generation.schema import (
    QA_RESPONSE_SCHEMA,
    SYSTEM_PROMPT,
    USER_TEMPLATE,
    validate_qa,
)

__all__ = [
    "QAGenerator",
    "generate_for_config",
    "QA_RESPONSE_SCHEMA",
    "SYSTEM_PROMPT",
    "USER_TEMPLATE",
    "validate_qa",
]
