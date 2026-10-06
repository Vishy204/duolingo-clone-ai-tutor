"""Small text helpers shared by the API and the agents."""
import re

# Pictographs, dingbats, symbols and the variation selector / zero-width joiner used to build emoji.
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿️‍]+"
)


def strip_emoji(text: str) -> str:
    """The UI is emoji-free, so learner-facing model output is cleaned before it is stored."""
    return re.sub(r"\s{2,}", " ", _EMOJI.sub("", text)).strip()
