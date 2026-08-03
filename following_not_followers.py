"""
Calcula usuarios que sigues (following) pero que no te siguen (followers),
usando los JSON exportados por Instagram.

Entradas (por defecto):
- followers_1.json: lista de objetos con `string_list_data[].value` (username) y `href`
- following.json: objeto con `relationships_following[]` y `title` (username) + `string_list_data[].href`

Salida (por defecto):
- following_not_in_followers.json: lista de objetos
  [{"username": "<user>", "href": "https://www.instagram.com/<user>/"}]
- following_not_in_followers.html: reporte visual con la misma información
"""

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


def _norm(s: str) -> str:
    """Normaliza strings para comparación: trim + lowercase; maneja None."""
    return (s or "").strip().lower()


def _canonical_profile_url(username: str, href: str | None = None) -> str:
    """
    Devuelve una URL canónica de perfil: https://www.instagram.com/{username}/

    Si `href` viene desde el export (a veces con '/_u/{user}'), se normaliza.
    """
    u = _norm(username)
    if not u:
        return ""
    if href:
        try:
            p = urlparse(href)
            if p.scheme in {"http", "https"} and p.netloc:
                path = (p.path or "").replace("/_u/", "/")
                parts = [seg for seg in path.split("/") if seg]
                if parts:
                    u = _norm(parts[0])
                return f"https://www.instagram.com/{u}/"
        except Exception:
            pass
    return f"https://www.instagram.com/{u}/"


def load_followers(path: Path) -> dict[str, str]:
    """
    Carga followers desde followers_1.json.

    Retorna un dict: username(normalizado) -> url canónica del perfil.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    if isinstance(data, list):
        for entry in data:
            sld = (entry or {}).get("string_list_data", [])
            if isinstance(sld, list):
                for item in sld:
                    username = _norm((item or {}).get("value", ""))
                    if not username:
                        continue
                    href = (item or {}).get("href") or ""
                    out[username] = _canonical_profile_url(username, href)
    return out


def load_following(path: Path) -> dict[str, str]:
    """
    Carga following desde following.json.

    Retorna un dict: username(normalizado) -> url canónica del perfil.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    rel = (data or {}).get("relationships_following", [])
    out: dict[str, str] = {}
    if isinstance(rel, list):
        for entry in rel:
            username = _norm((entry or {}).get("title", ""))
            if not username:
                continue
            sld = (entry or {}).get("string_list_data", [])
            href = ""
            if isinstance(sld, list) and sld:
                href = (sld[0] or {}).get("href") or ""
            out[username] = _canonical_profile_url(username, href)
    return out


def render_html(users: list[dict[str, str]]) -> str:
    """Genera un HTML autocontenido con la lista de usuarios embebida."""
    payload = json.dumps(users, ensure_ascii=False)
    # Evita romper el script si algún username contuviera </script>
    payload = payload.replace("<", "\\u003c")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Following · no te siguen</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --bg0: #f4f7fb;
      --bg1: #e9eef5;
      --ink: #152033;
      --muted: #5b6b80;
      --line: rgba(21, 32, 51, 0.1);
      --accent: #e11d48;
      --accent-soft: rgba(225, 29, 72, 0.12);
      --card: rgba(255, 255, 255, 0.72);
      --shadow: 0 18px 50px rgba(21, 32, 51, 0.08);
      --radius: 18px;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: "Outfit", sans-serif;
      background:
        radial-gradient(1100px 500px at 8% -12%, #d7e8ff 0%, transparent 55%),
        radial-gradient(900px 480px at 100% 0%, #ffd6e2 0%, transparent 48%),
        linear-gradient(165deg, var(--bg0), var(--bg1));
    }}

    .wrap {{
      width: min(920px, calc(100% - 2rem));
      margin: 0 auto;
      padding: 2.5rem 0 4rem;
    }}

    header {{
      display: grid;
      gap: 0.75rem;
      margin-bottom: 1.75rem;
      animation: rise 0.7s ease both;
    }}

    .eyebrow {{
      font-size: 0.8rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
      font-weight: 600;
    }}

    h1 {{
      margin: 0;
      font-family: "Instrument Serif", serif;
      font-weight: 400;
      font-size: clamp(2.2rem, 5vw, 3.4rem);
      line-height: 1.05;
      letter-spacing: -0.02em;
    }}

    h1 em {{
      font-style: italic;
      color: var(--accent);
    }}

    .lede {{
      margin: 0;
      max-width: 38rem;
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.5;
    }}

    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: center;
      margin-bottom: 1.25rem;
      animation: rise 0.7s ease 0.08s both;
    }}

    .stat {{
      display: inline-flex;
      align-items: baseline;
      gap: 0.45rem;
      padding: 0.65rem 0.95rem;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 999px;
      backdrop-filter: blur(10px);
      box-shadow: var(--shadow);
    }}

    .stat strong {{
      font-size: 1.25rem;
      font-weight: 700;
    }}

    .stat span {{
      color: var(--muted);
      font-size: 0.9rem;
    }}

    .search {{
      flex: 1 1 220px;
      position: relative;
    }}

    .search input {{
      width: 100%;
      border: 1px solid var(--line);
      background: var(--card);
      border-radius: 999px;
      padding: 0.8rem 1rem 0.8rem 2.55rem;
      font: inherit;
      color: var(--ink);
      outline: none;
      backdrop-filter: blur(10px);
      box-shadow: var(--shadow);
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}

    .search input:focus {{
      border-color: rgba(225, 29, 72, 0.45);
      box-shadow: 0 0 0 4px var(--accent-soft), var(--shadow);
    }}

    .search svg {{
      position: absolute;
      left: 0.95rem;
      top: 50%;
      transform: translateY(-50%);
      opacity: 0.45;
      pointer-events: none;
    }}

    .actions {{
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}

    button, .file-btn {{
      appearance: none;
      border: 1px solid var(--line);
      background: var(--ink);
      color: #f8fbff;
      border-radius: 999px;
      padding: 0.75rem 1.05rem;
      font: inherit;
      font-weight: 600;
      font-size: 0.92rem;
      cursor: pointer;
      transition: transform 0.15s ease, opacity 0.15s ease, background 0.15s ease;
    }}

    button.secondary, .file-btn {{
      background: transparent;
      color: var(--ink);
    }}

    button:hover, .file-btn:hover {{
      transform: translateY(-1px);
      opacity: 0.92;
    }}

    button:active, .file-btn:active {{
      transform: translateY(0);
    }}

    .file-btn input {{
      display: none;
    }}

    .list {{
      display: grid;
      gap: 0.55rem;
      animation: rise 0.7s ease 0.14s both;
    }}

    .row {{
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 0.9rem;
      align-items: center;
      padding: 0.85rem 1rem;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      backdrop-filter: blur(10px);
      text-decoration: none;
      color: inherit;
      transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    }}

    .row:hover {{
      transform: translateY(-2px);
      border-color: rgba(225, 29, 72, 0.35);
      background: rgba(255, 255, 255, 0.95);
    }}

    .avatar {{
      width: 2.5rem;
      height: 2.5rem;
      border-radius: 50%;
      display: grid;
      place-items: center;
      font-weight: 700;
      letter-spacing: 0.02em;
      color: var(--accent);
      background:
        linear-gradient(145deg, rgba(225, 29, 72, 0.16), rgba(225, 29, 72, 0.05));
      border: 1px solid rgba(225, 29, 72, 0.18);
    }}

    .meta {{
      min-width: 0;
    }}

    .meta .user {{
      font-weight: 600;
      font-size: 1.02rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .meta .url {{
      color: var(--muted);
      font-size: 0.82rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .chip {{
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--accent);
      background: var(--accent-soft);
      border-radius: 999px;
      padding: 0.35rem 0.7rem;
      white-space: nowrap;
    }}

    .empty {{
      padding: 2.5rem 1.25rem;
      text-align: center;
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: var(--radius);
      background: rgba(255, 255, 255, 0.45);
    }}

    .empty strong {{
      display: block;
      color: var(--ink);
      font-size: 1.15rem;
      margin-bottom: 0.35rem;
    }}

    footer {{
      margin-top: 1.75rem;
      color: var(--muted);
      font-size: 0.85rem;
      animation: rise 0.7s ease 0.2s both;
    }}

    @keyframes rise {{
      from {{ opacity: 0; transform: translateY(12px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    @media (max-width: 560px) {{
      .row {{
        grid-template-columns: auto 1fr;
      }}
      .chip {{
        display: none;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="eyebrow">Instagram · export</div>
      <h1>Sigues, pero <em>no te siguen</em></h1>
      <p class="lede">Lista generada a partir de tu export. Busca un usuario o abre su perfil en Instagram.</p>
    </header>

    <div class="toolbar">
      <div class="stat"><strong id="count">0</strong><span id="count-label">usuarios</span></div>
      <div class="search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2"/>
          <path d="M20 20l-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <input id="q" type="search" placeholder="Buscar username…" autocomplete="off" />
      </div>
      <div class="actions">
        <button type="button" id="copy-btn" class="secondary">Copiar lista</button>
        <label class="file-btn secondary">Cargar JSON<input id="file" type="file" accept="application/json,.json" /></label>
      </div>
    </div>

    <div id="list" class="list" aria-live="polite"></div>
    <footer>Datos locales · no se envían a ningún servidor. Puedes recargar otro <code>following_not_in_followers.json</code>.</footer>
  </div>

  <script>
    const embedded = {payload};

    const listEl = document.getElementById("list");
    const countEl = document.getElementById("count");
    const countLabel = document.getElementById("count-label");
    const qEl = document.getElementById("q");
    const copyBtn = document.getElementById("copy-btn");
    const fileEl = document.getElementById("file");

    let users = Array.isArray(embedded) ? embedded : [];

    function initials(name) {{
      const clean = String(name || "").replace(/[^a-z0-9]/gi, "");
      return (clean.slice(0, 2) || "?").toUpperCase();
    }}

    function normalize(list) {{
      if (!Array.isArray(list)) return [];
      return list
        .map((item) => {{
          if (!item || typeof item !== "object") return null;
          const username = String(item.username || "").trim();
          if (!username) return null;
          const href = String(item.href || ("https://www.instagram.com/" + username + "/"));
          return {{ username, href }};
        }})
        .filter(Boolean)
        .sort((a, b) => a.username.localeCompare(b.username));
    }}

    function render() {{
      const query = (qEl.value || "").trim().toLowerCase();
      const filtered = users.filter((u) => u.username.toLowerCase().includes(query));

      countEl.textContent = String(filtered.length);
      countLabel.textContent = filtered.length === 1 ? "usuario" : "usuarios";

      if (!filtered.length) {{
        listEl.innerHTML = `
          <div class="empty">
            <strong>${{users.length ? "Sin coincidencias" : "Lista vacía"}}</strong>
            ${{users.length
              ? "Prueba con otro término de búsqueda."
              : "Carga un JSON generado por el script o vuelve a ejecutarlo."}}
          </div>`;
        return;
      }}

      listEl.innerHTML = filtered.map((u, i) => `
        <a class="row" href="${{u.href}}" target="_blank" rel="noopener noreferrer" style="animation-delay:${{Math.min(i, 24) * 18}}ms">
          <div class="avatar" aria-hidden="true">${{initials(u.username)}}</div>
          <div class="meta">
            <div class="user">@${{u.username}}</div>
            <div class="url">${{u.href}}</div>
          </div>
          <span class="chip">Ver perfil</span>
        </a>
      `).join("");
    }}

    qEl.addEventListener("input", render);

    copyBtn.addEventListener("click", async () => {{
      const text = users.map((u) => u.username).join("\\n");
      try {{
        await navigator.clipboard.writeText(text);
        copyBtn.textContent = "Copiado";
        setTimeout(() => {{ copyBtn.textContent = "Copiar lista"; }}, 1400);
      }} catch {{
        copyBtn.textContent = "No se pudo copiar";
        setTimeout(() => {{ copyBtn.textContent = "Copiar lista"; }}, 1600);
      }}
    }});

    fileEl.addEventListener("change", async () => {{
      const file = fileEl.files && fileEl.files[0];
      if (!file) return;
      try {{
        const raw = JSON.parse(await file.text());
        users = normalize(raw);
        qEl.value = "";
        render();
      }} catch {{
        listEl.innerHTML = `<div class="empty"><strong>JSON inválido</strong>Revisa que sea la salida del script.</div>`;
      }}
      fileEl.value = "";
    }});

    users = normalize(users);
    render();
  </script>
</body>
</html>
"""


def main() -> int:
    """
    CLI:
      python following_not_followers.py --followers followers_1.json --following following.json --out out.json
    """
    p = argparse.ArgumentParser(description="Usuarios en following pero no en followers (Instagram export).")
    p.add_argument("--followers", default="followers_1.json", help="Ruta a followers_1.json")
    p.add_argument("--following", default="following.json", help="Ruta a following.json")
    p.add_argument("--out", default="following_not_in_followers.json", help="Ruta de salida JSON")
    p.add_argument(
        "--html",
        default=None,
        help="Ruta de salida HTML (por defecto: mismo nombre que --out con extensión .html)",
    )
    args = p.parse_args()

    followers_path = Path(args.followers)
    following_path = Path(args.following)
    out_path = Path(args.out)
    html_path = Path(args.html) if args.html else out_path.with_suffix(".html")

    if not followers_path.is_file():
        p.error(f"No existe el archivo de followers: {followers_path}")
    if not following_path.is_file():
        p.error(f"No existe el archivo de following: {following_path}")

    followers_by_user = load_followers(followers_path)
    following_by_user = load_following(following_path)

    followers = set(followers_by_user)
    following = set(following_by_user)

    # Usuarios que sigues pero no te siguen
    diff_users = sorted(following - followers)

    # Salida enriquecida con link de perfil
    diff = [{"username": u, "href": following_by_user.get(u) or _canonical_profile_url(u)} for u in diff_users]

    out_path.write_text(json.dumps(diff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_html(diff), encoding="utf-8")
    print(f"JSON: {out_path}")
    print(f"HTML: {html_path}")
    print(f"Usuarios: {len(diff)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
