from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("BEGONIA_DB", BASE_DIR / "begonia.db"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def html_page(title: str, body: str) -> str:
    return f"""
<!doctype html>
<html lang='zh-CN'>
<head>
  <meta charset='UTF-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f7f8fa; color: #1a1a1a; }}
    header {{ background:#114b3a; color:#fff; padding: 14px 24px; }}
    nav a {{ color:#fff; margin-right: 12px; text-decoration:none; }}
    main {{ padding: 24px; max-width: 1100px; margin: 0 auto; }}
    table {{ width:100%; border-collapse: collapse; background:#fff; }}
    th, td {{ border:1px solid #eceff5; padding:8px; text-align:left; }}
    .cards {{ display:grid; grid-template-columns: repeat(4,1fr); gap:12px; margin-bottom:16px; }}
    .card {{ background:#fff; border-radius:8px; padding:12px; border:1px solid #e7e9ef; }}
  </style>
</head>
<body>
  <header>
    <h1>秋海棠新种数据库</h1>
    <nav>
      <a href='/'>首页</a>
      <a href='/species'>物种列表</a>
      <a href='/map'>地图</a>
      <a href='/daily'>昨日新增</a>
      <a href='/submit'>提交线索</a>
      <a href='/admin'>后台</a>
    </nav>
  </header>
  <main>{body}</main>
</body>
</html>
"""


def parse_post(handler: BaseHTTPRequestHandler) -> dict[str, str]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length).decode("utf-8") if length else ""
    if "application/json" in (handler.headers.get("Content-Type") or ""):
        return json.loads(raw or "{}")
    qs = parse_qs(raw)
    return {k: v[0] if v else "" for k, v in qs.items()}


class AppHandler(BaseHTTPRequestHandler):
    def send_html(self, html: str, status: int = 200) -> None:
        payload = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, data: dict | list, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def redirect(self, location: str) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/":
            return self.page_home()
        if path == "/species":
            return self.page_species(qs)
        if path.startswith("/species/"):
            return self.page_species_detail(path.split("/", 2)[2])
        if path == "/map":
            return self.page_map()
        if path == "/daily":
            return self.page_daily(qs)
        if path == "/submit":
            return self.page_submit(False, "")
        if path == "/admin":
            return self.page_admin()

        if path == "/api/species":
            return self.api_species(qs)
        if path.startswith("/api/species/"):
            return self.api_species_children(path)
        if path == "/api/digests":
            return self.api_digests(qs)
        if path == "/api/facets":
            return self.api_facets()

        self.send_html("<h2>Not Found</h2>", status=404)

    def do_POST(self):  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/submit":
            data = parse_post(self)
            name = data.get("submitted_name", "").strip()
            if not name:
                return self.page_submit(False, "请填写投稿名称")
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO submissions(submitter_name, submitter_email, submitted_name, evidence_urls, message, status, created_at) VALUES(?,?,?,?,?,'pending',?)",
                    (
                        data.get("name", ""),
                        data.get("email", ""),
                        name,
                        data.get("evidence_urls", ""),
                        data.get("message", ""),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()
            return self.page_submit(True, "")

        if path.startswith("/admin/submissions/") and path.endswith("/status"):
            try:
                sid = int(path.split("/")[3])
            except Exception:  # noqa: BLE001
                return self.send_html("invalid", 400)
            data = parse_post(self)
            status = data.get("status", "pending")
            if status not in {"pending", "reviewed", "accepted", "rejected"}:
                return self.send_html("invalid status", 400)
            with get_conn() as conn:
                conn.execute(
                    "UPDATE submissions SET status=?, reviewed_at=? WHERE id=?",
                    (status, datetime.now(timezone.utc).isoformat(), sid),
                )
                conn.commit()
            return self.redirect("/admin")

        if path == "/api/submissions":
            data = parse_post(self)
            submitted = str(data.get("submitted_name", "")).strip()
            if not submitted:
                return self.send_json({"error": "submitted_name is required"}, status=400)
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO submissions(submitter_name, submitter_email, submitted_name, evidence_urls, message, status, created_at) VALUES(?,?,?,?,?,'pending',?)",
                    (
                        data.get("submitter_name"),
                        data.get("submitter_email"),
                        submitted,
                        json.dumps(data.get("evidence_urls", []), ensure_ascii=False),
                        data.get("message"),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()
            return self.send_json({"ok": True}, status=201)

        self.send_html("<h2>Not Found</h2>", status=404)

    # -------- pages --------
    def page_home(self):
        with get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM species").fetchone()[0]
            verified = conn.execute("SELECT COUNT(*) FROM species WHERE status='verified'").fetchone()[0]
            yesterday = conn.execute("SELECT COUNT(*) FROM species WHERE date(entered_at)=date('now','-1 day')").fetchone()[0]
            week = conn.execute("SELECT COUNT(*) FROM species WHERE date(entered_at)>=date('now','-7 day')").fetchone()[0]
            latest = conn.execute("SELECT slug, scientific_name, journal_title, published_on, status FROM species ORDER BY COALESCE(entered_at,created_at) DESC LIMIT 8").fetchall()

        items = "".join(
            f"<li><a href='/species/{r['slug']}'>{r['scientific_name']}</a> · {r['journal_title'] or '-'} · {r['published_on'] or '-'} · {r['status']}</li>"
            for r in latest
        )
        body = f"""
        <section class='cards'>
          <div class='card'><div>总记录</div><strong>{total}</strong></div>
          <div class='card'><div>已核验</div><strong>{verified}</strong></div>
          <div class='card'><div>昨日新增</div><strong>{yesterday}</strong></div>
          <div class='card'><div>近7天新增</div><strong>{week}</strong></div>
        </section>
        <h2>最新记录</h2><ul>{items}</ul>
        """
        return self.send_html(html_page("首页", body))

    def page_species(self, qs: dict[str, list[str]]):
        q = (qs.get("q") or [""])[0].strip()
        status = (qs.get("status") or [""])[0].strip()
        country = (qs.get("country") or [""])[0].strip()

        clauses = []
        params: list[str] = []
        if q:
            clauses.append("(s.scientific_name LIKE ? OR s.doi LIKE ? OR s.journal_title LIKE ?)")
            params += [f"%{q}%", f"%{q}%", f"%{q}%"]
        if status:
            clauses.append("s.status=?")
            params.append(status)
        if country:
            clauses.append("o.country=?")
            params.append(country)

        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with get_conn() as conn:
            rows = conn.execute(
                f"SELECT s.*, o.country FROM species s LEFT JOIN occurrences o ON o.species_id=s.id {where} ORDER BY COALESCE(s.entered_at,s.created_at) DESC",
                tuple(params),
            ).fetchall()

        trs = "".join(
            f"<tr><td><a href='/species/{r['slug']}'>{r['scientific_name']}</a></td><td>{r['authorship'] or '-'}</td><td>{r['journal_title'] or '-'}</td><td>{r['published_on'] or '-'}</td><td>{r['country'] or '-'}</td><td>{r['status']}</td></tr>"
            for r in rows
        )
        body = f"""
        <h2>物种列表</h2>
        <form method='get'>
          <input name='q' value='{q}' placeholder='学名/DOI/期刊' />
          <input name='country' value='{country}' placeholder='国家' />
          <input name='status' value='{status}' placeholder='状态' />
          <button>筛选</button>
        </form>
        <table><tr><th>学名</th><th>作者</th><th>期刊</th><th>日期</th><th>国家</th><th>状态</th></tr>{trs}</table>
        """
        return self.send_html(html_page("物种列表", body))

    def page_species_detail(self, slug: str):
        with get_conn() as conn:
            s = conn.execute("SELECT * FROM species WHERE slug=?", (slug,)).fetchone()
            if not s:
                return self.send_html("<h2>Not Found</h2>", 404)
            media = conn.execute("SELECT * FROM media_assets WHERE species_id=?", (s["id"],)).fetchall()
            sources = conn.execute("SELECT * FROM source_documents WHERE species_id=?", (s["id"],)).fetchall()
            occ = conn.execute("SELECT * FROM occurrences WHERE species_id=?", (s["id"],)).fetchall()

        media_html = "".join(
            f"<li>{m['media_role']} · {m['display_policy']} · <a href='{m['original_url']}' target='_blank'>来源链接</a></li>"
            for m in media
        ) or "<li>暂无</li>"
        sources_html = "".join(
            f"<li>{x['source_name']} · <a href='{x['url']}' target='_blank'>文章页</a></li>" for x in sources
        ) or "<li>暂无</li>"
        occ_html = "".join(
            f"<li>{o['country'] or '-'} / {o['admin1'] or '-'} / {o['locality'] or '-'} ({o['geometry_visibility']})</li>"
            for o in occ
        ) or "<li>暂无</li>"

        body = f"""
        <h2>{s['scientific_name']}</h2>
        <p><strong>作者：</strong>{s['authorship'] or '-'}</p>
        <p><strong>DOI：</strong>{s['doi'] or '-'}</p>
        <p><strong>Section：</strong>{s['section_name'] or '-'}</p>
        <p><strong>状态：</strong>{s['status']}</p>
        <p><strong>摘要：</strong>{s['abstract_text'] or '-'}</p>
        <h3>媒体</h3><ul>{media_html}</ul>
        <h3>文献</h3><ul>{sources_html}</ul>
        <h3>分布</h3><ul>{occ_html}</ul>
        """
        return self.send_html(html_page(s["scientific_name"], body))

    def page_map(self):
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT s.slug,s.scientific_name,o.latitude,o.longitude FROM species s JOIN occurrences o ON o.species_id=s.id WHERE o.latitude IS NOT NULL AND o.longitude IS NOT NULL"
            ).fetchall()
        points = [dict(r) for r in rows]
        body = f"""
        <h2>地图点位</h2>
        <p>当前点位数量：{len(points)}</p>
        <pre>{json.dumps(points, ensure_ascii=False, indent=2)}</pre>
        <p>注：MVP 用 JSON 点位展示；可后续替换为 MapLibre/Leaflet 地图渲染。</p>
        """
        return self.send_html(html_page("地图", body))

    def page_daily(self, qs: dict[str, list[str]]):
        d = (qs.get("date") or [(date.today() - timedelta(days=1)).isoformat()])[0]
        with get_conn() as conn:
            rows = conn.execute("SELECT slug, scientific_name, journal_title FROM species WHERE date(entered_at)=date(?) AND status='verified'", (d,)).fetchall()
        lis = "".join(f"<li><a href='/species/{r['slug']}'>{r['scientific_name']}</a> · {r['journal_title'] or '-'}</li>" for r in rows) or "<li>暂无新增</li>"
        body = f"<h2>昨日新增（{d}）</h2><ul>{lis}</ul>"
        return self.send_html(html_page("昨日新增", body))

    def page_submit(self, ok: bool, err: str):
        ok_html = "<p style='color:green'>提交成功，等待审核。</p>" if ok else ""
        err_html = f"<p style='color:red'>{err}</p>" if err else ""
        body = f"""
        <h2>提交候选新种</h2>
        {ok_html}{err_html}
        <form method='post' action='/submit'>
          <input name='name' placeholder='姓名'/><br/>
          <input name='email' placeholder='邮箱'/><br/>
          <input name='submitted_name' placeholder='投稿名称*' required/><br/>
          <textarea name='evidence_urls' placeholder='证据链接'></textarea><br/>
          <textarea name='message' placeholder='备注'></textarea><br/>
          <button>提交</button>
        </form>
        """
        return self.send_html(html_page("提交", body))

    def page_admin(self):
        with get_conn() as conn:
            pending = conn.execute("SELECT * FROM submissions WHERE status='pending' ORDER BY created_at DESC").fetchall()
            latest = conn.execute("SELECT scientific_name,status,updated_at FROM species ORDER BY COALESCE(updated_at,created_at) DESC LIMIT 15").fetchall()

        p_rows = "".join(
            f"<tr><td>{p['id']}</td><td>{p['submitted_name']}</td><td>{p['submitter_name'] or '-'}</td><td>{p['status']}</td><td><form method='post' action='/admin/submissions/{p['id']}/status'><input name='status' placeholder='accepted/rejected/reviewed'/><button>更新</button></form></td></tr>"
            for p in pending
        ) or "<tr><td colspan='5'>无待审核</td></tr>"
        l_rows = "".join(f"<li>{x['scientific_name']} · {x['status']} · {x['updated_at']}</li>" for x in latest)

        body = f"<h2>后台</h2><h3>待审核投稿</h3><table><tr><th>ID</th><th>名称</th><th>提交者</th><th>状态</th><th>操作</th></tr>{p_rows}</table><h3>最近更新</h3><ul>{l_rows}</ul>"
        return self.send_html(html_page("后台", body))

    # -------- apis --------
    def api_species(self, qs: dict[str, list[str]]):
        q = (qs.get("query") or [""])[0].strip()
        country = (qs.get("country") or [""])[0].strip()
        section = (qs.get("section") or [""])[0].strip()
        status = (qs.get("status") or ["verified"])[0].strip()
        page = max(int((qs.get("page") or [1])[0]), 1)
        page_size = min(max(int((qs.get("page_size") or [24])[0]), 1), 100)

        clauses = ["s.status=?"]
        params: list[str] = [status]
        if q:
            clauses.append("(s.scientific_name LIKE ? OR s.doi LIKE ? OR s.abstract_text LIKE ?)")
            params += [f"%{q}%", f"%{q}%", f"%{q}%"]
        if country:
            clauses.append("o.country=?")
            params.append(country)
        if section:
            clauses.append("s.section_name=?")
            params.append(section)
        where = " AND ".join(clauses)

        with get_conn() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM species s LEFT JOIN occurrences o ON o.species_id=s.id WHERE {where}",
                tuple(params),
            ).fetchone()[0]
            rows = conn.execute(
                f"""
                SELECT s.*, o.country,
                  EXISTS(SELECT 1 FROM occurrences x WHERE x.species_id=s.id AND x.latitude IS NOT NULL AND x.longitude IS NOT NULL) AS has_map_point,
                  COALESCE((SELECT display_policy FROM media_assets m WHERE m.species_id=s.id LIMIT 1),'linked_only') AS cover_media_policy
                FROM species s LEFT JOIN occurrences o ON o.species_id=s.id
                WHERE {where}
                ORDER BY COALESCE(s.entered_at,s.created_at) DESC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [page_size, (page - 1) * page_size]),
            ).fetchall()

        items = [
            {
                "id": r["id"],
                "slug": r["slug"],
                "scientific_name": r["scientific_name"],
                "authorship": r["authorship"],
                "section_name": r["section_name"],
                "status": r["status"],
                "published_on": r["published_on"],
                "country": r["country"],
                "doi": r["doi"],
                "cover_media_policy": r["cover_media_policy"],
                "has_map_point": bool(r["has_map_point"]),
            }
            for r in rows
        ]
        return self.send_json({"items": items, "page": page, "page_size": page_size, "total": total})

    def api_species_children(self, path: str):
        # /api/species/{slug}[/media|/sources|/occurrences]
        parts = path.split("/")
        if len(parts) < 4:
            return self.send_json({"error": "not found"}, 404)
        slug = parts[3]
        child = parts[4] if len(parts) > 4 else ""

        with get_conn() as conn:
            species = conn.execute("SELECT * FROM species WHERE slug=?", (slug,)).fetchone()
            if not species:
                return self.send_json({"error": "not found"}, 404)

            if not child:
                if species["status"] != "verified":
                    return self.send_json({"error": "not found"}, 404)
                return self.send_json(dict(species))
            if child == "media":
                rows = conn.execute("SELECT * FROM media_assets WHERE species_id=?", (species["id"],)).fetchall()
                return self.send_json([dict(r) for r in rows])
            if child == "sources":
                rows = conn.execute("SELECT * FROM source_documents WHERE species_id=?", (species["id"],)).fetchall()
                return self.send_json([dict(r) for r in rows])
            if child == "occurrences":
                rows = conn.execute("SELECT * FROM occurrences WHERE species_id=?", (species["id"],)).fetchall()
                return self.send_json([dict(r) for r in rows])

        return self.send_json({"error": "not found"}, 404)

    def api_digests(self, qs: dict[str, list[str]]):
        d = (qs.get("date") or [(date.today() - timedelta(days=1)).isoformat()])[0]
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM digests WHERE business_date=?", (d,)).fetchone()
        return self.send_json(dict(row) if row else {"business_date": d, "items": []})

    def api_facets(self):
        with get_conn() as conn:
            c = conn.execute("SELECT country as name, COUNT(*) as count FROM occurrences WHERE country IS NOT NULL GROUP BY country").fetchall()
            s = conn.execute("SELECT section_name as name, COUNT(*) as count FROM species WHERE section_name IS NOT NULL GROUP BY section_name").fetchall()
            st = conn.execute("SELECT status as name, COUNT(*) as count FROM species GROUP BY status").fetchall()
        return self.send_json({"country": [dict(r) for r in c], "section_name": [dict(r) for r in s], "status": [dict(r) for r in st]})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"[OK] serving on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
