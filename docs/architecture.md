# Architecture Notes

(Write-up of design decisions as you build — why LangGraph, why this
groundedness approach, what you'd do differently, etc. Good source
material for your final LinkedIn write-up post.)

## Known limitation: Arabic PDF extraction (as of initial build)

`src/ingestion/extract.py` uses PyMuPDF's default `get_text()`, which can
split single Arabic words into multiple fragments joined by stray
whitespace (a glyph-run artifact in how some Arabic PDFs encode text).
`src/ingestion/chunk.py` currently works around this with a
whitespace-normalization + index-mapping trick (`_flatten()`) so section
markers still match correctly despite the broken text.

This works, but treats the symptom rather than the cause. A more robust
fix: reconstruct text using word-level bounding boxes
(`page.get_text("words")`) sorted by position (right-to-left within a
line, top-to-bottom across lines) instead of trusting PyMuPDF's default
line reconstruction — optionally combined with the `python-bidi` /
`arabic-reshaper` libraries, which implement the Unicode Bidirectional
Algorithm (UAX #9) properly instead of a custom sort.

## Extraction & chunking — rebuilt (word/bbox reconstruction)

The original whitespace-normalization workaround described above has been
replaced. `src/ingestion/extract.py` now reconstructs text from raw
word-level spans and their bounding boxes (`page.get_text("dict")`)
instead of trusting PyMuPDF's own line-break logic, which proved
unreliable for this document's Arabic encoding (it was splitting single
words into multiple "line" objects). Spans are grouped into real visual
lines by y-position, then ordered right-to-left by x-position — correct
reading order for Arabic, with no stray mid-word newlines.

This also unlocked font-based section detection: `src/ingestion/chunk.py`
now treats bold lines in the document's "content" font family
(TimesNewRoman/Calibri, as used in this circular) as section headings,
excluding the "cover letter" font family (Arial) and headings with too
few real letters (filters out pure-punctuation/table-formatting noise
like signature-line dots). No hand-typed Arabic marker strings remain
anywhere in the pipeline.

**Known limitation:** heading detection is still font/boldness-based, not
true table-structure-aware. A small number of table *cells* that happen
to be bold, short, real words (e.g. "تراكم" / "cumulative", a column
header inside a certificate-type table) get misdetected as section
headings. Their associated chunk content is still genuinely relevant —
the issue is a slightly confusing chunk *label*, not garbage content.
Properly fixing this would require real table-region detection, which is
a meaningfully harder problem and out of scope for this project's
timeline. Worth 1-2 more real-document test cases before assuming this
heuristic transfers cleanly beyond the current corpus.

