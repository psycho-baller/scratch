# n8n Code node (Language: Python)
# Works in both modes. Minimal changes: fix regex replacement + remove stray ratings usage.

import re
from typing import Any, Dict, List, Optional
import base64


# ---------- Helpers ----------
def _to_py_str(val):
    """Turn a JsProxy (or anything) into a Python str safely."""
    try:
        # Works in Pyodide ≥0.21
        from pyodide.ffi import JsProxy

        if isinstance(val, JsProxy):
            try:
                # For JS strings, this returns a real Python str
                return val.to_py()
            except Exception:
                return str(val)
    except Exception:
        pass
    # If it's already bytes, make a str for consistency
    if isinstance(val, bytes):
        return val.decode("ascii", errors="ignore")
    return str(val)


def coalesce_md_and_ai() -> (str, Dict[str, Any], Optional[str]):
    """
    Try to find:
      - md (markdown string)
      - ai (your AI `output` dict)
      - fileName (optional)
    """
    binary_md_js = _input.first().binary.md
    binary_md = _to_py_str(binary_md_js)
    md_text = base64.b64decode(binary_md["data"]).decode("utf-8")
    ai = _input.first().json.output or {}
    file_name = binary_md["fileName"]

    # if not md:
    #     try:
    #         ext = _("Extract From File").first()
    #         md = (ext.get("json") or {}).get("md")
    #     except Exception:
    #         pass

    if not ai:
        try:
            ai_node = _("AI Transform").first()
            ai = (ai_node.get("json") or {}).get("output") or {}
        except Exception:
            pass

    return str(md_text or ""), dict(ai or {}), file_name


def maybe_int(v):
    try:
        return None if v is None or v == "" else int(v)
    except Exception:
        return None


def replace_frontmatter_line(md_text: str, key: str, value: Optional[str]) -> str:
    """
    Replace a YAML-style 'Key:' line in the frontmatter with the provided value.
    If value is None => DO NOTHING (leave existing content as-is).
    Uses a callable replacement to avoid accidental backrefs like \14.
    """
    if value is None:
        return md_text

    pattern = rf"^({re.escape(key)}\s*:\s*)(.*)$"

    def repl(m):
        return m.group(1) + value  # safe literal insert; no backref parsing

    if md_text.strip().startswith("---"):
        try:
            header_part, body_part = md_text.split("---", 2)[1:]
            header_lines = header_part.splitlines()
            found = False
            for i, line in enumerate(header_lines):
                if re.match(pattern, line.strip()):
                    header_lines[i] = re.sub(pattern, repl, line.strip())
                    found = True
            if not found:
                header_lines.append(f"{key}: {value}")
            return f"---\n{'\n'.join(header_lines)}\n---{body_part}"
        except ValueError:
            pass

    return re.sub(pattern, repl, md_text, flags=re.MULTILINE)


def upsert_section(md_text: str, heading: str, content: Optional[str]) -> str:
    """
    Insert or replace a Markdown section by its '### Heading' title.
    If content is None/empty, we leave the section as-is (do not create).
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


# ---------- Main ----------
md, ai, file_name = coalesce_md_and_ai()
print(md)

if not isinstance(md, str) or not md.strip():
    raise ValueError(
        "Input is missing 'md' (the Markdown text). Add an Extract From File node before this and map it to 'md'."
    )

# Normalize AI keys and coerce numbers (leave unchanged if missing/null)
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

# Summary (update only if provided and non-empty string)
summary = ai.get("summary")
if isinstance(summary, str) and summary.strip():
    md = replace_frontmatter_line(md, "Summary", summary.strip())

# Numbers (skip null/missing)
for k in num_fields:
    iv = maybe_int(ai.get(k))
    if iv is None:
        continue
    md = replace_frontmatter_line(md, k.capitalize(), str(iv))

# Rating / Overall (skip if null/missing)
r = maybe_int(ai.get("rating", ai.get("overall")))
if r is not None:
    md = replace_frontmatter_line(md, "Rating", str(r))

storyworthy: Optional[bool] = ai.get("storyworthy")
zettel: List[str] = list(ai.get("zettelNotes") or [])
improvements: Optional[str] = ai.get("improvements")
accomplishments: Optional[str] = ai.get("accomplishments")

# Upsert body sections
if improvements:
    # Ensure bullet points are bullets
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
if isinstance(storyworthy, bool):
    if storyworthy and "tags:" in md:
        md = re.sub(r"(?m)^tags:\s*\n", "tags:\n  - storyworthy\n", md)

# Output for Convert to File → Google Drive Update
return {
    "json": {
        "fileName": file_name,
        "md": md,
    }
}
