/* RAN Energy Observatory — interactive research workbench. */
const $ = id => document.getElementById(id);
const policies = ['always_on', 'micro_sleep', 'compact'];
const names = { always_on: 'Always on', micro_sleep: 'Micro sleep', compact: 'Compact + sleep' };
const colors = ['#0d1b2c', '#42d6c0', '#36aeb7', '#8a8dff', '#b09bf4', '#617fe6', '#a4b8f2'];
const policyColors = { always_on: '#8594aa', micro_sleep: '#8a8dff', compact: '#42d6c0' };
const stateNames = ['Active', 'Idle', 'Micro sleep', 'Wake'];
const stateColors = ['#7188a6', '#34475f', '#42d6c0', '#e7b970'];
let result, policy = 'compact', timer = null, liveTimer = null, imported = null;
let selected = { prb: 0, symbol: 0 }, pinned = false, hoverTime = null, requestSerial = 0;
let acceptedConfig = null, acceptedTrace = null;

function config() {
  return {
    radio: $('radio').value, scenario: $('scenario').value,
    load: +$('load').value / 100, batch_ms: +$('batch').value,
    seed: +$('seed').value, duration_ms: +$('duration').value, drain_ms: +$('drain').value,
    active_w: +$('active').value, slope_w: +$('slope').value,
    sleep_w: +$('sleep').value, wake_mj: +$('wake').value,
  };
}

function markDirty() {
  $('dirty').hidden = acceptedConfig === null ||
    (JSON.stringify(config()) === acceptedConfig && imported === acceptedTrace);
  document.querySelectorAll('[data-preset]').forEach(b => b.classList.remove('selected'));
}

function error(message) {
  $('error').textContent = String(message);
  $('error').hidden = false;
  setTimeout(() => { $('error').hidden = true; }, 9000);
}

function fit(id) {
  const canvas = $(id), box = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(box.width * dpr));
  canvas.height = Math.max(1, Math.round(box.height * dpr));
  const context = canvas.getContext('2d');
  context.scale(dpr, dpr);
  return [context, box.width, box.height];
}

function stop() {
  clearInterval(timer); timer = null;
  $('play').textContent = '▶ Replay';
  $('play').setAttribute('aria-pressed', 'false');
}

function disconnectTelemetry() {
  clearInterval(liveTimer); liveTimer = null;
  $('live').textContent = 'Connect telemetry';
  $('liveStatus').textContent = 'Disconnected';
  $('livePreview').hidden = true;
}

async function run() {
  if (!$('configForm').reportValidity()) return;
  stop(); if (liveTimer) disconnectTelemetry();
  $('livePreview').hidden = true;
  const serial = ++requestSerial, c = config(), trace = imported;
  $('run').disabled = true;
  $('status').textContent = 'Computing paired policy comparisons…';
  try {
    const response = await fetch(trace ? '/api/trace' : '/api/compare', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(trace ? { config: c, csv: trace } : c),
    });
    const data = await response.json();
    if (!response.ok) {
      const detail = data.detail;
      throw new Error(Array.isArray(detail) ? detail.map(x => x.msg).join('; ') : detail);
    }
    if (serial !== requestSerial) return;
    result = data;
    acceptedConfig = JSON.stringify(c); acceptedTrace = trace;
    $('dirty').hidden = JSON.stringify(config()) === acceptedConfig && imported === trace;
    $('meta').textContent = `${result.meta.prbs} PRBs · ${result.meta.scs_khz} kHz · ${c.duration_ms} ms`;
    $('status').textContent = trace ? 'Imported packet trace · power estimated' :
      c.scenario === 'milan' ? 'Simulation complete · Milan-derived activity envelope' :
      c.drain_ms ? 'Simulation complete · arrival-free drain enabled' : 'Simulation complete · seeded demand';
    $('sourceNote').textContent = `Source: ${result.meta.source} · power estimated`;
    $('clearTrace').hidden = !trace;
    $('scrub').step = result.meta.slot_ms;
    $('scrub').max = Math.max(0, c.duration_ms - +$('window').value);
    $('scrub').value = 0;
    selected = { prb: 0, symbol: 0 }; pinned = false;
    render();
  } catch (e) {
    if (serial === requestSerial) { error(e.message); $('status').textContent = 'Experiment failed · check configuration'; }
  } finally {
    if (serial === requestSerial) $('run').disabled = false;
  }
}

function metric(value, unit) {
  return value == null ? 'N/A' : `${value}<span class="metric-unit">${unit}</span>`;
}

function setPolicy(next) {
  policy = next;
  document.querySelectorAll('[data-policy]').forEach(b => {
    const active = b.dataset.policy === policy;
    b.classList.toggle('selected', active); b.setAttribute('aria-selected', String(active));
  });
  document.querySelectorAll('[data-mini]').forEach(b => b.classList.toggle('selected', b.dataset.mini === policy));
  render();
}

function render() {
  if (!result) return;
  const s = result.runs[policy].stats;
  $('saving').innerHTML = metric(s.saving_pct, '%');
  $('throughput').innerHTML = metric(s.throughput_mbps, 'Mbps');
  $('latency').innerHTML = metric(s.p95_latency_ms, 'ms');
  $('sleepPct').innerHTML = metric(s.sleep_pct, '%');
  $('activePolicy').textContent = names[policy];
  $('delivered').textContent = `${s.completed_packets}/${s.packets} packets · ${s.backlog_bits.toLocaleString()} bits queued`;
  $('misses').textContent = `${s.deadline_miss_pct}% missed · ${s.censored_packets} censored`;
  $('wakeups').textContent = `${s.wakeups} wakes · transition cost included`;
  $('gridSubtitle').textContent = `${result.config.radio} · ${names[policy]} · one PRB × one OFDM symbol per cell`;
  $('prbTop').textContent = result.meta.prbs - 1;
  $('prbMid').textContent = Math.floor((result.meta.prbs - 1) / 2);
  $('comparison').innerHTML = policies.map(p => {
    const x = result.runs[p].stats;
    return `<tr class="${p === policy ? 'best' : ''}"><td><i class="policy-dot" style="background:${policyColors[p]}"></i>${names[p]}</td><td>${x.energy_j.toFixed(2)} J</td><td>${x.p95_latency_ms ?? 'N/A'} ms</td><td><span class="miss-badge ${x.deadline_miss_pct > 0 ? 'bad' : ''}">${x.deadline_miss_pct}%</span></td></tr>`;
  }).join('');
  const c = result.runs.compact.stats, b = result.runs.always_on.stats;
  $('insight').textContent = `Compaction reduces modelled energy by ${c.saving_pct}%. p95 latency changes from ${b.p95_latency_ms ?? 'N/A'} to ${c.p95_latency_ms ?? 'N/A'} ms. ${c.backlog_bits.toLocaleString()} bits remain queued; service and energy must be read together.`;
  renderReview(s); renderStateSummary();
  drawGrid();
}

function renderReview(s) {
  const stats = Object.values(result.runs).map(r => r.stats);
  const allFinished = stats.every(x => x.backlog_bits === 0);
  const sameDelivered = stats.every(x => x.delivered_bits === stats[0].delivered_bits);
  const fullEqualWork = allFinished && sameDelivered && s.offered_bits > 0;
  const severe = s.deadline_miss_pct > 5;
  $('serviceReview').className = `service-review${severe ? ' danger' : fullEqualWork && s.deadline_miss_pct === 0 ? ' equal' : ''}`;
  $('reviewTitle').textContent = !s.offered_bits ? 'No payload offered.' : severe ? 'Service quality degraded.' :
    fullEqualWork ? 'Equal payload delivered.' : 'Review unfinished traffic.';
  $('reviewDetail').textContent = !s.offered_bits ? 'Energy reflects signalling, idle and sleep states only.' :
    severe ? `${s.deadline_miss_pct}% of observable deadlines missed. A positive energy saving does not imply acceptable service.` :
    fullEqualWork ? 'All policies finished the same demand. Compare energy alongside packet latency.' :
    'Residual queues can differ across policies. Use the equal-work preset for a drain interval.';
  const ratio = s.offered_bits ? 100 * s.delivered_bits / s.offered_bits : 0;
  $('deliveryRatio').textContent = s.offered_bits ? `${ratio.toFixed(1)}% bits delivered` : 'No demand';
}

function renderStateSummary() {
  const states = result.runs[policy].states, counts = [0, 0, 0, 0];
  states.forEach(s => counts[s]++);
  $('stateBar').innerHTML = counts.map((n, i) => `<span style="width:${100 * n / states.length}%;background:${stateColors[i]}"></span>`).join('');
  $('stateLegend').innerHTML = counts.map((n, i) => `<span><i style="background:${stateColors[i]}"></i>${stateNames[i]}<b>${(100 * n / states.length).toFixed(1)}%</b></span>`).join('');
}

function bounds() {
  const start = Math.floor(+$('scrub').value / result.meta.symbol_ms);
  const total = result.runs[policy].states.length;
  return { start, count: Math.max(1, Math.min(Math.ceil(+$('window').value / result.meta.symbol_ms), total - start)) };
}

function paintGrid(id, run, start, count, highlight = false) {
  const [ctx, w, h] = fit(id), rows = run.grid.length;
  ctx.fillStyle = colors[0]; ctx.fillRect(0, 0, w, h);
  for (let f = 0; f < rows; f++) {
    for (let t = 0; t < count; t++) {
      const value = run.grid[f][start + t];
      if (value === 0) continue;
      ctx.fillStyle = value === -1 ? '#718298' : colors[value];
      ctx.fillRect(t * w / count, (rows - 1 - f) * h / rows, Math.max(1, w / count), Math.max(.5, h / rows - .35));
    }
  }
  ctx.strokeStyle = '#2b3d56'; ctx.lineWidth = .4;
  for (let t = 0; t < count; t++) if ((start + t) % 14 === 0) {
    ctx.beginPath(); ctx.moveTo(t * w / count, 0); ctx.lineTo(t * w / count, h); ctx.stroke();
  }
  if (highlight && selected.symbol >= start && selected.symbol < start + count) {
    const x = (selected.symbol - start + .5) * w / count, y = (rows - selected.prb - .5) * h / rows;
    ctx.strokeStyle = '#d5e6ff88'; ctx.lineWidth = .7; ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    ctx.setLineDash([]); ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.3;
    ctx.strokeRect(x - 3, y - 3, 6, 6);
  }
}

function drawGrid() {
  if (!result) return;
  const { start, count } = bounds(), run = result.runs[policy];
  if (!pinned && (selected.symbol < start || selected.symbol >= start + count)) selected.symbol = start;
  paintGrid('grid', run, start, count, true);
  const [ctx, w, h] = fit('states');
  for (let t = 0; t < count; t++) {
    ctx.fillStyle = stateColors[run.states[start + t]];
    ctx.fillRect(t * w / count, 0, Math.ceil(w / count), h);
  }
  const a = start * result.meta.symbol_ms, b = (start + count) * result.meta.symbol_ms;
  $('startTime').textContent = `${a.toFixed(1)} ms`;
  $('endTime').textContent = `${b.toFixed(1)} ms`;
  $('cursorLabel').textContent = `TIME → ${a.toFixed(1)}–${b.toFixed(1)} ms`;
  if (!$('compareStrip').hidden) policies.forEach(p => {
    paintGrid(`mini-${p}`, result.runs[p], start, count);
    $(`miniStat-${p}`).textContent = `${result.runs[p].stats.energy_j.toFixed(2)} J`;
  });
  inspect(); drawPower();
}

function inspect() {
  if (!result) return;
  const run = result.runs[policy], { prb, symbol } = selected;
  const value = run.grid[prb][symbol], state = run.states[symbol];
  let occupied = 0;
  run.grid.forEach(row => { if (row[symbol] !== 0) occupied++; });
  $('inspectTime').textContent = (symbol * result.meta.symbol_ms).toFixed(3);
  $('inspectPrb').textContent = prb;
  $('inspectSymbol').textContent = symbol % 14;
  $('inspectAllocation').textContent = value === -1 ? 'Required signalling' : value === 0 ? 'Unallocated resource' : `UE ${value} · ${value <= 2 ? 'urgent' : 'flexible'} traffic`;
  $('inspectAllocation').style.color = value > 0 ? colors[value] : '#b6cee6';
  $('inspectState').textContent = stateNames[state];
  $('inspectOccupancy').textContent = `${occupied}/${result.meta.prbs} PRBs`;
  $('inspectPower').textContent = `${run.timeline[Math.floor(symbol / 14)].power_w.toFixed(1)} W`;
  $('pinState').textContent = pinned ? 'PINNED' : 'FOLLOW';
  $('pinState').classList.toggle('pinned', pinned);
  $('selectionHint').textContent = pinned ? 'Selection pinned. Click another cell to move; Escape to release.' : 'Hover or use arrow keys to inspect. Click a cell to pin the selection.';
}

function drawPower() {
  if (!result) return;
  const [ctx, w, h] = fit('power'), left = 34, right = w - 8, top = 9, bottom = h - 23;
  const max = Math.max(...Object.values(result.runs).flatMap(r => r.timeline.map(t => t.power_w))) * 1.12;
  const { start, count } = bounds(), duration = result.config.duration_ms;
  const xForTime = t => left + (right - left) * t / duration;
  const x1 = xForTime(start * result.meta.symbol_ms), x2 = xForTime((start + count) * result.meta.symbol_ms);
  ctx.fillStyle = '#42d6c018'; ctx.fillRect(x1, top, x2 - x1, bottom - top);
  ctx.strokeStyle = '#42d6c05f'; ctx.lineWidth = .7; ctx.strokeRect(x1, top, x2 - x1, bottom - top);
  ctx.font = '9px DM Sans,Arial';
  for (let i = 0; i < 4; i++) {
    const y = top + (bottom - top) * i / 3;
    ctx.strokeStyle = '#2b3c54'; ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(right, y); ctx.stroke();
    ctx.fillStyle = '#8da6c7'; ctx.fillText(Math.round(max * (1 - i / 3)), 0, y + 3);
  }
  policies.forEach(p => {
    ctx.strokeStyle = policyColors[p]; ctx.lineWidth = p === policy ? 1.8 : 1;
    ctx.setLineDash(p === 'always_on' ? [4, 3] : []); ctx.beginPath();
    result.runs[p].timeline.forEach((point, i) => {
      const x = xForTime(point.time_ms), y = bottom - (bottom - top) * point.power_w / max;
      if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y);
    });
    ctx.stroke(); ctx.setLineDash([]);
  });
  if (hoverTime !== null) {
    const x = xForTime(hoverTime);
    ctx.strokeStyle = '#d6e6fc88'; ctx.setLineDash([3, 3]); ctx.beginPath(); ctx.moveTo(x, top); ctx.lineTo(x, bottom); ctx.stroke(); ctx.setLineDash([]);
  }
  ctx.fillStyle = '#8da6c7'; ctx.fillText('0 ms', left, h - 4); ctx.fillText(`${duration} ms`, right - 37, h - 4);
  const [sp, sw, sh] = fit('spark'); sp.strokeStyle = '#42d6c0'; sp.beginPath();
  result.runs[policy].timeline.forEach((v, i) => { const x = i * sw / result.runs[policy].timeline.length, y = sh - v.power_w / max * sh; if (i) sp.lineTo(x, y); else sp.moveTo(x, y); });
  sp.stroke();
}

function cellAt(event) {
  const box = $('grid').getBoundingClientRect(), { start, count } = bounds();
  return {
    prb: Math.max(0, Math.min(result.meta.prbs - 1, result.meta.prbs - 1 - Math.floor((event.clientY - box.top) / box.height * result.meta.prbs))),
    symbol: start + Math.max(0, Math.min(count - 1, Math.floor((event.clientX - box.left) / box.width * count))),
  };
}

function download(blob, filename) {
  const url = URL.createObjectURL(blob), anchor = document.createElement('a');
  anchor.href = url; anchor.download = filename; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

$('configForm').onsubmit = event => { event.preventDefault(); run(); };
$('configForm').addEventListener('input', () => {
  $('loadValue').textContent = `${$('load').value}%`;
  $('batchValue').textContent = `${(+$('batch').value).toFixed(1)} ms`;
  markDirty();
});
$('scenario').onchange = () => { imported = null; $('trace').value = ''; $('clearTrace').hidden = true; markDirty(); };

document.querySelectorAll('[data-preset]').forEach(button => {
  button.onclick = async () => {
    imported = null; $('trace').value = ''; $('clearTrace').hidden = true;
    const choice = button.dataset.preset;
    $('radio').value = 'NR'; $('scenario').value = choice === 'stress' ? 'overload' : 'bursty';
    $('load').value = choice === 'stress' ? '65' : '28';
    $('drain').value = choice === 'equal' ? '40' : '0';
    $('duration').value = '160'; $('batch').value = '2'; $('seed').value = '42';
    $('loadValue').textContent = `${$('load').value}%`; $('batchValue').textContent = '2.0 ms';
    document.querySelectorAll('[data-preset]').forEach(b => { b.classList.toggle('selected', b === button); b.setAttribute('aria-pressed', String(b === button)); });
    setPolicy('compact'); await run();
  };
});
document.querySelectorAll('[data-policy]').forEach(b => b.onclick = () => setPolicy(b.dataset.policy));
document.querySelectorAll('[data-mini]').forEach(b => b.onclick = () => setPolicy(b.dataset.mini));
document.querySelectorAll('.tabs [role="tab"]').forEach((tab, index) => {
  tab.onkeydown = event => {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
    event.preventDefault();
    const next = (index + (event.key === 'ArrowRight' ? 1 : 2)) % 3;
    setPolicy(policies[next]); document.querySelector(`[data-policy="${policies[next]}"]`).focus();
  };
});
$('scrub').oninput = () => { stop(); drawGrid(); };
$('window').onchange = () => {
  if (!result) return;
  $('scrub').max = Math.max(0, result.config.duration_ms - +$('window').value); drawGrid();
};
$('play').onclick = () => {
  if (!result) return;
  if (timer) { stop(); return; }
  $('play').textContent = 'Ⅱ Pause'; $('play').setAttribute('aria-pressed', 'true');
  timer = setInterval(() => { const next = +$('scrub').value + result.meta.slot_ms * 2; $('scrub').value = next > +$('scrub').max ? 0 : next; drawGrid(); }, 100);
};
$('compareToggle').onclick = () => {
  const open = $('compareStrip').hidden;
  $('compareStrip').hidden = !open;
  $('compareToggle').setAttribute('aria-expanded', String(open));
  $('compareToggle').innerHTML = `${open ? 'Hide comparison' : 'Compare grids'} <span>${open ? '−' : '＋'}</span>`;
  drawGrid();
};
$('grid').onpointermove = event => {
  if (!result || pinned) return;
  selected = cellAt(event); drawGrid();
};
$('grid').onclick = event => { if (!result) return; stop(); selected = cellAt(event); pinned = true; drawGrid(); };
$('grid').onkeydown = event => {
  if (!result) return;
  if (event.key === 'Escape') { pinned = false; inspect(); return; }
  const movements = { ArrowLeft: [0, -1], ArrowRight: [0, 1], ArrowUp: [1, 0], ArrowDown: [-1, 0] };
  const movement = movements[event.key]; if (!movement) return;
  event.preventDefault(); stop(); pinned = true;
  selected.prb = Math.max(0, Math.min(result.meta.prbs - 1, selected.prb + movement[0]));
  selected.symbol = Math.max(0, Math.min(result.runs[policy].states.length - 1, selected.symbol + movement[1]));
  const { start, count } = bounds();
  if (selected.symbol < start || selected.symbol >= start + count) {
    $('scrub').value = Math.min(+$('scrub').max, Math.floor(selected.symbol / 14) * result.meta.slot_ms);
  }
  drawGrid();
};
function chartTime(event) {
  const box = $('power').getBoundingClientRect();
  return Math.max(0, Math.min(result.config.duration_ms, (event.clientX - box.left - 34) / (box.width - 42) * result.config.duration_ms));
}
$('power').onpointermove = event => {
  if (!result) return;
  hoverTime = chartTime(event);
  const i = Math.min(result.runs[policy].timeline.length - 1, Math.floor(hoverTime / result.meta.slot_ms));
  $('powerReadout').textContent = `${hoverTime.toFixed(1)} ms · ` + policies.map(p => `${names[p]} ${result.runs[p].timeline[i].power_w.toFixed(1)} W`).join(' / ');
  drawPower();
};
$('power').onpointerleave = () => { hoverTime = null; $('powerReadout').textContent = ''; drawPower(); };
$('power').onclick = event => { if (!result) return; stop(); $('scrub').value = Math.min(+$('scrub').max, chartTime(event)); drawGrid(); };
$('power').onkeydown = event => {
  if (!result || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
  event.preventDefault(); stop();
  $('scrub').value = Math.max(0, Math.min(+$('scrub').max, +$('scrub').value + (event.key === 'ArrowRight' ? 1 : -1) * result.meta.slot_ms));
  drawGrid();
};
$('trace').onchange = async event => {
  const file = event.target.files[0]; if (!file) return;
  if (file.size > 4000000) { error('Choose a packet CSV smaller than 4 MB.'); return; }
  imported = await file.text(); $('clearTrace').hidden = false; markDirty(); await run();
};
$('clearTrace').onclick = () => { imported = null; $('trace').value = ''; $('clearTrace').hidden = true; markDirty(); run(); };
$('export').onclick = () => {
  if (result) download(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }), `ran-experiment-${result.config.radio}-${result.config.seed}.json`);
};
$('imageExport').onclick = () => {
  if (!result) return;
  const source = $('grid'), canvas = document.createElement('canvas');
  canvas.width = Math.max(1200, source.width + 64);
  const gridHeight = Math.min(520, Math.max(220, source.height / source.width * (canvas.width - 64)));
  canvas.height = gridHeight + 112;
  const ctx = canvas.getContext('2d'); ctx.fillStyle = '#0b1220'; ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#e9eff8'; ctx.font = '18px Arial'; ctx.fillText(`RAN Energy Observatory · ${result.config.radio} · ${names[policy]}`, 24, 30);
  ctx.fillStyle = '#9db3cf'; ctx.font = '12px Arial';
  ctx.fillText(`Frequency axis: PRB 0 (bottom) to ${result.meta.prbs - 1} (top) · ${$('cursorLabel').textContent}`, 24, 53);
  ctx.drawImage(source, 32, 68, canvas.width - 64, gridHeight);
  ctx.fillText('Allocation simulation · power estimated · one PRB × one OFDM symbol per cell', 24, canvas.height - 15);
  canvas.toBlob(blob => { if (blob) download(blob, `ran-grid-${result.config.radio}-${policy}.png`); });
};

let telemetryPolling = false;
async function pollTelemetry() {
  if (telemetryPolling) return;
  telemetryPolling = true;
  try {
    const response = await fetch('/api/telemetry'); if (!response.ok) throw new Error('Could not read allocation telemetry.');
    const data = await response.json(); if (!liveTimer) return;
    const frame = data.frames.at(-1);
    $('liveStatus').textContent = frame ? `${frame.source} · ${frame.estimated_power_w} W estimated · t=${frame.timestamp_ms} ms` : 'Connected · waiting for external allocation frames';
    if (frame) {
      $('livePreview').hidden = false;
      paintGrid('liveGrid', frame, 0, 14);
    }
  } catch (e) { error(e.message); } finally { telemetryPolling = false; }
}
$('live').onclick = () => {
  if (liveTimer) { disconnectTelemetry(); return; }
  stop(); $('live').textContent = 'Disconnect telemetry';
  liveTimer = setInterval(pollTelemetry, 750); pollTelemetry();
};
document.querySelectorAll('.rail nav a').forEach(link => link.onclick = () => {
  document.querySelectorAll('.rail nav a').forEach(a => a.classList.toggle('active', a === link));
});
window.addEventListener('resize', () => render());
run();
