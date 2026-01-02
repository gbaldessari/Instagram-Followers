"""
Calcula usuarios que sigues (following) pero que no te siguen (followers),
usando los JSON exportados por Instagram.

Entradas (por defecto):
- followers_1.json: lista de objetos con `string_list_data[].value` (username) y `href`
- following.json: objeto con `relationships_following[]` y `title` (username) + `string_list_data[].href`

Salida (por defecto):
- following_not_in_followers.json: lista de objetos
  [{"username": "<user>", "href": "https://www.instagram.com/<user>/"}]
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


def main() -> int:
    """
    CLI:
      python following_not_followers.py --followers followers_1.json --following following.json --out out.json
    """
    p = argparse.ArgumentParser(description="Usuarios en following pero no en followers (Instagram export).")
    p.add_argument("--followers", default="followers_1.json", help="Ruta a followers_1.json")
    p.add_argument("--following", default="following.json", help="Ruta a following.json")
    p.add_argument("--out", default="following_not_in_followers.json", help="Ruta de salida JSON")
    args = p.parse_args()

    followers_path = Path(args.followers)
    following_path = Path(args.following)
    out_path = Path(args.out)

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
