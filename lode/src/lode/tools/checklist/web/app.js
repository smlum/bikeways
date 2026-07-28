let rows = [];

async function loadRows() {
  const res = await fetch("/api/rows");
  rows = await res.json();
  render();
}

function isDone(row) {
  // A judgment call was made this run — not just that data (e.g. a prior-vintage
  // lead, already-scaffolded source_ids) happens to be sitting in the row.
  return Boolean(row.checked_date) || Boolean(row.checked);
}

function render() {
  const uncheckedOnly = document.getElementById("unchecked-only").checked;
  const body = document.getElementById("rows-body");
  body.innerHTML = "";

  const visible = uncheckedOnly ? rows.filter((r) => !isDone(r)) : rows;
  const doneCount = rows.filter(isDone).length;
  document.getElementById("progress").textContent = `${doneCount} / ${rows.length} checked`;

  for (const row of visible) {
    body.appendChild(renderRow(row));
  }
}

function renderRow(row) {
  const tr = document.createElement("tr");
  tr.className = isDone(row) ? "done" : "";

  const nameTd = document.createElement("td");
  nameTd.innerHTML = `<div class="name">${escapeHtml(row.name)}</div><div class="meta">${row.province} · ${row.geography_level}</div>`;
  tr.appendChild(nameTd);

  const portalTd = document.createElement("td");
  if (row.portal_url) {
    portalTd.innerHTML = `<a class="portal-link" href="${escapeHtml(row.portal_url)}" target="_blank" rel="noopener">${escapeHtml(truncateUrl(row.portal_url))}</a>`;
  } else {
    portalTd.innerHTML = `<span class="meta">no portal known</span>`;
  }
  tr.appendChild(portalTd);

  const urlTd = document.createElement("td");
  if (isDone(row)) {
    urlTd.innerHTML = row.source_url
      ? `<a href="${escapeHtml(row.source_url)}" target="_blank" rel="noopener">${escapeHtml(truncateUrl(row.source_url))}</a>`
      : `<span class="meta">not found</span>`;
  } else {
    if (row.source_url) {
      const lead = document.createElement("div");
      lead.innerHTML = `<a href="${escapeHtml(row.source_url)}" target="_blank" rel="noopener">Open lead ↗</a> <span class="meta">from a prior run — re-verify</span>`;
      urlTd.appendChild(lead);
    }
    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "paste dataset URL or a note";
    input.id = `input-${row.row_index}`;
    input.value = row.source_url || "";
    urlTd.appendChild(input);
  }
  tr.appendChild(urlTd);

  const actionsTd = document.createElement("td");
  if (!isDone(row)) {
    const foundBtn = document.createElement("button");
    foundBtn.className = "found";
    foundBtn.textContent = "Found";
    foundBtn.onclick = () => submitFound(row);
    actionsTd.appendChild(foundBtn);

    const notFoundBtn = document.createElement("button");
    notFoundBtn.className = "not-found";
    notFoundBtn.textContent = "Not found";
    notFoundBtn.onclick = () => submitNotFound(row);
    actionsTd.appendChild(notFoundBtn);

    const errorDiv = document.createElement("div");
    errorDiv.className = "error";
    errorDiv.id = `error-${row.row_index}`;
    actionsTd.appendChild(errorDiv);
  }
  tr.appendChild(actionsTd);

  const notesTd = document.createElement("td");
  const notesInput = document.createElement("input");
  notesInput.type = "text";
  notesInput.className = "notes-input";
  notesInput.placeholder = "notes";
  notesInput.value = row.notes || "";
  notesInput.addEventListener("change", () => saveNote(row.row_index, notesInput.value));
  notesTd.appendChild(notesInput);
  tr.appendChild(notesTd);

  return tr;
}

async function saveNote(rowIndex, notes) {
  const res = await postJson("/api/note", { row_index: rowIndex, notes });
  if (res.ok) {
    const row = rows.find((r) => r.row_index === rowIndex);
    if (row) row.notes = notes;
  }
}

async function submitFound(row) {
  const input = document.getElementById(`input-${row.row_index}`);
  const sourceUrl = input.value.trim();
  const errorDiv = document.getElementById(`error-${row.row_index}`);
  errorDiv.textContent = "";

  if (!sourceUrl) {
    errorDiv.textContent = "Paste a URL first.";
    return;
  }

  const res = await postJson("/api/found", { row_index: row.row_index, source_url: sourceUrl });
  if (!res.ok) {
    errorDiv.textContent = res.error || "Failed";
    return;
  }
  await loadRows();
}

async function submitNotFound(row) {
  const input = document.getElementById(`input-${row.row_index}`);
  const notes = input.value.trim();
  const res = await postJson("/api/not_found", { row_index: row.row_index, notes });
  if (!res.ok) {
    document.getElementById(`error-${row.row_index}`).textContent = res.error || "Failed";
    return;
  }
  await loadRows();
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) return { ok: false, error: data.error };
  return { ok: true, ...data };
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function truncateUrl(url, maxLen = 40) {
  const stripped = url.replace(/^https?:\/\//, "");
  return stripped.length <= maxLen ? stripped : stripped.slice(0, maxLen - 1) + "…";
}

document.getElementById("unchecked-only").addEventListener("change", render);
loadRows();
