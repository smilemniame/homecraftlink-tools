// ─────────────────────────────────────────────
// FAST TABLE — FINAL STABLE
// page / per_page / prev / next / go / enter
// URL = source of truth
// ─────────────────────────────────────────────


// === 🔥 GLOBALNY KONTROLER ABORTA (MASTER CONTROL) ===
// === GLOBALNY KONTROLER PAGINACJI ===
let GLOBAL_ABORT = new AbortController();

// === KONTROLER TYLKO BACKGROUND API ===
let FAST_API_ABORT = new AbortController();

// === 🔥 GENERATION ID (do zabijania starych timeoutów) ===
let CURRENT_GENERATION = 0;

let IS_PAGE_LOADING = false;
let FAST_PENDING_PAGE = null;


function showFastWakeSpinner(label = "Loading…") {
  let overlay = document.getElementById("fastWakeOverlay");

  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "fastWakeOverlay";

    overlay.style.cssText = `
      position: fixed;
      inset: 0;
      z-index: 99999;
      display: none;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.12);
      pointer-events: none;
    `;

    overlay.innerHTML = `
      <div style="
        display:flex;
        align-items:center;
        gap:10px;
        padding:10px 16px;
        border-radius:8px;
        background:rgba(30,30,30,.92);
        color:#fff;
        font-size:14px;
        box-shadow:0 4px 18px rgba(0,0,0,.35);
      ">
        <span class="spinner-border spinner-border-sm"
              role="status"
              aria-hidden="true"></span>
        <span id="fastWakeOverlayText">Loading…</span>
      </div>
    `;

    document.body.appendChild(overlay);
  }

  const text = overlay.querySelector("#fastWakeOverlayText");
  if (text) text.textContent = label;

  overlay.style.display = "flex";


}

function hideFastWakeSpinner() {
  const overlay = document.getElementById("fastWakeOverlay");
  if (overlay) overlay.style.display = "none";


}

let ACTIVE_TIMEOUTS = new Set();

function safeTimeout(fn, delay) {
  const id = setTimeout(() => {
    ACTIVE_TIMEOUTS.delete(id);
    fn();
  }, delay);

  ACTIVE_TIMEOUTS.add(id);
  return id;
}

function clearAllTimeouts() {
  ACTIVE_TIMEOUTS.forEach(id => clearTimeout(id));
  ACTIVE_TIMEOUTS.clear();
}


let TOTAL_PAGES = null;
let isSwitching = false;


//  Zaznaczenia w runtime (czyszczone przy reload)
let selectedFast = new Set();

// ====================== FAST META CACHE (runtime) ======================
const fastMetaCache = new Map(); // Pamięć podręczna dla status + title

const FAST_CACHE_LIMIT = 500;

function setLimitedCache(cache, key, value, limit = FAST_CACHE_LIMIT) {
  if (cache.has(key)) {
    cache.delete(key);
  }

  cache.set(key, value);

  while (cache.size > limit) {
    const oldestKey = cache.keys().next().value;
    cache.delete(oldestKey);
  }
}

// ─────────────────────────────────────────────
// GLOBAL API TOGGLE (STATUS + TITLE)
// ─────────────────────────────────────────────


let API_FAST_ENABLED = false;      // status + title (auto-refresh)
let API_ANALYZE_ENABLED = true;    // rozwijany wiersz (chevron)
//  FAST API — licznik pracy (auto-shutdown)
let API_FAST_TOTAL = 0;
let API_FAST_DONE  = 0;

let FAST_AUTO_MODE = true;


let AUTO_FAST_SUPPRESS_UNTIL = 0;

function suppressAutoFast(ms = 1500) {
  AUTO_FAST_SUPPRESS_UNTIL = Date.now() + ms;
}

function stopTableApisForUserAction() {
  

  // Nie pozwól AUTO API wystartować ponownie podczas akcji użytkownika
  suppressAutoFast(3000);

  // Wyłącz automatyczne status/title
  API_FAST_ENABLED = false;
  API_FAST_DONE = 0;
  API_FAST_TOTAL = 0;

// Zabij WYŁĄCZNIE background API — nigdy paginację użytkownika
if (FAST_API_ABORT) {
  try {
    FAST_API_ABORT.abort();
  } catch (e) {
    console.warn("[USER ACTION] FAST API abort failed:", e);
  }
}

// Nowy kontroler dla przyszłego background API
FAST_API_ABORT = new AbortController();

  // Wyczyść kolejkę background API
  ApiGate.cancelAll();
  ApiGate.running = 0;
  ApiGate.queue = [];
  ApiGate.pending.clear();

  // Zabij oczekujące timery AUTO API
  clearAllTimeouts();

  syncApiButtons();
}

function closeAllFastAnalyses() {
  document.querySelectorAll('.analysis-row').forEach(r => r.remove());

  document.querySelectorAll('.analyze-btn').forEach(btn => {
    btn.dataset.open = '0';

    const icon = btn.querySelector('i');
    if (icon) {
      icon.classList.remove('bi-chevron-up');
      icon.classList.add('bi-chevron-down');
    }
  });

  if (window.__FAST_SCROLL_LOCK__) {
    requestAnimationFrame(() => {
      window.__FAST_SCROLL_LOCK__.applyScrollState();
    });
  }
}

// ─────────────────────────────────────────────
// STATE FROM URL
// ─────────────────────────────────────────────
function getCurrentPage() {
  const v = parseInt(new URLSearchParams(location.search).get("page"), 10);
  return Number.isFinite(v) && v > 0 ? v : 1;
}

function getPerPage() {
  const v = parseInt(new URLSearchParams(location.search).get("per_page"), 10);
  return Number.isFinite(v) && v > 0 ? v : 10;
}

function getCurrentSnapshot() {
  const sp = new URLSearchParams(location.search);
  const v = (sp.get("snapshot") || "").trim();
  return v || null;
}

let currentPage = getCurrentPage();

document.addEventListener("click", (e) => {
  const trigger = e.target.closest('[data-table-snapshot]');
  if (!trigger) return;

  e.preventDefault();

  const newSnapshot = (trigger.dataset.tableSnapshot || "").trim();
  const oldSnapshot = new URLSearchParams(location.search).get("snapshot");

  // tylko jeśli SNAPSHOT faktycznie się zmienia
  if (newSnapshot && newSnapshot !== oldSnapshot) {
    stopTableApisForUserAction();

    const sp = new URLSearchParams(location.search);
    sp.set("snapshot", newSnapshot);
    sp.set("page", "1");

	history.replaceState(null, "", "?" + sp.toString());

	// Aktualizacja widocznej daty rankingu i stopki
	const snapshotText =
	  `${newSnapshot.slice(0, 4)}-${newSnapshot.slice(4, 6)}`;

	const rankDateLabel =
	  document.getElementById("rankDateLabel");

	if (rankDateLabel) {
	  rankDateLabel.textContent = snapshotText;
	}

	const footerSnapshotLabel =
	  document.getElementById("footerSnapshotLabel");

	if (footerSnapshotLabel) {
	  footerSnapshotLabel.textContent = snapshotText;
	}

	// Aktualny miesiąc w menu
	document
	  .querySelectorAll("[data-table-snapshot]")
	  .forEach(item => {
		item.classList.toggle(
		  "active",
		  item.dataset.tableSnapshot === newSnapshot
		);
	  });

	// Aktualizacja źródła dla list zależnych od miesiąca
	const prefixDropdown = document.getElementById("prefixDropdown");

	if (prefixDropdown) {
	  prefixDropdown.dataset.snapshot = newSnapshot;
	}
	const wordsDropdown =
	  document.getElementById("wordsDropdownContainer");

	if (wordsDropdown) {
	  wordsDropdown.dataset.snapshot = newSnapshot;
	}

	resetPageOnSourceChange();
	showFastWakeSpinner("Loading snapshot…");
	safePageChange(1);
  }
});

document.addEventListener("change", (e) => {
  const sel = e.target.closest('select[name="snapshot"], #snapshot, #snapshotSelect');
  if (!sel) return;

  const newSnapshot = (sel.value || "").trim();
  const oldSnapshot = new URLSearchParams(location.search).get("snapshot");

if (newSnapshot && newSnapshot !== oldSnapshot) {
  stopTableApisForUserAction();
  resetPageOnSourceChange();
}
});

function resetPageOnSourceChange() {
  currentPage = 1;

  const sp = new URLSearchParams(location.search);
  sp.set("page", "1");

  //  jeśli q jest puste w input — usuń je
  const searchInput = document.querySelector('#searchInput, input[name="q"]');
  if (searchInput && searchInput.value.trim() === "") {
    sp.delete("q");
  }

  history.replaceState(null, "", "?" + sp.toString());

  document.querySelectorAll('[data-role="page-input"]').forEach(inp => {
    inp.value = "1";
  });
}


// ─────────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────────
function idle(fn) {
  if ("requestIdleCallback" in window) {
    requestIdleCallback(fn, { timeout: 800 });
  } else {
    setTimeout(fn, 80);
  }
}

function buildFastPayload(page) {
  const sp = new URLSearchParams(location.search);

  sp.set("page", String(page));
  sp.set("per_page", String(getPerPage()));

  const snapshot = getCurrentSnapshot();

  if (snapshot) {
    sp.set("snapshot", snapshot);
  } else {
    sp.delete("snapshot");
  }

  return sp;
}
// ─────────────────────────────────────────────
// API GATE — kontrola wąskiego gardła
// ─────────────────────────────────────────────
// ─────────────────────────────────────────────
// API GATE — kontrola wąskiego gardła
// ─────────────────────────────────────────────
const ApiGate = {
  running: 0,
  max: 1,
  queue: [],
  cancelled: false,
  pending: new Set(), //  Śledzi pending requesty

  async run(task) {
    if (this.cancelled) return;

    if (this.running >= this.max) {
      this.queue.push(task);
      return;
    }
	this.pending.add(task);

    this.running++;
    try {
      await task();
    } catch (e) {
      console.error('[ApiGate] task error:', e);
    } finally {
      this.running--;
      this.pending.delete(task); //  Usuń z pending
      if (this.queue.length && !this.cancelled) {
        this.run(this.queue.shift());
      }
    }
  },

cancelAll() {
  this.queue = [];
  this.cancelled = true;

  this.pending.forEach(task => {
    if (task.abort && typeof task.abort === 'function') {
      task.abort();
    }
  });

  this.pending.clear();

  // 🔥 KLUCZOWE — RESET STANU
  this.running = 0;

  setTimeout(() => (this.cancelled = false), 0);
}
};


function syncTotalPagesFromResponse(res) {
	
	  const totalRows = res.headers.get("X-Total-Rows");

  if (totalRows !== null) {
    const totalRowsValue =
      document.getElementById("totalRowsValue");

    if (totalRowsValue) {
      const number = Number(totalRows);

      totalRowsValue.textContent =
        Number.isFinite(number)
          ? number.toLocaleString()
          : totalRows;
    }
  }
	
  const tp = res.headers.get("X-Total-Pages");
  if (!tp) return;

  const n = parseInt(tp, 10);
  if (!Number.isFinite(n) || n < 1) return;

	TOTAL_PAGES = n;

	document.querySelectorAll('[data-role="total-pages"]').forEach(el => {
	  el.textContent = TOTAL_PAGES.toLocaleString();
	});

	document.querySelectorAll('[data-role="page-input"]').forEach(inp => {
	  inp.max = String(TOTAL_PAGES);

	  if (parseInt(inp.value || "1", 10) > TOTAL_PAGES) {
		inp.value = TOTAL_PAGES;
	  }
	});
}

function syncPagerUI() {
  document.querySelectorAll('[data-role="page-input"]').forEach(inp => {
    inp.value = currentPage;
  });

  document.querySelectorAll('[data-role="page-prev"]').forEach(btn => {
    const disabled = currentPage <= 1;
    btn.disabled = disabled;
    btn.closest("li.page-item")?.classList.toggle("disabled", disabled);
  });

  document.querySelectorAll('[data-role="page-next"]').forEach(btn => {
    const disabled = TOTAL_PAGES && currentPage >= TOTAL_PAGES;
    btn.disabled = disabled;
    btn.closest("li.page-item")?.classList.toggle("disabled", disabled);
  });
}

// ─────────────────────────────────────────────
// FETCH
// ─────────────────────────────────────────────
async function fetchTbody(page) {
  const payload = buildFastPayload(page);
  const startedAt = performance.now();



  const res = await fetch("/top_sites_fast", {
    method: "POST",
    body: payload,
    signal: GLOBAL_ABORT.signal,
    headers: {
      "X-Partial": "tbody",
      "X-Embed": "1",
      "X-Requested-With": "table-fast",
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
  });



  if (!res.ok) {
    throw new Error(`fetch failed: ${res.status}`);
  }

  syncTotalPagesFromResponse(res);

  const html = await res.text();



  return html;
}

// ─────────────────────────────────────────────
// CORE
// ─────────────────────────────────────────────
// ─────────────────────────────────────────────
// CORE
// ─────────────────────────────────────────────
async function goToPage(page) {


if (isSwitching || IS_PAGE_LOADING) {
  FAST_PENDING_PAGE = page;



  return;
}

  window.__FAST_SCROLL_LOCK__?.stopObservers?.();
  closeAllFastAnalyses();

  clearAllTimeouts();

  suppressAutoFast(2000);  

  IS_PAGE_LOADING = true;
  isSwitching = true;
  


  CURRENT_GENERATION++;

  if (GLOBAL_ABORT) {
    try {
      GLOBAL_ABORT.abort();
    } catch (e) {
      console.warn('[ABORT] previous controller abort failed:', e);
    }
  }

  GLOBAL_ABORT = new AbortController();

  const myGen = CURRENT_GENERATION;

  ApiGate.cancelAll();
  
  ApiGate.running = 0;
  ApiGate.queue = [];
  ApiGate.pending.clear();

  
  API_FAST_ENABLED = false;
  API_FAST_DONE = 0;
  API_FAST_TOTAL = 0;
  syncApiButtons();

  page = parseInt(page, 10);
  if (!Number.isFinite(page)) page = 1;
  if (page < 1) page = 1;
  if (TOTAL_PAGES && page > TOTAL_PAGES) page = TOTAL_PAGES;

  const tbody = document.querySelector("#fastTable tbody");
if (!tbody) {
  IS_PAGE_LOADING = false;
  isSwitching = false;
  
  hideFastWakeSpinner();
  console.warn("[FAST PAGE] Brak tbody");
  return;
}

  try {
	const html = await fetchTbody(page);


	// 1️⃣ najpierw czysty render
	tbody.innerHTML = html;



	// 2️⃣ event po renderze


	document.dispatchEvent(new Event('fastTable:tbodyReplaced'));

		
    // 3️⃣ stan / URL
    currentPage = page;

	const sp = new URLSearchParams(location.search);
	sp.set("page", String(page));
	sp.set("per_page", String(getPerPage()));

	const snapshot = getCurrentSnapshot();
	if (snapshot) {
	  sp.set("snapshot", snapshot);
	} else {
	  sp.delete("snapshot");
	}

	history.replaceState(null, "", "?" + sp.toString());

    syncPagerUI();
	

    // 4️⃣ dopiero po 2 klatkach uznajemy stronę za gotową
	requestAnimationFrame(() => {



	  requestAnimationFrame(() => {



		window.__FAST_SCROLL_LOCK__?.startObservers?.();
		

		isSwitching = false;
		IS_PAGE_LOADING = false;

			
			hideFastWakeSpinner();


			
						if (
			  FAST_PENDING_PAGE !== null &&
			  FAST_PENDING_PAGE !== currentPage
			) {
			  const queuedPage = FAST_PENDING_PAGE;
			  FAST_PENDING_PAGE = null;


			  showFastWakeSpinner(`Loading page ${queuedPage}…`);
			  safePageChange(queuedPage);
			} else {
			  FAST_PENDING_PAGE = null;
			}

		const startApi = () => {
		  if (
			isSwitching ||
			IS_PAGE_LOADING ||
			myGen !== CURRENT_GENERATION ||
			!API_FAST_ENABLED
		  ) return;

		  const tbodyNow = document.querySelector("#fastTable tbody");
		  if (!tbodyNow) return;

		  API_FAST_DONE = 0;
		  API_FAST_TOTAL = tbodyNow.querySelectorAll('[data-domain]').length;

		  
		  refreshVisibleTitleStatus(tbodyNow, myGen);
		};

		const waitMs = Math.max(0, AUTO_FAST_SUPPRESS_UNTIL - Date.now());

		safeTimeout(() => {
		  if (myGen !== CURRENT_GENERATION) return;
		  if (isSwitching || IS_PAGE_LOADING) return;

		  API_FAST_ENABLED = true;
		  syncApiButtons();

		  requestAnimationFrame(() => {
			startApi();
		  });

		  safeTimeout(() => {
			if (
			  API_FAST_ENABLED &&
			  !IS_PAGE_LOADING &&
			  !isSwitching &&
			  API_FAST_DONE === 0 &&
			  myGen === CURRENT_GENERATION
			) {
			  
			  startApi();
			}
		  }, 1300);

		}, waitMs + 150);
      });
    });

} catch (e) {
if (e.name === 'AbortError') {
  
  isSwitching = false;
  IS_PAGE_LOADING = false;
  
  hideFastWakeSpinner();
  return;
}

console.error("goToPage error:", e);
isSwitching = false;
IS_PAGE_LOADING = false;

hideFastWakeSpinner();
}
}

function safePageChange(targetPage) {

  // USER FOREGROUND PRIORITY
  stopTableApisForUserAction();

  targetPage = parseInt(targetPage, 10);

  if (!Number.isFinite(targetPage)) {
    targetPage = 1;
  }

  if (targetPage < 1) {
    targetPage = 1;
  }

  if (TOTAL_PAGES && targetPage > TOTAL_PAGES) {
    targetPage = TOTAL_PAGES;
  }



  if (isSwitching || IS_PAGE_LOADING) {
    FAST_PENDING_PAGE = targetPage;

    showFastWakeSpinner(`Queued page ${targetPage}…`);



    return;
  }

  FAST_PENDING_PAGE = null;

  closeAllFastAnalyses();

  suppressAutoFast(2000);
  API_FAST_ENABLED = false;
  syncApiButtons();

  goToPage(targetPage);
}

// ─────────────────────────────────────────────
// USER PRIORITY — DROPDOWN NAVIGATION
// ─────────────────────────────────────────────
document.addEventListener("click", (e) => {
  const link = e.target.closest("a.dropdown-item[href]");
  if (!link) return;

  const href = (link.getAttribute("href") || "").trim();

  // samo otwieranie submenu nie jest akcją tabeli
  if (!href || href === "#" || href.startsWith("javascript:")) return;

  stopTableApisForUserAction();
}, true);

// ─────────────────────────────────────────────
// EVENTS
// ─────────────────────────────────────────────
document.addEventListener("click", (e) => {
  const prev = e.target.closest('[data-role="page-prev"]');
  const next = e.target.closest('[data-role="page-next"]');
  const go   = e.target.closest('[data-role="page-go"]');

if (prev) {
  e.preventDefault();
  showFastWakeSpinner("Previous page…");
  const basePage =
    FAST_PENDING_PAGE !== null
      ? FAST_PENDING_PAGE
      : currentPage;
  safePageChange(basePage - 1);
  return;
}

if (next) {
  e.preventDefault();
  showFastWakeSpinner("Next page…");
  const basePage =
    FAST_PENDING_PAGE !== null
      ? FAST_PENDING_PAGE
      : currentPage;
  safePageChange(basePage + 1);
  return;
}
if (go) {
  e.preventDefault();

  const pager = go.closest("[data-pager]");
  const input = pager?.querySelector('[data-role="page-input"]');
  if (!input) return;

  showFastWakeSpinner("Loading page…");

  suppressAutoFast(2000);
  API_FAST_ENABLED = false;
  syncApiButtons();

  safePageChange(parseInt(input.value, 10) || 1);
}
});

document.addEventListener("keydown", (e) => {
  if (e.key !== "Enter") return;
  const input = e.target.closest('[data-role="page-input"]');
  if (!input) return;

  e.preventDefault();
  
  showFastWakeSpinner("Loading page…");

  suppressAutoFast(2000);
  API_FAST_ENABLED = false;
  syncApiButtons();

  safePageChange(parseInt(input.value, 10) || 1);
});

document.addEventListener("change", (e) => {
  const sel = e.target.closest('#per_page, select[name="per_page"]');
  if (!sel) return;

  const v = parseInt(sel.value, 10);
  if (!Number.isFinite(v)) return;

  closeAllFastAnalyses();

  suppressAutoFast(2000);
  API_FAST_ENABLED = false;
  syncApiButtons();

  const sp = new URLSearchParams(location.search);
  sp.set("per_page", String(v));
  sp.set("page", "1");

  const snapshot = getCurrentSnapshot();
  if (snapshot) {
    sp.set("snapshot", snapshot);
  } else {
    sp.delete("snapshot");
  }

  history.replaceState(null, "", "?" + sp.toString());

  currentPage = 1;
  
  showFastWakeSpinner("Loading table…");
  
  safePageChange(1);
});

document.addEventListener("input", (e) => {
  const input = e.target.closest('#searchInput, input[name="q"]');
  if (!input) return;

  stopTableApisForUserAction();

  const value = input.value.trim();
  const sp = new URLSearchParams(location.search);

	if (value === "") {
	  if (sp.has("q")) {
		sp.delete("q");
		sp.set("page", "1");

		history.replaceState(null, "", "?" + sp.toString());
		showFastWakeSpinner("Loading table…");
		safePageChange(1);
	  }
	}
});

document.addEventListener("submit", (e) => {
  const form = e.target.closest("form.fast-search-bar");
  if (!form) return;

  e.preventDefault();
  stopTableApisForUserAction();

  const input = form.querySelector('input[name="q"]');
  const value = (input?.value || "").trim();
  const sp = new URLSearchParams(location.search);

  if (value) {
    sp.set("q", value);
  } else {
    sp.delete("q");
  }

  sp.set("page", "1");
  history.replaceState(null, "", "?" + sp.toString());

  currentPage = 1;
  showFastWakeSpinner("Searching…");
  safePageChange(1);
});

document.addEventListener("click", (e) => {
  const link = e.target.closest("a.dropdown-item[href]");
  if (!link) return;

  const href = (link.getAttribute("href") || "").trim();

  // Kliknięcie otwierające submenu nie filtruje tabeli.
  if (!href || href === "#" || href.startsWith("javascript:")) {
    return;
  }

  const url = new URL(href, location.href);

  // Przechwytujemy tylko nawigację wewnątrz ciężkiej tabeli.
  if (
    url.origin !== location.origin ||
    url.pathname !== "/top_sites_fast"
  ) {
    return;
  }

  e.preventDefault();
  e.stopPropagation();

	const params = new URLSearchParams(url.search);

	// Link dropdownu mógł powstać dla poprzedniego miesiąca.
	// Zawsze używamy miesiąca aktualnie wybranego w tabeli.
	const currentSnapshot = getCurrentSnapshot();

	if (currentSnapshot) {
	  params.set("snapshot", currentSnapshot);
	}

	params.set("page", "1");

	const searchInput =
	  document.querySelector('#searchInput, input[name="q"]');

	if (searchInput) {
	  searchInput.value = params.get("q") || "";
	}

	history.replaceState(
    null,
    "",
    "?" + params.toString()
  );

  currentPage = 1;
  stopTableApisForUserAction();
  showFastWakeSpinner("Loading table…");
  safePageChange(1);
});


// RESET FILTRA — kliknięcie w Total rows
document.addEventListener("click", (e) => {
  const reset = e.target.closest("#totalRowsReset");
  if (!reset) return;

  e.preventDefault();

  const params = new URLSearchParams(location.search);
  params.delete("q");
  params.set("page", "1");

  const searchInput =
    document.querySelector('#searchInput, input[name="q"]');

  if (searchInput) {
    searchInput.value = "";
  }

  history.replaceState(
    null,
    "",
    "?" + params.toString()
  );

  currentPage = 1;
  stopTableApisForUserAction();
  showFastWakeSpinner("Loading all rows…");
  safePageChange(1);
});

// ─────────────────────────────────────────────
// KEYBOARD PAGINATION (ARROWS)
// SAFE: uses same pipeline as buttons
// ─────────────────────────────────────────────

// ─────────────────────────────────────────────
// KEYBOARD PAGINATION (ARROWS)
// SAFE: uses same pipeline as buttons
// ─────────────────────────────────────────────

document.addEventListener("keydown", (e) => {

  // nie reaguj gdy piszemy w inputach
  if (
    e.target.closest("input, textarea, select, [contenteditable]")
  ) return;

  // nie reaguj podczas przełączania
  if (IS_PAGE_LOADING || isSwitching) return;

  // blokada gdy focus w pager input
  if (e.target.closest('[data-role="page-input"]')) return;

  // → następna strona
if (e.key === "ArrowRight") {
  if (TOTAL_PAGES && currentPage >= TOTAL_PAGES) return;
  e.preventDefault();
  showFastWakeSpinner("Next page…");
  suppressAutoFast(1200);
  API_FAST_ENABLED = false;
  syncApiButtons();
  const basePage =
    FAST_PENDING_PAGE !== null
      ? FAST_PENDING_PAGE
      : currentPage;
  safePageChange(basePage + 1);
  return;
}

  // ← poprzednia strona
if (e.key === "ArrowLeft") {
  if (currentPage <= 1) return;
  e.preventDefault();
  showFastWakeSpinner("Previous page…");
  suppressAutoFast(1200);
  API_FAST_ENABLED = false;
  syncApiButtons();
  const basePage =
    FAST_PENDING_PAGE !== null
      ? FAST_PENDING_PAGE
      : currentPage;
  safePageChange(basePage - 1);
  return;
}
  // HOME = pierwsza strona
  if (e.key === "Home") {

    if (currentPage === 1) return;

    e.preventDefault();

    suppressAutoFast(1200);
    API_FAST_ENABLED = false;
    syncApiButtons();
	
	showFastWakeSpinner("First page…");

    safePageChange(1);
    return;
  }

  // END = ostatnia strona (jeśli znamy)
  if (e.key === "End") {

    if (!TOTAL_PAGES) return;
    if (currentPage === TOTAL_PAGES) return;

    e.preventDefault();

    suppressAutoFast(1200);
    API_FAST_ENABLED = false;
    syncApiButtons();
	
	showFastWakeSpinner("Last page…");

    safePageChange(TOTAL_PAGES);
    return;
  }

});

// ─────────────────────────────────────────────
// PAGE INPUT GUARD (max digits / clamp live)
// ─────────────────────────────────────────────
document.addEventListener("input", (e) => {
  const input = e.target.closest('[data-role="page-input"]');
  if (!input) return;

  // tylko cyfry
  input.value = input.value.replace(/\D+/g, "");

  // max długość (np. 6 cyfr)
  const MAX_DIGITS = 6;
  if (input.value.length > MAX_DIGITS) {
    input.value = input.value.slice(0, MAX_DIGITS);
  }

  // clamp do TOTAL_PAGES jeśli znamy
  if (TOTAL_PAGES) {
    const v = parseInt(input.value || "0", 10);
    if (v > TOTAL_PAGES) {
      input.value = String(TOTAL_PAGES);
    }
  }
});

function refreshVisibleTitleStatus(root, gen) {
	

	
  // 🔥 GENERATION GUARD: jeśli to wywołanie jest stare, nic nie rób
  if (gen !== CURRENT_GENERATION) {
    
    return;
  }

  // WARTOWNIK: Jeśli globalny abort jest w trakcie, nie zaczynaj niczego nowego
  if (FAST_API_ABORT.signal.aborted) return;

  if (!root || !API_FAST_ENABLED || isSwitching) return;

  const cells = Array.from(root.querySelectorAll('.title-cell[data-domain]'));

  cells.forEach((cell, index) => {
    const domain = (cell.dataset.domain || '').trim();
    if (!domain) return;

    setTimeout(() => {
      // 🔥 GENERATION GUARD: sprawdź przed wykonaniem
      if (gen !== CURRENT_GENERATION) {
        
        return;
      }
      if (!API_FAST_ENABLED) return;

      ApiGate.run(async () => {
        // 🔥 GENERATION GUARD: sprawdź przed wejściem do ApiGate
        if (gen !== CURRENT_GENERATION) return;

        showStatusSpinner(domain);

        let data = null;
        try {
          data = await fetchFastStatus(domain);
          if (data?.aborted) return;
          if (gen !== CURRENT_GENERATION) return; // Kolejny guard po async

          updateTableCells(domain, data);
        } finally {
          if (gen !== CURRENT_GENERATION) return;

          if (!data?.check?.http_status) {
            clearStatusSpinner(domain);
          }
          if (!data?.meta?.title) {
            const titleCell = document.querySelector(
              `.title-cell[data-domain="${CSS.escape(domain)}"]`
            );
            if (titleCell) titleCell.classList.remove('loading');
          }

          API_FAST_DONE++;
          if (API_FAST_ENABLED && API_FAST_DONE >= API_FAST_TOTAL) {
            shutdownFastAPI();
          }
        }
      });
    }, index * 40);
  });
}


function refreshChevronIcons() {

  requestAnimationFrame(()=>{

    document.querySelectorAll('.analyze-btn i').forEach(icon => {

      // force repaint font icon
      icon.style.display = 'none';
      icon.offsetHeight;
      icon.style.display = 'inline-block';

    });

  });

}

// ─────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────
function initFastTable() {
  const tbody = document.querySelector("#fastTable tbody");
  if (!tbody) return;

  document.querySelectorAll('.analysis-row').forEach(r => r.remove());
  document.querySelectorAll('.analyze-btn').forEach(btn => {
    btn.dataset.open = '0';
    const icon = btn.querySelector('i');
    if (icon) {
      icon.classList.remove('bi-chevron-up');
      icon.classList.add('bi-chevron-down');
    }
  });

  // ✅ NIC nie dociągamy drugi raz przy starcie
  document.dispatchEvent(new Event('fastTable:tbodyReplaced'));
  syncPagerUI();

  // ✅ API dopiero po spokojnym wejściu strony
  
setTimeout(() => {

  if (IS_PAGE_LOADING || isSwitching) return;

  const tbodyNow = document.querySelector('#fastTable tbody');
  if (!tbodyNow) return;


  API_FAST_ENABLED = true;
  API_FAST_DONE = 0;
  API_FAST_TOTAL = tbodyNow.querySelectorAll('[data-domain]').length;

  syncApiButtons();

  requestAnimationFrame(() => {
    refreshVisibleTitleStatus(tbodyNow, CURRENT_GENERATION);
  });

}, 900);



}

document.addEventListener('fastTable:tbodyReplaced', () => {
  // Przywróć zaznaczenia z Set
  document.querySelectorAll('.row-check').forEach(cb => {
    if (selectedFast.has(cb.dataset.domain)) {
      cb.checked = true;
      cb.closest('tr')?.classList.add('row-selected');
    }
  });

  // Zsynchronizuj checkbox "zaznacz wszystko"
  const header = document.getElementById('selectAllFast');
  if (header) {
    const visible = Array.from(document.querySelectorAll('.row-check'));
    const checked = visible.filter(cb => cb.checked).length;

    header.indeterminate = checked > 0 && checked < visible.length;
    header.checked = visible.length > 0 && checked === visible.length;
  }

  updateFastCopyButton();
});

// ===============================
// FAST TABLE — CHECKBOX LOGIC (v59-style)
// ===============================
(function () {

  function getRowCheckboxes() {
    return Array.from(document.querySelectorAll('.row-check'));
  }

  function getSelectAll() {
    return document.getElementById('selectAllFast');
  }

  function updateRowHighlight(cb) {
    const tr = cb.closest('tr');
    if (!tr) return;
    tr.classList.toggle('row-selected', cb.checked);
  }

  function syncHeaderCheckbox() {
    const all = getRowCheckboxes();
    const header = getSelectAll();
    if (!header || all.length === 0) return;

    const checked = all.filter(cb => cb.checked).length;

    header.indeterminate = checked > 0 && checked < all.length;
    header.checked = checked === all.length;
  }

function onRowCheckboxChange(e) {
  if (!e.target.classList.contains('row-check')) return;

  const cb = e.target;
  const domain = cb.dataset.domain;

  if (cb.checked) {
    selectedFast.add(domain);
  } else {
    selectedFast.delete(domain);
  }

	updateRowHighlight(cb);
	syncHeaderCheckbox();
	updateFastCopyButton();
}

function onSelectAllChange(e) {
  const checked = e.target.checked;

  getRowCheckboxes().forEach(cb => {
    cb.checked = checked;

    const domain = cb.dataset.domain;
    if (!domain) return;

    if (checked) {
      selectedFast.add(domain);
    } else {
      selectedFast.delete(domain);
    }

    updateRowHighlight(cb);
  });

  e.target.indeterminate = false;
  updateFastCopyButton();
}


  // Delegacja eventów (ważne dla AJAX!)
  document.addEventListener('change', function (e) {
    onRowCheckboxChange(e);
    if (e.target.id === 'selectAllFast') {
      onSelectAllChange(e);
    }
  });



})();

function updateFastCopyButton() {
  const btn = document.getElementById('copySelectedFast');
  if (!btn) return;

  const active = selectedFast.size > 0;

  btn.disabled = !active;
  btn.classList.toggle('fast-disabled', !active);
  btn.setAttribute('aria-disabled', String(!active));
}

updateFastCopyButton();

function clearFastSelection() {
	selectedFast.clear();  //  Czyścimy Set
  document.querySelectorAll('.row-check').forEach(cb => {
    cb.checked = false;
    cb.closest('tr')?.classList.remove('row-selected');
  });

	const header = document.getElementById('selectAllFast');
	if (header) {
	  header.checked = false;
	  header.indeterminate = false;
	}

	updateFastCopyButton();
}


// ================================
// FAST TABLE – COPY / EXPORT
// ================================
(function () {


  // COPY
document.getElementById('copySelectedFast')?.addEventListener('click', () => {
  const rows = Array.from(selectedFast);
  if (!rows.length) return;

  const text = rows.join('\n');

  navigator.clipboard.writeText(text)
    .then(() => {
      selectedFast.clear();
      clearFastSelection();
    })
    .catch(err => console.error('Copy failed:', err));
});



})();

function showStatusSpinner(domain) {
  const cell = document.querySelector(
    `.status-cell[data-domain="${CSS.escape(domain)}"]`
  );
  if (!cell) return;

  cell.innerHTML = `
    <span class="spinner-border spinner-border-sm text-secondary"
          role="status"
          title="Sprawdzanie…"></span>
  `;
}

function clearStatusSpinner(domain) {
  const cell = document.querySelector(
    `.status-cell[data-domain="${CSS.escape(domain)}"]`
  );
  if (!cell) return;

  // jeśli nie nadpisze tego updateTableCells(), zostanie „—”
  cell.innerHTML = `<span class="badge bg-secondary">—</span>`;
}



// =========================================================
// FAST TABLE — TABLE CELL UPDATE (TITLE + STATUS)
// =========================================================
function updateTableCells(domain, data) {
  if (!domain || !data) return;
  
    if (typeof fastMetaCache !== "undefined" && !fastMetaCache.has(domain)) {
    setLimitedCache(fastMetaCache, domain, data);
  }

// TITLE
const titleCell = document.querySelector(
  `.title-cell[data-domain="${CSS.escape(domain)}"]`
);

if (titleCell) {
  const rawTitle = (data?.meta?.title || '').trim();

  if (rawTitle) {
    const safeTitle = rawTitle.replace(/\s+/g, ' ');

	const span = document.createElement('span');
	span.className = 'title-text';
	span.textContent = safeTitle;

	titleCell.replaceChildren(span);

    //  tylko jeśli tekst się nie mieści
    titleCell.addEventListener('mouseenter', () => {
      const textWidth = span.scrollWidth;
      const visibleWidth = titleCell.clientWidth;

      if (textWidth <= visibleWidth) return;

      const end = visibleWidth - textWidth - 4;
      span.style.setProperty('--scroll-end', end + 'px');

      const duration = Math.max(4, textWidth / 80);
      span.style.animationDuration = duration + 's';
    });

    titleCell.addEventListener('mouseleave', () => {
      span.style.animationDuration = '';
      span.style.removeProperty('--scroll-end');
    });

} else {
  titleCell.textContent = '';
  titleCell.removeAttribute('title');
}

  titleCell.classList.remove('loading');
}
  // STATUS
  const statusCell = document.querySelector(
    `.status-cell[data-domain="${CSS.escape(domain)}"]`
  );
  if (statusCell && data?.check?.http_status) {
    const code = data.check.http_status;
    let badgeClass = 'bg-secondary';

    if (code >= 200 && code < 300) badgeClass = 'bg-success';
    else if (code >= 300 && code < 400) badgeClass = 'bg-info';
    else if (code >= 400 && code < 500) badgeClass = 'bg-warning';
    else if (code >= 500) badgeClass = 'bg-danger';

    statusCell.innerHTML = `
      <span class="badge ${badgeClass}">
        ${code}
      </span>
    `;
  }
}


// ─────────────────────────────────────────────
// FAST STATUS FETCH (only for table cells - lightweight)
// ─────────────────────────────────────────────
async function fetchFastStatus(domain) {
  const cached = fastMetaCache.get(domain);
  if (cached) return cached;

  if (!API_FAST_ENABLED) {
    return { error: true };
  }

  try {
    const signal = FAST_API_ABORT.signal;

    const r = await fetchWithSoftTimeout(
      `/api/fast_row?domain=${encodeURIComponent(domain)}`,
      6000,
      { signal }
    );

    if (!r.ok) {
      throw new Error(`fast_row failed: ${r.status}`);
    }

    const result = await r.json();

    setLimitedCache(fastMetaCache, domain, result);
    return result;

  } catch (err) {
		if (err.name === 'AbortError') {
		  return { aborted: true };
		}
    console.warn('[FAST-ROW] error:', domain, err.message);
    return { error: true };
  }
}

// Zaktualizuj fetchWithSoftTimeout, aby przyjmowała opcje
function fetchWithSoftTimeout(url, timeoutMs = 5000, options = {}) {
  const controller = new AbortController();

  

  const timeoutId = setTimeout(() => {
    
    try {
      controller.abort();
    } catch(e) {}
  }, timeoutMs);

  const extSignal = options.signal;

  const onAbort = () => {
    try {
      controller.abort();
    } catch(e) {}
  };

  if (extSignal) {
    if (extSignal.aborted) onAbort();
    else extSignal.addEventListener('abort', onAbort, { once: true });
  }

return fetch(url, {
  ...options,
  signal: controller.signal
}).finally(() => {
    clearTimeout(timeoutId);
    if (extSignal) extSignal.removeEventListener('abort', onAbort);
  });
}
const analysisCache = new Map();


const DOMAIN_COOLDOWN_MS = 15000; // 15s
const domainLastFetch = new Map();


async function fetchFullAnalysis(domain) {
  if (!API_ANALYZE_ENABLED) {
    return { error: true };
  }
  //  cooldown per domena
  const last = domainLastFetch.get(domain) || 0;
  const now = Date.now();
  if (now - last < DOMAIN_COOLDOWN_MS) {
    return analysisCache.get(domain) || { error: true };
  }
  domainLastFetch.set(domain, now);

  if (analysisCache.has(domain)) {
    return analysisCache.get(domain);
  }

  const result = {
    check: null,
    meta: null
  };

  try {
    // 1️⃣ STATUS — krótki timeout
	const r1 = await fetchWithSoftTimeout(
	  `/api/check_page_simple?domain=${encodeURIComponent(domain)}`,
	  2000,
	  { signal: FAST_API_ABORT.signal }
	);
    if (!r1.ok) throw new Error('check_page failed');
    result.check = await r1.json();

    // 2️⃣ META — trochę dłużej, ale nadal krótko
	const r2 = await fetchWithSoftTimeout(
	  `/api/fetch_meta_simple?domain=${encodeURIComponent(domain)}`,
	  2500,
	  { signal: FAST_API_ABORT.signal }
	);
    if (!r2.ok) throw new Error('fetch_meta failed');
    result.meta = await r2.json();

    setLimitedCache(analysisCache, domain, result);
    return result;

  } catch (err) {
    console.warn('[API] soft-timeout / error:', domain);
    return { error: true };
  }
}

function renderAnalysisHTML(data) {
  if (data.error) {
    return `<div class="text-danger">Błąd pobierania analizy</div>`;
  }

  const { check, meta } = data;

  return `
    <div class="analysis-content">
      <h6>HTTP</h6>
      <ul>
        <li>Status: <strong>${check.http_status}</strong> ${check.status_txt || ''}</li>
        <li>Final URL: ${check.final_url || ''}</li>
      </ul>

      <h6>META</h6>
      <ul>
        <li>Title: ${meta.title || '(brak)'}</li>
        <li>Lang: ${meta.html_lang || '(?)'}</li>
        <li>Description length: ${meta.meta_description_length || 0}</li>
      </ul>
    </div>
  `;
}



// =========================================================
// FAST TABLE — ANALYSIS TOGGLE (CACHE FIRST + SMART UX + COLLAPSE)
// =========================================================
(function () {

  //  0. CSS INJECTION (Spinner + Collapse Mode)
  const styleId = 'analysis-spinner-style';
  if (!document.getElementById(styleId)) {
      const style = document.createElement('style');
      style.id = styleId;
      style.textContent = `
          /* Loading States */
          .analysis-loading { color: #666; font-style: italic; font-size: 0.9em; }
          .analysis-spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid #ccc; border-top-color: #666; border-radius: 50%; animation: analysis-spin 0.8s linear infinite; vertical-align: -2px; }
          @keyframes analysis-spin { to { transform: rotate(360deg); } }

          /* Collapse Mode */
          .analysis-box.collapsed {
            max-height: 300px;
            overflow-y: auto;
            overflow-x: hidden;
            border: 1px dashed #ccc;
          }
          .analysis-collapse-btn { margin-left: 6px; }
      `;
      document.head.appendChild(style);
	  
	  style.textContent += `
  /* Global Error Status */
  .analysis-global-error {
    color: #dc3545;
    font-size: 0.85em;
    font-weight: 500;
    margin-left: 8px;
    padding: 2px 6px;
    background: rgba(220, 53, 69, 0.1);
    border-radius: 3px;
  }
  /* ===============================
   COLLAPSED MODE — STICKY IP PANEL
   =============================== */

.analysis-box.collapsed .analysis-panel-ip {
  position: sticky;
  top: 0;
  z-index: 5;
  background: #2d2d2d;
}
.analysis-box.collapsed .analysis-links-list {
  max-height: 220px;
  overflow-y: auto;
}


/* delikatna linia oddzielająca od linków */
.analysis-box.collapsed .analysis-panel-ip::after {
  content: "";
  display: block;
  height: 1px;
  background: rgba(255,255,255,0.15);
  margin-top: 4px;
}

/* ===============================
   COLLAPSED MODE — MOVE & HIGHLIGHT COLLAPSE BUTTON
   =============================== */

/* kontener przycisków */
.analysis-box.collapsed .analysis-actions-inline {
  position: relative;
}

/* sam przycisk collapse */
.analysis-box.collapsed .analysis-collapse-btn {
  
  right: 6px;
  top: -4px;

  padding: 4px 6px;
  border-radius: 6px;

  background: rgba(255,255,255,0.12);
  border-color: rgba(255,255,255,0.35);
  color: #fff;

  opacity: 0.85;
  z-index: 10;
}

.analysis-box.collapsed .analysis-collapse-btn:hover {
  opacity: 1;
  background: rgba(255,255,255,0.22);
  border-color: #fff;
}

.analysis-box.collapsed .analysis-collapse-btn i {
  font-size: 1rem;
}
.analysis-box.collapsed .analysis-collapse-btn {
  box-shadow: 0 0 0 1px rgba(255,255,255,0.15);
}
/* ===============================
   ANALYSIS — COLLAPSE BUTTON (ALL STATES)
   =============================== */

/* panel IP jako punkt odniesienia */
.analysis-panel-ip {
  position: relative;
}

/* przycisk — domyślnie (ROZWINIĘTY) */
.analysis-collapse-btn {
  
  top: 6px;
  right: 8px;

  padding: 4px 6px;
  border-radius: 6px;

  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.25);
  color: #eee;

  opacity: 0.65;
  z-index: 10;
}

/* hover — zawsze */
.analysis-collapse-btn:hover {
  opacity: 1;
  background: rgba(255,255,255,0.18);
  border-color: #fff;
}

/* ===============================
   COLLAPSED — lekko wzmocniony
   =============================== */

.analysis-box.collapsed .analysis-collapse-btn {
  background: rgba(255,255,255,0.18);
  border-color: rgba(255,255,255,0.45);
  opacity: 0.9;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.15);
}

/* ===============================
   ANALYSIS — COLLAPSE BUTTON (FINAL)
   =============================== */

/* kontener przycisków */
.analysis-actions-inline {
  display: flex;
  align-items: center;
  gap: .25rem;
}

/* przycisk collapse — ZAWSZE POD TABELKĄ */
.analysis-collapse-btn {
  margin-left: auto;            /* ⬅️ wypycha w prawo */
  padding: 4px 6px;
  border-radius: 6px;

  background: rgba(255,255,255,0.10);
  border-color: rgba(255,255,255,0.30);
  color: #eee;

  opacity: 0.75;
}

/* hover */
.analysis-collapse-btn:hover {
  opacity: 1;
  background: rgba(255,255,255,0.20);
  border-color: #fff;
}

/* collapsed — lekko wzmocniony */
.analysis-box.collapsed .analysis-collapse-btn {
  background: rgba(255,255,255,0.18);
  border-color: rgba(255,255,255,0.45);
  box-shadow: 0 0 0 1px rgba(255,255,255,0.15);
}

  
  
  /* Error State for IP field */
  .analysis-ip.error {
    color: #dc3545 !important;
  }
`
  }

  //  1. Dedykowany cache
  const fullAnalysisCache = new Map();

  //  2. Funkcja renderująca (HTML Update)
// W funkcji renderAnalysisIntoRow() (~linia 630) dodaj:
function renderAnalysisIntoRow(analysisRowEl, data) {
  if (!analysisRowEl) return;

  // A) IP / GEO - BRAK DANYCH
  const ipTd = analysisRowEl.querySelector('.analysis-ip');
  if (ipTd) {
    if (data.ip) {
      ipTd.classList.remove('analysis-loading');
      ipTd.textContent = data.ip;
      ipTd.removeAttribute('data-empty');
	  
	  //  AKTYWACJA PRZYCSKU "RELATED IP"
const ipBtn = analysisRowEl.querySelector('.google-related-ip');
if (ipBtn && data.ip) {
  ipBtn.dataset.ip = data.ip;   // ⬅️ ustaw IP
  ipBtn.disabled = false;       // ⬅️ odblokuj
  ipBtn.classList.remove('btn-outline-secondary');
  ipBtn.classList.add('btn-outline-primary');
}

	  
    } else {
      ipTd.classList.remove('analysis-loading');
      ipTd.innerHTML = '<span class="text-muted fst-italic">no data</span>';
    }
  }

  // Location Info - BRAK DANYCH
  const loc = data.location || {};
  const countryCell = analysisRowEl.querySelector('.analysis-country');
  const regionCell = analysisRowEl.querySelector('.analysis-region');
  const cityCell = analysisRowEl.querySelector('.analysis-city');
  const ispCell = analysisRowEl.querySelector('.analysis-isp');
  
  if (countryCell) countryCell.textContent = loc.country || '—';
  if (regionCell) regionCell.textContent = loc.region || '—';
  if (cityCell) cityCell.textContent = loc.city || '—';
  if (ispCell) ispCell.textContent = loc.isp || '—';

  // B) Helper do renderowania listy linków - BRAK DANYCH
  const renderLinkList = (list, containerClass, countClass) => {
    const listEl = analysisRowEl.querySelector(containerClass);
    const countEl = analysisRowEl.querySelector(countClass);

    if (listEl && Array.isArray(list)) {
      if (countEl) countEl.textContent = list.length;

      if (list.length === 0) {
        listEl.innerHTML = '<div class="text-muted fst-italic">no links</div>';
      } else {
        listEl.innerHTML = list
          .slice(0, 50)
          .map(h => {
            let d = '';
            try { d = new URL(h).hostname; } catch(e){}
            const fav = d
              ? `https://www.google.com/s2/favicons?sz=16&domain=${d}`
              : '';

			return `
			  <div class="analysis-link small mb-1">
				<a
				  href="${h}"
				  target="_blank"
				  rel="noopener"
				  class="text-truncate d-inline-flex align-items-center gap-1"
				  style="max-width: 90%;"
				>
				  ${fav ? `<img src="${fav}" class="analysis-favicon" width="16" height="16" alt="" onerror="handleFaviconError(this)">` : ''}
				  <span>${h}</span>
				</a>
			  </div>
			`;
          })
          .join('');
      }
    }
  };

  renderLinkList(data.internal_links || [], '.analysis-home-list', '.analysis-home-count');
  renderLinkList(data.external_links || [], '.analysis-external-list', '.analysis-external-count');
}


  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.analyze-btn');
    if (!btn) return;

    e.preventDefault();
    e.stopPropagation();

    const tr = btn.closest('tr');
    if (!tr) return;

    const domain = (btn.dataset.domain || '').trim();
    if (!domain) return;

    const isOpen = btn.dataset.open === '1';

    if (isOpen) {
      const next = tr.nextElementSibling;
      if (next && next.classList.contains('analysis-row')) next.remove();
      btn.dataset.open = '0';
      const icon = btn.querySelector('i');
      if (icon) {
        icon.classList.remove('bi-chevron-up');
        icon.classList.add('bi-chevron-down');
      }
      return;
    }

    closeAllFastAnalyses();

    btn.dataset.open = '1';
    const icon = btn.querySelector('i');
    if (icon) {
      icon.classList.remove('bi-chevron-down');
      icon.classList.add('bi-chevron-up');
    }

    const analysisRow = document.createElement('tr');
    analysisRow.className = 'analysis-row';
analysisRow.innerHTML = `
  <td colspan="6">
    <div class="analysis-box p-2 collapsed"></div>
  </td>
`;
    
tr.after(analysisRow);

requestAnimationFrame(() => {
  const rect = tr.getBoundingClientRect();
  const absoluteTop = rect.top + window.pageYOffset;

  window.scrollTo({
    top: absoluteTop,
    behavior: "instant"
  });
});
    const box = analysisRow.querySelector('.analysis-box');
    if (!box) return;

    // ⬇️ SZKIELET + NOWY BUTTON COLLAPSE
box.insertAdjacentHTML('afterbegin', `
<div class="analysis-grid">
  <div class="analysis-panel analysis-panel-ip">
    <div class="analysis-panel-h">
      IP / GEO
      <!--  TU POJAWI SIĘ analysis-global-error W PRZYPADKU BŁĘDU -->
    </div>
    <div class="analysis-panel-b">
      <table class="table table-sm table-bordered mb-2">
        <tbody>
          <tr>
            <th style="width:130px;">IP</th>
            <td class="analysis-ip analysis-loading" data-empty="1">
              <span class="analysis-spinner me-1"></span> Connection attempt…
            </td>
          </tr>
          <tr><th>Country</th><td class="analysis-country">—</td></tr>
          <tr><th>Region</th><td class="analysis-region">—</td></tr>
          <tr><th>City</th><td class="analysis-city">—</td></tr>
          <tr><th>ISP</th><td class="analysis-isp">—</td></tr>
        </tbody>
      </table>
      <div class="analysis-actions-inline">
        <button type="button" class="btn btn-sm btn-outline-primary google-related-domain d-inline-flex align-items-center gap-1" title="Search related:domain"><i class="bi bi-google"></i> Related <i class="bi bi-arrow-up-right"></i></button>
        <button type="button" class="btn btn-sm btn-outline-secondary google-related-ip d-inline-flex align-items-center gap-1" disabled data-ip="" title="Search IP"><i class="bi bi-google"></i> Related IP <i class="bi bi-arrow-up-right"></i></button>
        <button type="button" class="btn btn-sm btn-outline-dark analysis-collapse-btn" title="Expand">
          <i class="bi bi-arrows-collapse"></i>
        </button>
      </div>
    </div>
  </div>

  <div class="analysis-panel analysis-panel-links">
    <div class="analysis-panel-h">LINKS — HOME <span class="analysis-count analysis-home-count">—</span></div>
    <div class="analysis-panel-b analysis-links-list analysis-home-list">—</div>
  </div>

  <div class="analysis-panel analysis-panel-links">
    <div class="analysis-panel-h">LINKS — EXTERNAL <span class="analysis-count analysis-external-count">—</span></div>
    <div class="analysis-panel-b analysis-links-list analysis-external-list">—</div>
  </div>
</div>
`);
// =========================================================
//  LOGIKA CACHE-FIRST + ERROR HANDLING
// =========================================================
const analysisRowEl = tr.nextElementSibling;
if (analysisRowEl && domain) {
  const cacheKey = domain;

  if (fullAnalysisCache.has(cacheKey)) {
    const data = fullAnalysisCache.get(cacheKey);
    renderAnalysisIntoRow(analysisRowEl, data);
    return;
  }

  const infoTimer = setTimeout(() => {
    const ipTd = analysisRowEl.querySelector('.analysis-ip');
    if (ipTd && ipTd.dataset.empty === '1') {
      ipTd.innerHTML = `<span class="analysis-spinner me-1"></span> Connecting to server…`;
    }
  }, 10000);

	  fetch(
	  `/api/analyze?url=${encodeURIComponent(`https://${domain}`)}`,
	  { signal: FAST_API_ABORT.signal }
	)
    .then(r => {
      if (!r.ok) throw new Error('Fetch failed');
      return r.json();
    })
    .then(data => {
      setLimitedCache(fullAnalysisCache, cacheKey, data);
      renderAnalysisIntoRow(analysisRowEl, data);
    })
	.catch(err => {

	  if (err.name === "AbortError") {
		
		return;
	  }

	  console.warn('[ANALYSIS] Connection error:', err);
      
      //  GLOBALNY STATUS BŁĘDU POŁĄCZENIA
      const panelHeader = analysisRowEl.querySelector('.analysis-panel-h');
      if (panelHeader) {
        // Sprawdź czy już nie ma statusu
        if (!panelHeader.querySelector('.analysis-global-error')) {
          const errorSpan = document.createElement('span');
          errorSpan.className = 'analysis-global-error';
          errorSpan.textContent = 'brak połączenia';
          panelHeader.appendChild(errorSpan);
        }
      }
      
      //  IP - SPECJALNY STATUS
      const ipTd = analysisRowEl.querySelector('.analysis-ip');
      if (ipTd) {
        ipTd.classList.remove('analysis-loading');
        ipTd.classList.add('error');
        ipTd.innerHTML = '<span class="text-danger"> błąd połączenia</span>';
      }
      
      //  Reszta pól zostaje "—" (już jest domyślnie)
      const homeList = analysisRowEl.querySelector('.analysis-home-list');
      const extList = analysisRowEl.querySelector('.analysis-external-list');
      if (homeList) homeList.innerHTML = '—';
      if (extList) extList.innerHTML = '—';
    })
    .finally(() => {
      clearTimeout(infoTimer);
    });
}
  }, true);

})();
function resetAllStatusBadges() {
  document.querySelectorAll('.status-cell[data-domain]').forEach(cell => {
    cell.innerHTML = `<span class="badge bg-secondary">—</span>`;
  });
}

function shutdownFastAPI() {
  

  if (window.__AUTO_FAST_API) {
    window.__AUTO_FAST_API.markAsRan();
  }

  API_FAST_ENABLED = false;
  ApiGate.cancelAll();
  syncApiButtons();

  
}

// ─────────────────────────────────────────────
// API TOGGLE BUTTONS (TOP + BOTTOM)
// ─────────────────────────────────────────────
function syncApiButtons() {
  document.querySelectorAll('.api-toggle-btn').forEach(btn => {
    if (API_FAST_ENABLED) {
      btn.textContent = 'API: ON';
      btn.classList.remove('btn-outline-danger');
      btn.classList.add('btn-outline-success');
    } else {
      btn.textContent = 'API: OFF';
      btn.classList.remove('btn-outline-success');
      btn.classList.add('btn-outline-danger');
    }
  });
}
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.api-toggle-btn');
  if (!btn) return;

  API_FAST_ENABLED = !API_FAST_ENABLED;

  if (API_FAST_ENABLED) {
    
    const tbody = document.querySelector('#fastTable tbody');
    if (tbody) {
      API_FAST_TOTAL = tbody.querySelectorAll('[data-domain]').length;
      API_FAST_DONE = 0;
      

      idle(() => {
        setTimeout(() => {
          // ✅ Przekaż aktualną generację
          refreshVisibleTitleStatus(tbody, CURRENT_GENERATION);
        }, 300);
      });
    }
  } else {
    
    ApiGate.cancelAll();
  }

  syncApiButtons();
});


// =========================================================
// ANALYSIS — GOOGLE RELATED (DOMAIN)
// =========================================================
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.google-related-domain');
  if (!btn) return;

  e.preventDefault();
  e.stopPropagation();

  // znajdź wiersz analizy
  const analysisRow = btn.closest('.analysis-row');
  if (!analysisRow) return;

  // wiersz domeny jest TUŻ NAD analizą
  const domainRow = analysisRow.previousElementSibling;
  if (!domainRow) return;

  const domain = (domainRow.dataset.domain || '').trim();
  if (!domain) return;

  const url = `https://www.google.com/search?q=related:${domain}`;
  window.open(url, '_blank', 'noopener');
});

// =========================================================
// ANALYSIS — COLLAPSE / EXPAND (UI ONLY)
// =========================================================
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.analysis-collapse-btn');
  if (!btn) return;

  e.preventDefault();
  e.stopPropagation();

  const analysisBox = btn.closest('.analysis-box');
  if (!analysisBox) return;

  // Toggle klasy CSS (robi całą magię)
const collapsed = analysisBox.classList.toggle('collapsed');

//  WYMUSZENIE PRZELICZENIA SCROLL LOCK
if (window.__FAST_SCROLL_LOCK__) {
  requestAnimationFrame(() => {
    window.__FAST_SCROLL_LOCK__.applyScrollState();
  });
}

//  KOREKTA SCROLLA JEŚLI STRONA SIĘ SKRÓCIŁA
requestAnimationFrame(() => {
  const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
  if (window.scrollY > maxScroll) {
    window.scrollTo({
      top: maxScroll,
      behavior: "instant"
    });
  }
});


  
  // Zmiana ikony i tytułu
  const icon = btn.querySelector('i');
  if (icon) {
    if (collapsed) {
        icon.classList.remove('bi-arrows-collapse');
        icon.classList.add('bi-arrows-expand');
        btn.title = "Expand";
    } else {
        icon.classList.remove('bi-arrows-expand');
        icon.classList.add('bi-arrows-collapse');
        btn.title = "Collapse";
    }
  }
});

// =========================================================
// ANALYSIS — GOOGLE RELATED (IP)
// =========================================================
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.google-related-ip');
  if (!btn) return;


  e.preventDefault();
  e.stopPropagation();

  const ip = (btn.dataset.ip || '').trim();
  if (!ip) return;

  const url = `https://www.google.com/search?q=${ip}`;
  window.open(url, '_blank', 'noopener');
});


initFastTable();

// ─────────────────────────────────────────────
// VISIBILITY / FOCUS — UI REFRESH ONLY
// Nie przerywamy aktywnego fetch.
// ─────────────────────────────────────────────
document.addEventListener("visibilitychange", () => {


  if (document.hidden) return;

  suppressAutoFast(1500);

  requestAnimationFrame(() => {
    window.__FAST_SCROLL_LOCK__?.startObservers?.();
    window.__FAST_SCROLL_LOCK__?.applyScrollState?.();
    window.dispatchEvent(new Event("resize"));
  });
});

window.addEventListener("focus", () => {
  suppressAutoFast(1500);

  requestAnimationFrame(() => {
    window.__FAST_SCROLL_LOCK__?.startObservers?.();
    window.__FAST_SCROLL_LOCK__?.applyScrollState?.();
  });
});
// =========================================================
//  AUTO FAST ON — po 500ms bezczynności (INTELIGENTNY)
// =========================================================
(function autoFastAfterIdle() {
  let timer = null;

  let FAST_ALREADY_RAN = false;

  function isPagerInteractionTarget(el) {
    return !!el?.closest?.(
      '[data-pager], [data-role="page-prev"], [data-role="page-next"], [data-role="page-go"], [data-role="page-input"], #per_page, select[name="per_page"]'
    );
  }

  function arm(ev) {
    if (!FAST_AUTO_MODE) return;
    if (IS_PAGE_LOADING || isSwitching) return;
    if (Date.now() < AUTO_FAST_SUPPRESS_UNTIL) return;
    if (FAST_ALREADY_RAN && !API_FAST_ENABLED) return;

    // ❌ nie uzbrajaj auto-API od ruchu związanego z paginacją
    if (ev && isPagerInteractionTarget(ev.target)) return;

    clearTimeout(timer);

    timer = setTimeout(() => {
      if (!FAST_AUTO_MODE) return;
      if (IS_PAGE_LOADING || isSwitching) return;
      if (Date.now() < AUTO_FAST_SUPPRESS_UNTIL) return;
      if (API_FAST_ENABLED || FAST_ALREADY_RAN) return;

      const active = document.activeElement;
      if (isPagerInteractionTarget(active)) return;

      const tbody = document.querySelector('#fastTable tbody');
      if (!tbody) return;

      

      API_FAST_ENABLED = true;
      API_FAST_DONE = 0;
      API_FAST_TOTAL = tbody.querySelectorAll('[data-domain]').length;

      syncApiButtons();

      setTimeout(() => {
        if (
          !isSwitching &&
          !IS_PAGE_LOADING &&
          API_FAST_ENABLED &&
          !FAST_ALREADY_RAN &&
          Date.now() >= AUTO_FAST_SUPPRESS_UNTIL
        ) {
          requestAnimationFrame(() => {
            refreshVisibleTitleStatus(tbody, CURRENT_GENERATION);
          });
        }
      }, 400);
    }, 900);
  }

  function resetForNewPage() {
    
    FAST_ALREADY_RAN = false;
    clearTimeout(timer);
  }

  // ✅ usuwamy mousemove, bo to on najczęściej odpalał konflikt przed kliknięciem
  ['keydown', 'wheel', 'touchstart', 'pointerdown'].forEach(evt => {
    document.addEventListener(evt, arm, { passive: true });
  });

  document.addEventListener('fastTable:tbodyReplaced', resetForNewPage);

  window.__AUTO_FAST_API = {
    markAsRan: function() {
      FAST_ALREADY_RAN = true;
      
    },
    resetForNewPage: resetForNewPage
  };
})();

// cache nazw krajów (wydajność)
const _countryNameCache = {};

function countryLabelForTld(tld) {
  tld = String(tld || "").toLowerCase();
  if (_countryNameCache[tld]) return _countryNameCache[tld];

  try {
    const locale = navigator.language || "en";
    const dn = new Intl.DisplayNames([locale], { type: "region" });

    let label;
    if (tld === "uk") label = dn.of("GB");       // .uk → United Kingdom
    else if (tld === "eu") label = dn.of("EU"); // .eu
    else if (/^[a-z]{2}$/.test(tld)) label = dn.of(tld.toUpperCase());
    else label = tld.toUpperCase();

    _countryNameCache[tld] = label || tld.toUpperCase();
    return _countryNameCache[tld];
  } catch (e) {
    return tld.toUpperCase();
  }
}


// ─────────────────────────────────────────────
// COUNTRY DROPDOWN (prefix stats)
// ─────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  const dd = document.getElementById("prefixDropdown");
  const menu = document.getElementById("prefixMenu");

  if (!dd || !menu) return;

	const snapshot = dd.dataset.snapshot || "202601";

  fetch(`/api/prefix_stats?snapshot=${snapshot}`)
    .then(r => r.json())
    .then(data => {
      const entries = Object.entries(data)
        .sort((a, b) => b[1] - a[1]);

      if (!entries.length) {
        menu.innerHTML = `<li class="px-3 py-1 text-muted">Empty</li>`;
        return;
      }

      // zachowaj aktualne parametry URL
      const params = new URLSearchParams(window.location.search);

      menu.innerHTML = entries.map(([cc, count]) => {
        let tld = String(cc).toLowerCase();

tld = tld
  .replace(/[\u0000-\u001F\u007F]/g, '')
  .replace(/[^a-z0-9]/gi, '')
  .trim();
        let flagCode = tld === "uk" ? "gb" : tld;

//  CRITICAL FIX — usuń wszystkie niedozwolone znaki CSS selector
flagCode = String(flagCode)
  .replace(/[^a-z0-9\-]/gi, '')
  .trim();

        params.set("q", `.${tld}`);
        params.set("page", "1");

        return `
          <li>
            <a class="dropdown-item d-flex justify-content-between align-items-center"
               href="?${params.toString()}">
              <span>
                <span class="fi fi-${flagCode} me-2"
                      data-bs-toggle="tooltip"
                      title="${countryLabelForTld(tld)}"></span>
                .${tld}
              </span>
              <span class="badge bg-secondary ms-2">${count}</span>
            </a>
          </li>`;
      }).join("");

      //  AKTYWACJA TOOLTIPÓW (KLUCZOWE)
      const tooltipTriggerList = menu.querySelectorAll('[data-bs-toggle="tooltip"]');
      tooltipTriggerList.forEach(el => {
        //new bootstrap.Tooltip(el);
      });
    })
    .catch(err => {
      console.error("prefix_stats error", err);
      menu.innerHTML = `<li class="px-3 py-1 text-danger">Error</li>`;
    });
});

// ─────────────────────────────────────────────
// TOP NAMES — GLOBAL (all tables)
// source: word_counts_global_rank.csv
// ─────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("globalWordsDropdownContainer");
  const menu = document.getElementById("globalWordsDropdownMenu");
  const btn = document.getElementById("globalWordDropdownBtn");

  if (!container || !menu || !btn) return;

  const baseUrl = container.dataset.baseUrl || "/top_sites_fast";
  const csvUrl = "/static/csv/word_counts_global_rank.csv";

  fetch(csvUrl)
    .then(r => {
      if (!r.ok) throw new Error("global word csv fetch failed");
      return r.text();
    })
    .then(text => {
      const lines = text.split(/\r?\n/).filter(Boolean);
      if (lines.length <= 1) {
        menu.innerHTML = `<li class="px-3 py-1 text-muted">Empty</li>`;
        return;
      }

      const rows = [];
      for (let i = 1; i < lines.length; i++) {
        const [word, totalCount, months] = lines[i].split(",");
        if (!word) continue;
        rows.push({
          word: word.trim(),
          months: parseInt(months || "0", 10) || 0
        });
      }

      // sort DESC by months
      rows.sort((a, b) => b.months - a.months);

      // infinite-like chunk (jak było)
      const chunkSize = 500;
      let loaded = 0;

      menu.innerHTML = "";

      function loadChunk() {
        const slice = rows.slice(loaded, loaded + chunkSize);
        slice.forEach((r, i) => {
          const params = new URLSearchParams(window.location.search);
          params.set("q", r.word);
          params.set("page", "1");

          const li = document.createElement("li");
          li.innerHTML = `
            <a class="dropdown-item d-flex justify-content-between align-items-center"
               href="${baseUrl}?${params.toString()}">
              <span class="text-truncate" style="max-width:200px"
                    title="${r.word}">
                ${r.word}
              </span>
              <span class="badge bg-secondary ms-2"
                    title="Months present">
                ${r.months}
              </span>
            </a>`;
          menu.appendChild(li);
        });
        loaded += slice.length;
      }

      loadChunk();

      menu.addEventListener("scroll", () => {
        if (
          menu.scrollTop + menu.clientHeight >= menu.scrollHeight - 10 &&
          loaded < rows.length
        ) {
          loadChunk();
        }
      });

      btn.textContent = "Select";
    })
    .catch(err => {
      console.error("Global words dropdown error:", err);
      menu.innerHTML = `<li class="px-3 py-1 text-danger">Error</li>`;
    });
});

// ─────────────────────────────────────────────
// CATEGORIES DROPDOWN (CSV + SAFE SUBMENU)
// ─────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const menu = document.getElementById("categoriesDropdownMenu");
  if (!menu) return;

  fetch("/static/csv/categories.csv")
    .then(r => r.text())
    .then(txt => {
      // Parsowanie CSV: MainCategory, Sub1, Sub2...
      const rows = txt.trim().split(/\r?\n/).slice(1);
      const tree = {};

      rows.forEach(line => {
        // splitowanie po przecinku
        const parts = line.split(",");
        const main = parts[0].trim();
        // reszta to subkategorie
        const subs = parts.slice(1).map(s => s.trim()).filter(Boolean);

        if (main) {
           tree[main] = subs;
        }
      });

      // Budowanie HTML
      menu.innerHTML = Object.entries(tree).map(([main, subs]) => {
        // Jeśli nie ma podkategorii - zwykły link
        if (!subs || subs.length === 0) {
          return `<li><a class="dropdown-item" href="?q=${main}">${main}</a></li>`;
        }

        // Jeśli są podkategorie - submenu
        // Dodano: class="dropdown-toggle" i href="#"
        return `
          <li class="dropdown-submenu">
            <a class="dropdown-item dropdown-toggle d-flex justify-content-between align-items-center" href="#">
              ${main}
            </a>
            <ul class="dropdown-menu dropdown-menu-dark">
              ${subs.map(s => `
                  <li><a class="dropdown-item" href="?q=${s}">${s}</a></li>
              `).join("")}
            </ul>
          </li>`;
      }).join("");

      // Uruchomienie "Inteligentnego pozycjonowania" (żeby nie uciekało za ekran w prawo)
      
    })
    .catch(err => {
      console.error("categories error", err);
      menu.innerHTML = `<li class="px-3 py-1 text-danger">Error</li>`;
    });
});

// =====================================================
// BLOCK: middle-click / ctrl-click opening new tab in dropdowns
// =====================================================
(function blockDropdownNewTabOpen() {

  function isInsideDropdown(el) {
    return !!el.closest('.dropdown-menu, .dropdown-item, .dropdown');
  }

  // 1) Middle click (wheel click) – największy problem
  document.addEventListener('auxclick', function (e) {
    if (e.button !== 1) return;                 // tylko środkowy
    if (!isInsideDropdown(e.target)) return;    // tylko dropdowny
    e.preventDefault();
    e.stopPropagation();
  }, true);

  // 2) Czasem przeglądarka reaguje już na mousedown
  document.addEventListener('mousedown', function (e) {
    if (e.button !== 1) return;
    if (!isInsideDropdown(e.target)) return;
    e.preventDefault();
    e.stopPropagation();
  }, true);

  // 3) Ctrl+klik / Cmd+klik (też otwiera nową kartę) – opcjonalnie blokujemy w dropdownach
  document.addEventListener('click', function (e) {
    if (!isInsideDropdown(e.target)) return;
    if (!(e.ctrlKey || e.metaKey)) return;      // ctrl / cmd
    // jeśli kliknięto w link dropdowna
    const a = e.target.closest('a.dropdown-item, .dropdown-menu a');
    if (!a) return;
    e.preventDefault();
    e.stopPropagation();
  }, true);

})();

// Zarządzanie scrollem strony - FINALNA WERSJA
(function() {
  let isLocked = false;
  let rafPending = false;

function lockScroll() {
  if (isLocked) return;
  document.body.classList.add('no-scroll');
  isLocked = true;
}
  function unlockScroll() {
    if (!isLocked) return;
    document.body.classList.remove('no-scroll');
    isLocked = false;
  }

  //  logika: jeśli jest rozwinięta analiza LUB content wyższy niż viewport → odblokuj
function shouldUnlock() {
  return true;
}
  //  POPRAWIONY GUARD - niezależne warunki dla obu przejść
  function applyScrollState() {
    if (IS_PAGE_LOADING || isSwitching) return;

    const wantUnlock = shouldUnlock();

    if (wantUnlock && isLocked) {
      unlockScroll();
    }

    if (!wantUnlock && !isLocked) {
      lockScroll();
    }
  }

  // 🎬 Debounce przez requestAnimationFrame (1 klatka)
  function applyScrollStateDebounced() {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(() => {
      rafPending = false;
      applyScrollState();
    });
  }

  // ── Automaty: MutationObserver + ResizeObserver ──

let mo = null;
let ro = null;

function startObservers() {
  if (mo || ro) return;

  const fastTable = document.querySelector('#fastTable');
  if (!fastTable) return;

  mo = new MutationObserver(() => applyScrollStateDebounced());
  mo.observe(fastTable, { childList: true, subtree: true });

  ro = new ResizeObserver(() => applyScrollStateDebounced());
  ro.observe(document.body);
}

function stopObservers() {
  if (mo) {
    mo.disconnect();
    mo = null;
  }
  if (ro) {
    ro.disconnect();
    ro = null;
  }
}

  // 3) resize okna
  window.addEventListener('resize', applyScrollStateDebounced);

  //  POPRAWIONY START - używamy debounced wersji
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    startObservers();
    applyScrollStateDebounced();
  }, { once: true });
} else {
  startObservers();
  applyScrollStateDebounced();
}

  // ręczny dostęp + kontrola observerów
  window.__FAST_SCROLL_LOCK__ = {
    lockScroll,
    unlockScroll,
    applyScrollState,
    startObservers,
    stopObservers
  };
})();

window.addEventListener("load", () => {
  // adjustOverflow disabled – natural DOM height
});

// Layout stabilization (prevents rare render glitches)
window.addEventListener("load", () => {
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      window.dispatchEvent(new Event("resize"));
    });
  });
});

window.addEventListener('load', () => {

  setTimeout(()=>{
    refreshChevronIcons();
  }, 60);

});



