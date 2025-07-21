# report_merge_tool.py
"""
Tool: merge_scan_reports
Merge JSON cyber-security scan outputs found in ./scan_outputs/ into one
standardised report bundle (JSON + PDF).  Optional filters let you merge only
recent or matching files, so the agent can answer requests like
“consolidate yesterday’s Web-App scans” or “give me a report for host-A only”.
"""
from __future__ import annotations

import json, uuid, shutil, datetime as dt, logging, re
from pathlib import Path
from typing import List, Dict, Iterable, Optional

from agno.tools import tool            # ✅ Agno auto-registers the function
from pydantic import BaseModel, Field, ValidationError

# ---------------------------------------------------------------------------#
#  Adjustable paths – keep together so they can be overridden via env var     #
# ---------------------------------------------------------------------------#
SCAN_DIR   = Path(__file__).with_name("scan_outputs")
MERGE_ROOT = Path(__file__).with_name("merged_reports")
TEMPLATE   = Path(__file__).with_name("report_template.md")   # for PDF build

# ---------------------------------------------------------------------------#
#  Pydantic models – give early validation & autocompletion                  #
# ---------------------------------------------------------------------------#
class Finding(BaseModel):
    id:        str
    severity:  str
    title:     str
    details:   str

class Scan(BaseModel):
    scan_id:      str
    scanned_at:   dt.datetime
    target:       str
    findings:     List[Finding]
    tool:         Optional[str] = "unknown"

class MergedReport(BaseModel):
    merged_report_id: str
    generated_at:     dt.datetime
    scan_count:       int
    scans:            List[Scan]
    summary:          str
    findings:         List[Finding]
    severity_stats:   Dict[str, int]
    recommendations:  str

# ---------------------------------------------------------------------------#
#  Public tool – the Agno-visible entry-point                                #
# ---------------------------------------------------------------------------#
@tool(
    name="merge_scan_reports",
    description=(
        "Merge JSON security-scan outputs in ./scan_outputs/ into a single "
        "standardised report (PDF + JSON). "
        "Optionally pass a JSON string with filter keys:\n"
        "• include:  glob pattern or list of patterns (default **/*.json)\n"
        "• since:    ISO date or relative like '7d', '24h'\n"
        "• target:   regex that the scan['target'] must match\n"
        "Example: '{\"include\":\"*.json\",\"since\":\"3d\"}'"
    ),
)
def merge_scan_reports(config: str = "") -> str:
    """
    Combine selected scan JSON files into one consolidated report bundle.

    Parameters
    ----------
    config : str, optional
        JSON string with optional keys:
          include (str | List[str])  – glob(s) to include, default **/*.json
          since   (str)              – e.g. '2025-07-20T00:00Z', '48h', '7d'
          target  (str)              – regex to filter Scan.target
    """
    try:
        cfg = json.loads(config or "{}")
    except json.JSONDecodeError as e:
        return f"❌ Invalid config JSON: {e}"

    # ------------------------------------------------------------------#
    # Resolve filters                                                    #
    # ------------------------------------------------------------------#
    patterns: Iterable[str] = (
        cfg.get("include", ["**/*.json"])
        if isinstance(cfg.get("include"), list) else [cfg.get("include", "**/*.json")]
    )
    since_ts = _parse_since(cfg.get("since"))
    target_re = re.compile(cfg["target"]) if cfg.get("target") else None

    files = {
        p for pattern in patterns
        for p in SCAN_DIR.glob(pattern)
        if p.is_file() and (since_ts is None or _mtime(p) >= since_ts)
    }

    if not files:
        return "⚠️ No matching scan JSON files found."

    scans: List[Scan] = []
    errors: List[str] = []
    for f in sorted(files):
        try:
            with open(f, encoding="utf-8") as fh:
                raw = json.load(fh)
            candidate = Scan.model_validate(raw)
            if target_re and not target_re.search(candidate.target):
                continue
            scans.append(candidate)
        except (json.JSONDecodeError, ValidationError) as exc:
            errors.append(f"{f.name}: {exc}")

    if not scans:
        return "⚠️ No scans survived validation / filters."

    merged = _build_report(scans)

    # ------------------------------------------------------------------#
    # Persist outputs                                                   #
    # ------------------------------------------------------------------#
    timestamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    target_dir = MERGE_ROOT / f"merged_{timestamp}"
    target_dir.mkdir(parents=True, exist_ok=True)

    json_path = target_dir / "report.json"
    json_path.write_text(json.dumps(merged.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Build PDF from markdown template via Pandoc ------------------#
    pdf_path  = target_dir / "report.pdf"
    _write_pdf(merged, pdf_path)

    # Optionally archive the source scans alongside the bundle
    for src in files:
        shutil.copy2(src, target_dir / src.name)

    msg = [
        "📝 **Merged report created!**",
        f"- JSON → {json_path}",
        f"- PDF  → {pdf_path}",
        f"Total scans merged: {merged.scan_count}",
    ]
    if errors:
        msg.append("\nThe following files had validation errors and were skipped:")
        msg.extend(f"  • {e}" for e in errors)
    return "\n".join(msg)

# ---------------------------------------------------------------------------#
#  Helpers                                                                   #
# ---------------------------------------------------------------------------#
def _parse_since(value: Optional[str]) -> Optional[dt.datetime]:
    """Convert '7d', '24h', or ISO date to timezone-aware UTC datetime."""
    if not value:
        return None
    now = dt.datetime.now(dt.timezone.utc)
    if m := re.match(r"(?i)(\d+)([dh])", value.strip()):
        qty, unit = int(m.group(1)), m.group(2).lower()
        delta = dt.timedelta(hours=qty) if unit == "h" else dt.timedelta(days=qty)
        return now - delta
    try:
        # Accept 2025-07-20T00:00:00Z or 2025-07-20
        dt_val = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt_val if dt_val.tzinfo else dt_val.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        logging.warning("Unrecognised 'since' value: %s", value)
        return None

def _mtime(path: Path) -> dt.datetime:
    return dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)

def _build_report(scans: List[Scan]) -> MergedReport:
    unique_findings: Dict[str, Finding] = {}
    severity_tally: Dict[str, int] = {}
    for scan in scans:
        for f in scan.findings:
            unique_findings.setdefault(f.id.lower(), f)
            severity_tally[f.severity] = severity_tally.get(f.severity, 0) + 1

    return MergedReport(
        merged_report_id = str(uuid.uuid4()),
        generated_at     = dt.datetime.utcnow(),
        scan_count       = len(scans),
        scans            = scans,
        summary          = f"Aggregated {len(scans)} scans with {len(unique_findings)} unique findings.",
        findings         = list(unique_findings.values()),
        severity_stats   = severity_tally,
        recommendations  = "Refer to ‘Recommendations’ per-finding inside the PDF.",
    )

def _write_pdf(report: MergedReport, out_path: Path) -> None:
    """
    Render markdown template → PDF via Pandoc (or fallback to plain text PDF).
    create_pdf_report() from your original helper is still supported; use the
    markdown route if Pandoc is available for richer formatting.
    """
    try:
        import pypandoc, tempfile
        md = TEMPLATE.read_text(encoding="utf-8").format(**_template_vars(report))
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            tmp.write(md.encode("utf-8"))
            tmp.flush()
            pypandoc.convert_file(tmp.name, "pdf", outputfile=str(out_path))
    except Exception as e:  # noqa: BLE001
        logging.warning("Pandoc failed (%s); falling back to create_pdf_report()", e)
        from app import create_pdf_report
        out_path.write_bytes(Path(create_pdf_report(report.model_dump())).read_bytes())

def _template_vars(r: MergedReport) -> Dict[str, str]:
    """Flatten the model for Jinja-lite formatting inside the .md template."""
    return {
        "merged_report_id": r.merged_report_id,
        "generated_at":     r.generated_at.isoformat(timespec="seconds"),
        "scan_count":       str(r.scan_count),
        "severity_table":   "\n".join(f"- **{k}**: {v}" for k, v in r.severity_stats.items()),
        "summary":          r.summary,
        # More placeholders can be added to TEMPLATE.md as you wish
    }
