import subprocess
import uuid
import os
import json
import re
import math
import socket
import threading
import logging
import time
import tempfile
import glob
import csv
import ipaddress
import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


from typing import Tuple, List, Dict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin, urlunparse, parse_qsl, urlencode

# --- External Libs ---
import requests

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    mysql = None
    MYSQL_AVAILABLE = False


from dotenv import load_dotenv
from flask import (
    Flask, request, jsonify, render_template, 
    redirect, url_for, abort, send_from_directory, 
    make_response, send_file, current_app, Response
)
from requests.adapters import HTTPAdapter
from requests.exceptions import SSLError, RequestException
from urllib3.util.retry import Retry
import urllib3
from bs4 import BeautifulSoup
from langdetect import detect



# Optional Libs (Try/Except import)


try:
    from readability import Document
except ImportError:
    Document = None

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

# --- Local Imports ---
try:
    from fetch_meta import extract_page_title
except ImportError:
    def extract_page_title(html):
        return ""
    
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 1. KONFIGURACJA I ZMIENNE ÅšRODOWISKOWE
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
load_dotenv()

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# OPTYMALIZACJA CSV (RAM CACHE)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CSV_CACHE = {}
CSV_CACHE_LIMIT = 1  # max 1 plik CSV w RAM na worker
CSV_CACHE_MTIME = {}
CSV_CACHE_LOCK = threading.Lock()

MAIN_CSV = None
MAIN_SNAPSHOT = None

# Logowanie
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-5s %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Konfiguracja analizy
AN_TIMEOUT   = float(os.getenv("ANALYZE_TIMEOUT", "3.0"))
AN_MAX_BYTES = int(os.getenv("ANALYZE_MAX_BYTES", str(1024*1024)))
AN_GEO       = os.getenv("ANALYZE_GEO", "1") == "1"
AN_IPV4      = os.getenv("ANALYZE_FORCE_IPV4", "0") == "1"

# Wymuszenie IPv4 (fix na wiszÄ…ce IPv6)
if AN_IPV4:
    try:
        import urllib3.util.connection as urllib3_conn
        def _allowed_gai_family():
            return socket.AF_INET
        urllib3_conn.allowed_gai_family = _allowed_gai_family
    except Exception:
        pass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# StaÅ‚e
DOMAIN_RX = re.compile(r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z]{2,})+$', re.IGNORECASE)
SCHEME_RX = re.compile(r'^[a-zA-Z][a-zA-Z0-9+\-.]*://')
MAX_BATCH_DOMAINS = 50
MAX_DOMAIN_LENGTH = 255
MAX_URL_LENGTH = 2000
DEFAULT_TIMEOUT = 4

MAX_EXTRACT_HTML_BYTES = 5 * 1024 * 1024  # 5 MB

# Parametry trackingowe do wyciÄ™cia
TRACKING_PARAMS = {
    "utm_source","utm_medium","utm_campaign",
    "utm_term","utm_content","gclid","fbclid","fbp","ref",
    "utm_id","mkt_tok","mc_cid","mc_eid"
}

here = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(here, "templates"),
    static_folder=os.path.join(here, "static"),
    static_url_path="/static"
)


app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['VERSION'] = '1.4-unified-fixed'
app.config['DEBUG'] = False


@app.after_request
def disable_html_browser_cache(response):
    """HTML is always fresh; heavy non-HTML assets keep their own cache."""
    if response.mimetype == "text/html":
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CACHE SNAPSHOTÃ“W (60 sekund)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SNAPSHOT_CACHE = {
    "snaps": [],
    "latest": None,
    "use_db": False,
    "ts": time.time()
}
SNAPSHOT_TTL = 60  # sekundy

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FILTER CACHE (10 sekund dla czÄ™sto wyszukiwanych zapytaÅ„)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FILTER_CACHE = {}
FILTER_CACHE_TTL = 10  # sekundy

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FAST FILTER RESULT CACHE
# Gotowy wynik snapshot + q trzymamy w RAM,
# Å¼eby paginacja nie skanowaÅ‚a miliona rekordÃ³w ponownie.
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

FILTER_RESULT_CACHE = {}
FILTER_RESULT_CACHE_TTL = 300       # 5 minut
FILTER_RESULT_CACHE_MAX = 32        # max liczba rÃ³Å¼nych filtrÃ³w na worker
FILTER_RESULT_CACHE_MAX_ROWS = 100_000
FILTER_RESULT_CACHE_LOCK = threading.Lock() 

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FAST LANES â€” PRIORYTET CSV vs API
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
from threading import Semaphore

# CSV / PAGINACJA â€” RÃ“Å»NE SEMAFORY DLA RÃ“Å»NYCH TRAS
CSV_FAST_SEM_FAST = Semaphore(2)
CSV_FAST_SEM_NORMAL = Semaphore(10)
API_SEM = Semaphore(3)
CHECK_PAGE_SEM = Semaphore(4)
FETCH_META_SEM = Semaphore(2)
EXTRACT_TEXT_SEM = Semaphore(2)
CHECK_PAGE_SIMPLE_SEM = Semaphore(4)
FETCH_META_SIMPLE_SEM = Semaphore(4)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FAST TABLE â€” Production CSV-only architecture
# Instant render + hydration via AJAX
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



# ZakÅ‚adamy, Å¼e CSV_CACHE i CSV_CACHE_MTIME sÄ… zdefiniowane globalnie
# tak jak ustaliliÅ›my wczeÅ›niej.

FILTER_CACHE_MAX = 200  # ðŸ”¥ limit cache

def filter_cache_cleanup():
    now = time.time()

    # usuÅ„ przeterminowane
    expired_keys = [
        k for k, v in FILTER_CACHE.items()
        if now - v["ts"] > FILTER_CACHE_TTL
    ]
    for k in expired_keys:
        FILTER_CACHE.pop(k, None)

    # jeÅ›li nadal za duÅ¼y â†’ usuÅ„ najstarsze
    while len(FILTER_CACHE) > FILTER_CACHE_MAX:
        oldest = min(FILTER_CACHE, key=lambda k: FILTER_CACHE[k]["ts"])
        FILTER_CACHE.pop(oldest, None)
        
def filter_result_cache_cleanup():
    now = time.time()

    with FILTER_RESULT_CACHE_LOCK:

        expired = [
            key
            for key, item in FILTER_RESULT_CACHE.items()
            if now - item["ts"] > FILTER_RESULT_CACHE_TTL
        ]

        for key in expired:
            FILTER_RESULT_CACHE.pop(key, None)

        while len(FILTER_RESULT_CACHE) > FILTER_RESULT_CACHE_MAX:
            oldest = min(
                FILTER_RESULT_CACHE,
                key=lambda key: FILTER_RESULT_CACHE[key]["ts"]
            )
            FILTER_RESULT_CACHE.pop(oldest, None)


def get_filtered_fast_rows(all_sites, snapshot, q, csv_mtime):
    """
    Filtruje caÅ‚y snapshot tylko przy pierwszym uÅ¼yciu snapshot + q.
    Kolejne strony uÅ¼ywajÄ… gotowej listy z RAM.
    """

    result_key = f"{snapshot}:{csv_mtime}:{q}"

    now = time.time()

    with FILTER_RESULT_CACHE_LOCK:
        cached = FILTER_RESULT_CACHE.get(result_key)

        if cached:
            if now - cached["ts"] <= FILTER_RESULT_CACHE_TTL:
                cached["ts"] = now

                logger.info(
                    f"[FILTER RESULT HIT] snapshot={snapshot} "
                    f"q={q!r} rows={len(cached['rows'])}"
                )

                return cached["rows"]

            FILTER_RESULT_CACHE.pop(result_key, None)

    # CACHE MISS â€” tylko tutaj skanujemy milion
    started = time.perf_counter()

    # Country dropdown wysyÅ‚a np. ".pl", ".de", ".uk".
    # Dla dokÅ‚adnie 2-literowego TLD filtrujemy WYÅÄ„CZNIE koÅ„cÃ³wkÄ™ domeny.
    if re.fullmatch(r"\.[a-z]{2}", q):
        matched = [
            s
            for s in all_sites
            if s["domain"].lower().rstrip(".").endswith(q)
        ]
    else:
        # ZwykÅ‚a wyszukiwarka nadal dziaÅ‚a jak wczeÅ›niej:
        # fragment moÅ¼e wystÄ™powaÄ‡ w dowolnym miejscu domeny.
        matched = [
            s
            for s in all_sites
            if q in s["domain"].lower()
        ]
    
    elapsed = time.perf_counter() - started

    logger.info(
        f"[FILTER RESULT BUILD] snapshot={snapshot} "
        f"q={q!r} rows={len(matched)} "
        f"elapsed={elapsed:.3f}s"
    )

    # Nie pozwalamy bardzo szerokim zapytaniom zjadaÄ‡ RAM.
    if len(matched) <= FILTER_RESULT_CACHE_MAX_ROWS:

        filter_result_cache_cleanup()

        with FILTER_RESULT_CACHE_LOCK:
            FILTER_RESULT_CACHE[result_key] = {
                "ts": time.time(),
                "rows": matched,
            }

        logger.info(
            f"[FILTER RESULT SAVE] snapshot={snapshot} "
            f"q={q!r} rows={len(matched)}"
        )

    else:
        logger.info(
            f"[FILTER RESULT SKIP] snapshot={snapshot} "
            f"q={q!r} rows={len(matched)} "
            f"limit={FILTER_RESULT_CACHE_MAX_ROWS}"
        )

    return matched        

@app.route("/top_sites_fast", methods=["GET", "POST"])
def top_sites_fast():
    # Public GET is the light entry point only. Dynamic table operations are
    # accepted solely from the page's JavaScript over POST, so crawlers cannot
    # build an expensive URL frontier from snapshot/q/page links.
    if request.method == "GET" and request.query_string:
        return "Dynamic table URLs are not available over GET", 404

    if request.method == "POST":
        if (
            request.headers.get("X-Requested-With") != "table-fast"
            or request.headers.get("X-Partial") != "tbody"
        ):
            return "Forbidden", 403
        params = request.form
    else:
        params = request.args

    request_started = time.perf_counter()
    request_page = params.get("page", "1")
    request_partial = request.headers.get("X-Partial", "")

    logger.info(
        f"[TOP_FAST ENTER] page={request_page} "
        f"partial={request_partial} "
        f"time={datetime.now().strftime('%H:%M:%S.%f')[:-3]}"
    )

    semaphore_started = time.perf_counter()

    if not CSV_FAST_SEM_FAST.acquire(blocking=False):
        logger.warning(
            f"[TOP_FAST BUSY] page={request_page} "
            f"elapsed={time.perf_counter() - request_started:.3f}s"
        )
        return "CSV busy, retry", 503

    logger.info(
        f"[TOP_FAST SEM ACQUIRED] page={request_page} "
        f"wait={time.perf_counter() - semaphore_started:.3f}s"
    )

    try:
        is_embed = request.headers.get("X-Embed") == "1"
        is_partial = request.headers.get("X-Partial") == "tbody"

        raw_q = params.get("q", "", type=str)
        q = normalize_search_query(raw_q)

        page = max(1, params.get("page", 1, type=int) or 1)
        per_page = max(
            1,
            min(params.get("per_page", 10, type=int) or 10, 100)
        )
        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # SNAPSHOT / CSV
        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        csv_dir = Path(current_app.static_folder) / "csv"

        available_snapshots = sorted(
            [p.stem for p in csv_dir.glob("*.csv") if p.stem.isdigit()],
            reverse=True
        )

        requested_snapshot = normalize_snapshot_arg(
            params.get("snapshot", "")
        )

        snapshot = (
            requested_snapshot
            if requested_snapshot in available_snapshots
            else MAIN_SNAPSHOT
        )

        csv_path = csv_dir / f"{snapshot}.csv"

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # FILTER CACHE
        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        mode = "partial" if is_partial else "full"
        filter_key = f"{snapshot}:{q}:{page}:{per_page}:{mode}"

        cached = FILTER_CACHE.get(filter_key)
        if cached:
            if time.time() - cached["ts"] < FILTER_CACHE_TTL:
                logger.info(f"[CACHE HIT] {filter_key}")

                resp = make_response(cached["html"])
                for k, v in cached["headers"].items():
                    resp.headers[k] = v
                return resp
            else:
                FILTER_CACHE.pop(filter_key, None)

        start_idx = (page - 1) * per_page
        end_idx = page * per_page

        if not csv_path.exists():
            return f"BÅ‚Ä…d: Plik {csv_path} nie istnieje.", 404

        csv_started = time.perf_counter()

        logger.info(
            f"[TOP_FAST CSV START] page={request_page} "
            f"file={csv_path.name}"
        )

        load_csv_into_cache(csv_path)

        logger.info(
            f"[TOP_FAST CSV READY] page={request_page} "
            f"elapsed={time.perf_counter() - csv_started:.3f}s"
        )

        cache_key = str(csv_path.absolute())
        all_sites = CSV_CACHE.get(cache_key, [])
        
        cache_lookup_done = time.perf_counter()

        logger.info(
            f"[TOP_FAST RAM READY] page={request_page} "
            f"rows={len(all_sites)} "
            f"elapsed_from_csv={cache_lookup_done - csv_started:.3f}s"
        )        

        if not all_sites:
            logger.error(f"[FAST TABLE] No sites in cache for {csv_path.name}")
            return "Internal server error: CSV cache empty", 500

        filter_started = time.perf_counter()
        
        # ðŸš€ FILTER + PAGINATION
        if not q:
            # PeÅ‚ny snapshot â€” najszybsza Å›cieÅ¼ka.
            total = len(all_sites)
            rows = all_sites[start_idx:end_idx]

        else:
            # Filtr snapshot + q liczony tylko RAZ.
            csv_mtime = CSV_CACHE_MTIME.get(cache_key, 0)

            matched = get_filtered_fast_rows(
                all_sites,
                snapshot,
                q,
                csv_mtime
            )

            total = len(matched)

            # Paginacja dziaÅ‚a juÅ¼ wyÅ‚Ä…cznie na gotowym maÅ‚ym zbiorze.
            rows = matched[start_idx:end_idx]

        total_pages = max(1, (total + per_page - 1) // per_page) if per_page else 1

        filter_done = time.perf_counter()

        logger.info(
            f"[TOP_FAST FILTER DONE] page={request_page} "
            f"q={bool(q)} "
            f"rows={len(rows)} "
            f"total_rows={total} "
            f"elapsed={filter_done - filter_started:.3f}s"
        )

        render_started = time.perf_counter()

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # PARTIAL (tbody)
        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if is_partial:
            resp = make_response(render_template(
                "top_sites_fast_tbody.html",
                rows=rows,
                q=raw_q
            ))
            resp.headers["X-Total-Pages"] = str(total_pages)
            resp.headers["X-Total-Rows"] = str(total)
            resp.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
            resp.headers["Cache-Control"] = "no-store"

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # FULL PAGE
        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        else:
            resp = make_response(render_template(
                "top_sites_fast.html",
                rows=rows,
                page=page,
                total_pages=total_pages,
                per_page=per_page,
                total_rows=total,
                available_snapshots=available_snapshots,
                is_embed_mode=is_embed,
                q=raw_q,
                snapshot=snapshot,
            ))
            resp.headers["X-Total-Pages"] = str(total_pages)

        render_done = time.perf_counter()

        logger.info(
            f"[TOP_FAST RENDER DONE] page={request_page} "
            f"partial={is_partial} "
            f"elapsed={render_done - render_started:.3f}s"
        )
        save_cache_started = time.perf_counter()

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # ðŸš€ SAVE CACHE (SAFE)
        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if len(FILTER_CACHE) >= FILTER_CACHE_MAX:
            oldest = min(FILTER_CACHE, key=lambda k: FILTER_CACHE[k]["ts"])
            FILTER_CACHE.pop(oldest, None)
        
        filter_cache_cleanup()
        
        FILTER_CACHE[filter_key] = {
            "ts": time.time(),
            "html": resp.get_data(),
            "headers": dict(resp.headers)
        }

        logger.info(f"[CACHE SAVE] {filter_key}")
        
        logger.info(
            f"[TOP_FAST CACHE SAVE DONE] page={request_page} "
            f"elapsed={time.perf_counter() - save_cache_started:.3f}s"
        )        

        return resp

    except Exception as e:
        logger.exception("[FAST TABLE ERROR]")
        return "Internal server error", 500

    finally:
        total_elapsed = time.perf_counter() - request_started

        logger.info(
            f"[TOP_FAST EXIT] page={request_page} "
            f"total={total_elapsed:.3f}s "
            f"time={datetime.now().strftime('%H:%M:%S.%f')[:-3]}"
        )

        CSV_FAST_SEM_FAST.release() 
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 2. BAZA DANYCH (MYSQL)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
db_config = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "database": os.getenv("DB_NAME", "similar_sites"),
    "user":     os.getenv("DB_USER", "root"),
    "charset":  "utf8mb4",
    "use_unicode": True,
}
pwd = os.getenv("DB_PASS") or os.getenv("DB_PASSWORD")
if pwd:
    db_config["password"] = pwd

def get_db_connection():
    """
    Tworzy poÅ‚Ä…czenie z bazÄ….
    JeÅ›li baza nie dziaÅ‚a/nie istnieje, rzuci wyjÄ…tek, ktÃ³ry obsÅ‚uÅ¼ymy w widokach (fallback do CSV).
    """
    return mysql.connector.connect(**db_config)

def verify_ssl(domain: str) -> bool:
    bad_ssl = {'login-account.net'}
    return domain not in bad_ssl

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 3. HELPERY (CACHE, URL, FORMATOWANIE)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# â”€â”€â”€â”€â”€â”€â”€â”€â”€ GEO CACHE + FALLBACK â”€â”€â”€â”€â”€â”€â”€â”€â”€
GEO_CACHE_TTL = 86400  # 24h
_geo_cache = {}       # ip -> (ts, data)
GEO_CACHE_MAX = 2000

GEO_PRIMARY_COOLDOWN = 300  # 5 minut
_geo_primary_blocked_until = 0.0



GEO_FALLBACK_COOLDOWN = 65
_geo_fallback_blocked_until = 0.0


def _geo_primary_available():
    return time.time() >= _geo_primary_blocked_until


def _geo_primary_block(reason="limit"):
    global _geo_primary_blocked_until

    _geo_primary_blocked_until = time.time() + GEO_PRIMARY_COOLDOWN

    logger.warning(
        f"[GEO] ip-api temporarily disabled for "
        f"{GEO_PRIMARY_COOLDOWN}s reason={reason}"
    )

def _geo_fallback_available():
    return time.time() >= _geo_fallback_blocked_until


def _geo_fallback_block(reason="limit"):
    global _geo_fallback_blocked_until

    _geo_fallback_blocked_until = time.time() + GEO_FALLBACK_COOLDOWN

    logger.warning(
        f"[GEO] FreeIPAPI temporarily disabled for "
        f"{GEO_FALLBACK_COOLDOWN}s reason={reason}"
    )

def _geo_cache_get(ip):
    v = _geo_cache.get(ip)
    if not v:
        return None
    ts, data = v
    if time.time() - ts > GEO_CACHE_TTL:
        _geo_cache.pop(ip, None)
        return None
    return data

def _geo_cache_set(ip, data):
    if len(_geo_cache) >= GEO_CACHE_MAX:
        oldest = min(_geo_cache, key=lambda k: _geo_cache[k][0])
        _geo_cache.pop(oldest, None)

    _geo_cache[ip] = (time.time(), data)

def geo_lookup(ip: str):
    # 0ï¸âƒ£ CACHE
    cached = _geo_cache_get(ip)
    if cached:
        return cached

    # 1ï¸âƒ£ PRIMARY â€” ip-api.com
    if _geo_primary_available():
        try:
            r = session.get(
                f"http://ip-api.com/json/{ip}"
                "?fields=status,country,countryCode,regionName,city,"
                "timezone,isp,as,asname,lat,lon,message",
                timeout=1.0
            )

            # Jawny HTTP rate limit
            if r.status_code == 429:
                _geo_primary_block("HTTP 429")

            elif r.ok:
                j = r.json()

                if j.get("status") == "success":
                    data = {
                        "country":      j.get("country", "Unknown"),
                        "country_code": j.get("countryCode", ""),
                        "region":       j.get("regionName", "Unknown"),
                        "city":         j.get("city", "Unknown"),
                        "timezone":     j.get("timezone", ""),
                        "isp":          j.get("isp", "Unknown"),
                        "as":           j.get("as", ""),
                        "asname":       j.get("asname", ""),
                        "lat":          j.get("lat"),
                        "lon":          j.get("lon"),
                        "source":       "ip-api"
                    }

                    _geo_cache_set(ip, data)
                    return data

                # ip-api moÅ¼e odpowiedzieÄ‡ HTTP 200,
                # ale status wewnÄ…trz JSON bÄ™dzie "fail".
                message = str(j.get("message", "")).lower()

                if "limit" in message or "too many" in message:
                    _geo_primary_block(message or "api limit")

                else:
                    logger.info(
                        f"[GEO] ip-api failed ip={ip} "
                        f"message={message!r}"
                    )

            else:
                logger.warning(
                    f"[GEO] ip-api HTTP {r.status_code} ip={ip}"
                )

        except Exception as e:
            logger.warning(
                f"[GEO] ip-api error ip={ip}: {e}"
            )

    # 2ï¸âƒ£ FALLBACK â€” FreeIPAPI
    if _geo_fallback_available():
        try:
            r = session.get(
                f"https://free.freeipapi.com/api/json/{ip}",
                timeout=1.2
            )

            if r.status_code == 429:
                _geo_fallback_block("HTTP 429")

            elif r.ok:
                j = r.json()

                timezones = j.get("timeZones") or []

                data = {
                    "country":      j.get("countryName", "Unknown"),
                    "country_code": j.get("countryCode", ""),
                    "region":       j.get("regionName", "Unknown"),
                    "city":         j.get("cityName", "Unknown"),
                    "timezone":     timezones[0] if timezones else "",
                    "isp":          j.get("asnOrganization", "Unknown"),
                    "as":           j.get("asn", ""),
                    "asname":       j.get("asnOrganization", ""),
                    "lat":          j.get("latitude"),
                    "lon":          j.get("longitude"),
                    "source":       "freeipapi"
                }

                _geo_cache_set(ip, data)
                return data

            else:
                logger.warning(
                    f"[GEO] FreeIPAPI HTTP {r.status_code} ip={ip}"
                )

        except Exception as e:
            logger.warning(
                f"[GEO] FreeIPAPI error ip={ip}: {e}"
            )

    logger.warning(
        f"[GEO] no provider available or all providers failed ip={ip}"
    )

    return None
               
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CSV LOADER HELPER (uÅ¼ywany przez FAST TABLE)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def load_csv_into_cache(csv_path: Path):
    """Trzyma maksymalnie CSV_CACHE_LIMIT plikÃ³w CSV w RAM na worker."""
    cache_key = str(csv_path.absolute())

    try:
        mtime = csv_path.stat().st_mtime
    except FileNotFoundError:
        logger.warning(f"[CSV LOAD] File not found: {csv_path}")
        return

    with CSV_CACHE_LOCK:

        # Ten sam plik i ta sama wersja juÅ¼ siedzi w RAM.
        if (
            cache_key in CSV_CACHE
            and CSV_CACHE_MTIME.get(cache_key) == mtime
        ):
            logger.debug(
                f"[CSV CACHE HIT] {csv_path.name} already in RAM"
            )
            return

        # JeÅ›li ten sam plik istnieje, ale zostaÅ‚ zmieniony na dysku,
        # usuÅ„ starÄ… wersjÄ™ przed ponownym zaÅ‚adowaniem.
        if cache_key in CSV_CACHE:
            logger.info(
                f"[CSV CACHE STALE] removing old {csv_path.name}"
            )
            CSV_CACHE.pop(cache_key, None)
            CSV_CACHE_MTIME.pop(cache_key, None)

        # ZWOLNIJ RAM PRZED budowaniem nowego milionowego CSV.
        while len(CSV_CACHE) >= CSV_CACHE_LIMIT:
            old_key = next(iter(CSV_CACHE))

            logger.info(
                f"[CSV CACHE EVICT] removing {Path(old_key).name} from RAM"
            )

            CSV_CACHE.pop(old_key, None)
            CSV_CACHE_MTIME.pop(old_key, None)

        logger.info(
            f"[CSV PRELOAD] {csv_path.name} -> RAM "
            f"(size: {csv_path.stat().st_size} bytes)"
        )

        temp_sites = []
        start_time = time.time()
        row_count = 0

        with open(
            csv_path,
            newline="",
            encoding="utf-8",
            errors="ignore"
        ) as f:
            reader = csv.reader(f)

            for row in reader:
                row_count += 1

                if len(row) < 2:
                    continue

                try:
                    rank_val = int(row[0].strip())
                except ValueError:
                    continue

                temp_sites.append({
                    "rank": rank_val,
                    "domain": row[1].strip()
                })

        CSV_CACHE[cache_key] = temp_sites
        CSV_CACHE_MTIME[cache_key] = mtime

        elapsed = time.time() - start_time

        logger.info(
            f"[CSV PRELOAD DONE] {csv_path.name}: "
            f"{row_count} rows -> {len(temp_sites)} sites "
            f"in {elapsed:.2f}s"
        )
def detect_latest_snapshot():
    """Wykrywa najnowszy snapshot CSV (YYYYMM.csv)."""
    
    csv_dir = Path(app.static_folder) / "csv"

    candidates = sorted(
        [p.stem for p in csv_dir.glob("*.csv") if p.stem.isdigit()],
        reverse=True
    )

    if not candidates:
        raise RuntimeError("No CSV snapshots found")

    latest = candidates[0]

    logger.info(f"[SNAPSHOT] latest detected: {latest}")

    return latest, f"{latest}.csv"
    
    
def preload_fast_csv():
    """Åaduje tylko gÅ‚Ã³wny CSV do RAM."""
    csv_dir = Path(app.static_folder) / "csv"
    main_file = csv_dir / MAIN_CSV

    if not main_file.exists():
        logger.warning("[CSV PRELOAD] Main CSV not found")
        return

    logger.info(f"[CSV PRELOAD MAIN] {main_file.name}")
    load_csv_into_cache(main_file)
    logger.info("[CSV PRELOAD COMPLETE] Only main CSV loaded")



@app.route("/api/preload_csv")
def api_preload_csv():
    """RÄ™czne wywoÅ‚anie preload CSV (przydatne po deploy)."""

    remote_ip = request.remote_addr or ""

    if remote_ip not in ("127.0.0.1", "::1"):
        logger.warning(f"[CSV PRELOAD BLOCKED] ip={remote_ip}")
        return jsonify({"ok": False, "error": "forbidden"}), 403

    try:
        preload_fast_csv()
        return jsonify({"ok": True, "message": "CSV preloaded into RAM"})
    except Exception as e:
        logger.exception("[CSV PRELOAD ERROR]")
        return jsonify({"ok": False, "error": "internal error"}), 500
# Filtry Jinja i normalizacja snapshotÃ³w
@app.template_filter('extract_domain')
def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or parsed.netloc or "").lower()
    return host[4:] if host.startswith("www.") else host

def normalize_snapshot_arg(s: str | None) -> str | None:
    if not s or s == "current":
        return None
    s = s.strip()
    m = re.fullmatch(r"(\d{4})-?(\d{2})", s)
    if not m: return None
    y, mth = int(m.group(1)), int(m.group(2))
    if 2015 <= y <= 2099 and 1 <= mth <= 12:
        return f"{y:04d}{mth:02d}"
    return None

@app.template_filter('fmt_ym')
def fmt_ym(s: str | None) -> str:
    s = (s or "").strip()
    m = re.fullmatch(r'(\d{4})(\d{2})', s)
    if m: return f"{m.group(1)}-{m.group(2)}"    
    return s
    
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SEARCH QUERY HELPER
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def normalize_search_query(raw_q: str) -> str:
    """Normalizuje input szukajki (URL â†’ domain, trim, lower)."""
    if not raw_q:
        return ""
    q = raw_q.strip()
    if q.startswith(("http://", "https://")):
        try:
            from urllib.parse import urlparse
            q = (urlparse(q).hostname or "").replace("www.", "")
        except:
            pass
    return q.lower()    

def normalize_url(u: str, base_url: str | None = None) -> str:
    if not u: return ""
    u = u.strip()
    if u.startswith("//"): u = "https:" + u
    if not SCHEME_RX.match(u):
        if DOMAIN_RX.match(u): u = "https://" + u
        elif base_url: u = urljoin(base_url, u)
        else: return ""
    try:
        p = urlparse(u)
        if not (p.scheme and (p.netloc or p.hostname)): return ""
        host = (p.hostname or "").encode("idna").decode("ascii").lower()
        netloc = f"{host}:{p.port}" if p.port else host
        path = re.sub("/{2,}", "/", p.path or "/")
        if path != "/" and path.endswith("/"): path = path[:-1]
        
        qs = [(k, v) for (k, v) in parse_qsl(p.query, keep_blank_values=True)
              if k.lower() not in TRACKING_PARAMS]
        qs = sorted(qs)
        query = urlencode(qs, doseq=True)
        return urlunparse((p.scheme, netloc, path, "", query, ""))
    except Exception:
        return ""

def is_safe_public_url(url: str) -> bool:
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        host = parsed.hostname
        if not host:
            return False

        # bezpoÅ›redni adres IP
        try:
            ips = [ipaddress.ip_address(host)]
        except ValueError:
            # domena -> sprawdÅº WSZYSTKIE adresy z DNS
            infos = socket.getaddrinfo(
                host,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                0,
                socket.SOCK_STREAM
            )

            ips = list({
                ipaddress.ip_address(info[4][0])
                for info in infos
            })

        if not ips:
            return False

        for addr in ips:
            if (
                addr.is_private
                or addr.is_loopback
                or addr.is_link_local
                or addr.is_reserved
                or addr.is_multicast
                or addr.is_unspecified
            ):
                return False

        return True

    except Exception:
        return False
        
# Sesja HTTP (Requests)
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=retries)
session.mount('http://', adapter)
session.mount('https://', adapter)
session.headers.update({'User-Agent': 'Mozilla/5.0 (compatible; MyCrawler/1.3)', 'Accept-Encoding': 'identity'})

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FAST TABLE â€” ULTRA STABILITY CACHE + HTTP SESSION
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FAST_ROW_CACHE = {}          # domain -> {"ts": float, "data": {...}}
FAST_ROW_CACHE_TTL = 3600    # H1
FAST_ROW_CACHE_MAX = 5000

FAST_ROW_SEM = Semaphore(8)  # max rÃ³wnolegÅ‚ych FAST requestÃ³w backendowych

fast_http = requests.Session()
fast_http_adapter = HTTPAdapter(
    pool_connections=50,
    pool_maxsize=50,
    max_retries=Retry(total=0)
)
fast_http.mount("http://", fast_http_adapter)
fast_http.mount("https://", fast_http_adapter)
fast_http.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; FastTable/2.0)",
    "Accept-Encoding": "identity",
    "Connection": "keep-alive",
})

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SAFE OUTBOUND HTTP â€” requesty do domen kontrolowanych przez usera
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

outbound_http = requests.Session()

outbound_http_adapter = HTTPAdapter(
    pool_connections=50,
    pool_maxsize=50,
    max_retries=Retry(total=0)
)

outbound_http.mount("http://", outbound_http_adapter)
outbound_http.mount("https://", outbound_http_adapter)

outbound_http.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; SafeOutbound/1.0)",
    "Accept-Encoding": "identity",
    "Connection": "keep-alive",
})


def safe_outbound_request(
    url: str,
    *,
    method: str = "GET",
    timeout=(1.5, 3.0),
    verify: bool = True,
    stream: bool = True,
    max_redirects: int = 3,
):
    """
    Bezpieczny request HTTP/HTTPS do adresÃ³w kontrolowanych przez uÅ¼ytkownika.

    Zasady:
    - tylko http / https,
    - blokada prywatnych / lokalnych / specjalnych IP,
    - brak automatycznych redirectÃ³w Requests,
    - kaÅ¼dy redirect sprawdzany ponownie przez is_safe_public_url(),
    - maksymalna liczba redirectÃ³w,
    - brak retry.
    """

    current_url = (url or "").strip()

    if not current_url:
        raise ValueError("Empty URL")

    if len(current_url) > MAX_URL_LENGTH:
        raise ValueError("URL too long")

    method = (method or "GET").upper()

    if method not in ("GET", "HEAD"):
        raise ValueError("Unsupported HTTP method")

    for redirect_no in range(max_redirects + 1):

        if not is_safe_public_url(current_url):
            logger.warning(
                f"[OUTBOUND BLOCKED] unsafe URL: {current_url}"
            )
            raise ValueError("Unsafe outbound URL")

        response = outbound_http.request(
            method,
            current_url,
            timeout=timeout,
            verify=verify,
            stream=stream,
            allow_redirects=False,
        )

        # Brak redirectu â†’ zwracamy odpowiedÅº
        if response.status_code not in (301, 302, 303, 307, 308):
            return response

        # Redirect, ale wykorzystaliÅ›my juÅ¼ limit
        if redirect_no >= max_redirects:
            response.close()
            raise requests.TooManyRedirects(
                f"Too many redirects for {url}"
            )

        location = (response.headers.get("Location") or "").strip()

        if not location:
            response.close()
            raise requests.RequestException(
                "Redirect without Location header"
            )

        next_url = urljoin(current_url, location)

        response.close()

        if len(next_url) > MAX_URL_LENGTH:
            raise ValueError("Redirect URL too long")

        if not is_safe_public_url(next_url):
            logger.warning(
                f"[OUTBOUND REDIRECT BLOCKED] "
                f"{current_url} -> {next_url}"
            )
            raise ValueError("Unsafe redirect target")

        logger.info(
            f"[OUTBOUND REDIRECT] "
            f"{current_url} -> {next_url}"
        )

        current_url = next_url

    raise requests.TooManyRedirects(
        f"Too many redirects for {url}"
    )

def fast_cache_get(domain: str):
    item = FAST_ROW_CACHE.get(domain)
    if not item:
        return None
    if time.time() - item["ts"] > FAST_ROW_CACHE_TTL:
        FAST_ROW_CACHE.pop(domain, None)
        return None
    return item["data"]

def fast_cache_set(domain: str, data: dict):
    # prosty limit pamiÄ™ci
    if len(FAST_ROW_CACHE) >= FAST_ROW_CACHE_MAX:
        # usuÅ„ najstarszy wpis
        oldest_key = min(FAST_ROW_CACHE, key=lambda k: FAST_ROW_CACHE[k]["ts"])
        FAST_ROW_CACHE.pop(oldest_key, None)

    FAST_ROW_CACHE[domain] = {
        "ts": time.time(),
        "data": data
    }

def is_connection_refused(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "10061" in msg
        or "actively refused" in msg
        or "connection refused" in msg
    )


def _safe_get_html(url: str, *, timeout=None, verify=True, max_bytes=None):
    t = AN_TIMEOUT if timeout is None else float(timeout)
    m = AN_MAX_BYTES if max_bytes is None else int(max_bytes)

    try:
        connect = min(1.5, t)
        read = max(0.5, t - connect)

        r = safe_outbound_request(
            url,
            method="GET",
            timeout=(connect, read),
            verify=verify,
            stream=True,
            max_redirects=3,
        )

        try:
            status = r.status_code or 0
            buf = bytearray()
            got = 0

            for chunk in r.iter_content(chunk_size=16384):
                if not chunk:
                    continue

                n = len(chunk)

                if got + n > m:
                    remaining = max(m - got, 0)

                    if remaining:
                        buf.extend(chunk[:remaining])

                    break

                buf.extend(chunk)
                got += n

            enc = (r.encoding or "utf-8").lower()

            try:
                html = buf.decode(enc, errors="ignore")
            except Exception:
                html = buf.decode("utf-8", errors="ignore")

            return status, html

        finally:
            r.close()

    except Exception as e:
        if is_connection_refused(e):
            logger.info(
                f"[GET_HTML] connection refused -> skip: {url}"
            )
            return -1, ""

        logger.warning(
            "[GET_HTML] %s -> %s",
            url,
            e
        )

        return 0, ""
        
def get_page_title(domain: str) -> str:
    """
    Bezpieczne pobranie HTML + ekstrakcja <title>.
    Sam fetch_meta.py nie wykonuje juÅ¼ Å¼adnych requestÃ³w HTTP.
    """

    domain = (domain or "").strip().lower()

    if (
        not domain
        or len(domain) > MAX_DOMAIN_LENGTH
        or not DOMAIN_RX.fullmatch(domain)
    ):
        return ""

    url = f"https://{domain}"

    try:
        status, html = _safe_get_html(
            url,
            timeout=4.0,
            verify=verify_ssl(domain),
            max_bytes=512 * 1024,
        )

        if status <= 0 or not html:
            return ""

        return extract_page_title(html) or ""

    except Exception as e:
        logger.warning(
            "[PAGE TITLE] error for %s: %s",
            domain,
            e
        )
        return ""        
        
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 4. GÅÃ“WNA LOGIKA (TOP SITES: DB + CSV FALLBACK)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def query_top_sites_db(q: str | None, page: int, per_page: int, table: str) -> Tuple[int, List[Dict]]:
    """Logika pobierania z MySQL."""
    where_clause = "1"
    params = []
    if q:
        q = q.strip().lower()
        tld_match = None
        if q.startswith('.'):
            cand = q[1:]
            if re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', cand):
                tld_match = cand
        elif re.fullmatch(r'[a-z]{2}', q):
            tld_match = q

        if tld_match:
            where_clause = "LOWER(TRIM(domain)) REGEXP %s"
            params = [rf'\.{re.escape(tld_match)}$']
        else:
            where_clause = "LOWER(TRIM(domain)) LIKE %s"
            params = [f'%{q}%']

    conn = get_db_connection()
    with conn.cursor(dictionary=True) as cur:
        # ðŸš€ OPTYMALIZACJA: Limit dla COUNT przy duÅ¼ych zbiorach
        if not q:
            # Dla pustego zapytania uÅ¼yj oszacowania zamiast peÅ‚nego COUNT
            cur.execute(f"SELECT COUNT(*) AS cnt FROM {table} WHERE {where_clause} LIMIT 100000", params)
        else:
            cur.execute(f"SELECT COUNT(*) AS cnt FROM {table} WHERE {where_clause}", params)
        total = (cur.fetchone() or {}).get("cnt", 0)
        offset = max(page - 1, 0) * per_page
        cur.execute(
            f"SELECT `rank`, domain, http_status FROM {table} WHERE {where_clause} ORDER BY `rank` LIMIT %s OFFSET %s",
            params + [per_page, offset]
        )
        rows = cur.fetchall()
    conn.close()
    return total, rows
@app.route("/")
def root_redirect():
    return redirect(url_for("top_sites_page"))

@app.route("/top_sites/")
@app.route("/top_sites/<snapshot>")
def top_sites_page(snapshot: str | None = None):
    if snapshot is not None and snapshot != "current" and normalize_snapshot_arg(snapshot) is None:
        abort(404)
    # ðŸ”¥ FAST LANE â€” CSV MA PIERWSZEÅƒSTWO
    if not CSV_FAST_SEM_NORMAL.acquire(blocking=False):
        return render_template(
            "top_sites.html",
            sites=[],
            total_rows=0,
            page=1,
            per_page=10,
            total_pages=1,
            error="Server busy, retry"
        ), 503
    
    try:
        snap_norm = normalize_snapshot_arg(snapshot)
        
        # 1. CACHED SNAPSHOT DISCOVERY (raz na 60 sekund)
        now = time.time()
        if now - SNAPSHOT_CACHE["ts"] > SNAPSHOT_TTL:

            csv_dir = Path(app.static_folder) / "csv"

            available = sorted(
                [p.stem for p in csv_dir.glob("*.csv") if p.stem.isdigit()],
                reverse=True
            )

            SNAPSHOT_CACHE["snaps"] = available
            SNAPSHOT_CACHE["latest"] = available[0] if available else None

            # ðŸ”’ Obecnie zawsze CSV-only
            SNAPSHOT_CACHE["use_db"] = False

            SNAPSHOT_CACHE["ts"] = now

        # uÅ¼ycie z cache
        snaps = SNAPSHOT_CACHE["snaps"]
        use_db = SNAPSHOT_CACHE["use_db"]
        latest = SNAPSHOT_CACHE["latest"]

        effective_snapshot = MAIN_SNAPSHOT
        snaps = [MAIN_SNAPSHOT]
        latest = MAIN_SNAPSHOT
        
        # Parametry requestu
        raw_q = request.args.get("q", "", type=str)
        q = normalize_search_query(raw_q)  # UÅ¼yj nowej funkcji!
        
        # URL -> DOMAIN
        if raw_q.startswith(("http://", "https://")):
            try:
                from urllib.parse import urlparse
                raw_q = (urlparse(raw_q).hostname or "").replace("www.", "")
            except:
                pass

        page = max(1, request.args.get("page", 1, type=int) or 1)
        per_page = max(
            1,
            min(request.args.get("per_page", 10, type=int) or 10, 400)
        )
        
        sites, total = [], 0
        loaded_from_db = False

        # 2. PrÃ³ba pobrania danych (DB)
        if use_db and effective_snapshot:
            table = f"top_sites_{effective_snapshot}"
            try:
                total, sites = query_top_sites_db(raw_q, page, per_page, table)
                loaded_from_db = True
            except Exception as e:
                logger.warning(f"DB Query failed (fallback to CSV): {e}")
                loaded_from_db = False

        # 3. CSV + RAM CACHE + OPTIMIZATIONS
        if not loaded_from_db:
            csv_dir = Path(app.static_folder) / "csv"
            csv_path = csv_dir / f"{effective_snapshot}.csv" if effective_snapshot else None
            
            if not csv_path or not csv_path.exists():
                return render_template("top_sites.html", sites=[], total_rows=0, page=1, per_page=per_page, total_pages=1, q=raw_q, snapshots=snaps, snapshot=(effective_snapshot or "current"), button_stats=[], error="Brak danych.")

            try:
                load_csv_into_cache(csv_path)
                cache_key = str(csv_path.absolute())
                all_sites_cached = CSV_CACHE.get(cache_key, [])
                
                

                # KROK B: FILTR + SLICE (Single Pass) z CACHE
                start_idx = (page - 1) * per_page
                end_idx = page * per_page
                
                if not raw_q:
                    total = len(all_sites_cached)
                    sites = all_sites_cached[start_idx:end_idx]
                else:
                    # ðŸš€ CACHE WYNIKÃ“W FILTRA
                    q_low = raw_q.lower()
                    all_matches = [s for s in all_sites_cached if q_low in s["domain"].lower()]
                    total = len(all_matches)
                    sites = all_matches[start_idx:end_idx]
                
                # ðŸš€ OBSÅUGA PARTIAL RENDER (TU, nie w except!)
                if request.headers.get("X-Partial") == "table":
                    return render_template("top_sites_table.html", sites=sites)
                    
            except Exception as e:
                logger.exception("[TOP SITES CSV ERROR]")
                if request.headers.get("X-Partial") == "table":
                    return render_template("top_sites_table.html", sites=[])

                return render_template(
                    "top_sites.html",
                    sites=[],
                    total_rows=0,
                    page=1,
                    error="Internal server error"
                )
        
        # Standardowy render (pierwsze wejÅ›cie)
        button_stats = []
        if use_db:
            # (Twoja logika button_stats - bez zmian)
            pass 

        # ðŸš€ OPTYMALIZACJA: Obliczenie total_pages bez floatÃ³w
        total_pages = max(1, (total + per_page - 1) // per_page) if total else 1

        return render_template(
            "top_sites.html",
            sites=sites, 
            total_rows=total, 
            page=page, 
            per_page=per_page,
            total_pages=total_pages,
            q=raw_q, 
            snapshots=snaps, 
            snapshot=(effective_snapshot or "current"),
            button_stats=button_stats
        )
    
    finally:
        CSV_FAST_SEM_NORMAL.release()  

def fetch_fast_row_data(domain: str) -> dict:
    cached = fast_cache_get(domain)
    if cached:
        return cached

    http_status = 0
    final_url = ""
    status_txt = "FAIL"
    title = ""

    # 1) STATUS / FINAL URL
    try:
        r = safe_outbound_request(
            f"https://{domain}",
            method="GET",
            timeout=(1.5, 2.5),
            verify=verify_ssl(domain),
            stream=True,
            max_redirects=3,
        )
        http_status = r.status_code
        final_url = r.url or ""
        status_txt = "OK" if r.ok else "ERR"
        r.close()
    except Exception as e:
        if is_connection_refused(e):
            http_status = -1
            final_url = ""
            status_txt = "REFUSED"
        else:
            logger.warning(f"[FAST_ROW] status error for {domain}: {e}")
            http_status = 0
            final_url = ""
            status_txt = "FAIL"

    # 2) TITLE
    try:
        title = get_page_title(domain) or ""
    except Exception as e:
        logger.warning(f"[FAST_ROW] title error for {domain}: {e}")
        title = ""

    result = {
        "check": {
            "http_status": http_status,
            "final_url": final_url,
            "status_txt": status_txt
        },
        "meta": {
            "title": title,
            "html_lang": "",
            "meta_description_length": 0
        }
    }

    fast_cache_set(domain, result)
    return result        
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 5. ENDPOINTY API (Analiza, Tekst, Meta)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/analyze")
def analyze():
    # ðŸš§ API LOW PRIORITY
    if not API_SEM.acquire(blocking=False):
        return jsonify({"error": "api busy"}), 429
    
    try:
        url = request.args.get("url", "") or ""

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€ 1) LIMIT DÅUGOÅšCI â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if len(url) > MAX_URL_LENGTH:
            return jsonify({"error": "URL za dÅ‚ugi"}), 413

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€ 2) NORMALIZACJA â”€â”€â”€â”€â”€â”€â”€â”€â”€
        normalized_url = normalize_url(url)
        if not normalized_url:
            return jsonify({"error": "Invalid URL provided"}), 400

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€ 3) PARSING DOMENY â”€â”€â”€â”€â”€â”€â”€â”€â”€
        parsed = urlparse(normalized_url)
        domain = (parsed.hostname or parsed.netloc or "").lower()

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€ 4) DNS + BLOKADA SSRF â”€â”€â”€â”€â”€â”€â”€â”€â”€
        ip_address = ""
        try:
            infos = socket.getaddrinfo(domain, 443, 0, socket.SOCK_STREAM)  # 0 = IPv4/IPv6
            v4, v6 = [], []
            for af, *_, sockaddr in infos:
                ip = sockaddr[0]
                if af == socket.AF_INET:
                    v4.append(ip)
                elif af == socket.AF_INET6:
                    v6.append(ip)

            if AN_IPV4 and v4:
                ip_address = v4[0]
            else:
                ip_address = (v4[0] if v4 else (v6[0] if v6 else ""))

            if ip_address:
                addr = ipaddress.ip_address(ip_address)
                if addr.is_private or addr.is_loopback:
                    logger.warning(f"SSRF block: private IP {ip_address} for {domain}")
                    return jsonify({"error": "Access to private network not allowed"}), 403
        except Exception as ge:
            logger.warning(f"DNS lookup failed for domain {domain}: {ge}")
            ip_address = ""

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€ 5) POBRANIE HTML â”€â”€â”€â”€â”€â”€â”€â”€â”€
        http_status, html = _safe_get_html(
            normalized_url,
            verify=verify_ssl(domain) if 'verify_ssl' in globals() else True
        )

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€ 6) PARSOWANIE LINKÃ“W (BS4 + regex fallback + REKLAMA FILTER) â”€â”€â”€â”€â”€â”€â”€â”€â”€
        internal, external = set(), set()

        if html:
            try:
                soup = BeautifulSoup(html, "html.parser")

                # ðŸ§¹ WYCINANIE SYFU: reklamy, tracking, share-buttons, player controls
                for bad_sel in [
                    "script", "style", "noscript",
                    "div.ad", "div.ads", "div.reklama", "div.promo", "div.overlay",
                    "div.player", "figure.video", "figure.media",
                    "div#player", "aside", "header .ad",
                    "div.share", "ul.share", "div.social", "div.fb-share"
                ]:
                    for t in soup.select(bad_sel):
                        t.decompose()

                anchors = [a.get("href", "") for a in soup.find_all("a", href=True)]

            except Exception as pe:
                logger.warning("[BS4 EXTRACT LINK ERROR] %s", pe)
                anchors = []

            if not anchors:
                anchors = re.findall(
                    r'href=["\']([^"\']+)["\']',
                    html,
                    flags=re.IGNORECASE
                )

            base_host = (urlparse(normalized_url).hostname or "").lower()
            base_root = base_host[4:] if base_host.startswith("www.") else base_host

            def is_internal(h: str) -> bool:
                host = (urlparse(h).hostname or "").lower()
                if host.startswith("www."):
                    host = host[4:]
                if not host:
                    return True  # relative URL
                return host == base_root or (base_root and host.endswith("." + base_root))

            # ðŸ§¹ FILTROWANIE SMIECI Z LINKÃ“W
            def clean_link(h: str) -> str:
                if not h or h.startswith("#"):
                    return ""
                if h.startswith("javascript:"):
                    return ""
                if h.startswith("mailto:") or h.startswith("tel:"):
                    return ""
                if "facebook.com/sharer" in h.lower():
                    return ""
                if "twitter.com/share" in h.lower():
                    return ""
                if "utm_" in h.lower():
                    return ""
                if "adservice" in h.lower():
                    return ""
                if "doubleclick" in h.lower():
                    return ""
                if "tracking" in h.lower():
                    return ""
                if h in ("/", ""):
                    return ""

                # normalizacja adresu
                try:
                    fixed = normalize_url(h, normalized_url)
                except:
                    return ""

                if not fixed:
                    return ""

                # usuÅ„ koÅ„cowe slash'e
                if fixed.endswith("/"):
                    fixed = fixed[:-1]

                return fixed

            # PRZETWARZANIE KAÅ»DEGO LINKU
            for raw in anchors:
                cleaned = clean_link(raw)
                if not cleaned:
                    continue
                (internal if is_internal(cleaned) else external).add(cleaned)

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€ 7) GEOLOKALIZACJA (opcjonalna, krÃ³tki timeout) â”€â”€â”€â”€â”€â”€â”€â”€â”€
        location = {"country": "Unknown", "region": "Unknown", "city": "Unknown", "isp": "Unknown"}
        if AN_GEO and ip_address:
            geo = geo_lookup(ip_address)
            if geo:
                location.update({
                    "country": geo.get("country", "Unknown"),
                    "region":  geo.get("region", "Unknown"),
                    "city":    geo.get("city", "Unknown"),
                    "isp":     geo.get("isp", "Unknown"),
                })

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€ 8) ZWRÃ“Ä† JSON â”€â”€â”€â”€â”€â”€â”€â”€â”€
        return jsonify({
            "ip": ip_address,
            "http_status": http_status,
            "location": location,
            "internal_links":       list(internal),
            "external_links":       list(external),
            "internal_links_count": len(internal),
            "external_links_count": len(external),
        })
    
    finally:
        API_SEM.release()
        
        
@app.route("/api/check_page", methods=["POST"])
def api_check_page():
    if not CHECK_PAGE_SEM.acquire(blocking=False):
        return jsonify({
            "error": "Server busy, too many concurrent requests"
        }), 429

    try:
        data = request.get_json(silent=True) or {}
        domains = data.get("domains", [])

        if not isinstance(domains, list):
            return jsonify({"error": "Invalid domains"}), 400

        if len(domains) > MAX_BATCH_DOMAINS:
            return jsonify({"error": "Too many domains"}), 413

        clean = [
            d.strip().lower()
            for d in domains
            if isinstance(d, str)
            and len(d) <= MAX_DOMAIN_LENGTH
            and DOMAIN_RX.fullmatch(d.strip())
        ]

        results = {}
        lock = threading.Lock()

        def check_single(dom):
            s = 0

            try:
                r = safe_outbound_request(
                    f"https://{dom}",
                    method="HEAD",
                    timeout=(1.5, DEFAULT_TIMEOUT),
                    verify=verify_ssl(dom),
                    stream=True,
                    max_redirects=3,
                )

                try:
                    s = r.status_code
                finally:
                    r.close()

                # NiektÃ³re serwery blokujÄ… HEAD.
                if s in {403, 405}:
                    r = safe_outbound_request(
                        f"https://{dom}",
                        method="GET",
                        timeout=(1.5, DEFAULT_TIMEOUT),
                        verify=verify_ssl(dom),
                        stream=True,
                        max_redirects=3,
                    )

                    try:
                        s = r.status_code
                    finally:
                        r.close()

            except Exception as e:
                logger.warning(
                    "[CHECK_PAGE] error for %s: %s",
                    dom,
                    e
                )
                s = 0

            with lock:
                results[dom] = {
                    "http_status": s
                }

        with ThreadPoolExecutor(max_workers=5) as exc:
            list(exc.map(check_single, clean))

        return jsonify({
            "results": results
        })

    finally:
        CHECK_PAGE_SEM.release()        
@app.route("/api/extract_text", methods=["GET", "POST"])
def api_extract_text():
    if not EXTRACT_TEXT_SEM.acquire(blocking=False):
        return jsonify({
            "error": "Server busy, too many concurrent requests"
        }), 429

    try:
        html = ""

        if request.method == "GET":
            url = request.args.get("url", "").strip()

            if len(url) > MAX_URL_LENGTH:
                return jsonify({"error": "URL too long"}), 413

            if not is_safe_public_url(url):
                logger.warning(f"[EXTRACT TEXT BLOCKED URL] {url}")
                return jsonify({"error": "URL not allowed"}), 403

            _, html = _safe_get_html(url, timeout=10)

        else:
            if request.content_length and request.content_length > MAX_EXTRACT_HTML_BYTES:
                return jsonify({"error": "Content too large"}), 413

            data = request.get_json(silent=True) or {}
            html = data.get("html", "")

            if not isinstance(html, str):
                return jsonify({"error": "Invalid content"}), 400

            if len(html.encode("utf-8")) > MAX_EXTRACT_HTML_BYTES:
                return jsonify({"error": "Content too large"}), 413

        if not html:
            return jsonify({"error": "No content"}), 400

        try:
            if Document:
                doc = Document(html)
                html = doc.summary()

            soup = BeautifulSoup(html, "html.parser")

            for t in soup(["script", "style", "nav", "footer", "iframe"]):
                t.decompose()

            text = soup.get_text(separator="\n", strip=True)

            lines = [
                x.strip()
                for x in text.splitlines()
                if x.strip()
            ]

            return jsonify({
                "text": " ".join(lines)
            })

        except Exception:
            logger.exception("[EXTRACT TEXT ERROR]")
            return jsonify({
                "error": "Extraction failed"
            }), 500

    finally:
        EXTRACT_TEXT_SEM.release()
@app.route("/api/fetch_meta", methods=["POST"])
def api_fetch_meta():
    if not FETCH_META_SEM.acquire(blocking=False):
        return jsonify({
            "error": "Server busy, too many concurrent requests"
        }), 429

    try:
        data = request.get_json(silent=True) or {}

        domains = data.get("domains", [])

        if not isinstance(domains, list):
            return jsonify({"error": "Invalid domains"}), 400

        clean = [
            d.strip().lower()
            for d in domains[:MAX_BATCH_DOMAINS]
            if isinstance(d, str)
            and len(d) <= MAX_DOMAIN_LENGTH
            and DOMAIN_RX.fullmatch(d.strip())
        ]

        results = {}

        def worker(d):
            return d, get_page_title(d) or ""

        with ThreadPoolExecutor(max_workers=3) as exc:
            for d, t in exc.map(worker, clean):
                results[d] = t

        return jsonify(results)

    finally:
        FETCH_META_SEM.release()
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 6. STATYSTYKI WIZYT & UPDATE (FIXED)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# GLOBE VISITS â€” JSON, BEZ BAZY DANYCH
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

VISITS_DATA_DIR = Path(here) / "data"
VISITS_FILE = VISITS_DATA_DIR / "visits_countries.json"
VISITS_LOCK_FILE = VISITS_DATA_DIR / "visits_countries.lock"

# zabezpieczenie w obrÄ™bie jednego procesu Flask
VISITS_THREAD_LOCK = threading.Lock()

# folder utworzy siÄ™ sam
VISITS_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_visits_file():
    """
    Czyta statystyki globusa.

    Nowy format:
    {
        "countries": {...},
        "markers": [[lat, lng], ...] lub [[lat, lng, countryCode], ...]
    }

    ObsÅ‚uguje teÅ¼ automatycznie stary format pliku.
    """

    empty = {
        "countries": {},
        "markers": []
    }

    if not VISITS_FILE.exists():
        return empty

    try:
        with open(VISITS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return empty

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # NOWY FORMAT
        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if "countries" in data or "markers" in data:

            countries = data.get("countries", {})
            markers = data.get("markers", [])

            if not isinstance(countries, dict):
                countries = {}

            if not isinstance(markers, list):
                markers = []

            return {
                "countries": countries,
                "markers": markers
            }

        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # STARY FORMAT â†’ migracja w pamiÄ™ci
        # np. {"GB": {"count": 3, ...}}
        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        countries = {}
        markers = []

        for code, item in data.items():

            if not isinstance(item, dict):
                continue

            code = str(code).strip().upper()

            if len(code) != 2:
                continue

            try:
                count = int(item.get("count", 0))
            except Exception:
                count = 0

            countries[code] = {
                "count": count,
                "country": item.get("country") or code
            }

            # Ze starego formatu znamy tylko ostatniÄ… pozycjÄ™ kraju,
            # wiÄ™c zachowujemy jÄ… jako jeden marker.
            lat = item.get("lat")
            lng = item.get("lng")

            try:
                if lat is not None and lng is not None:
                    markers.append([
                        round(float(lat), 4),
                        round(float(lng), 4),
                        code
                    ])
            except Exception:
                pass

        return {
            "countries": countries,
            "markers": markers
        }

    except Exception as e:
        logger.warning(f"[VISITS] read error: {e}")
        return empty

def _acquire_visits_file_lock(timeout=1.5):
    """
    Prosta blokada miÄ™dzy procesami.
    DziaÅ‚a rÃ³wnieÅ¼ gdy Gunicorn ma kilka workerÃ³w.
    """
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            fd = os.open(
                str(VISITS_LOCK_FILE),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY
            )
            os.close(fd)
            return True

        except FileExistsError:
            # usuÅ„ bardzo stary lock po ewentualnym crashu procesu
            try:
                if time.time() - VISITS_LOCK_FILE.stat().st_mtime > 10:
                    VISITS_LOCK_FILE.unlink(missing_ok=True)
                    continue
            except Exception:
                pass

            time.sleep(0.02)

    return False


def _release_visits_file_lock():
    try:
        VISITS_LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def record_country_visit(country_code, country, lat, lon):
    """
    1. ZwiÄ™ksza licznik kraju o 1.
    2. Dla globusa zapisuje anonimowe [lat, lng, countryCode].

    Nie zapisuje:
    - IP
    - miasta
    - regionu
    - ISP
    - ASN
    - czasu wizyty
    """

    code = (country_code or "").strip().upper()

    if len(code) != 2 or code == "LO":
        return False

    with VISITS_THREAD_LOCK:

        locked = _acquire_visits_file_lock()

        if not locked:
            logger.warning("[VISITS] could not acquire file lock")
            return False

        try:
            stats = _read_visits_file()

            countries = stats.setdefault("countries", {})
            markers = stats.setdefault("markers", [])

            # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            # FLAGA / LICZNIK KRAJU
            # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            item = countries.get(code, {})

            try:
                old_count = int(item.get("count", 0))
            except Exception:
                old_count = 0

            item["count"] = old_count + 1
            item["country"] = country or code

            countries[code] = item

            # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            # MARKER â€” LAT + LNG + KOD KRAJU
            # Bez IP / miasta / regionu / czasu wizyty.
            # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            try:
                if lat is not None and lon is not None:

                    marker_lat = round(float(lat), 4)
                    marker_lng = round(float(lon), 4)

                    if (
                        -90 <= marker_lat <= 90
                        and -180 <= marker_lng <= 180
                    ):
                        markers.append([
                            marker_lat,
                            marker_lng,
                            code
                        ])

            except Exception:
                pass

            # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            # ATOMOWY ZAPIS
            # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            tmp_file = VISITS_FILE.with_name(
                f".{VISITS_FILE.name}.{os.getpid()}.tmp"
            )

            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(
                    stats,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True
                )

            os.replace(tmp_file, VISITS_FILE)

            logger.info(
                f"[VISITS] {code} -> {item['count']} "
                f"| markers={len(markers)}"
            )

            return True

        except Exception as e:
            logger.warning(f"[VISITS] save error: {e}")
            return False

        finally:
            _release_visits_file_lock()
def _parse_since(arg: str | None) -> datetime:
    now = datetime.utcnow()
    s = (arg or '').strip().lower()
    try:
        if s.endswith('d'): return now - timedelta(days=int(s[:-1]))
        if s.endswith('h'): return now - timedelta(hours=int(s[:-1]))
        return datetime.fromisoformat(s)
    except: return now - timedelta(days=30)

@app.route("/api/track_visit", methods=["GET", "POST"])
def api_track_visit():
    try:
        ip = (
            request.headers.get("X-Real-IP", "").strip()
            or request.remote_addr
            or ""
        )

        try:
            ip = str(ipaddress.ip_address(ip))
        except ValueError:
            logger.warning(f"[TRACK VISIT] invalid client IP: {ip!r}")
            return jsonify({"status": "fail", "message": "invalid ip"}), 400
        # --- LOCAL / FALLBACK ---
        if ip in ("127.0.0.1", "::1", ""):
            return jsonify({
                "status": "success",
                "query": ip or "127.0.0.1",
                "country": "Localhost",
                "countryCode": "LO",
                "regionName": "Local",
                "city": "Local",
                "lat": None,
                "lon": None,
                "timezone": "Local",
                "isp": "Localhost",
                "as": "",
                "asname": "",
                "source": "local"
            })

        # --- GEO LOOKUP (cache / fallback) ---
        geo = geo_lookup(ip)
        if not geo:
            return jsonify({"status": "fail", "message": "no geo"}), 200

        # --- POLA GEO ---
        country_code = geo.get("country_code")
        timezone = geo.get("timezone")
        asn = geo.get("as")
        asname = geo.get("asname")

        # --- ZAPIS WIZYTY DO STATYSTYK GLOBUSA ---
        record_country_visit(
            country_code=country_code,
            country=geo.get("country"),
            lat=geo.get("lat"),
            lon=geo.get("lon")
        )

        return jsonify({
            "status": "success",
            "query": ip,
            "country": geo.get("country"),
            "countryCode": country_code or "",
            "regionName": geo.get("region"),
            "city": geo.get("city"),
            "lat": geo.get("lat"),
            "lon": geo.get("lon"),
            "timezone": timezone or "",
            "isp": geo.get("isp"),
            "as": asn or "",
            "asname": asname or "",
            "source": geo.get("source", "")
        })

    except Exception as e:
        logger.exception("[TRACK VISIT ERROR]")
        return jsonify({
            "status": "fail",
            "error": "internal error"
        }), 200


@app.get("/api/visits_geo")
def api_visits_geo():
    """
    Zwraca osobno:

    countries = liczniki flag
    markers   = anonimowe wspÃ³Å‚rzÄ™dne punktÃ³w
    """

    try:
        limit = min(
            max(int(request.args.get("limit", 60)), 1),
            250
        )
    except Exception:
        limit = 60

    stats = _read_visits_file()

    countries_data = stats.get("countries", {})
    markers_data = stats.get("markers", [])

    countries = []

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # FLAGI
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    for country_code, item in countries_data.items():

        if not isinstance(item, dict):
            continue

        try:
            count = int(item.get("count", 0))
        except Exception:
            count = 0

        if count <= 0:
            continue

        countries.append({
            "countryCode": country_code,
            "country": item.get("country") or country_code,
            "count": count
        })

    countries.sort(
        key=lambda x: x["count"],
        reverse=True
    )

    countries = countries[:limit]

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # MARKERY
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    markers = []

    for marker in markers_data:

        if not isinstance(marker, (list, tuple)):
            continue

        # KompatybilnoÅ›Ä‡:
        # stary marker: [lat, lng]
        # nowy marker:  [lat, lng, countryCode]
        if len(marker) not in (2, 3):
            continue

        try:
            lat = float(marker[0])
            lng = float(marker[1])
        except Exception:
            continue

        if not (-90 <= lat <= 90):
            continue

        if not (-180 <= lng <= 180):
            continue

        country_code = ""

        if len(marker) >= 3:
            country_code = str(marker[2] or "").strip().upper()

            if len(country_code) != 2:
                country_code = ""

        marker_out = {
            "lat": lat,
            "lng": lng
        }

        if country_code:
            marker_out["countryCode"] = country_code

        markers.append(marker_out)

    return jsonify({
        "countries": countries,
        "markers": markers
    })
# âœ… NOWOÅšÄ†: Funkcja pomocnicza do czytania CSV ze statystykami
def load_prefix_stats(kind="cc"):
    csv_dir = Path(app.static_folder) / "csv"
    fname = "prefix_stats_cc.csv" if kind == "cc" else "prefix_stats_global.csv"
    path = csv_dir / fname

    if not path.exists():
        return []

    out = []
    try:
        with open(path, newline="", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    out.append({
                        "prefix": row.get("prefix"),
                        "count": int(row.get("count", 0))
                    })
                except:
                    pass
    except Exception:
        pass
    return out

# âœ… NOWOÅšÄ†: Endpoint zwracajÄ…cy dane z CSV (naprawia "wszystko 0")
# === Prefix stats (TLD) â€” kompatybilne z v13 (COUNTRY PREFIXES) ===

def _prefix_dirs():
    # gÅ‚Ã³wny katalog + fallback (jak w v13)
    base1 = os.path.join(app.static_folder, "csv")
    base2 = os.path.join(base1, "top_sites.csv")
    return [base1, base2]

def _find_file(relname: str) -> str | None:
    for base in _prefix_dirs():
        p = os.path.join(base, relname)
        if os.path.isfile(p):
            return p
    return None

@app.get("/api/prefix_stats")
def api_prefix_stats():
    """
    Kompatybilne z v13:
    GET /api/prefix_stats?snapshot=YYYYMM
    Czyta {YYYYMM}p.csv (tld,count). JeÅ›li brak, liczy z {YYYYMM}.csv.
    Zwraca dict: { "pl": 124, "com": 9999, ... }
    """
    snap = (request.args.get("snapshot", "") or "").strip()
    snap = normalize_snapshot_arg(snap) or snap
    if not snap or not re.fullmatch(r"\d{6}", snap):
        abort(400, "Bad snapshot")

    # 1) gotowy plik YYYYMMp.csv
    p_csv = _find_file(f"{snap}p.csv")
    if p_csv:
        data = {}
        with open(p_csv, "r", encoding="utf-8", errors="ignore") as f:
            for row in csv.DictReader(f):
                t = (row.get("tld") or "").strip().lower()
                try:
                    c = int((row.get("count") or "0").strip() or 0)
                except:
                    c = 0
                if t:
                    data[t] = c
        return jsonify(data)

    # 2) fallback: policz z YYYYMM.csv
    src_csv = _find_file(f"{snap}.csv")
    if not src_csv:
        abort(404, f"No stats for {snap}")

    from collections import Counter
    counts = Counter()
    with open(src_csv, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.rstrip("\n").split(",", 1)
            if len(parts) != 2:
                continue
            _, domain = parts
            d = (domain or "").strip().lower()
            if d.startswith("www."):
                d = d[4:]
            if "." in d:
                tld = d.split(".")[-1]
                counts[tld] += 1

    return jsonify(dict(counts))

   

# âœ… NOWOÅšÄ†: Endpoint do aktualizacji statusu HTTP (naprawia brak update'Ã³w)
@app.post("/api/update_status")
def api_update_status():
    remote_ip = request.remote_addr or ""

    if remote_ip not in ("127.0.0.1", "::1"):
        logger.warning(f"[UPDATE STATUS BLOCKED] ip={remote_ip}")
        return jsonify({"ok": False, "error": "forbidden"}), 403

    data = request.get_json() or {}
    domain = data.get("domain", "").strip().lower()
    snapshot = data.get("snapshot")

    # Walidacja
    if not DOMAIN_RX.fullmatch(domain) or not snapshot:
        return jsonify(ok=False), 400
    
    # Prosty security check na nazwÄ™ tabeli
    if not re.fullmatch(r"\d{6}", str(snapshot)):
         return jsonify(ok=False, error="Invalid snapshot"), 400

    status = 0
    final_url = None
    
    try:
        # ðŸ”¥ KLUCZOWA ZMIANA: UÅ¼ywamy GET zamiast HEAD i allow_redirects=True
        r = safe_outbound_request(
            f"https://{domain}",
            method="GET",
            timeout=(1.5, 3.0),
            verify=verify_ssl(domain),
            stream=True,
            max_redirects=3,
        )

        try:
            status = r.status_code
            final_url = r.url or None
        finally:
            r.close()
    except Exception as req_err:
        logger.warning(f"Status check failed for {domain}: {req_err}")
        status = 0

    saved = False
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # ðŸ”¥ Aktualizujemy status KOÅƒCOWY (200 zamiast 301)
            cur.execute(
                f"""
                UPDATE top_sites_{snapshot}
                SET http_status = %s
                WHERE
                    domain = %s
                    OR domain = CONCAT('www.', %s)
                    OR CONCAT('www.', domain) = %s
                """,
                (status, domain, domain, domain)
            )
            rows = cur.rowcount
            logger.info(f"[STATUS UPDATE] {domain} â†’ {status} | rows={rows}")

        conn.commit()
        conn.close()
        saved = True
        logger.info(f"Updated status for {domain}: {status}")
    except Exception as e:
        # Tryb CSV (read-only) lub bÅ‚Ä…d DB
        logger.warning(f"Status update failed (local/csv mode?): {e}")
        saved = False

    return jsonify(ok=True, status=status, saved=saved, final_url=final_url)

@app.route("/stats")
def stats_page():
    return render_template("stats_globe.html")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 7. WHISPER STT & TTS (UNIFIED) USUNIÄ˜TY
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 8. UTILS (PLIKI, PROXY, LOGI)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@app.route("/download-quicklinks")
def download_quicklinks():
    return send_from_directory(current_app.template_folder, "quicklinks.html", as_attachment=True)

@app.route("/quicklinks_page")
def quicklinks_page():
    return render_template("quicklinks_page.html")


@app.route("/slideshow.html")
def slideshow_page():
    return render_template('slideshow.html')

@app.get("/proxy/flag")
def proxy_flag():
    u = (request.args.get("u") or "").strip()

    if not u or len(u) > MAX_URL_LENGTH:
        abort(400)

    try:
        parsed = urlparse(u)

        if parsed.scheme not in ("http", "https"):
            abort(400)

        host = (parsed.hostname or "").lower().rstrip(".")

        if host != "flagcounter.com" and not host.endswith(".flagcounter.com"):
            logger.warning(f"[FLAG PROXY BLOCKED HOST] {host}")
            abort(403)

        if not is_safe_public_url(u):
            logger.warning(f"[FLAG PROXY BLOCKED URL] {u}")
            abort(403)

        r = safe_outbound_request(
            u,
            method="GET",
            timeout=(1.5, 3.0),
            verify=True,
            stream=True,
            max_redirects=0,
        )
        
        # FlagCounter normalnie powinien zwrÃ³ciÄ‡ obraz.
        content_type = (r.headers.get("Content-Type") or "").lower()

        if not content_type.startswith("image/"):
            r.close()
            abort(502)

        # Nie pozwalamy proxy pobieraÄ‡ gigantycznych odpowiedzi.
        max_bytes = 2 * 1024 * 1024
        content = bytearray()

        for chunk in r.iter_content(chunk_size=16384):
            if not chunk:
                continue

            if len(content) + len(chunk) > max_bytes:
                r.close()
                abort(413)

            content.extend(chunk)

        status_code = r.status_code
        r.close()

        resp = make_response(bytes(content), status_code)
        resp.headers["Content-Type"] = content_type
        resp.headers["Cache-Control"] = "public, max-age=3600"

        return resp

    except Exception as e:
        if hasattr(e, "code"):
            raise

        logger.warning(f"[FLAG PROXY ERROR] {e}")
        abort(502)
        
@app.get("/api/importer2_image_proxy")
def api_importer2_image_proxy():
    remote_ip = request.remote_addr or ""

    # Importer 2 is currently a local tool. Do not expose an open proxy.
    if remote_ip not in ("127.0.0.1", "::1"):
        logger.warning(f"[IMPORTER2 PROXY BLOCKED IP] {remote_ip}")
        return jsonify({"error": "forbidden"}), 403

    if request.headers.get("X-Requested-With") != "importer2-image-proxy":
        return jsonify({"error": "forbidden"}), 403

    u = (request.args.get("url") or "").strip()

    if not u or len(u) > MAX_URL_LENGTH:
        return jsonify({"error": "invalid url"}), 400

    try:
        r = safe_outbound_request(
            u,
            method="GET",
            timeout=(2.0, 6.0),
            verify=True,
            stream=True,
            max_redirects=3,
        )

        try:
            if not (200 <= r.status_code < 300):
                return jsonify({"error": "upstream failed"}), 502

            content_type = (
                (r.headers.get("Content-Type") or "")
                .split(";", 1)[0]
                .strip()
                .lower()
            )

            if not content_type.startswith("image/"):
                return jsonify({"error": "not an image"}), 415

            max_bytes = 12 * 1024 * 1024
            declared = (r.headers.get("Content-Length") or "").strip()

            if declared.isdigit() and int(declared) > max_bytes:
                return jsonify({"error": "image too large"}), 413

            content = bytearray()

            for chunk in r.iter_content(chunk_size=65536):
                if not chunk:
                    continue

                if len(content) + len(chunk) > max_bytes:
                    return jsonify({"error": "image too large"}), 413

                content.extend(chunk)

        finally:
            r.close()

        resp = make_response(bytes(content), 200)
        resp.headers["Content-Type"] = content_type
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    except ValueError as e:
        logger.warning(f"[IMPORTER2 PROXY BLOCKED URL] {e}")
        return jsonify({"error": "blocked url"}), 403

    except Exception as e:
        logger.warning(f"[IMPORTER2 PROXY ERROR] {e}")
        return jsonify({"error": "fetch failed"}), 502

@app.route('/api/log_event', methods=['POST'])
def api_log_event():
    return jsonify({"ok": True})
    

@app.route("/api/detect_lang", methods=["POST"])
def api_detect_lang():
    data = request.get_json(silent=True) or {}


    text = data.get("text", "")

    if not isinstance(text, str):
        return jsonify({"error": "NieprawidÅ‚owy tekst"}), 400

    text = text.strip()

    if not text:
        return jsonify({"error": "Brak tekstu"}), 400

    # Maksymalnie 20 000 znakÃ³w do samej detekcji jÄ™zyka.
    if len(text) > 20000:
        return jsonify({
            "error": "Tekst jest za dÅ‚ugi. Maksymalnie 20000 znakÃ³w."
        }), 413

    try:
        lang = detect(text)
        return jsonify({"lang": lang})

    except Exception as e:
        logger.warning(
            "[DETECT LANG ERROR] %s",
            e
        )
        return jsonify({
            "error": "Nie udaÅ‚o siÄ™ wykryÄ‡ jÄ™zyka."
        }), 500
        
@app.route('/api/list_csv')
def list_csv():
    subdir = (request.args.get("dir") or "").strip()

    csv_root = (Path(app.static_folder) / "csv").resolve()

    try:
        base = (csv_root / subdir).resolve()
    except Exception:
        return jsonify([]), 400

    # ðŸ”’ Nie pozwÃ³l wyjÅ›Ä‡ poza static/csv
    if base != csv_root and csv_root not in base.parents:
        logger.warning(f"[LIST CSV BLOCKED PATH] dir={subdir!r}")
        return jsonify({"error": "forbidden"}), 403

    if not base.is_dir():
        return jsonify([])

    files = sorted(
        p.name
        for p in base.iterdir()
        if p.is_file() and p.suffix.lower() == ".csv"
    )

    return jsonify(files)
@app.route("/download-slideshow")

def download_slideshow():
    return send_from_directory(
        current_app.template_folder,
        "slideshow.html",
        as_attachment=True
    )
        
# =========================================================
# FAST TABLE â€” SIMPLE GET ANALYSIS (frontend compatibility)
# =========================================================

@app.get("/api/check_page_simple")
def api_check_page_simple():
    if not CHECK_PAGE_SIMPLE_SEM.acquire(blocking=False):
        return jsonify({
            "error": "Server busy, too many concurrent requests"
        }), 429

    try:
        domain = (request.args.get("domain") or "").strip().lower()

        if not DOMAIN_RX.fullmatch(domain):
            return jsonify({"error": "invalid domain"}), 400

        try:
            r = safe_outbound_request(
                f"https://{domain}",
                method="GET",
                timeout=(1.5, 2.5),
                verify=verify_ssl(domain),
                stream=True,
                max_redirects=3,
            )

            try:
                status = r.status_code
                final_url = r.url or ""
                ok = r.ok
            finally:
                r.close()

            return jsonify({
                "http_status": status,
                "final_url": final_url,
                "ok": ok,
            })

        except Exception as e:
            logger.warning(
                "[CHECK_PAGE_SIMPLE] error for %s: %s",
                domain,
                e
            )

            return jsonify({
                "http_status": 0,
                "final_url": "",
                "ok": False,
            })

    finally:
        CHECK_PAGE_SIMPLE_SEM.release()

@app.get("/api/fetch_meta_simple")
def api_fetch_meta_simple():
    if not FETCH_META_SIMPLE_SEM.acquire(blocking=False):
        return jsonify({
            "error": "Server busy, too many concurrent requests"
        }), 429

    try:
        domain = (request.args.get("domain") or "").strip().lower()

        if not DOMAIN_RX.fullmatch(domain):
            return jsonify({"error": "invalid domain"}), 400

        title = get_page_title(domain) or ""

        return jsonify({
            "title": title,
            "html_lang": "",
            "meta_description_length": 0
        })

    finally:
        FETCH_META_SIMPLE_SEM.release()
@app.get("/api/fast_row")
def api_fast_row():
    domain = (request.args.get("domain") or "").strip().lower()
    if not DOMAIN_RX.fullmatch(domain):
        return jsonify({"error": "invalid domain"}), 400

    cached = fast_cache_get(domain)
    if cached:
        return jsonify(cached)

    if not FAST_ROW_SEM.acquire(blocking=False):
        stale = fast_cache_get(domain)
        if stale:
            return jsonify(stale)
        return jsonify({
            "check": {
                "http_status": 0,
                "final_url": "",
                "status_txt": "BUSY"
            },
            "meta": {
                "title": "",
                "html_lang": "",
                "meta_description_length": 0
            }
        }), 429

    try:
        data = fetch_fast_row_data(domain)
        return jsonify(data)
    finally:
        FAST_ROW_SEM.release()
  
@app.post("/api/fast_reset")
def api_fast_reset():
    remote_ip = request.remote_addr or ""

    if remote_ip not in ("127.0.0.1", "::1"):
        logger.warning(f"[FAST RESET BLOCKED] ip={remote_ip}")
        return jsonify({"ok": False, "error": "forbidden"}), 403

    FAST_ROW_CACHE.clear()
    FILTER_CACHE.clear()

    logger.info("[FAST RESET] FAST_ROW_CACHE + FILTER_CACHE cleared")
    return jsonify({"ok": True})
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 9. URUCHOMIENIE
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

try:
    MAIN_SNAPSHOT, MAIN_CSV = detect_latest_snapshot()
    logger.info(f"[STARTUP] using snapshot {MAIN_SNAPSHOT}")
except Exception as e:
    logger.warning(f"[STARTUP] snapshot detection failed: {e}")
    MAIN_SNAPSHOT = "202601"
    MAIN_CSV = f"{MAIN_SNAPSHOT}.csv"

try:
    preload_fast_csv()
    logger.info("[STARTUP] preload_fast_csv done")
except Exception as e:
    logger.warning(f"[STARTUP] preload_fast_csv failed: {e}")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
