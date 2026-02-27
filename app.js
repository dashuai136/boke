const state = {
  allRows: [],
  filteredRows: [],
  xlsxReady: false,
};

const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const libStatus = document.getElementById('libStatus');
const controlsPanel = document.getElementById('controlsPanel');
const summaryPanel = document.getElementById('summaryPanel');
const resultPanel = document.getElementById('resultPanel');
const countryFilter = document.getElementById('countryFilter');
const placementFilter = document.getElementById('placementFilter');
const exportCsvBtn = document.getElementById('exportCsvBtn');
const exportJsonBtn = document.getElementById('exportJsonBtn');
const retryLibBtn = document.getElementById('retryLibBtn');
const resultBody = document.querySelector('#resultTable tbody');
const summary = document.getElementById('summary');

const COUNTRY_HEADERS = ['country', '国家', '国家或地区', 'country/tier'];
const AD_UNIT_HEADERS = ['ad unit', 'adunit', '广告单元', 'ad unit name'];
const ECPM_HEADERS = ['ecpm', '估算每千次展示收入', 'estimated earnings / 1000 impressions'];

const XLSX_CDNS = [
  'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js',
  'https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js',
  'https://unpkg.com/xlsx@0.18.5/dist/xlsx.full.min.js',
  'https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js',
];

fileInput.addEventListener('change', onFileChange);
countryFilter.addEventListener('change', applyFilters);
placementFilter.addEventListener('change', applyFilters);
exportCsvBtn.addEventListener('click', exportCsv);
exportJsonBtn.addEventListener('click', exportJson);
retryLibBtn.addEventListener('click', boot);

boot();

async function boot() {
  retryLibBtn.hidden = true;
  fileInput.disabled = false;
  libStatus.textContent = '正在初始化 Excel 解析库...（若失败仍可直接解析 CSV）';

  try {
    await ensureXlsxLoaded();
    state.xlsxReady = true;
    libStatus.textContent = 'Excel 解析库已加载，支持 xlsx/xls/csv。';
  } catch (error) {
    console.error(error);
    state.xlsxReady = false;
    libStatus.textContent = 'Excel 解析库加载失败：当前可直接解析 CSV；xlsx/xls 请转为 CSV 后上传。';
    retryLibBtn.hidden = false;
  }
}

function ensureXlsxLoaded() {
  if (window.XLSX) return Promise.resolve();

  return new Promise((resolve, reject) => {
    let idx = 0;

    const loadNext = () => {
      if (idx >= XLSX_CDNS.length) {
        reject(new Error('All XLSX CDN URLs failed.'));
        return;
      }

      const script = document.createElement('script');
      script.src = XLSX_CDNS[idx];
      script.async = true;
      script.onload = () => (window.XLSX ? resolve() : next());
      script.onerror = next;
      document.head.appendChild(script);

      function next() {
        idx += 1;
        loadNext();
      }
    };

    loadNext();

    setTimeout(() => {
      if (!window.XLSX) {
        reject(new Error('XLSX load timeout.'));
      }
    }, 7000);
  });
}

async function onFileChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  fileName.textContent = file.name;

  try {
    const rawRows = await readRows(file);
    processRows(rawRows);
  } catch (error) {
    console.error(error);
    alert(error.message || '文件解析失败，请检查文件格式。');
  }
}

async function readRows(file) {
  const ext = getFileExt(file.name);

  if (ext === 'csv') {
    const text = await file.text();
    return parseCsvToRows(text);
  }

  if (!state.xlsxReady || !window.XLSX) {
    throw new Error('当前环境无法加载 Excel 解析库，请将文件另存为 CSV 再上传。');
  }

  const buffer = await file.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: 'array' });
  const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
  return XLSX.utils.sheet_to_json(firstSheet, { defval: '' });
}

function processRows(rawRows) {
  if (!rawRows.length) {
    throw new Error('文件中没有可解析的数据。');
  }

  const mapping = resolveColumnMapping(rawRows[0]);
  if (!mapping.country || !mapping.adUnit || !mapping.ecpm) {
    throw new Error('无法识别必要列：国家、广告单元、eCPM。请检查列名。');
  }

  state.allRows = rawRows
    .map((row) => normalizeRow(row, mapping))
    .filter((row) => row.country && row.adUnitName && Number.isFinite(row.ecpm))
    .sort((a, b) => b.ecpm - a.ecpm);

  if (!state.allRows.length) {
    throw new Error('未找到有效数据，请确认 eCPM 列为数字。');
  }

  setupFilters();
  controlsPanel.hidden = false;
  summaryPanel.hidden = false;
  resultPanel.hidden = false;
  applyFilters();
}

function getFileExt(name) {
  const parts = String(name).toLowerCase().split('.');
  return parts.length > 1 ? parts.pop() : '';
}

function parseCsvToRows(text) {
  const rows = [];
  const parsed = parseCsv(text);
  if (!parsed.length) return rows;
  const headers = parsed[0];

  for (let i = 1; i < parsed.length; i += 1) {
    const row = {};
    headers.forEach((header, index) => {
      row[header] = parsed[i][index] ?? '';
    });
    rows.push(row);
  }

  return rows;
}

function parseCsv(text) {
  const out = [];
  let row = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    const n = text[i + 1];

    if (c === '"') {
      if (inQuotes && n === '"') {
        field += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (c === ',' && !inQuotes) {
      row.push(field);
      field = '';
    } else if ((c === '\n' || c === '\r') && !inQuotes) {
      if (c === '\r' && n === '\n') i += 1;
      row.push(field);
      if (row.length > 1 || row[0] !== '') out.push(row);
      row = [];
      field = '';
    } else {
      field += c;
    }
  }

  row.push(field);
  if (row.length > 1 || row[0] !== '') out.push(row);
  return out;
}

function normalizeHeader(text) {
  return String(text).trim().toLowerCase();
}

function resolveColumnMapping(sampleRow) {
  const keys = Object.keys(sampleRow);
  const normalized = keys.map((key) => ({ key, normalized: normalizeHeader(key) }));

  const findHeader = (dict) =>
    normalized.find((item) => dict.some((name) => item.normalized.includes(name)))?.key;

  return {
    country: findHeader(COUNTRY_HEADERS),
    adUnit: findHeader(AD_UNIT_HEADERS),
    ecpm: findHeader(ECPM_HEADERS),
  };
}

function parseEcpm(value) {
  if (typeof value === 'number') return value;
  const cleaned = String(value).replace(/[$,\s]/g, '');
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : NaN;
}

function parseAdUnitName(adUnitName) {
  const parts = String(adUnitName).split('_');
  return {
    product: parts[0] || '未知产品',
    placement: parts[1] || '未知广告位',
    adType: parts[2] || '未知广告类型',
    bidType: parts[3] || '未知出价类型',
  };
}

function normalizeRow(row, mapping) {
  const country = String(row[mapping.country]).trim();
  const adUnitName = String(row[mapping.adUnit]).trim();
  const ecpm = parseEcpm(row[mapping.ecpm]);
  const parsed = parseAdUnitName(adUnitName);

  return {
    country,
    adUnitName,
    ecpm,
    ...parsed,
  };
}

function setupFilters() {
  const countries = [...new Set(state.allRows.map((item) => item.country))].sort();
  const placements = [...new Set(state.allRows.map((item) => item.placement))].sort();

  countryFilter.innerHTML = '<option value="">全部国家</option>';
  placementFilter.innerHTML = '<option value="">全部广告位</option>';

  countries.forEach((country) => {
    const option = document.createElement('option');
    option.value = country;
    option.textContent = country;
    countryFilter.appendChild(option);
  });

  placements.forEach((placement) => {
    const option = document.createElement('option');
    option.value = placement;
    option.textContent = placement;
    placementFilter.appendChild(option);
  });
}

function applyFilters() {
  const country = countryFilter.value;
  const placement = placementFilter.value;

  state.filteredRows = state.allRows.filter((row) => {
    if (country && row.country !== country) return false;
    if (placement && row.placement !== placement) return false;
    return true;
  });

  renderSummary(state.filteredRows);
  renderTable(state.filteredRows);
}

function renderSummary(rows) {
  if (!rows.length) {
    summary.innerHTML = '<p>当前筛选条件无数据。</p>';
    return;
  }

  const ecpmValues = rows.map((item) => item.ecpm);
  const avg = ecpmValues.reduce((sum, n) => sum + n, 0) / ecpmValues.length;
  const max = Math.max(...ecpmValues);
  const min = Math.min(...ecpmValues);

  summary.innerHTML = [
    card('记录数', rows.length),
    card('国家数', new Set(rows.map((r) => r.country)).size),
    card('广告位数', new Set(rows.map((r) => r.placement)).size),
    card('平均 eCPM', avg.toFixed(4)),
    card('最高 eCPM', max.toFixed(4)),
    card('最低 eCPM', min.toFixed(4)),
  ].join('');
}

function card(label, value) {
  return `<div class="summary-card"><div class="label">${label}</div><div class="value">${value}</div></div>`;
}

function renderTable(rows) {
  resultBody.innerHTML = '';
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${escapeHtml(row.country)}</td>
      <td>${escapeHtml(row.placement)}</td>
      <td>${escapeHtml(row.adUnitName)}</td>
      <td>${escapeHtml(row.product)}</td>
      <td>${escapeHtml(row.adType)}</td>
      <td>${escapeHtml(row.bidType)}</td>
      <td>${row.ecpm.toFixed(4)}</td>
    `;
    resultBody.appendChild(tr);
  });
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function exportCsv() {
  if (!state.filteredRows.length) {
    alert('暂无可导出的数据。');
    return;
  }

  const header = ['country', 'placement', 'adUnitName', 'product', 'adType', 'bidType', 'ecpm'];
  const lines = [header.join(',')];

  state.filteredRows.forEach((row) => {
    const values = header.map((field) => csvSafe(row[field]));
    lines.push(values.join(','));
  });

  downloadFile(lines.join('\n'), 'admob-analysis.csv', 'text/csv;charset=utf-8;');
}

function exportJson() {
  if (!state.filteredRows.length) {
    alert('暂无可导出的数据。');
    return;
  }

  const grouped = state.filteredRows.reduce((acc, row) => {
    if (!acc[row.country]) acc[row.country] = {};
    if (!acc[row.country][row.placement]) acc[row.country][row.placement] = [];
    acc[row.country][row.placement].push(row);
    return acc;
  }, {});

  Object.keys(grouped).forEach((country) => {
    Object.keys(grouped[country]).forEach((placement) => {
      grouped[country][placement].sort((a, b) => b.ecpm - a.ecpm);
    });
  });

  downloadFile(JSON.stringify(grouped, null, 2), 'admob-analysis.json', 'application/json;charset=utf-8;');
}

function csvSafe(value) {
  const text = String(value ?? '');
  if (text.includes(',') || text.includes('"') || text.includes('\n')) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function downloadFile(content, outFileName, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = outFileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
