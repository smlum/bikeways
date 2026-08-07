const STORAGE_KEY = "streetview-review:v1";

let manifest = null;
let reviews = {};
let currentGroupIndex = 0;
let filterText = "";
let selectedMunicipality = "";

// The first group_by column is treated as the primary "which place" level for the
// dropdown; remaining columns (e.g. source_class) are what the sidebar list filters/shows.
function primaryCol() {
  return manifest.group_by[0];
}

function loadReviews() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function saveReviews() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reviews));
}

function groupTitle(group) {
  return manifest.group_by.map((col) => group[col]).join(" / ");
}

function secondaryTitle(group) {
  return manifest.group_by.slice(1).map((col) => group[col]).join(" / ");
}

function streetViewUrl(sample) {
  const params = new URLSearchParams({
    api: "1",
    map_action: "pano",
    viewpoint: `${sample.lat},${sample.lng}`,
    heading: sample.heading,
    pitch: "0",
    fov: "80",
  });
  return `https://www.google.com/maps/@?${params.toString()}`;
}

function sampleKey(group, sampleIndex) {
  const sample = group.samples[sampleIndex];
  const groupKey = manifest.group_by.map((col) => group[col]).join("||");
  return `${groupKey}||${sample.id ?? sampleIndex}`;
}

function groupProgress(group) {
  const total = group.samples.length;
  const done = group.samples.filter((_, i) => reviews[sampleKey(group, i)]?.verdict).length;
  return { done, total };
}

function visibleGroupIndices() {
  const needle = filterText.trim().toLowerCase();
  const col = primaryCol();
  return manifest.groups
    .map((group, i) => ({ group, i }))
    .filter(({ group }) => !selectedMunicipality || group[col] === selectedMunicipality)
    .filter(({ group }) => !needle || `${secondaryTitle(group)} ${group.label ?? ""}`.toLowerCase().includes(needle))
    .sort((a, b) => b.group.length_km - a.group.length_km)
    .map(({ i }) => i);
}

function populateMunicipalitySelect() {
  const col = primaryCol();
  const values = [...new Set(manifest.groups.map((g) => g[col]))].sort();
  const select = document.getElementById("municipality-select");
  select.innerHTML = values.map((v) => `<option value="${v}">${v}</option>`).join("");
  selectedMunicipality = values[0] ?? "";
  select.value = selectedMunicipality;
  select.addEventListener("change", (e) => {
    selectedMunicipality = e.target.value;
    renderSidebar();
    const first = visibleGroupIndices()[0];
    if (first !== undefined) selectGroup(first);
  });
}

async function init() {
  const res = await fetch("manifest.json");
  manifest = await res.json();
  reviews = loadReviews();

  populateMunicipalitySelect();

  document.getElementById("filter-box").addEventListener("input", (e) => {
    filterText = e.target.value;
    renderSidebar();
  });
  document.getElementById("export-btn").addEventListener("click", exportReviews);

  renderSidebar();
  const first = visibleGroupIndices()[0] ?? 0;
  selectGroup(first);
  updateOverallProgress();
}

function renderSidebar() {
  const list = document.getElementById("group-list");
  list.innerHTML = "";
  visibleGroupIndices().forEach((i) => {
    const group = manifest.groups[i];
    const { done, total } = groupProgress(group);
    const li = document.createElement("li");
    li.className = "group-item" + (done === total ? " done" : "");
    li.textContent = `${secondaryTitle(group)} (${group.label ?? "?"}) — ${group.length_km} km — ${done}/${total}`;
    li.dataset.index = i;
    li.addEventListener("click", () => selectGroup(i));
    list.appendChild(li);
  });
  highlightSelected();
}

function highlightSelected() {
  document.querySelectorAll(".group-item").forEach((li) => {
    li.classList.toggle("selected", Number(li.dataset.index) === currentGroupIndex);
  });
}

function loadPanorama(panoDiv, sample, key, card) {
  panoDiv.innerHTML = '<div class="no-pano">Loading…</div>';
  const svService = new google.maps.StreetViewService();
  svService.getPanorama(
    { location: { lat: sample.lat, lng: sample.lng }, radius: 50 },
    (data, status) => {
      if (status === "OK") {
        panoDiv.innerHTML = "";
        new google.maps.StreetViewPanorama(panoDiv, {
          pano: data.location.pano,
          pov: { heading: sample.heading, pitch: 0 },
          zoom: 1,
          addressControl: false,
          fullscreenControl: false,
        });
      } else {
        panoDiv.innerHTML = '<div class="no-pano">No Street View imagery within 50m of this point.</div>';
        if (!reviews[key]?.verdict) {
          setReview(key, { verdict: "no_imagery", note: reviews[key]?.note });
          card.querySelectorAll("button[data-v]").forEach((b) => b.classList.toggle("active", b.dataset.v === "no_imagery"));
        }
      }
    }
  );
}

function renderSampleCard(group, i) {
  const sample = group.samples[i];
  const key = sampleKey(group, i);
  const saved = reviews[key] || {};
  const spares = group.spare_samples || [];

  const card = document.createElement("div");
  card.className = "sample-card";
  card.innerHTML = `
    <div class="pano-header">
      <span>Sample ${i + 1}</span>
      <button type="button" class="refresh-btn">⟳ Try another point</button>
    </div>
    <div class="pano" id="pano-${i}"></div>
    <div class="verdicts">
      <button data-v="correct" class="${saved.verdict === "correct" ? "active" : ""}">Correct</button>
      <button data-v="incorrect" class="${saved.verdict === "incorrect" ? "active" : ""}">Incorrect</button>
      <button data-v="unsure" class="${saved.verdict === "unsure" ? "active" : ""}">Unsure</button>
      <button data-v="no_imagery" class="${saved.verdict === "no_imagery" ? "active" : ""}">No imagery</button>
    </div>
    <input type="text" class="note" placeholder="note (optional)" />
    <div class="coords">
      ${sample.lat.toFixed(6)}, ${sample.lng.toFixed(6)}
      &nbsp;·&nbsp;<a href="${streetViewUrl(sample)}" target="_blank" rel="noopener">Open in Google Maps ↗</a>
    </div>
  `;

  const noteInput = card.querySelector(".note");
  noteInput.value = saved.note || "";
  noteInput.addEventListener("input", (e) => {
    setReview(key, { verdict: reviews[key]?.verdict, note: e.target.value });
  });

  card.querySelectorAll("button[data-v]").forEach((btn) => {
    btn.addEventListener("click", () => {
      card.querySelectorAll("button[data-v]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      setReview(key, { verdict: btn.dataset.v, note: reviews[key]?.note });
    });
  });

  const refreshBtn = card.querySelector(".refresh-btn");
  if (spares.length === 0) {
    refreshBtn.disabled = true;
    refreshBtn.title = "No more alternate points for this class — regenerate the manifest for more";
  } else {
    refreshBtn.title = "Discard this point and load a different random one along this class's geometry";
    refreshBtn.addEventListener("click", () => {
      group.samples[i] = spares.shift();
      card.replaceWith(renderSampleCard(group, i));
    });
  }

  loadPanorama(card.querySelector(`#pano-${i}`), sample, key, card);
  return card;
}

function selectGroup(index) {
  currentGroupIndex = index;
  const group = manifest.groups[index];
  document.getElementById("group-header").textContent =
    `${groupTitle(group)} → ${group.label ?? "(no label)"} (n=${group.n_features}, ${group.length_km} km)`;

  const container = document.getElementById("samples");
  container.innerHTML = "";
  group.samples.forEach((_, i) => container.appendChild(renderSampleCard(group, i)));

  highlightSelected();
}

function setReview(key, value) {
  reviews[key] = { ...reviews[key], ...value, updated_at: new Date().toISOString() };
  saveReviews();
  renderSidebar();
  updateOverallProgress();
}

function updateOverallProgress() {
  let doneGroups = 0;
  manifest.groups.forEach((g) => {
    const { done, total } = groupProgress(g);
    if (done === total) doneGroups += 1;
  });
  document.getElementById("overall-progress").textContent =
    `${doneGroups}/${manifest.groups.length} groups fully reviewed`;
}

function exportReviews() {
  const rows = [];
  manifest.groups.forEach((group) => {
    group.samples.forEach((sample, i) => {
      const key = sampleKey(group, i);
      const review = reviews[key];
      const row = {};
      manifest.group_by.forEach((col) => (row[col] = group[col]));
      row.label = group.label;
      row.length_km = group.length_km;
      row.sample_id = sample.id;
      row.lat = sample.lat;
      row.lng = sample.lng;
      row.street_view_url = streetViewUrl(sample);
      row.verdict = review?.verdict ?? null;
      row.note = review?.note ?? "";
      row.updated_at = review?.updated_at ?? null;
      rows.push(row);
    });
  });

  const blob = new Blob([JSON.stringify(rows, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `streetview-reviews-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}

window.initReviewApp = init;

(function loadMapsScript() {
  const script = document.createElement("script");
  script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&callback=initReviewApp`;
  script.async = true;
  document.head.appendChild(script);
})();
