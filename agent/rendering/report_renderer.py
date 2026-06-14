from agent.models.types import PulseReport
from agent.rendering.models import DocContent
from datetime import datetime

def _sentiment_emoji(sentiment: str) -> str:
    sentiment = sentiment.lower()
    if "positive" in sentiment:
        return "🟢"
    elif "negative" in sentiment:
        return "🔴"
    return "🟡"

def _rating_distribution(report: PulseReport) -> str:
    # We don't have the original reviews directly in PulseReport, just quotes
    # The architecture doc says "Rating distribution: ★1(12%) ...", but PulseReport doesn't
    # currently store the full rating distribution. Let's just output a placeholder or skip the distribution
    # if it's not provided. Wait, I'll calculate it if it's in the data, else skip or mock.
    # Actually, PulseReport does not have rating distribution. I will omit it for now or just put N/A.
    return "Rating distribution: (Not available in this summary level)"

def render_doc_content(report: PulseReport, app_info: dict) -> DocContent:
    product_name = app_info.get("title", report.product.capitalize())
    iso_week = report.iso_week.upper()
    
    start_date_str = report.review_window[0].strftime("%b %d").replace(" 0", " ")
    end_date_str = report.review_window[1].strftime("%b %d").replace(" 0", " ")
    
    heading_text = f"{product_name} — Week {iso_week} ({start_date_str}–{end_date_str})"
    anchor_id = f"{report.product}-pulse-{iso_week}".lower()
    
    generated_str = report.generated_at.strftime("%a %b %d, %Y %H:%M %Z").replace(" 0", " ").strip()
    
    lines = []
    lines.append(f"== {heading_text} ==")
    lines.append(f"[Bookmark: {anchor_id}]")
    lines.append(f"Generated: {generated_str} | Reviews analyzed: {report.total_reviews_analyzed}")
    lines.append("")
    
    lines.append("-- Top Themes --")
    for theme in report.themes:
        emoji = _sentiment_emoji(theme.sentiment)
        lines.append(f" {emoji} {theme.name}: {theme.description}")
    lines.append("")
    
    lines.append("-- Real User Quotes --")
    for q in report.quotes:
        lines.append(f" • \"{q.text}\" (★{q.rating})")
    lines.append("")
    
    lines.append("-- Action Ideas --")
    for i, a in enumerate(report.action_ideas, 1):
        lines.append(f" {i}. {a.title}: {a.description}")
    lines.append("")
    
    lines.append("-- Stats --")
    lines.append(f" • Reviews: {report.total_reviews_analyzed} | Themes surfaced: {len(report.themes)}")
    lines.append(f" • {_rating_distribution(report)}")
    lines.append("\n" + "="*40 + "\n")
    
    plain_text = "\n".join(lines)
    
    return DocContent(
        anchor_id=anchor_id,
        plain_text=plain_text
    )
