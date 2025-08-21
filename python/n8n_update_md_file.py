# n8n Code node (Language: Python)
import re
from typing import Any, Dict, List, Optional, Tuple
import base64
import datetime as dt
from textwrap import dedent

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


def _parse_title_date(file_title: Optional[str]) -> Tuple[dt.date, str]:
    """
    Try to get a date from a file title like 'YYYY-MM-DD' (with or without .md).
    Returns (date, normalized_title_string).
    Fallback to today if parsing fails.
    """
    today = dt.date.today()
    if not file_title:
        return today, today.isoformat()

    # strip extension if present
    title = re.sub(r"\.md$", "", str(file_title).strip(), flags=re.I)

    # match YYYY-MM-DD at start or whole title
    m = re.match(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$", title)
    if not m:
        # try leading date before extra text: "YYYY-MM-DD something"
        m = re.match(r"^\s*(\d{4})-(\d{2})-(\d{2})", title)

    if m:
        y, mo, d = map(int, m.groups())
        try:
            dd = dt.date(y, mo, d)
            return dd, dd.isoformat()
        except Exception:
            pass

    return today, today.isoformat()


def _iso_week_link(d: dt.date) -> str:
    """
    Build the 'YYYY-WWW' link like moment.format('YYYY-[W]WW').
    Uses ISO-year/weeks so weeks near year-boundaries resolve correctly.
    """
    iso_year, iso_week, _ = d.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _build_daily_template(*, file_title: Optional[str] = None) -> Tuple[str, str]:
    """
    Python port of your Templater template.
    Returns (markdown_text, file_name).
    """
    date_obj, normalized_title = _parse_title_date(file_title)
    prev_day = (date_obj - dt.timedelta(days=1)).isoformat()
    next_day = (
        date_obj + dt.timedelta(days=1)
    ).isoformat()  # computed for parity; not used below
    week_link = _iso_week_link(date_obj)
    created = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    md = (
        dedent(
            f"""\
        ---
        tags:
          - reviews/daily
        Created: {created}
        Headings:
          - "[[{normalized_title}#Improvements|💪]] [[{normalized_title}#Obstacles|🚧]]"
          - "[[{normalized_title}#Accomplishments|✅]]"
        Parent: "[[My Calendar/My Weekly Notes/{week_link}|{week_link}]]"
        Dreams:
        Summary:
        Mindfulness:
        Discipline:
        Engagement:
        Focus:
        Courage:
        Authenticity:
        Purpose:
        Energy:
        Communication:
        Uniqueness:
        Rating:

        ---
        ## Reminders

        **Today's Big 3**
        1.
        2.
        3.

        Remember ![[{prev_day}#Improvements]]

        ## Journals

        - [ ] **3 things I'm grateful for in my life & about myself
        - [ ] mentally planned out how to achieve my top 5 habits
        ### Morning Mindset

        **I'm excited today for:**

        **One word to describe the person I want to be today would be \\_ because:**

        **Someone who needs me on my a-game/needs my help today is:**

        **What's a potential obstacle/stressful situation for today and how would my best self deal with it?**

        **Someone I could surprise with a note, gift, or sign of appreciation is:**

        **One action I could take today to demonstrate excellence or real value is:**

        **One bold/unfomfortable action I could take today is:**

        **An overseeing high performance coach would tell me today that:**

        **What would I do if I knew I wouldn't fail**

        **What is the goal?**

        **What is the bottleneck?**

        **I know today would be successful if I did or felt this by the end:**

        ## Reflection
        ### Accomplishments
        %% What did I get done today that I would like to remember for the rest of my life? %%

        ### Obstacles
        %% What was an obstacle I faced, how did I deal with it, and what can I learn from for the future? %%

        ### Improvements
        %% What can I do tomorrow to be 1% better? How can I increase my ratings?  %%

        ## Today's Notes

        ```dataview
        TABLE file.tags as "Note Type", Created
        from ""
        WHERE contains(dateformat(Created, "yyyy-MM-dd"), this.file.name)
        SORT file.name
        ```
        """
        )
        .replace("\r\n", "\n")
        .rstrip()
        + "\n"
    )
    file_name = f"{normalized_title}.md"
    return md, file_name


def coalesce_md_and_ai() -> (str, Dict[str, Any], Optional[str]):
    """
    Return:
      - md (markdown text string)
      - ai (your AI `output` dict)
      - file_name (from Drive binary)
    (Uses your existing inputs; just adds robust decoding.)
    """
    item = _input.first()

    # Try to read binary -> text
    try:
        # Binary -> base64 -> UTF-8 text
        bin_md = _to_py(item.binary.md)  # {'data': '...', 'fileName': '...'}
        b64_str = _to_ascii_str(bin_md["data"])
        md_text = base64.b64decode(b64_str.encode("ascii")).decode("utf-8")
        file_name = bin_md.get("fileName") or "note.md"
        # If we do have the file loaded, we keep it as-is.
    except Exception:
        # No incoming file → create a fresh one from the template (Python port of Templater)
        # Prefer a title/date provided by upstream JSON (optional), else today.
        title_hint = None
        try:
            # try common fields you might set upstream
            title_hint = (
                item.json.get("fileName")
                or item.json.get("title")
                or item.json.get("date")
            )
        except Exception:
            pass
        md_text, file_name = _build_daily_template(file_title=title_hint)

    # AI payload (as you already had)
    ai = _("AI Tools Agent2").first().json.output

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

md_base64 = base64.b64encode(md.encode("utf-8")).decode("utf-8")
# Output for Convert to File → Google Drive Update
return [
    {
        "binary": {
            "data": {
                "data": md_base64,
                "fileName": file_name,
                "mimeType": "text/markdown",
            }
        }
    }
]
