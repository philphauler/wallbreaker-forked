from __future__ import annotations

from textual.theme import Theme

RTH_THEME = Theme(
    name="claude-red",
    primary="#E5484D",
    secondary="#C77DFF",
    accent="#FF7A85",
    success="#56D364",
    warning="#E8A33D",
    error="#FF4D4D",
    surface="#1B0E10",
    panel="#2A1216",
    background="#100A0B",
    dark=True,
    variables={
        "verdict-good": "#56D364",
        "verdict-partial": "#E8A33D",
        "verdict-bad": "#FF4D4D",
        "field-label": "#9C6B6F",
        "feedback": "#C77DFF",
    },
)

PALETTE = {
    "user": "#FF7A85",
    "assistant": "#56D364",
    "tool_call": "#E8A33D",
    "tool_result": "#C77DFF",
    "info": "#FF7A85",
    "error": "#FF4D4D",
    "feedback": "#C77DFF",
    "label": "#9C6B6F",
    "muted": "#9C6B6F",
    "accent": "#FF7A85",
    "secondary": "#C77DFF",
    "verdict_good": "#56D364",
    "verdict_partial": "#E8A33D",
    "verdict_bad": "#FF4D4D",
}
