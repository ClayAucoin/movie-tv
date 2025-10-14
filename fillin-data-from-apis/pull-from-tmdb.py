# C:\Users\Administrator\projects\movie-tv\fillin-data-from-apis\pull-from-tmdb.py


import csv
import time
import requests
import os
import sys
import random
import re
from typing import Tuple, Optional


# ==== CONFIG ====
INPUT_CSV = "trakt_base.csv"
OUTPUT_CSV = "movies_enriched.csv"

TMDB_KEY = os.getenv("TMDB_KEY") or "233469629197eedb0360cdcc44c77703"
TMDB_IMG_BASE = (
    "https://image.tmdb.org/t/p/original"  # change to /w500 if you prefer smaller
)
TMDB_TIMEOUT = 25
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WD_HEADERS = {
    "Accept": "application/sparql+json",
    "User-Agent": "clay-movies-enricher/1.0",
}
WD_TIMEOUT = 30

REQUIRED_COLS = {"imdb_id"}  # tmdb_id is optional now


CURRENCY_LABEL_TO_CODE = {
    # Wikidata common labels → ISO-ish codes
    "United States dollar": "USD",
    "euro": "EUR",
    "British pound sterling": "GBP",
    "Japanese yen": "JPY",
    "Canadian dollar": "CAD",
    "Australian dollar": "AUD",
    "Indian rupee": "INR",
    # add more here as you encounter them
}


def parse_money_with_unit(value: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Accepts strings like '467222728 United States dollar' or '190000000'.
    Returns (amount_int, currency_code or None).
    Assumes bare integers are USD (TMDB style).
    """
    if value is None:
        return None, None
    if isinstance(value, (int, float)):
        return int(value), "USD"
    s = str(value).strip()
    if not s:
        return None, None

    # Try "<amount> <unit label>"
    m = re.match(r"^\s*([0-9][0-9_,\.]*)\s+(.+?)\s*$", s)
    if m:
        amt_str, unit_label = m.group(1), m.group(2)
        amt = int(float(amt_str.replace(",", "").replace("_", "")))
        code = CURRENCY_LABEL_TO_CODE.get(unit_label.strip(), unit_label.strip())
        return amt, code

    # Try a bare number, assume USD
    m2 = re.match(r"^\s*([0-9][0-9_,\.]*)\s*$", s)
    if m2:
        amt = int(float(m2.group(1).replace(",", "").replace("_", "")))
        return amt, "USD"

    return None, None


def money_pretty(amount: Optional[int], code: Optional[str]) -> str:
    """
    Pretty formatter. For USD/GBP/EUR it prints a common symbol.
    Otherwise prints like '123,456 XYZ'.
    """
    if amount is None:
        return ""
    if code == "USD":
        return f"${amount:,.0f}"
    if code == "GBP":
        return f"£{amount:,.0f}"
    if code == "EUR":
        return f"€{amount:,.0f}"
    return f"{amount:,.0f} {code or ''}".strip()


# ==== HELPERS ====


def log(msg):
    print(msg, flush=True)


def ensure_input():
    if not os.path.exists(INPUT_CSV):
        log(f"❌ Input file not found: {os.path.abspath(INPUT_CSV)}")
        sys.exit(1)

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            log("❌ Input CSV has no header row.")
            sys.exit(1)
        missing = [c for c in REQUIRED_COLS if c not in reader.fieldnames]
        if missing:
            log(f"❌ Missing required columns in input: {missing}")
            log(f"   Found columns: {reader.fieldnames}")
            sys.exit(1)


def tmdb_get_movie_by_id(tmdb_id):
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    r = requests.get(
        url,
        params={"api_key": TMDB_KEY, "append_to_response": "credits"},
        timeout=TMDB_TIMEOUT,
    )
    if r.status_code != 200:
        log(f"   TMDB id={tmdb_id} -> HTTP {r.status_code}")
        return None
    return r.json()


def tmdb_find_by_imdb(imdb_id):
    # Resolve TMDB movie by external IMDb ID
    url = "https://api.themoviedb.org/3/find/" + imdb_id
    r = requests.get(
        url,
        params={"api_key": TMDB_KEY, "external_source": "imdb_id"},
        timeout=TMDB_TIMEOUT,
    )
    if r.status_code != 200:
        log(f"   TMDB find imdb={imdb_id} -> HTTP {r.status_code}")
        return None
    j = r.json()
    results = j.get("movie_results") or []
    return results[0] if results else None


def tmdb_details(tmdb_id, imdb_id=None):
    """
    Returns dict of: Poster Link, Background poster, Description (long),
    Producer, Director(s), Writer(s), Stars, Worldwide Gross (optional)
    """
    j = None
    if tmdb_id:
        j = tmdb_get_movie_by_id(tmdb_id)

    if not j and imdb_id:
        # Try to resolve tmdb_id from imdb_id then fetch details
        found = tmdb_find_by_imdb(imdb_id)
        if found and found.get("id"):
            tmdb_id_resolved = found["id"]
            log(f"   Resolved TMDB id via IMDb: {imdb_id} -> {tmdb_id_resolved}")
            j = tmdb_get_movie_by_id(tmdb_id_resolved)

    if not j:
        return {}

    poster = TMDB_IMG_BASE + j["poster_path"] if j.get("poster_path") else ""
    backdrop = TMDB_IMG_BASE + j["backdrop_path"] if j.get("backdrop_path") else ""
    overview = j.get("overview") or ""

    crew = (j.get("credits") or {}).get("crew", []) or []
    cast = (j.get("credits") or {}).get("cast", []) or []

    directors = sorted(
        {
            c.get("name", "")
            for c in crew
            if c.get("job") == "Director" and c.get("name")
        }
    )
    writers = sorted(
        {
            c.get("name", "")
            for c in crew
            if c.get("job") in ("Writer", "Screenplay") and c.get("name")
        }
    )
    producers = sorted(
        {
            c.get("name", "")
            for c in crew
            if c.get("job") == "Producer" and c.get("name")
        }
    )
    stars = [c.get("name", "") for c in cast[:5] if c.get("name")]

    out = {
        "Poster Link": poster,
        "Background poster": backdrop,
        "Description (long)": overview,
        "Producer": "; ".join(producers),
        "Director(s)": "; ".join(directors),
        "Writer(s)": "; ".join(writers),
        "Stars": "; ".join(stars),
    }

    # TMDB total revenue as a fallback for worldwide gross if Wikidata doesn't have it
    revenue = j.get("revenue")
    if isinstance(revenue, int) and revenue > 0:
        out["Worldwide Gross (TMDB)"] = str(revenue)  # USD integer
    return out


# --- replace your existing wikidata_finances_from_imdb with this ---
def wikidata_finances_from_imdb(imdb_id, max_retries=3):
    """
    Budget (P2130) and Box office (P2142) via SPARQL.
    Retries on non-JSON / transient errors, throttles between tries.
    Returns dict with Budget and Worldwide Gross when available.
    """
    if not imdb_id:
        return {}

    query = f"""
    SELECT ?budgetAmount ?budgetUnitLabel ?boxAmount ?boxUnitLabel WHERE {{
      ?film wdt:P345 "{imdb_id}" .
      OPTIONAL {{
        ?film p:P2130/psv:P2130 ?bnode .
        ?bnode wikibase:quantityAmount ?budgetAmount ;
               wikibase:quantityUnit ?budgetUnit .
      }}
      OPTIONAL {{
        ?film p:P2142/psv:P2142 ?xnode .
        ?xnode wikibase:quantityAmount ?boxAmount ;
               wikibase:quantityUnit ?boxUnit .
      }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 1
    """.strip()

    # IMPORTANT: personalize this UA per Wikidata etiquette (add email or site)
    headers = {
        "Accept": "application/sparql+json",
        "User-Agent": "clay-movies-enricher/1.1 (contact: you@example.com)",
    }

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(
                WIKIDATA_SPARQL,
                params={"query": query, "format": "json"},
                headers=headers,
                timeout=WD_TIMEOUT,
            )
            # Log unexpected statuses with a short body sample
            if r.status_code != 200 or "application/sparql-results+json" not in (
                r.headers.get("Content-Type", "")
            ):
                sample = r.text[:120].replace("\n", " ")
                log(
                    f"   Wikidata imdb={imdb_id} -> HTTP {r.status_code} [{sample!r}] (try {attempt}/{max_retries})"
                )
                raise RuntimeError(f"Non-JSON or bad status: {r.status_code}")

            data = r.json()
            rows = data.get("results", {}).get("bindings", [])
            if not rows:
                return {}

            row = rows[0]

            def getnum(key):
                return float(row[key]["value"]) if key in row else None

            def getlab(key):
                return row[key]["value"] if key in row else None

            budget_amt = getnum("budgetAmount")
            budget_unit = getlab("budgetUnitLabel") or ""
            box_amt = getnum("boxAmount")
            box_unit = getlab("boxUnitLabel") or ""

            out = {}
            if budget_amt is not None:
                out["Budget"] = f"{int(budget_amt)} {budget_unit}".strip()
            if box_amt is not None:
                out["Opening weekend"] = ""  # not provided by WD
                out["Domestic Gross"] = ""  # not split by WD
                out["International Gross"] = ""  # not split by WD
                out["Worldwide Gross"] = f"{int(box_amt)} {box_unit}".strip()
            return out

        except Exception as e:
            # Backoff with jitter to be nice (and to avoid hammering when 429)
            sleep_s = 0.8 * attempt + random.uniform(0.0, 0.4)
            log(
                f"   Wikidata attempt {attempt} failed ({e}); retrying in {sleep_s:.1f}s…"
            )
            time.sleep(sleep_s)

    # If all retries failed, return empty (TMDB fallback will still populate Worldwide)
    return {}


# ==== MAIN ====


def main():
    ensure_input()
    total = 0
    written = 0

    with (
        open(INPUT_CSV, newline="", encoding="utf-8") as fin,
        open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fout,
    ):
        reader = csv.DictReader(fin)
        # Compose output header
        extra_money_cols = [
            "Budget_amount",
            "Budget_currency",
            "Budget_pretty",
            "Worldwide_amount",
            "Worldwide_currency",
            "Worldwide_pretty",
        ]

        out_fields = (
            list(reader.fieldnames)
            + [
                "Poster Link",
                "Background poster",
                "Description (long)",
                "Producer",
                "Director(s)",
                "Writer(s)",
                "Stars",
                "Budget",
                "Opening weekend",
                "Domestic Gross",
                "International Gross",
                "Worldwide Gross",
                "Worldwide Gross (TMDB)",  # TMDB fallback
            ]
            + extra_money_cols
        )

        # Deduplicate in case re-running
        seen = set()
        fieldnames = []
        for f in out_fields:
            if f not in seen:
                fieldnames.append(f)
                seen.add(f)

        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            total += 1
            title = row.get("title") or ""
            year = row.get("year") or ""
            imdb_id = (row.get("imdb_id") or "").strip()
            tmdb_id = (row.get("tmdb_id") or "").strip()

            if not imdb_id:
                log(f"[{total}] Skipping (no imdb_id): {title} ({year})")
                writer.writerow(row)  # write the base row to keep alignment
                continue

            log(f"[{total}] {title} ({year})  imdb={imdb_id} tmdb={tmdb_id or '—'}")

            try:
                t = tmdb_details(tmdb_id, imdb_id=imdb_id)
            except Exception as e:
                log(f"   TMDB error: {e}")
                t = {}

            time.sleep(0.2)  # gentle on TMDB

            try:
                w = wikidata_finances_from_imdb(imdb_id)
            except Exception as e:
                log(f"   Wikidata error: {e}")
                w = {}

            time.sleep(0.2)  # gentle on WD

            out = {**row, **t, **w}
            # --- Normalize money fields before writing ---
            budget_raw = out.get("Budget")
            b_amt, b_code = parse_money_with_unit(budget_raw)
            out["Budget_amount"] = b_amt if b_amt is not None else ""
            out["Budget_currency"] = b_code or ""
            out["Budget_pretty"] = money_pretty(b_amt, b_code)

            world_raw = out.get("Worldwide Gross") or out.get("Worldwide Gross (TMDB)")
            w_amt, w_code = parse_money_with_unit(world_raw)
            out["Worldwide_amount"] = w_amt if w_amt is not None else ""
            out["Worldwide_currency"] = w_code or ""
            out["Worldwide_pretty"] = money_pretty(w_amt, w_code)
            # --- End normalization ---
            writer.writerow(out)
            written += 1

    log(f"\n✅ Done. Read {total} rows, wrote {written}.")
    log(f"➡️  Output: {os.path.abspath(OUTPUT_CSV)}")


if __name__ == "__main__":
    main()
