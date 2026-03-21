from types import SimpleNamespace

from backend.app.models import Link
from backend.app import tasks


def test_update_post_task_sends_notification_when_enabled(monkeypatch):
    called = {"notify": 0, "links_added": 0}

    async def fake_fetch_html(url):
        return "<html></html>"

    async def fake_parse_links_with_gemini(html, today_iso, timezone):
        link = Link(url="https://example.com/a", title="A", published_date_iso=today_iso)
        return SimpleNamespace(links=[link])

    async def fake_update_post_links_section(post_id, deduped):
        return {"links_added": len(deduped)}

    async def fake_notify(post_id, links_added):
        called["notify"] += 1
        called["links_added"] = links_added

    monkeypatch.setattr(tasks, "fetch_html", fake_fetch_html)
    monkeypatch.setattr(tasks, "parse_links_with_gemini", fake_parse_links_with_gemini)
    monkeypatch.setattr(tasks, "extract_links_with_heading_filter", lambda html, today_iso: [])
    monkeypatch.setattr(tasks, "filter_only_today", lambda links, today_iso: links)
    monkeypatch.setattr(tasks, "get_known_fingerprints", lambda post_id, today_iso: set())
    monkeypatch.setattr(tasks, "dedupe_by_fingerprint", lambda only_today, known_fingerprints: only_today)
    monkeypatch.setattr(tasks, "save_new_links", lambda post_id, today_iso, fps: None)
    monkeypatch.setattr(tasks, "update_post_links_section", fake_update_post_links_section)
    monkeypatch.setattr(tasks, "notify_rewards_update_for_post", fake_notify)

    tasks.update_post_task(
        post_id=206,
        source_urls=["https://example.com/source"],
        timezone="Asia/Kolkata",
        today_iso="2026-03-21",
        send_notifications=True,
    )

    assert called["notify"] == 1
    assert called["links_added"] == 1


def test_update_post_task_does_not_send_notification_when_disabled(monkeypatch):
    called = {"notify": 0}

    async def fake_fetch_html(url):
        return "<html></html>"

    async def fake_parse_links_with_gemini(html, today_iso, timezone):
        link = Link(url="https://example.com/a", title="A", published_date_iso=today_iso)
        return SimpleNamespace(links=[link])

    async def fake_update_post_links_section(post_id, deduped):
        return {"links_added": len(deduped)}

    async def fake_notify(post_id, links_added):
        called["notify"] += 1

    monkeypatch.setattr(tasks, "fetch_html", fake_fetch_html)
    monkeypatch.setattr(tasks, "parse_links_with_gemini", fake_parse_links_with_gemini)
    monkeypatch.setattr(tasks, "extract_links_with_heading_filter", lambda html, today_iso: [])
    monkeypatch.setattr(tasks, "filter_only_today", lambda links, today_iso: links)
    monkeypatch.setattr(tasks, "get_known_fingerprints", lambda post_id, today_iso: set())
    monkeypatch.setattr(tasks, "dedupe_by_fingerprint", lambda only_today, known_fingerprints: only_today)
    monkeypatch.setattr(tasks, "save_new_links", lambda post_id, today_iso, fps: None)
    monkeypatch.setattr(tasks, "update_post_links_section", fake_update_post_links_section)
    monkeypatch.setattr(tasks, "notify_rewards_update_for_post", fake_notify)

    tasks.update_post_task(
        post_id=206,
        source_urls=["https://example.com/source"],
        timezone="Asia/Kolkata",
        today_iso="2026-03-21",
        send_notifications=False,
    )

    assert called["notify"] == 0
