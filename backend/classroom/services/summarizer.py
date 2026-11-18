"""Extractive lecture summarization using TextRank through the Sumy library."""
from __future__ import annotations

import re
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.text_rank import TextRankSummarizer


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text or ""))


def summarize_transcript(transcript: str, minimum_words: int = 300, maximum_words: int = 500) -> tuple[str, int]:
    """Return a 300–500 word extractive summary when the transcript is long enough.

    TextRank selects the most relevant sentences. Those sentences are then returned in
    their original order so that the lecture's explanation remains readable. When the
    transcript itself is shorter than 300 words, the available text is returned rather
    than inventing content to meet a word target.
    """
    clean = re.sub(r"\s+", " ", (transcript or "")).strip()
    if not clean:
        return "", 0

    parser = PlaintextParser.from_string(clean, Tokenizer("english"))
    source_sentences = [str(sentence).strip() for sentence in parser.document.sentences]
    if not source_sentences:
        return clean, word_count(clean)

    # Ask TextRank to rank the complete sentence set, then select by relevance.
    ranked = list(TextRankSummarizer()(parser.document, len(source_sentences)))
    if not ranked:
        return clean, word_count(clean)

    original_order = {sentence: index for index, sentence in enumerate(source_sentences)}
    chosen = []
    current_words = 0
    for sentence_obj in ranked:
        sentence = str(sentence_obj).strip()
        count = word_count(sentence)
        if not sentence or count == 0:
            continue
        if current_words + count > maximum_words:
            continue
        chosen.append(sentence)
        current_words += count
        if current_words >= minimum_words:
            break

    if not chosen:
        # A single long sentence may exceed the target; keep the most relevant one.
        chosen = [str(ranked[0]).strip()]

    # Preserve the speaker's original sequence rather than ranking order.
    chosen.sort(key=lambda sentence: original_order.get(sentence, len(source_sentences)))
    summary = " ".join(chosen).strip()
    return summary, word_count(summary)
