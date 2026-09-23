/**
 * 1942 Flat Top web client.
 *
 * This client renders server-authoritative projections only. It never
 * calculates combat, movement legality, or hidden information locally;
 * every state change is requested from the API (see api.js) and the
 * resulting projection is re-rendered. See docs/UI_SPEC.md and
 * docs/design/WEB_ARCHITECTURE.md section 4.1 for the rules this follows.
 */

const HEX_SIZE = 20;

const state = {
  gameId: null,
  side: null,
  projection: null,
  selectedUnitId: null,
  scenarios: [],
  selectedScenarioId: null,
  reachableHexes: new Set(),
  draggingUnitId: null,
  zoom: 1,
};

const MIN_ZOOM = 0.4;
const MAX_ZOOM = 2.5;

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

// ---------------------------------------------------------------------
// New game screen
// ---------------------------------------------------------------------

async function initNewGameScreen() {
  try {
    state.scenarios = await FlatTopApi.listScenarios();
  } catch (error) {
    showNewGameError(`Could not load scenario catalog: ${error.message}`);
    return;
  }
  renderScenarioList();
}

function renderScenarioList() {
  const container = $('#scenarioList');
  if (!state.scenarios.length) {
    container.textContent = 'No published scenarios are available.';
    return;
  }
  container.innerHTML = state.scenarios
    .map(
      (scenario) => `
      <button class="scenario-option ${scenario.id === state.selectedScenarioId ? 'selected' : ''}" data-scenario-id="${scenario.id}">
        <div>
          <strong>${scenario.name}</strong>
          <small>${scenario.description}</small>
          <small>${scenario.setup_summary.bases} bases &middot; ${scenario.setup_summary.task_forces} task forces &middot; version ${scenario.version}</small>
        </div>
        <span class="board-size">${scenario.board.width} &times; ${scenario.board.height}</span>
      </button>`
    )
    .join('');
  $$('.scenario-option', container).forEach((button) =>
    button.addEventListener('click', () => {
      state.selectedScenarioId = button.dataset.scenarioId;
      renderScenarioList();
      $('#startGameButton').disabled = false;
    })
  );
}

function showNewGameError(message) {
  const el = $('#newGameError');
  el.textContent = message;
  el.hidden = false;
}

async function startNewGame() {
  const side = $('#playerSideSelect').value;
  const opponent = $('#opponentSelect').value;
  const button = $('#startGameButton');
  button.disabled = true;
  try {
    const projection = await FlatTopApi.createGame(state.selectedScenarioId, side, opponent);
    state.gameId = projection.game_id;
    state.side = side;
    state.projection = projection;
    $('#newGameShell').hidden = true;
    $('#appRoot').hidden = false;
    renderProjection(projection);
  } catch (error) {
    showNewGameError(`Could not create game: ${error.message}`);
    button.disabled = false;
  }
}

// ---------------------------------------------------------------------
// Main game screen rendering
// ---------------------------------------------------------------------

function renderProjection(projection) {
  state.projection = projection;
  $('#scenarioTitle').textContent = projection.scenario.name;
  $('#phaseLabel').textContent = projection.turn.phase.toUpperCase();
  $('#turnLabel').textContent = `Turn ${projection.turn.turn_number} \u00b7 ${String(projection.turn.hour).padStart(2, '0')}00 \u00b7 ${
    projection.turn.is_night ? 'Night' : 'Daylight'
  }`;
  $('#sideAvatar').textContent = projection.viewing_side[0];
  $('#alliedScore').textContent = projection.score.allied;
  $('#japaneseScore').textContent = projection.score.japanese;
  $('#mapTitle').textContent = projection.scenario.name;
  $('#mapSubtitle').textContent = `${projection.board.width} \u00d7 ${projection.board.height} hexes \u00b7 initiative: ${
    projection.turn.initiative || 'unresolved'
  }`;

  renderPhaseRail(projection);
  renderForceList(projection);
  renderContactList(projection);
  renderMap(projection);

  if (state.selectedUnitId) {
    const stillExists = projection.units.some((u) => u.id === state.selectedUnitId);
    if (stillExists) renderUnitPanel(state.selectedUnitId);
    else clearSelection();
  }
}

function renderPhaseRail(projection) {
  const rail = $('#phaseRail');
  const phaseButtons = projection.turn.phases
    .map((phase, index) => {
      const currentIndex = projection.turn.phases.indexOf(projection.turn.phase);
      const cls = phase === projection.turn.phase ? 'active' : index < currentIndex ? 'complete' : '';
      return `<div class="phase-item ${cls}"><span>${String(index + 1).padStart(2, '0')}</span><b>${phase}</b></div>`;
    })
    .join('');
  rail.innerHTML = `${phaseButtons}<button class="advance-button" data-action="advance">Advance phase <span>\u2192</span></button>`;
}

function renderForceList(projection) {
  const friendly = projection.units.filter((u) => u.friendly && u.kind !== 'Weather');
  $('#forceCount').textContent = `${friendly.length} groups`;
  $('#forceList').innerHTML = friendly
    .map(
      (unit) => `
      <button class="force-card ${unit.id === state.selectedUnitId ? 'selected' : ''}" data-unit="${unit.id}">
        <span class="unit-icon ${iconClassFor(unit)}">${iconFor(unit)}</span>
        <span><strong>${unit.name}</strong><small>${summaryLineFor(unit)}</small></span>
      </button>`
    )
    .join('');
  $$('#forceList [data-unit]').forEach((button) => button.addEventListener('click', () => renderUnitPanel(button.dataset.unit)));
}

function renderContactList(projection) {
  const contacts = projection.units.filter((u) => !u.friendly && u.kind !== 'Weather');
  $('#contactCount').textContent = contacts.length;
  $('#contactList').innerHTML = contacts
    .map(
      (unit) => `
      <button class="contact-row" data-unit="${unit.id}">
        <span class="contact-marker">?</span>
        <span><strong>${unit.kind === 'Base' ? unit.name : `Unknown ${unit.kind}`}</strong><small>Condition ${unit.observed_condition}</small></span>
      </button>`
    )
    .join('');
  $$('#contactList [data-unit]').forEach((button) => button.addEventListener('click', () => renderUnitPanel(button.dataset.unit)));
}

function iconClassFor(unit) {
  if (unit.kind === 'Base') return 'base';
  if (unit.kind === 'TaskForce') return 'carrier';
  if (unit.kind === 'AirFormation') return 'air';
  return '';
}

function iconFor(unit) {
  if (unit.kind === 'Base') return '\u2302';
  if (unit.kind === 'TaskForce') return 'TF';
  if (unit.kind === 'AirFormation') return '\u2726';
  return '?';
}

function summaryLineFor(unit) {
  if (unit.kind === 'Base') return `Damage ${unit.damage}`;
  if (unit.kind === 'TaskForce') return unit.ships ? `${unit.ships.length} ships` : `${unit.ship_count ?? '?'} ships`;
  if (unit.kind === 'AirFormation') {
    const count = unit.aircraft ? unit.aircraft.reduce((sum, ac) => sum + ac.count, 0) : unit.aircraft_count;
    return `${count} aircraft \u00b7 ${unit.altitude}`;
  }
  return '';
}

// ---------------------------------------------------------------------
// Map rendering (hex grid + unit markers)
// ---------------------------------------------------------------------

function hexGeometry(width, height) {
  return { viewWidth: 1.5 * (width - 1) + 2, viewHeight: Math.sqrt(3) * (height + 0.5) };
}

function hexCenter(q, r) {
  return { x: 1.5 * q + 1, y: Math.sqrt(3) * (r + 0.5 * (q % 2) + 0.5) };
}

function renderMap(projection) {
  const { width, height } = projection.board;
  const land = new Set(projection.board.land_hexes.map(([x, y]) => `${x},${y}`));
  const { viewWidth, viewHeight } = hexGeometry(width, height);
  const hexRadius = 1;
  const hexHeight = Math.sqrt(3) * hexRadius;
  const polygons = [];
  for (let x = 0; x < width; x += 1) {
    for (let y = 0; y < height; y += 1) {
      const center = hexCenter(x, y);
      const points = [
        [center.x + hexRadius, center.y],
        [center.x + hexRadius * 0.5, center.y - hexHeight * 0.5],
        [center.x - hexRadius * 0.5, center.y - hexHeight * 0.5],
        [center.x - hexRadius, center.y],
        [center.x - hexRadius * 0.5, center.y + hexHeight * 0.5],
        [center.x + hexRadius * 0.5, center.y + hexHeight * 0.5],
      ]
        .map(([px, py]) => `${px},${py}`)
        .join(' ');
      polygons.push(`<polygon class="${land.has(`${x},${y}`) ? 'land-hex' : 'sea-hex'}" points="${points}" data-x="${x}" data-y="${y}" />`);
    }
  }
  $('#mapGrid').innerHTML = `<svg class="hex-board" viewBox="0 0 ${viewWidth} ${viewHeight}" preserveAspectRatio="none">${polygons.join(
    ''
  )}</svg>`;
  $('#mapGrid').style.width = `${viewWidth * HEX_SIZE}px`;
  $('#mapGrid').style.height = `${viewHeight * HEX_SIZE}px`;
  $('#mapOverlays').style.width = `${viewWidth * HEX_SIZE}px`;
  $('#mapOverlays').style.height = `${viewHeight * HEX_SIZE}px`;
  $('#mapContent').style.width = `${viewWidth * HEX_SIZE + 40}px`;
  $('#mapContent').style.height = `${viewHeight * HEX_SIZE + 40}px`;

  const markers = projection.units
    .filter((unit) => unit.kind !== 'Weather')
    .map((unit) => {
      const [x, y] = unit.position;
      const center = hexCenter(x, y);
      const left = (center.x / viewWidth) * 100;
      const top = (center.y / viewHeight) * 100;
      const draggable = unit.friendly && phaseAllowsMove(unit);
      const showName = unit.friendly || unit.kind === 'Base';
      return `
        <button class="map-unit ${unit.friendly ? 'friendly-unit' : 'enemy-unit'} ${draggable ? 'draggable-unit' : ''}" style="left:${left}%;top:${top}%" data-unit="${
        unit.id
      }" draggable="${draggable}" title="${unit.name}">
          <span class="map-unit-badge ${unit.friendly ? 'allied-badge' : 'enemy-badge'}">${iconFor(unit)}</span>
          <span class="map-unit-label">${showName ? unit.name : `Contact [${x},${y}]`}</span>
        </button>`;
    })
    .join('');
  $('#mapOverlays').innerHTML = markers;
  $$('#mapOverlays [data-unit]').forEach((button) => {
    button.addEventListener('click', () => renderUnitPanel(button.dataset.unit));
    button.addEventListener('dragstart', (event) => onMarkerDragStart(event, button.dataset.unit));
    button.addEventListener('dragend', onMarkerDragEnd);
  });
  applyReachableHighlightClasses();
  applyMapZoom();
}

// ---------------------------------------------------------------------
// Map zoom
// ---------------------------------------------------------------------

function applyMapZoom() {
  const content = $('#mapContent');
  const viewport = $('#mapViewport');
  if (!content || !viewport) return;
  content.style.transform = `scale(${state.zoom})`;
  content.style.transformOrigin = 'top left';
  viewport.style.width = `${content.offsetWidth * state.zoom}px`;
  viewport.style.height = `${content.offsetHeight * state.zoom}px`;
  $('#zoomLevel').textContent = `${Math.round(state.zoom * 100)}%`;
}

function setZoom(nextZoom) {
  state.zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, nextZoom));
  applyMapZoom();
}

// ---------------------------------------------------------------------
// Drag-and-drop movement + movement range highlight
// ---------------------------------------------------------------------

function onMarkerDragStart(event, unitId) {
  const unit = findUnit(unitId);
  if (!unit || !unit.friendly || !phaseAllowsMove(unit)) {
    event.preventDefault();
    return;
  }
  state.draggingUnitId = unitId;
  event.dataTransfer.setData('text/plain', unitId);
  event.dataTransfer.effectAllowed = 'move';
  renderUnitPanel(unitId);
}

function onMarkerDragEnd() {
  state.draggingUnitId = null;
}

function onMapGridDragOver(event) {
  const polygon = event.target.closest('polygon');
  if (polygon && polygon.classList.contains('reachable-hex')) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }
}

async function onMapGridDrop(event) {
  const polygon = event.target.closest('polygon');
  if (!polygon || !polygon.classList.contains('reachable-hex')) return;
  event.preventDefault();
  const unitId = event.dataTransfer.getData('text/plain') || state.draggingUnitId;
  if (!unitId) return;
  const q = Number(polygon.dataset.x);
  const r = Number(polygon.dataset.y);
  clearReachableHighlight();
  const result = await FlatTopApi.movePiece(state.gameId, state.side, unitId, q, r);
  handleCommandResult(result);
}

async function highlightReachableForSelection(unitId) {
  const unit = findUnit(unitId);
  if (!unit || !unit.friendly || !phaseAllowsMove(unit)) {
    clearReachableHighlight();
    return;
  }
  try {
    const { hexes } = await FlatTopApi.getReachableHexes(state.gameId, unitId);
    if (state.selectedUnitId !== unitId) return; // selection changed while awaiting
    state.reachableHexes = new Set(hexes.map(([q, r]) => `${q},${r}`));
    applyReachableHighlightClasses();
  } catch (error) {
    toast(`Could not compute movement range: ${error.message}`);
  }
}

function applyReachableHighlightClasses() {
  $$('#mapGrid polygon').forEach((polygon) => {
    const key = `${polygon.dataset.x},${polygon.dataset.y}`;
    polygon.classList.toggle('reachable-hex', state.reachableHexes.has(key));
  });
}

function clearReachableHighlight() {
  state.reachableHexes = new Set();
  $$('#mapGrid polygon').forEach((polygon) => polygon.classList.remove('reachable-hex'));
}

// ---------------------------------------------------------------------
// Unit selection / detail panel
// ---------------------------------------------------------------------

function findUnit(unitId) {
  return state.projection.units.find((u) => u.id === unitId);
}

function clearSelection() {
  state.selectedUnitId = null;
  clearReachableHighlight();
  $('#panelEyebrow').textContent = 'SELECTED UNIT';
  $('#panelTitle').textContent = 'No selection';
  $('#unitPanel').innerHTML = '';
  $('#selectedMapLabel').textContent = 'None';
}

function renderUnitPanel(unitId) {
  const unit = findUnit(unitId);
  if (!unit) return;
  state.selectedUnitId = unitId;
  $('#selectedMapLabel').textContent = unit.name;
  $('#panelEyebrow').textContent = unit.friendly ? 'SELECTED UNIT' : 'OBSERVED CONTACT';
  $('#panelTitle').textContent = unit.friendly ? unit.name : `${unit.kind} contact`;

  const stats = `
    <div class="stat-grid">
      <div><small>LOCATION</small><b>${unit.position[0]},${unit.position[1]}</b></div>
      <div><small>KIND</small><b>${unit.kind}</b></div>
      <div><small>CONDITION</small><b>${unit.friendly ? 'OWN' : `C${unit.observed_condition}`}</b></div>
      <div><small>MOVEMENT</small><b>${unit.has_moved ? 'Used' : unit.movement_factor}</b></div>
    </div>`;

  let body = '';
  if (unit.kind === 'Base' && unit.friendly) body = airOperationsPanel(unit);
  else if (unit.kind === 'TaskForce' && unit.friendly) body = taskForcePanel(unit);
  else if (unit.kind === 'AirFormation' && unit.friendly) body = airFormationPanel(unit);
  else body = `<p class="muted-copy">Only information legally observed by ${state.side} is shown for this contact.</p>`;

  $('#unitPanel').innerHTML = `
    <div class="unit-summary"><span class="large-unit-icon ${iconClassFor(unit)}">${iconFor(unit)}</span><div><strong>${unit.kind}</strong><span>${unit.side}</span></div></div>
    ${stats}
    <div class="panel-divider"></div>
    ${body}`;

  bindPanelActions(unit);
  renderForceList(state.projection);
  highlightReachableForSelection(unitId);
  $('#rightPanel').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function taskForcePanel(unit) {
  // Ship roster is intentionally not shown inline here - it's a popup, opened via "Inspect ship detail", matching the mockup.
  const carriersWithAir = (unit.ships || []).filter((s) => s.air_operations);
  const carrierPanels = carriersWithAir
    .map(
      (ship) => `
      <div class="subheading"><span>${ship.name} AIR OPERATIONS</span></div>
      ${airOpsPreview(ship.air_operations)}
      <button class="primary-action" data-action="open-operations" data-base="${unit.id}"><span>\u25a6</span> Open operations chart <b>\u2192</b></button>`
    )
    .join('');
  const moveDisabled = phaseAllowsMove(unit) ? '' : 'disabled title="Only available during the Task Force Movement phase"';
  return `
    ${carrierPanels}
    <div class="panel-divider"></div>
    <div class="subheading"><span>ACTIONS</span></div>
    <button class="secondary-action" data-action="move" data-unit="${unit.id}" ${moveDisabled}><span>\u2341</span> Move (enter target hex) <b>\u2192</b></button>
    <button class="secondary-action" data-action="inspect-ships" data-unit="${unit.id}"><span>\u2299</span> Inspect ship detail <b>\u2192</b></button>`;
}

function shipClassFor(type) {
  if (type === 'CV' || type === 'CVL') return 'carrier';
  if (['CA', 'CL'].includes(type)) return 'cruiser';
  return 'destroyer';
}

function airOperationsPanel(unit) {
  return `
    <div class="subheading"><span>AIR OPERATIONS</span></div>
    ${airOpsPreview(unit.air_operations)}
    <button class="primary-action" data-action="open-operations" data-base="${unit.id}"><span>\u25a6</span> Open operations chart <b>\u2192</b></button>`;
}

function airOpsPreview(airOps) {
  if (!airOps) return '<p class="muted-copy">No air operations data available.</p>';
  const allAircraft = [...airOps.ready, ...airOps.readying, ...airOps.just_landed];
  const rows = allAircraft
    .map((ac) => `<div><span class="plane-dot ${planeDotClassFor(ac.type)}"></span><span>${ac.type}</span><b>${ac.count}</b></div>`)
    .join('');
  return `
    <div class="capacity-bar">
      <div><span>Launch factor</span><b>${airOps.used_launch_factor} / ${airOps.launch_factor_max}</b></div>
      <div class="bar"><i style="width:${Math.min(100, (airOps.used_launch_factor / Math.max(1, airOps.launch_factor_max)) * 100)}%"></i></div>
      <small>Ready factor used ${airOps.used_ready_factor} / ${airOps.ready_factor}</small>
    </div>
    <div class="air-mini-list">${rows || '<p class="muted-copy">No aircraft on hand.</p>'}</div>`;
}

function planeDotClassFor(type) {
  const fighters = ['Wildcat', 'Zero', 'P-40', 'P-38', 'P-39'];
  const torpedoBombers = ['Devastator', 'Kate', 'Avenger'];
  if (fighters.includes(type)) return 'fighter';
  if (torpedoBombers.includes(type)) return 'torpedo';
  return 'bomber';
}

function airFormationPanel(unit) {
  const rows = (unit.aircraft || [])
    .map((ac) => `<div><span class="plane-dot ${planeDotClassFor(ac.type)}"></span><span>${ac.type}</span><b>${ac.count}</b><small>range ${ac.range_remaining}/${ac.range_factor}</small></div>`)
    .join('');
  const moveDisabled = phaseAllowsMove(unit) ? '' : 'disabled title="Only available during the Plane Movement phase"';
  return `
    <div class="subheading"><span>AIRCRAFT</span></div>
    <div class="air-mini-list">${rows}</div>
    <div class="panel-divider"></div>
    <div class="subheading"><span>ACTIONS</span></div>
    <button class="secondary-action" data-action="move" data-unit="${unit.id}" ${moveDisabled}><span>\u2341</span> Move (enter target hex) <b>\u2192</b></button>
    <button class="secondary-action" data-action="move" data-unit="${unit.id}" ${moveDisabled}><span>\u2193</span> Land (move onto a friendly base/carrier) <b>\u2192</b></button>`;
}

function phaseAllowsMove(unit) {
  const phase = state.projection.turn.phase;
  if (unit.kind === 'TaskForce') return phase === 'Task Force Movement';
  if (unit.kind === 'AirFormation') return phase === 'Plane Movement';
  return false;
}

function phaseAllowsAirOps() {
  return state.projection.turn.phase === 'Air Operations';
}

function bindPanelActions(unit) {
  $$('#unitPanel [data-action="move"]').forEach((button) =>
    button.addEventListener('click', async () => {
      const target = window.prompt('Move to hex "q,r":');
      if (!target) return;
      const [q, r] = target.split(',').map((n) => Number(n.trim()));
      if (Number.isNaN(q) || Number.isNaN(r)) return toast('Enter a target hex as "q,r".');
      const result = await FlatTopApi.movePiece(state.gameId, state.side, button.dataset.unit, q, r);
      handleCommandResult(result);
    })
  );
  $$('#unitPanel [data-action="open-operations"]').forEach((button) =>
    button.addEventListener('click', () => openOperationsModal(button.dataset.base))
  );
  $$('#unitPanel [data-action="inspect-ships"]').forEach((button) =>
    button.addEventListener('click', () => openShipRosterModal(button.dataset.unit))
  );
}

function handleCommandResult(result, reopenBaseId) {
  if (result.accepted === false) {
    toast(`${result.error.code}: ${result.error.message}`);
    return;
  }
  renderProjection(result.projection);
  if (reopenBaseId) openOperationsModal(reopenBaseId);
}

// ---------------------------------------------------------------------
// Operations tracker modal (Ready / Readying / Just Landed / In Flight)
// ---------------------------------------------------------------------

const pendingFormation = { baseId: null, formationNumber: 1, selections: {} };

function openOperationsModal(baseId) {
  if (pendingFormation.baseId !== baseId) {
    pendingFormation.baseId = baseId;
    pendingFormation.selections = {};
  }
  $('#modal').innerHTML = operationsModalMarkup(baseId);
  $('#modalBackdrop').hidden = false;
  bindOperationsModalActions(baseId);
}

function operationsModalMarkup(baseId) {
  const unit = findUnit(baseId);
  const airOps = unit.kind === 'Base' ? unit.air_operations : (unit.ships || []).find((s) => s.air_operations)?.air_operations;
  if (!airOps) {
    return modalShell('Air operations tracker', unit.name, '<div class="modal-body"><p>No air operations data available.</p></div>');
  }
  const canEdit = phaseAllowsAirOps();
  const remainingRf = airOps.ready_factor - airOps.used_ready_factor;
  const statusGroup = (label, list, statusKey) =>
    list.length
      ? `<tr class="status-row"><th colspan="19">${label}</th></tr>${list.map((ac) => aircraftRow(ac, statusKey, baseId, canEdit)).join('')}`
      : `<tr class="status-row"><th colspan="19">${label} \u00b7 none</th></tr>`;

  const pendingEntries = Object.entries(pendingFormation.selections).filter(([, count]) => count > 0);
  const pendingTotal = pendingEntries.reduce((sum, [, count]) => sum + count, 0);

  return modalShell(
    'Air operations tracker',
    `${unit.name} \u00b7 ${state.projection.turn.phase} phase${canEdit ? '' : ' \u00b7 read-only outside Air Operations phase'}`,
    `<div class="modal-body">
      <div class="air-ops-budget">
        <div><span>LAUNCH FACTOR</span><b>${airOps.launch_factor_max - airOps.used_launch_factor} remaining</b><small>${airOps.used_launch_factor} used of ${airOps.launch_factor_max} \u00b7 min ${airOps.launch_factor_min} \u00b7 normal ${airOps.launch_factor_normal}</small></div>
        <div><span>READYING FACTOR \u00b7 THIS TURN</span><b>${remainingRf} remaining</b><small>${airOps.used_ready_factor} used of ${airOps.ready_factor}</small></div>
      </div>
      <div class="tracker-toolbar"><span>Aircraft combat values</span><small>Values are shown before armament and attack selection</small></div>
      <div class="air-table-wrap">
        <table class="air-combat-table">
          <thead>
            <tr><th rowspan="2">Aircraft</th><th rowspan="2">Count</th><th rowspan="2">A2A</th><th colspan="6">vs Base</th><th colspan="7">vs Ship</th><th rowspan="2">Move</th><th rowspan="2">Range</th><th rowspan="2">Armament</th><th rowspan="2">Actions</th></tr>
            <tr><th colspan="2">High</th><th colspan="2">Low</th><th colspan="2">Dive</th><th colspan="2">High</th><th colspan="2">Low</th><th colspan="2">Dive</th><th>Torp</th></tr>
            <tr class="table-subhead"><th></th><th></th><th></th><th>GP</th><th>AP</th><th>GP</th><th>AP</th><th>GP</th><th>AP</th><th>GP</th><th>AP</th><th>GP</th><th>AP</th><th>GP</th><th>AP</th><th>TORP</th><th></th><th></th><th></th><th></th></tr>
          </thead>
          <tbody>
            ${statusGroup('READY \u00b7 select factors for the pending formation', airOps.ready, 'ready')}
            ${statusGroup('READYING', airOps.readying, 'readying')}
            ${statusGroup('JUST LANDED', airOps.just_landed, 'just_landed')}
            ${statusGroup('IN FLIGHT', airOps.in_flight, 'in_flight')}
          </tbody>
        </table>
      </div>
      <div class="formation-planner">
        <div class="formation-planner-head"><h3>Build Air Formation</h3><span class="condition-pill">${pendingTotal} selected</span></div>
        <div class="formation-controls">
          <label>Formation number
            <select id="formationNumberSelect">
              ${Array.from({ length: 35 }, (_, i) => i + 1)
                .map((n) => `<option value="${n}" ${n === pendingFormation.formationNumber ? 'selected' : ''}>${n}</option>`)
                .join('')}
            </select>
          </label>
          <label>Selected factors <strong>${pendingTotal} / ${airOps.launch_factor_max - airOps.used_launch_factor} LF</strong></label>
        </div>
        <div class="armament-list">
          ${pendingEntries.length ? pendingEntries.map(([type, count]) => `<div><span>${type} \u00b7 ${count}</span></div>`).join('') : '<div><span>No aircraft selected yet.</span></div>'}
        </div>
        <div class="modal-actions">
          <button type="button" class="ghost-button" data-action="close-modal">Close</button>
          <button type="button" class="primary-button" id="commitFormationButton" ${pendingTotal && canEdit ? '' : 'disabled'}>Create formation <span>&rarr;</span></button>
        </div>
      </div>
    </div>`
  );
}

function aircraftRow(ac, statusKey, baseId, canEdit) {
  const pendingCount = pendingFormation.selections[ac.type] || 0;
  const cd = ac.combat_data;
  const cells = [
    cd.air_to_air,
    cd.level_bombing_high_base_gp,
    cd.level_bombing_high_base_ap,
    cd.level_bombing_low_base_gp,
    cd.level_bombing_low_base_ap,
    cd.dive_bombing_base_gp,
    cd.dive_bombing_base_ap,
    cd.level_bombing_high_ship_gp,
    cd.level_bombing_high_ship_ap,
    cd.level_bombing_low_ship_gp,
    cd.level_bombing_low_ship_ap,
    cd.dive_bombing_ship_gp,
    cd.dive_bombing_ship_ap,
    cd.torpedo_bombing_ship,
  ]
    .map((value, index) => (index === 0 ? `<td class="combat-value">${value}</td>` : `<td class="combat-value">${value}</td>`))
    .join('');

  let controls = '';
  if (statusKey === 'ready') {
    controls = `
      <button class="table-step" data-pending-adjust="${ac.type}" data-delta="-1" ${canEdit ? '' : 'disabled'}>&minus;</button>
      <b>${pendingCount}</b>
      <button class="table-step" data-pending-adjust="${ac.type}" data-max="${ac.count}" data-delta="1" ${canEdit ? '' : 'disabled'}>+</button>
      <button class="table-step transfer" data-readiness data-base="${baseId}" data-type="${ac.type}" data-from="ready" data-to="readying" ${canEdit ? '' : 'disabled'}>&darr;</button>`;
  } else if (statusKey === 'readying') {
    controls = `
      <button class="table-step" data-readiness data-base="${baseId}" data-type="${ac.type}" data-from="readying" data-to="just_landed" title="Move to Just Landed" aria-label="Move ${ac.type} to Just Landed" ${canEdit ? '' : 'disabled'}>&minus;</button>
      <button class="table-step" data-readiness data-base="${baseId}" data-type="${ac.type}" data-from="readying" data-to="ready" title="Move to Ready" aria-label="Move ${ac.type} to Ready" ${canEdit ? '' : 'disabled'}>&plus;</button>`;
  } else if (statusKey === 'just_landed') {
    controls = `<button class="table-step" data-readiness data-base="${baseId}" data-type="${ac.type}" data-from="just_landed" data-to="readying" title="Move to Readying" aria-label="Move ${ac.type} to Readying" ${canEdit ? '' : 'disabled'}>&plus;</button>`;
  } else {
    controls = '<small class="muted-copy">airborne</small>';
  }

  const armamentLabel = ac.armament || 'None';
  const armamentOptions = armamentOptionsFor(cd);
  const canCycleArmament = canEdit && statusKey === 'readying' && armamentOptions.length > 1;
  const armamentCell = `<td><button class="armament-cycle ${canCycleArmament ? '' : 'locked'}" data-armament-cycle="${ac.type}" data-base="${baseId}" data-options='${JSON.stringify(armamentOptions)}' ${canCycleArmament ? '' : 'disabled'}>${armamentLabel}</button></td>`;

  return `<tr class="aircraft-row ${pendingCount ? 'selected' : ''}"><td>${ac.type}</td><td><b>${ac.count}</b></td>${cells}<td>${ac.move_factor}</td><td>${ac.range_remaining}/${ac.range_factor}</td>${armamentCell}<td><span class="aircraft-row-controls">${controls}</span></td></tr>`;
}

function armamentOptionsFor(cd) {
  const options = ['None'];
  if (cd.level_bombing_high_base_gp || cd.level_bombing_low_base_gp || cd.dive_bombing_base_gp || cd.level_bombing_high_ship_gp || cd.level_bombing_low_ship_gp || cd.dive_bombing_ship_gp) {
    options.push('GP');
  }
  if (cd.level_bombing_high_base_ap || cd.level_bombing_low_base_ap || cd.dive_bombing_base_ap || cd.level_bombing_high_ship_ap || cd.level_bombing_low_ship_ap || cd.dive_bombing_ship_ap) {
    options.push('AP');
  }
  if (cd.torpedo_bombing_ship) {
    options.push('Torpedo');
  }
  return options;
}

function bindOperationsModalActions(baseId) {
  $('#modal [data-action="close-modal"]').addEventListener('click', () => ($('#modalBackdrop').hidden = true));
  $('#formationNumberSelect')?.addEventListener('change', (event) => {
    pendingFormation.formationNumber = Number(event.target.value);
  });
  $$('#modal [data-pending-adjust]').forEach((button) =>
    button.addEventListener('click', () => {
      const type = button.dataset.pendingAdjust;
      const delta = Number(button.dataset.delta);
      const max = Number(button.dataset.max || Infinity);
      const next = Math.max(0, Math.min(max, (pendingFormation.selections[type] || 0) + delta));
      pendingFormation.selections[type] = next;
      openOperationsModal(baseId);
    })
  );
  $$('#modal [data-readiness]').forEach((button) =>
    button.addEventListener('click', async () => {
      const result = await FlatTopApi.readinessMove(
        state.gameId,
        state.side,
        button.dataset.base,
        button.dataset.type,
        button.dataset.from,
        button.dataset.to,
        1
      );
      handleCommandResult(result, baseId);
    })
  );
  $$('#modal [data-armament-cycle]').forEach((button) =>
    button.addEventListener('click', async () => {
      const options = JSON.parse(button.dataset.options);
      const currentIndex = options.indexOf(button.textContent.trim());
      const next = options[(currentIndex + 1) % options.length];
      const result = await FlatTopApi.setArmament(
        state.gameId,
        state.side,
        button.dataset.base,
        button.dataset.armamentCycle,
        next === 'None' ? null : next
      );
      handleCommandResult(result, baseId);
    })
  );
  $('#commitFormationButton')?.addEventListener('click', async () => {
    const aircraft = Object.entries(pendingFormation.selections)
      .filter(([, count]) => count > 0)
      .map(([type, count]) => ({ type, count }));
    if (!aircraft.length) return toast('Select at least one aircraft type.');
    const result = await FlatTopApi.createFormation(state.gameId, state.side, baseId, pendingFormation.formationNumber, aircraft);
    if (result.accepted !== false) {
      pendingFormation.selections = {};
      $('#modalBackdrop').hidden = true;
    }
    handleCommandResult(result);
  });
}

function modalShell(title, subtitle, body) {
  return `<div class="modal-head"><div><p class="eyebrow">COMMAND VIEW</p><h2 id="modalTitle">${title}</h2><p>${subtitle}</p></div><button class="modal-close" data-action="close-modal" aria-label="Close">&times;</button></div>${body}`;
}

// ---------------------------------------------------------------------
// Ship roster modal
// ---------------------------------------------------------------------

function openShipRosterModal(unitId) {
  const unit = findUnit(unitId);
  const rows = (unit.ships || [])
    .map(
      (ship) => `
      <div class="ship-roster-row">
        <span><strong>${ship.name}</strong><small>${ship.type}</small></span>
        <b>${ship.type}</b><b>${ship.gunnery_factor}</b><b>${ship.anti_air_factor}</b><b>${ship.torpedo_factor}</b><b>${ship.move_factor}</b><b>${ship.damage} / ${ship.damage_factor}</b><b>${ship.status}</b>
      </div>`
    )
    .join('');
  $('#modal').innerHTML = modalShell(
    unit.name,
    'Ship detail \u00b7 roster combat and operations values',
    `<div class="modal-body">
      <div class="ship-roster ship-roster-table">
        <div class="ship-roster-header"><span>Ship</span><span>Class</span><span>Gun</span><span>AA</span><span>Torp</span><span>MF</span><span>Damage</span><span>Status</span></div>
        ${rows}
      </div>
    </div>`
  );
  $('#modalBackdrop').hidden = false;
  $('#modal [data-action="close-modal"]').addEventListener('click', () => ($('#modalBackdrop').hidden = true));
}

// ---------------------------------------------------------------------
// Misc UI wiring
// ---------------------------------------------------------------------

function toast(message) {
  const el = $('#toast');
  el.textContent = message;
  el.classList.add('show');
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => el.classList.remove('show'), 3000);
}

async function advancePhase() {
  try {
    const projection = await FlatTopApi.advancePhase(state.gameId, state.side);
    renderProjection(projection);
  } catch (error) {
    toast(`Could not advance phase: ${error.message}`);
  }
}

function bindGlobalActions() {
  document.body.addEventListener('click', (event) => {
    const button = event.target.closest('[data-action]');
    if (!button) return;
    const action = button.dataset.action;
    if (action === 'advance') advancePhase();
    else if (action === 'clear-selection') clearSelection();
    else if (action === 'close-modal') $('#modalBackdrop').hidden = true;
    else if (action === 'log') openLogModal();
    else if (action === 'zoom-in') setZoom(state.zoom + 0.2);
    else if (action === 'zoom-out') setZoom(state.zoom - 0.2);
    else if (action === 'zoom-reset') setZoom(1);
  });
  $('#modalBackdrop').addEventListener('click', (event) => {
    if (event.target.id === 'modalBackdrop') $('#modalBackdrop').hidden = true;
  });
  $('#startGameButton').addEventListener('click', startNewGame);
  $('#mapGrid').addEventListener('dragover', onMapGridDragOver);
  $('#mapGrid').addEventListener('drop', onMapGridDrop);
}

function openLogModal() {
  const log = state.projection?.log || [];
  $('#modal').innerHTML = `
    <div class="modal-head"><div><h2 id="modalTitle">Event log</h2><p>Most recent events for this game.</p></div><button class="modal-close" data-action="close-modal">&times;</button></div>
    <div class="modal-body">${log.map((line) => `<div class="ledger-row"><span>&bull;</span><div>${line}</div></div>`).join('') || '<p>No events yet.</p>'}</div>`;
  $('#modalBackdrop').hidden = false;
}

bindGlobalActions();
initNewGameScreen();
