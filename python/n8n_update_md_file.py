# n8n Code node (Language: Python)
import re
from typing import Any, Dict, List, Optional
import base64

# ---------- Helpers ----------


def _to_py(val):
    """Convert JsProxy (or nested) to Python types where possible."""
    try:
        from pyodide.ffi import to_py

        return to_py(val)
    except Exception:
        return val


def _to_ascii_str(val) -> str:
    """Coerce to a Python str suitable for base64 decoding."""
    val = _to_py(val)
    if isinstance(val, (bytes, bytearray)):
        try:
            return val.decode("ascii")
        except Exception:
            return val.decode("utf-8", errors="ignore")
    return str(val)


def coalesce_md_and_ai() -> (str, Dict[str, Any], Optional[str]):
    """
    Return:
      - md (markdown text string)
      - ai (your AI `output` dict)
      - file_name (from Drive binary)
    (Uses your existing inputs; just adds robust decoding.)
    """
    item = _input.first()

    # Binary -> base64 -> UTF-8 text
    bin_md = _to_py(item.binary.md)  # dict-like: {'data': '...', 'fileName': '...'}
    b64_str = _to_ascii_str(bin_md["data"])  # handle JsProxy
    md_text = base64.b64decode(b64_str.encode("ascii")).decode("utf-8")
    file_name = bin_md.get("fileName") or "note.md"

    # AI payload (as you already had)
    ai = item.json.output or {}
    if not ai:
        try:
            ai_node = _("AI Transform").first()
            ai = (ai_node.get("json") or {}).get("output") or {}
        except Exception:
            pass

    return md_text, dict(ai or {}), file_name


def _extract_frontmatter(md_text: str):
    """
    Find YAML front-matter and return (start, end, lines(list), pre, body).
    Ensures lines are de-blanked at both ends.
    """
    m = re.search(r"^---[ \t]*\r?\n([\s\S]*?)\r?\n---[ \t]*", md_text, flags=re.M)
    if not m:
        return None, None, [], "", md_text

    fm_text = m.group(1)
    lines = fm_text.splitlines()
    # Trim leading/trailing blank lines inside front-matter
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    pre = md_text[: m.start()]
    body = md_text[m.end() :]
    return m.start(), m.end(), lines, pre, body


def replace_frontmatter_line(md_text: str, key: str, value: Optional[str]) -> str:
    """
    Replace or append Key: value in front-matter.
    - If value is None: leave as-is (do not blank).
    - Always writes as 'Key: value' (one space after colon).
    - Rebuilds the front-matter with normalized spacing (no runaway newlines).
    """
    if value is None:
        return md_text

    fm_start, fm_end, lines, pre, body = _extract_frontmatter(md_text)

    if fm_start is None:
        # No front-matter: create one
        new_lines = [f"{key}: {value}"]
        fm_block = f"---\n" + "\n".join(new_lines) + "\n---\n"
        # Ensure body starts with exactly one newline after '---'
        body_norm = body.lstrip("\r\n")
        return pre + fm_block + body_norm

    # Find existing key (top-level, not indented)
    idx = None
    for i, ln in enumerate(lines):
        if re.match(rf"^{re.escape(key)}\s*:", ln.strip()):
            idx = i
            break

    if idx is not None:
        lines[idx] = f"{key}: {value}"
    else:
        lines.append(f"{key}: {value}")

    # Rebuild normalized FM: no leading/trailing blanks inside
    fm_block = f"---\n" + "\n".join(lines) + "\n---\n"
    body_norm = body.lstrip(
        "\r\n"
    )  # avoid accumulating blank lines after the closing '---'
    return pre + fm_block + body_norm


def upsert_section(md_text: str, heading: str, content: Optional[str]) -> str:
    """
    Insert or replace a Markdown section by its '### Heading' title.
    If content is None/empty, leave the section as-is (do not create).
    """
    if not content or not content.strip():
        return md_text
    section_pattern = rf"(?ms)^###\s+{re.escape(heading)}\s*(?:\n+.*?)(?=^\#\#\#|\Z)"
    new_block = f"### {heading}\n{content.strip()}\n"
    if re.search(section_pattern, md_text):
        return re.sub(section_pattern, new_block, md_text)
    else:
        anchor = "## Today's Notes"
        if anchor in md_text:
            return md_text.replace(anchor, f"{new_block}\n{anchor}")
        return md_text.rstrip() + "\n\n" + new_block


def maybe_int(v):
    try:
        return None if v is None or v == "" else int(v)
    except Exception:
        return None


# ---------- Main ----------
md, ai, file_name = coalesce_md_and_ai()

if not isinstance(md, str) or not md.strip():
    raise ValueError("Missing markdown text.")

# Numeric fields (update only if provided)
num_fields = [
    "mindfulness",
    "discipline",
    "engagement",
    "focus",
    "courage",
    "authenticity",
    "purpose",
    "energy",
    "communication",
    "uniqueness",
]

# Summary
summary = ai.get("summary")
if isinstance(summary, str) and summary.strip():
    md = replace_frontmatter_line(md, "Summary", summary.strip())

# Numbers
for k in num_fields:
    iv = maybe_int(ai.get(k))
    if iv is not None:
        md = replace_frontmatter_line(md, k.capitalize(), str(iv))

# Rating / Overall
r = maybe_int(ai.get("rating", ai.get("overall")))
if r is not None:
    md = replace_frontmatter_line(md, "Rating", str(r))

# Sections
improvements: Optional[str] = ai.get("improvements")
accomplishments: Optional[str] = ai.get("accomplishments")

if improvements:
    block = "\n".join(
        f"- {line.strip('- ').strip()}"
        for line in improvements.splitlines()
        if line.strip()
    )
    md = upsert_section(md, "Improvements", block)

if accomplishments:
    block = "\n".join(
        f"- {line.strip('- ').strip()}"
        for line in accomplishments.splitlines()
        if line.strip()
    )
    md = upsert_section(md, "Accomplishments", block)

# Optional: reflect storyworthy as a tag in frontmatter if you keep tags
storyworthy = ai.get("storyworthy")
if isinstance(storyworthy, bool) and storyworthy and "tags:" in md:
    md = re.sub(r"(?m)^tags:\s*\n", "tags:\n  - storyworthy\n", md)

# Output for Convert to File → Google Drive Update
return {"json": {"fileName": file_name, "md": md}}
