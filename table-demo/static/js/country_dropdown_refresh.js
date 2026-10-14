(() => {
  "use strict";

  let loadedSnapshot = null;
  let requestNumber = 0;

  function getSnapshot() {
    const params = new URLSearchParams(location.search);
    const fromUrl = (params.get("snapshot") || "").trim();

    if (fromUrl) {
      return fromUrl;
    }

    const dropdown =
      document.getElementById("prefixDropdown");

    return (dropdown?.dataset.snapshot || "").trim();
  }

  async function refreshCountryDropdown(snapshot, force = false) {
    const menu =
      document.getElementById("prefixMenu");

    if (!menu || !/^\d{6}$/.test(snapshot)) {
      return;
    }

    if (!force && loadedSnapshot === snapshot) {
      return;
    }

    const thisRequest = ++requestNumber;

    menu.innerHTML =
      `<li class="px-3 py-1 text-muted">Loading…</li>`;

    try {
      const response = await fetch(
        `/api/prefix_stats?snapshot=${encodeURIComponent(snapshot)}`,
        {
          cache: "no-store",
          credentials: "same-origin"
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // Ignorujemy odpowiedź starego miesiąca,
      // jeśli użytkownik zdążył wybrać kolejny.
      if (thisRequest !== requestNumber) {
        return;
      }

      const entries = Object.entries(data)
        .filter(([tld]) => /^[a-z]{2}$/i.test(tld))
        .sort((a, b) => Number(b[1]) - Number(a[1]));

      const params =
        new URLSearchParams(location.search);

      params.set("snapshot", snapshot);
      params.set("page", "1");

      menu.innerHTML = entries.map(([rawTld, count]) => {
        const tld = rawTld.toLowerCase();
        const flagCode = tld === "uk" ? "gb" : tld;
        const countryName = new Intl.DisplayNames(['en'], { type: 'region' })
          .of(flagCode.toUpperCase())
          .replaceAll('&', '&amp;').replaceAll(String.fromCharCode(34), '&quot;')
          .replaceAll('<', '&lt;').replaceAll('>', '&gt;');

        const linkParams =
          new URLSearchParams(params);

        linkParams.set("q", `.${tld}`);

        return `
          <li>
            <a class="dropdown-item d-flex justify-content-between align-items-center"
               href="/top_sites_fast?${linkParams.toString()}">
              <span>
                <span class="fi fi-${flagCode} me-2" title="${countryName}"></span>
                .${tld}
              </span>
              <span class="badge bg-secondary ms-2">${count}</span>
            </a>
          </li>
        `;
      }).join("");

      loadedSnapshot = snapshot;
    } catch (error) {
      console.error("Country refresh error:", error);

      if (thisRequest === requestNumber) {
        menu.innerHTML =
          `<li class="px-3 py-1 text-danger">Error</li>`;
      }
    }
  }

  // Po wyborze innego miesiąca odśwież Country.
  document.addEventListener("click", event => {
    const month =
      event.target.closest("[data-table-snapshot]");

    if (!month) {
      return;
    }

    const snapshot =
      (month.dataset.tableSnapshot || "").trim();

    if (!/^\d{6}$/.test(snapshot)) {
      return;
    }

    loadedSnapshot = null;

    // Pozwalamy najpierw table_fast.js zmienić URL.
    setTimeout(() => {
      refreshCountryDropdown(snapshot, true);
    }, 0);
  });

  // Kontrola przy każdym otwieraniu Country.
  document.addEventListener("click", event => {
    const button = event.target.closest(
      '#prefixDropdown [data-bs-toggle="dropdown"]'
    );

    if (!button) {
      return;
    }

    const snapshot = getSnapshot();

    refreshCountryDropdown(snapshot);
  });

  // NEW: preload Country on page start
  const initialSnapshot = getSnapshot();

  if (/^\d{6}$/.test(initialSnapshot)) {
    refreshCountryDropdown(initialSnapshot);
  }
})();

(() => {
  "use strict";

  let loadedSnapshot = null;
  let requestNumber = 0;

  function getSnapshot() {
    const params = new URLSearchParams(location.search);
    const fromUrl = (params.get("snapshot") || "").trim();

    if (fromUrl) return fromUrl;

    const container =
      document.getElementById("wordsDropdownContainer");

    return (container?.dataset.snapshot || "").trim();
  }

  async function refreshThisWords(snapshot, force = false) {
    const menu = document.getElementById("wordsDropdownMenu");
    const button = document.getElementById("wordDropdownBtn");

    if (!menu || !button || !/^\d{6}$/.test(snapshot)) return;
    if (!force && loadedSnapshot === snapshot) return;

    const thisRequest = ++requestNumber;
    menu.onscroll = null;
    menu.innerHTML =
      `<li class="px-3 py-1 text-muted">Loading…</li>`;

    try {
      const response = await fetch(
        `/static/csv/word_counts_${encodeURIComponent(snapshot)}.csv`,
        { cache: "no-store", credentials: "same-origin" }
      );

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const text = await response.text();
      if (thisRequest !== requestNumber) return;

      const rows = text
        .split(/\r?\n/)
        .slice(1)
        .map(line => {
          const comma = line.lastIndexOf(",");
          if (comma < 1) return null;

          const word = line.slice(0, comma).trim();
          const count = Number.parseInt(line.slice(comma + 1), 10) || 0;
          return word ? [word, count] : null;
        })
        .filter(Boolean)
        .sort((a, b) => b[1] - a[1]);

      menu.replaceChildren();

      let loaded = 0;
      const chunkSize = 150;

      function appendChunk() {
        const end = Math.min(loaded + chunkSize, rows.length);
        const fragment = document.createDocumentFragment();

        for (; loaded < end; loaded += 1) {
          const [word, count] = rows[loaded];
          const params = new URLSearchParams(location.search);

          params.set("snapshot", snapshot);
          params.set("q", word);
          params.set("page", "1");

          const li = document.createElement("li");
          const link = document.createElement("a");
          const label = document.createElement("span");
          const badge = document.createElement("span");

          link.className =
            "dropdown-item d-flex justify-content-between align-items-center";
          link.href = `/top_sites_fast?${params.toString()}`;

          label.className = "text-truncate";
          label.style.maxWidth = "180px";
          label.title = word;
          label.textContent = word;

          badge.className = "badge bg-secondary ms-2";
          badge.textContent = String(count);

          link.append(label, badge);
          li.append(link);
          fragment.append(li);
        }

        menu.append(fragment);
      }

      appendChunk();

      menu.onscroll = () => {
        const nearBottom =
          menu.scrollTop + menu.clientHeight >= menu.scrollHeight - 80;

        if (nearBottom && loaded < rows.length) appendChunk();
      };

      button.textContent = "Select";
      loadedSnapshot = snapshot;
    } catch (error) {
      console.error("Top names (this) refresh error:", error);

      if (thisRequest === requestNumber) {
        menu.innerHTML =
          `<li class="px-3 py-1 text-danger">Error</li>`;
      }
    }
  }

  document.addEventListener("click", event => {
    const month = event.target.closest("[data-table-snapshot]");
    if (!month) return;

    const snapshot =
      (month.dataset.tableSnapshot || "").trim();

    if (!/^\d{6}$/.test(snapshot)) return;

    loadedSnapshot = null;

    setTimeout(() => {
      refreshThisWords(snapshot, true);
    }, 0);
  });

  document.addEventListener("click", event => {
    const button = event.target.closest(
      '#wordsDropdownContainer [data-bs-toggle="dropdown"]'
    );

    if (!button) return;
    refreshThisWords(getSnapshot());
  });
})();
