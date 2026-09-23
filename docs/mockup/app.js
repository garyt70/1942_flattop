const state = {
  selected: 'tf7',
  phaseIndex: 1,
  phaseNames: ['WEATHER', 'AIR OPERATIONS', 'TASK FORCE MOVEMENT PLOTTING', 'SHADOWING', 'TASK FORCE MOVEMENT', 'INITIATIVE', 'PLANE MOVEMENT', 'COMBAT'],
  overlay: 'movement',
  zoom: 1,
  launchMode: 'normal',
  scenario: 'one',
  formationNumber: 19,
  formationSelection: { wildcat: 0, dauntless: 0, devastator: 0 },
  formationArmament: { wildcat: 'None', dauntless: 'GP', devastator: 'Torpedo' },
  pendingPiece: null
};

const units = {
  tf7: { title: 'Task Force 7', eyebrow: 'SELECTED UNIT', type: 'Carrier task force', detail: 'Allied · observed by enemy', icon: 'CV', iconClass: 'carrier', condition: 'C3', location: 'CC16', stats: [['SHIPS','7'],['MF','3'],['STATUS','Ready']], note: 'Weather front reaches CC18 next turn. Aircraft in formation 18 must land by 1400.' },
  air18: { title: 'Air Formation 18', eyebrow: 'SELECTED UNIT', type: 'Strike formation', detail: 'Allied · low altitude · airborne', icon: '✦', iconClass: 'air', condition: 'C2', location: 'BB14', stats: [['AIR FACTORS','16'],['RF DUE','1400'],['STATUS','In flight']], note: 'Formation has 4 movement points remaining. Landing at Task Force 7 is possible if it turns east.' },
  base: { title: 'Port Moresby', eyebrow: 'SELECTED BASE', type: 'Air operations base', detail: 'Allied · friendly base · coastwatcher', icon: '⌂', iconClass: 'base', condition: 'OWN', location: 'AA09', stats: [['LF','8 / 4'],['DAMAGE','1'],['STATUS','Repairable']], note: 'Base was not attacked this turn. Repair phase will restore one damage point.' }
};

const landBoardOne = [[0,9],[0,10],[0,11],[0,12],[0,13],[0,14],[0,15],[0,16],[0,17],[0,18],[0,19],[0,20],[0,21],[0,22],[0,23],[1,9],[1,10],[1,11],[1,12],[1,13],[1,14],[1,15],[1,16],[1,17],[1,18],[1,19],[1,20],[1,21],[1,22],[1,23],[2,5],[2,10],[2,11],[2,12],[2,13],[2,14],[2,15],[2,16],[2,17],[2,18],[2,19],[2,20],[2,21],[2,22],[2,23],[3,7],[3,10],[3,11],[3,12],[3,16],[3,17],[3,18],[3,19],[3,20],[3,21],[3,22],[3,23],[3,24],[4,8],[4,17],[4,18],[4,19],[4,20],[4,21],[4,22],[4,23],[4,24],[4,25],[4,26],[5,8],[5,17],[5,18],[5,19],[5,20],[5,21],[5,22],[5,23],[5,24],[5,25],[5,26],[6,8],[6,20],[6,21],[6,22],[6,23],[6,24],[6,25],[6,26],[6,28],[7,7],[7,8],[7,21],[7,22],[7,23],[7,24],[7,25],[7,26],[7,27],[8,7],[8,8],[8,9],[8,21],[8,22],[8,23],[8,24],[8,25],[8,26],[8,27],[9,8],[9,9],[9,10],[9,21],[9,22],[9,23],[9,24],[9,25],[9,26],[9,27],[10,8],[10,9],[10,10],[10,21],[10,23],[10,24],[10,25],[10,26],[10,27],[11,8],[11,9],[11,10],[11,23],[11,24],[11,25],[11,26],[11,27],[12,7],[12,8],[12,9],[12,10],[12,24],[12,25],[12,26],[12,27],[13,6],[13,7],[13,8],[13,9],[13,10],[13,24],[13,26],[13,27],[14,5],[14,6],[14,7],[14,8],[14,9],[14,10],[14,26],[14,27],[15,7],[15,8],[15,9],[15,10],[15,26],[15,27],[16,7],[16,8],[16,9],[16,10],[16,26],[16,27],[17,7],[17,8],[17,9],[17,26],[17,27],[18,7],[18,8],[18,9],[18,26],[18,27],[19,7],[19,8],[19,9],[19,26],[19,27],[20,7],[20,8],[20,9],[20,26],[20,27],[21,3],[21,4],[21,5],[21,6],[21,7],[21,8],[21,9],[22,0],[22,4],[22,5],[22,6],[22,7],[22,8],[22,9],[23,0],[23,1],[23,3],[23,4],[23,6],[23,7],[24,2],[25,2],[25,3],[25,4],[26,3],[26,4],[33,6],[33,7],[34,8],[34,9],[34,10],[34,11],[34,12],[35,9],[35,10],[35,11],[35,12],[35,13],[35,14],[36,11],[36,12],[36,13],[36,14],[37,13],[37,14]];
const landBoardTwo = [[38,16],[39,16],[40,14],[41,14],[41,16],[41,17],[42,15],[42,17],[42,18],[43,17],[43,18],[44,16],[44,18],[44,19],[45,18],[45,19],[47,16],[47,17],[47,21],[48,18],[48,22],[48,23],[49,18],[49,19],[49,23],[78,35],[78,36],[79,35]];

const BOARD_ONE_LABEL = 'Board One';
const BOARD_TWO_LABEL = 'Board Two';
const MOCK_HEX_SIZE = 20;
const scenarios = {
    one: {
      sourceSetup: 'scenario_one_setup', boardLabel: BOARD_ONE_LABEL, dimensionLabel: '44x50',
      displayOrigin: [0, 0],
      name: 'Scenario One · Coral Sea approach', dimensions: [44, 50], land: landBoardOne,
      bases: [
        ['Rabaul','J',[23,4]], ['Gasmata','J',[14,10]], ['Kavieng','J',[12,0]], ['Truk','J',[17,0]],
        ['Port Moresby','A',[3,23]]
      ],
      forces: [
        { id:'allied-tf1', title:'Allied Task Force 1', side:'A', icon:'CV', type:'Carrier task force', detail:'CV Lexington · 4 cruisers · 10 destroyers', pos:[20,10], ships:'15 ships', air:'8 F4F · 12 SBD · 4 TBD' },
        { id:'j-air1', title:'Japanese Air Formation 1', side:'J', icon:'✦', type:'Air formation contact', detail:'6 Zero · 4 Val · low altitude', pos:[10,10], ships:'', air:'10 aircraft' }
      ]
    },
    two: {
      sourceSetup: 'scenario_two_setup', boardLabel: `${BOARD_ONE_LABEL} + ${BOARD_TWO_LABEL}`, dimensionLabel: '80x50',
      displayOrigin: [0, 0],
      name: 'Scenario Two · Coral Sea', dimensions: [80, 50], land: [...landBoardOne, ...landBoardTwo],
      bases: [
        ['Rabaul','J',[23,4]], ['Gasmata','J',[14,10]], ['Kavieng','J',[12,0]], ['Truk','J',[17,0]], ['Lae','J',[2,13]], ['Shortland','J',[38,16]],
        ['Port Moresby','A',[3,23]], ['Australia','A',[0,49]], ['New Caledonia','A',[70,49]]
      ],
      forces: [
        { id:'lexington', title:'Lexington Task Force', side:'A', icon:'CV', type:'Carrier task force', detail:'CV Lexington · Chester · New Orleans · Astoria · Portland · 7 DD · 2 AO', pos:[35,45], ships:'17 ships', air:'7 F4F · 12 SBD · 4 TBD' },
        { id:'yorktown', title:'Yorktown Task Force', side:'A', icon:'CV', type:'Carrier task force', detail:'CV Yorktown · Minneapolis · Australia · Chicago · Hobart · 7 DD', pos:[40,35], ships:'12 ships', air:'7 F4F · 12 SBD · 4 TBD' },
        { id:'shokaku', title:'Shokaku Task Force', side:'J', icon:'CV', type:'Carrier task force contact', detail:'CV Shokaku · 4 cruisers · 4 destroyers', pos:[30,10], ships:'9 ships', air:'8 Zero · 7 Val · 7 Kate' },
        { id:'zuikaku', title:'Zuikaku Task Force', side:'J', icon:'CV', type:'Carrier task force contact', detail:'CV Zuikaku · 4 cruisers · 4 destroyers', pos:[32,10], ships:'9 ships', air:'8 Zero · 7 Val · 7 Kate' },
        { id:'shoho', title:'Shoho Task Force', side:'J', icon:'CV', type:'Light carrier contact', detail:'CV Shoho · AV Kamikawa · 6 destroyers', pos:[28,10], ships:'8 ships', air:'3 Kate · 3 Dave · 4 Pete' },
        { id:'landing1a', title:'Landing Force 1a', side:'J', icon:'AP', type:'Landing force contact', detail:'6 AP · 2 PG · AO · DD', pos:[26,5], ships:'10 ships', air:'none' },
        { id:'landing1b', title:'Landing Force 1b', side:'J', icon:'AP', type:'Landing force contact', detail:'6 AP · 2 PG · AO · DD', pos:[26,5], ships:'10 ships', air:'none' },
        { id:'landing2', title:'Landing Force 2', side:'J', icon:'AP', type:'Landing force contact', detail:'Tatsuta · AP · 3 DD · 4 PG', pos:[27,10], ships:'9 ships', air:'none' }
      ]
    }
  };
/*
    sourceSetup: 'scenario_one_setup', boardLabel: BOARD_ONE_LABEL, dimensionLabel: '44x50',
    displayOrigin: [0, 0],
    name: 'Scenario One · Coral Sea approach', dimensions: [44, 50], land: landBoardOne,
    bases: [
      ['Rabaul','J',[23,4]], ['Gasmata','J',[14,10]], ['Kavieng','J',[12,0]], ['Truk','J',[17,0]],
      ['Port Moresby','A',[3,23]]
    ],
    forces: [
      { id:'allied-tf1', title:'Allied Task Force 1', side:'A', icon:'CV', type:'Carrier task force', detail:'CV Lexington · 4 cruisers · 10 destroyers', pos:[20,10], ships:'15 ships', air:'8 F4F · 12 SBD · 4 TBD' },
      { id:'j-air1', title:'Japanese Air Formation 1', side:'J', icon:'✦', type:'Air formation contact', detail:'6 Zero · 4 Val · low altitude', pos:[10,10], ships:'', air:'10 aircraft' }
    ]
  },
  two: {
    sourceSetup: 'scenario_two_setup', boardLabel: `${BOARD_ONE_LABEL} + ${BOARD_TWO_LABEL}`, dimensionLabel: '80x50',
    displayOrigin: [0, 0],
    name: 'Scenario Two · Coral Sea', dimensions: [80, 50], land: [...landBoardOne, ...landBoardTwo],
    bases: [
      ['Rabaul','J',[23,4]], ['Gasmata','J',[14,10]], ['Kavieng','J',[12,0]], ['Truk','J',[17,0]], ['Lae','J',[2,13]], ['Shortland','J',[38,16]],
      ['Port Moresby','A',[3,23]], ['Australia','A',[0,49]], ['New Caledonia','A',[70,49]]
    ],
    forces: [
      { id:'lexington', title:'Lexington Task Force', side:'A', icon:'CV', type:'Carrier task force', detail:'CV Lexington · Chester · New Orleans · Astoria · Portland · 7 DD · 2 AO', pos:[35,45], ships:'17 ships', air:'7 F4F · 12 SBD · 4 TBD' },
      { id:'yorktown', title:'Yorktown Task Force', side:'A', icon:'CV', type:'Carrier task force', detail:'CV Yorktown · Minneapolis · Australia · Chicago · Hobart · 7 DD', pos:[40,35], ships:'12 ships', air:'7 F4F · 12 SBD · 4 TBD' },
      { id:'shokaku', title:'Shokaku Task Force', side:'J', icon:'CV', type:'Carrier task force contact', detail:'CV Shokaku · 4 cruisers · 4 destroyers', pos:[30,10], ships:'9 ships', air:'8 Zero · 7 Val · 7 Kate' },
      { id:'zuikaku', title:'Zuikaku Task Force', side:'J', icon:'CV', type:'Carrier task force contact', detail:'CV Zuikaku · 4 cruisers · 4 destroyers', pos:[32,10], ships:'9 ships', air:'8 Zero · 7 Val · 7 Kate' },
      { id:'shoho', title:'Shoho Task Force', side:'J', icon:'CV', type:'Light carrier contact', detail:'CV Shoho · AV Kamikawa · 6 destroyers', pos:[28,10], ships:'8 ships', air:'3 Kate · 3 Dave · 4 Pete' },
      { id:'landing1a', title:'Landing Force 1a', side:'J', icon:'AP', type:'Landing force contact', detail:'6 AP · 2 PG · AO · DD', pos:[26,5], ships:'10 ships', air:'none' },
      { id:'landing1b', title:'Landing Force 1b', side:'J', icon:'AP', type:'Landing force contact', detail:'6 AP · 2 PG · AO · DD', pos:[26,5], ships:'10 ships', air:'none' },
      { id:'landing2', title:'Landing Force 2', side:'J', icon:'AP', type:'Landing force contact', detail:'Tatsuta · AP · 3 DD · 4 PG', pos:[27,10], ships:'9 ships', air:'none' }
    ]
  }
};
*/

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function renderScenario(scenarioId) {
  const scenario = scenarios[scenarioId];
  const displayDimensions = getDisplayDimensions(scenario);
  state.scenario = scenarioId;
  scenario.bases.forEach(([name, side, position]) => {
    units[`base-${name}`] = { title: name, eyebrow: side === 'A' ? 'SELECTED BASE' : 'KNOWN BASE', type: 'Air operations base', detail: `${side === 'A' ? 'Allied' : 'Japanese'} · scenario setup location`, icon: '⌂', iconClass: 'base', condition: side === 'A' ? 'OWN' : 'MAP', location: `${position[0]},${position[1]}`, stats: [['LF', name === 'Rabaul' ? '6 / 12 / 24' : '4 / 8 / 16'], ['AA', name === 'Rabaul' ? '8' : '5'], ['STATUS', 'Operational']], note: `${name} is defined at source coordinate (${position[0]}, ${position[1]}) in ${scenario.name}.` };
  });
  $('#mapTitle').textContent = scenario.name;
  $('#mapSubtitle').textContent = `${scenario.dimensionLabel} source · view starts at y=${scenario.displayOrigin[1]} · ${scenario.sourceSetup}`;
  $('#forceCount').textContent = `${scenario.forces.filter(force => force.side === 'A').length} groups`;
  $('#mapGrid').innerHTML = renderHexBoard(scenario);
  const baseMarkers = scenario.bases.map(([name, side, [x, y]]) => markerMarkup(`base-${name}`, 'base', side, name, x, y, scenario)).join('');
  const forceMarkers = scenario.forces.map(force => markerMarkup(force.id, 'force', force.side, force.title, force.pos[0], force.pos[1], scenario)).join('');
  $('#mapOverlays').innerHTML = baseMarkers + forceMarkers;
  $('#mapGrid').style.setProperty('--board-width', scenario.dimensions[0]);
  $('#mapGrid').style.setProperty('--board-height', scenario.dimensions[1]);
  const geometry = hexGeometry(displayDimensions);
  const boardWidth = geometry.viewWidth * MOCK_HEX_SIZE;
  const boardHeight = geometry.viewHeight * MOCK_HEX_SIZE;
  $('#mapGrid').style.width = `${boardWidth}px`;
  $('#mapGrid').style.height = `${boardHeight}px`;
  $('#mapOverlays').style.width = `${boardWidth}px`;
  $('#mapOverlays').style.height = `${boardHeight}px`;
  $('#mapContent').style.width = `${boardWidth + 40}px`;
  $('#mapContent').style.height = `${boardHeight + 40}px`;
  applyMapZoom();
  $('#mapGrid').style.aspectRatio = 'auto';
  $('#mapOverlays').style.aspectRatio = 'auto';
  $('#mapCanvas').classList.toggle('wide-board', scenario.dimensions[0] > 44);
  const forceCards = scenario.forces.filter(force => force.side === 'A').map(force => `<button class="force-card ${force.id === state.selected ? 'selected' : ''}" data-unit="${force.id}"><span class="unit-icon ${force.icon === 'AP' ? 'base' : 'carrier'}">${force.icon}</span><span><strong>${force.title}</strong><small>${force.detail}</small></span><i class="unit-state ready-state"></i></button>`).join('');
  $('.fleet-section').innerHTML = `<div class="section-heading"><span>YOUR FORCES</span><span class="muted" id="forceCount">${scenario.forces.filter(force => force.side === 'A').length} groups</span></div>${forceCards}`;
  scenario.forces.filter(force => force.side === 'J').forEach(force => { units[force.id] = forceToUnit(force); });
  scenario.forces.filter(force => force.side === 'A').forEach(force => { units[force.id] = forceToUnit(force); });
  bindDynamicActions();
  $$('.force-card[data-unit]').forEach(button => button.addEventListener('click', () => renderUnit(button.dataset.unit)));
  $$('[data-map-piece]').forEach(button => button.addEventListener('click', () => { state.pendingPiece = button.dataset.mapPiece; openModal('piece-menu'); }));
}

function getDisplayDimensions(scenario) {
  return [scenario.dimensions[0], scenario.dimensions[1] - scenario.displayOrigin[1]];
}

function applyMapZoom() {
  const content = $('#mapContent');
  const viewport = $('#mapViewport');
  if (!content || !viewport) return;
  const width = content.offsetWidth;
  const height = content.offsetHeight;
  viewport.style.width = `${width * state.zoom}px`;
  viewport.style.height = `${height * state.zoom}px`;
  content.style.transform = `scale(${state.zoom})`;
  content.style.transformOrigin = 'top left';
}

function hexGeometry(dimensions) {
  const [columns, rows] = dimensions;
  return { viewWidth: 1.5 * (columns - 1) + 2, viewHeight: Math.sqrt(3) * (rows + 0.5) };
}

function hexCenter(q, r) {
  return { x: 1.5 * q + 1, y: Math.sqrt(3) * (r + 0.5 * (q % 2) + 0.5) };
}

function renderHexBoard(scenario) {
  const [columns, rows] = getDisplayDimensions(scenario);
  const hexRadius = 1;
  const hexHeight = Math.sqrt(3) * hexRadius;
  const { viewWidth, viewHeight } = hexGeometry(scenario.dimensions);
  const originY = scenario.displayOrigin[1];
  const land = new Set(scenario.land.filter(([, y]) => y >= originY).map(([x, y]) => `${x},${y - originY}`));
  const polygons = [];
  for (let x = 0; x < columns; x += 1) {
    for (let y = 0; y < rows; y += 1) {
      const center = hexCenter(x, y);
      const centerX = center.x;
      const centerY = center.y;
      const points = [
        [centerX + hexRadius, centerY], [centerX + hexRadius * 0.5, centerY - hexHeight * 0.5],
        [centerX - hexRadius * 0.5, centerY - hexHeight * 0.5], [centerX - hexRadius, centerY],
        [centerX - hexRadius * 0.5, centerY + hexHeight * 0.5], [centerX + hexRadius * 0.5, centerY + hexHeight * 0.5]
      ].map(([pointX, pointY]) => `${pointX},${pointY}`).join(' ');
      polygons.push(`<polygon class="${land.has(`${x},${y}`) ? 'land-hex' : 'sea-hex'}" points="${points}" data-x="${x}" data-y="${y}" />`);
    }
  }
  return `<svg class="hex-board" viewBox="0 0 ${viewWidth} ${viewHeight}" preserveAspectRatio="none" role="img" aria-label="${scenario.name} hex map">${polygons.join('')}</svg>`;
}

function markerMarkup(id, kind, side, label, x, y, scenario) {
  const displayDimensions = getDisplayDimensions(scenario);
  const geometry = hexGeometry(displayDimensions);
  const displayY = y - scenario.displayOrigin[1];
  const center = hexCenter(x, displayY);
  const left = (center.x / geometry.viewWidth) * 100;
  const top = (center.y / geometry.viewHeight) * 100;
  const enemy = side === 'J';
  const icon = kind === 'base' ? '⌂' : enemy ? '?' : label.includes('Task') ? 'A' : '✦';
  return `<button class="map-unit ${kind}-unit ${enemy ? 'enemy-unit' : ''}" style="left:${left}%;top:${top}%" data-map-piece="${id}" data-${enemy ? 'contact' : 'unit'}="${id}" title="${label} · source hex ${x},${y} · view row ${displayY}"><span class="map-unit-badge ${enemy ? 'enemy-badge' : 'allied-badge'}">${icon}</span><span class="map-unit-label">${label} <em>[${x},${y}] / view ${displayY}</em></span>${kind === 'force' && !enemy ? '<i class="unit-pulse"></i>' : ''}</button>`;
}

function forceToUnit(force) {
  return { title: force.title, eyebrow: force.side === 'A' ? 'SELECTED TASK FORCE' : 'OBSERVED CONTACT', type: force.type, detail: `${force.side === 'A' ? 'Allied' : 'Japanese'} · ${force.detail}`, icon: force.icon, iconClass: force.icon === 'AP' ? 'base' : 'carrier', condition: force.side === 'A' ? 'OWN' : 'C2', location: `${force.pos[0]},${force.pos[1]}`, stats: [['SHIPS', force.ships || ''], ['AIR', force.air || ''], ['STATUS', force.side === 'A' ? 'Ready' : 'Contact']], note: `${force.title} is positioned at source coordinate (${force.pos[0]}, ${force.pos[1]}). This mock displays scenario setup data without resolving movement or combat.` };
}

function toast(message) {
  const element = $('#toast');
  element.textContent = message;
  element.classList.add('show');
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => element.classList.remove('show'), 2600);
}

function renderUnit(unitId) {
  const unit = units[unitId];
  if (!unit) return;
  state.selected = unitId;
  $('#panelEyebrow').textContent = unit.eyebrow;
  $('#panelTitle').textContent = unit.title;
  const stats = unit.stats.map(([label, value]) => `<div><small>${label}</small><b class="${value === 'Ready' ? 'text-green' : ''}">${value}</b></div>`).join('');
  $('#unitPanel').innerHTML = `
    <div class="unit-summary"><span class="large-unit-icon ${unit.iconClass}">${unit.icon}</span><div><strong>${unit.type}</strong><span>${unit.detail}</span></div><span class="condition-pill">${unit.condition}</span></div>
    <div class="stat-grid"><div><small>LOCATION</small><b>${unit.location}</b></div>${stats}</div>
    <div class="panel-divider"></div>
    <div class="subheading"><span>${unitId === 'base' ? 'BASE OPERATIONS' : 'AIR OPERATIONS'}</span><button class="text-button" data-action="operations">Open chart</button></div>
    ${unitId === 'base' ? basePanel() : airPanel(unitId)}
    <div class="panel-divider"></div>
    <div class="subheading"><span>AVAILABLE ACTIONS</span></div>
    <button class="primary-action" data-action="${unitId === 'base' ? 'operations' : 'operations'}"><span>▦</span> ${unitId === 'base' ? 'Manage base operations' : 'Manage air operations'} <b>→</b></button>
    <button class="secondary-action" data-action="plot"><span>⌁</span> ${unitId === 'base' ? 'View coverage' : 'Plot movement'} <b>→</b></button>
    <button class="secondary-action" data-action="inspect"><span>⊙</span> Inspect detail <b>→</b></button>
    <div class="warning-callout"><strong>Planning note</strong><p>${unit.note}</p></div>`;
  $$('.force-card').forEach(card => card.classList.toggle('selected', card.dataset.unit === unitId));
  bindDynamicActions();
}

function airPanel(unitId) {
  if (unitId === 'air18') return `<div class="capacity-bar"><div><span>Flight endurance</span><b>2 turns</b></div><div class="bar"><i style="width: 42%; background:var(--yellow)"></i></div><small>Must land by 1400 · RF consumed: 3</small></div><div class="air-mini-list"><div><span class="plane-dot bomber"></span><span>SBD Dauntless</span><b>10</b><small>armed</small></div><div><span class="plane-dot fighter"></span><span>F4F Wildcat</span><b>6</b><small>escort</small></div></div><div class="air-combat-preview"><div><span>COMBAT DETAIL</span><b>Formation profile</b></div><div class="combat-preview-row"><span>SBD · AP · dive</span><b>6 BHT</b></div><div class="combat-preview-row"><span>F4F · escort</span><b>9 A2A</b></div><small>16 factors · click Inspect detail for the full combat profile</small></div>`;
  return `<div class="capacity-bar"><div><span>Launch factor</span><b>11 / 3</b></div><div class="bar"><i style="width: 72%"></i></div><small>7 aircraft ready · 4 in flight</small></div><div class="air-mini-list"><div><span class="plane-dot fighter"></span><span>F4F Wildcat</span><b>6</b><small>ready</small></div><div><span class="plane-dot bomber"></span><span>SBD Dauntless</span><b>8</b><small>readying</small></div><div><span class="plane-dot torpedo"></span><span>TBD Devastator</span><b>4</b><small>just landed</small></div></div><div class="air-combat-preview"><div><span>COMBAT DETAIL</span><b>Ready aircraft</b></div><div class="combat-preview-row"><span>F4F · air-to-air</span><b>9 BHT</b></div><div class="combat-preview-row"><span>SBD · low GP</span><b>5 BHT</b></div><div class="combat-preview-row"><span>TBD · torpedo</span><b>6 BHT</b></div><small>Values update with armament, altitude, and range remaining</small></div>`;
}

function basePanel() {
  return `<div class="capacity-bar"><div><span>Launch factor</span><b>8 / 4</b></div><div class="bar"><i style="width: 54%; background:var(--coral)"></i></div><small>1 damage · 8 readying moves remaining</small></div><div class="air-mini-list"><div><span class="plane-dot fighter"></span><span>P-40 Warhawk</span><b>12</b><small>ready</small></div><div><span class="plane-dot bomber"></span><span>B-17 Fortress</span><b>4</b><small>readying</small></div></div>`;
}

function openModal(type) {
  const backdrop = $('#modalBackdrop');
  const modal = $('#modal');
  let content = '';
  if (type === 'operations') content = interactiveOperationsModal();
  if (type === 'piece-menu') content = pieceMenuModal(state.pendingPiece);
  if (type === 'details') content = detailsModal(state.pendingPiece);
  if (type === 'combat') content = combatModal();
  if (type === 'score') content = scoreModal();
  if (type === 'rules' || type === 'help') content = rulesModal();
  if (type === 'log') content = logModal();
  content = content.replace('>A2A</th>', '>Air2Air</th>');
  modal.innerHTML = content;
  renderOperationsCombatDetails();
  backdrop.hidden = false;
  bindDynamicActions();
}

function pieceMenuModal(unitId) {
  const unit = units[unitId] || { title: unitId, type: 'Map piece' };
  const isAir = unit.type && unit.type.toLowerCase().includes('air');
  return modalShell(unit.title, `${unit.type} · phase-aware actions`, `<div class="modal-body piece-action-list"><button class="secondary-action" data-piece-action="details"><span>⊙</span> Details <b>→</b></button>${isAir ? '<button class="secondary-action" data-piece-action="land"><span>↓</span> Land formation <b>→</b></button>' : ''}<button class="secondary-action" data-piece-action="move"><span>⌁</span> Move <b>→</b></button><button class="secondary-action" data-piece-action="combat"><span>⚔</span> Combat <b>→</b></button><button class="ghost-button" data-action="close-modal">Cancel</button></div>`);
}

function aircraftDetailsModal() {
  return modalShell('F4F Wildcat', 'Aircraft combat detail · Task Force 7 · Ready', `<div class="modal-body"><div class="detail-hero"><span class="large-unit-icon air">✦</span><div><strong>Fighter · factor 6</strong><small>Ready · armament None · altitude unrestricted</small></div><span class="condition-pill">READY</span></div><div class="detail-section"><h3>PERFORMANCE</h3><div class="detail-grid"><div><small>MOVEMENT</small><b>8 hexes</b></div><div><small>RANGE</small><b>6 factors</b></div><div><small>RANGE LEFT</small><b>6</b></div><div><small>ATTACK TYPE</small><b>Air / escort</b></div></div></div><div class="detail-section"><h3>COMBAT DATA</h3><div class="detail-table"><div><span>Air-to-air</span><b>9 BHT</b><em>intercept / escort</em></div><div><span>Low bombing</span><b>4 GP BHT</b><em>ship or base</em></div><div><span>High bombing</span><b>unavailable</b><em>no high-level value</em></div><div><span>Torpedo</span><b>unavailable</b><em>no torpedo payload</em></div></div></div><div class="detail-section"><h3>FORMATION EFFECT</h3><div class="formula">6 factors × air-to-air BHT 9 · escort assigned · no armament selected</div><p class="muted-copy">Combat values are read from the aircraft catalog. Armament and altitude determine which BHT entry is legal for the attack.</p></div><div class="detail-actions"><button class="primary-action" data-action="close-modal"><span>×</span> Close detail <b>→</b></button></div></div>`);
}

function shipDetailsModal() {
  return modalShell('Lexington task force', 'Ship detail · individual records and derived combat state', `<div class="modal-body"><div class="detail-hero"><span class="large-unit-icon carrier">CV</span><div><strong>Allied carrier task force</strong><small>Source coordinate CC16 · 7 ships · operational screen</small></div><span class="condition-pill">C3</span></div><div class="detail-section"><h3>SHIP ROSTER</h3><div class="ship-roster"><button class="ship-card selected"><span class="ship-class carrier">CV</span><span><strong>USS Lexington</strong><small>Carrier · damage 0 / 6</small></span><b>MF 2</b></button><button class="ship-card"><span class="ship-class cruiser">CA</span><span><strong>USS Minneapolis</strong><small>Heavy cruiser · damage 1 / 5</small></span><b>MF 2</b></button><button class="ship-card"><span class="ship-class cruiser">CA</span><span><strong>USS San Francisco</strong><small>Heavy cruiser · damage 0 / 5</small></span><b>MF 2</b></button><button class="ship-card"><span class="ship-class cruiser">CA</span><span><strong>USS Indianapolis</strong><small>Heavy cruiser · damage 0 / 5</small></span><b>MF 2</b></button><button class="ship-card"><span class="ship-class destroyer">DD</span><span><strong>USS Morris</strong><small>Destroyer · damage 0 / 3</small></span><b>MF 3</b></button><button class="ship-card"><span class="ship-class destroyer">DD</span><span><strong>USS Anderson</strong><small>Destroyer · damage 0 / 3</small></span><b>MF 3</b></button><button class="ship-card"><span class="ship-class destroyer">DD</span><span><strong>USS Hughes</strong><small>Destroyer · damage 0 / 3</small></span><b>MF 3</b></button></div></div><div class="detail-section"><h3>SELECTED SHIP · USS LEXINGTON</h3><div class="detail-grid"><div><small>CLASS</small><b>CV</b></div><div><small>GUNNERY</small><b>1</b></div><div><small>AA FACTOR</small><b>4</b></div><div><small>TORPEDO</small><b>0</b></div><div><small>MF</small><b>2</b></div><div><small>DAMAGE</small><b>0 / 6</b></div><div><small>LAUNCH</small><b>11 / 3</b></div><div><small>AMMO</small><b>Ready</b></div></div></div><div class="detail-section"><h3>DERIVED STATUS</h3><div class="detail-table"><div><span>Air capacity</span><b>30 factors</b><em>7 ready · 4 in flight</em></div><div><span>Readying</span><b>9 RF</b><em>available this turn</em></div><div><span>Damage effects</span><b>None</b><em>full movement and launch</em></div><div><span>Screen status</span><b>Operational</b><em>3 destroyers assigned</em></div></div></div><div class="detail-actions"><button class="primary-action" data-action="operations"><span>▦</span> Open air operations <b>→</b></button><button class="secondary-action" data-action="close-modal"><span>×</span> Close detail <b>→</b></button></div></div>`);
}

function shipRosterColumnsModal() {
  return modalShell('Lexington task force', 'Ship detail · roster combat and operations values', `<div class="modal-body"><div class="detail-hero"><span class="large-unit-icon carrier">CV</span><div><strong>Allied carrier task force</strong><small>Source coordinate CC16 · 7 ships · operational screen</small></div><span class="condition-pill">C3</span></div><div class="detail-section"><h3>SHIP ROSTER</h3><div class="ship-roster ship-roster-table"><div class="ship-roster-header"><span>Ship</span><span>Class</span><span>Gun</span><span>AA</span><span>Torp</span><span>MF</span><span>Damage</span><span>Launch</span><span>Ammo</span></div><button class="ship-card ship-roster-row selected"><span><strong>USS Lexington</strong><small>Carrier</small></span><b>CV</b><b>1</b><b>4</b><b>0</b><b>2</b><b>0 / 6</b><b>11 / 3</b><b>Ready</b></button><button class="ship-card ship-roster-row"><span><strong>USS Minneapolis</strong><small>Heavy cruiser</small></span><b>CA</b><b>4</b><b>2</b><b>6</b><b>2</b><b>1 / 5</b><b>-</b><b>Ready</b></button><button class="ship-card ship-roster-row"><span><strong>USS San Francisco</strong><small>Heavy cruiser</small></span><b>CA</b><b>4</b><b>2</b><b>6</b><b>2</b><b>0 / 5</b><b>-</b><b>Ready</b></button><button class="ship-card ship-roster-row"><span><strong>USS Indianapolis</strong><small>Heavy cruiser</small></span><b>CA</b><b>4</b><b>2</b><b>6</b><b>2</b><b>0 / 5</b><b>-</b><b>Ready</b></button><button class="ship-card ship-roster-row"><span><strong>USS Morris</strong><small>Destroyer</small></span><b>DD</b><b>1</b><b>1</b><b>1</b><b>3</b><b>0 / 3</b><b>-</b><b>Ready</b></button><button class="ship-card ship-roster-row"><span><strong>USS Anderson</strong><small>Destroyer</small></span><b>DD</b><b>1</b><b>1</b><b>1</b><b>3</b><b>0 / 3</b><b>-</b><b>Ready</b></button><button class="ship-card ship-roster-row"><span><strong>USS Hughes</strong><small>Destroyer</small></span><b>DD</b><b>1</b><b>1</b><b>1</b><b>3</b><b>0 / 3</b><b>-</b><b>Ready</b></button></div></div><div class="detail-section"><h3>DERIVED TASK FORCE STATUS</h3><div class="detail-table"><div><span>Air capacity</span><b>30 factors</b><em>7 ready · 4 in flight</em></div><div><span>Readying</span><b>9 RF</b><em>available this turn</em></div><div><span>Damage effects</span><b>None</b><em>full movement and launch</em></div><div><span>Screen status</span><b>Operational</b><em>3 destroyers assigned</em></div></div></div><div class="detail-actions"><button class="primary-action" data-action="operations"><span>▦</span> Open air operations <b>→</b></button><button class="secondary-action" data-action="close-modal"><span>×</span> Close detail <b>→</b></button></div></div>`);
}

function detailsModal(unitId) {
  const unit = units[unitId] || {};
  const isBase = unit.icon === '⌂' || unit.type === 'Air operations base';
  const title = unit.title || 'Selected unit';
  if (!isBase && unit.type && unit.type.toLowerCase().includes('formation')) return aircraftDetailsModal();
  if (!isBase) return shipRosterColumnsModal();
  const body = isBase ? `<div class="modal-body"><div class="detail-hero"><span class="large-unit-icon base">⌂</span><div><strong>Air operations base</strong><small>Allied · source coordinate ${unit.location || 'unknown'}</small></div><span class="condition-pill">${unit.condition || 'OWN'}</span></div><div class="detail-section"><h3>BASE CAPABILITIES</h3><div class="detail-grid"><div><small>MAX CAPACITY</small><b>Unlimited</b></div><div><small>LF NORMAL / MIN</small><b>20 / 10</b></div><div><small>AA FACTOR</small><b>5</b></div><div><small>DAMAGE</small><b>0</b></div></div></div><div class="detail-section"><h3>AIRCRAFT ON BASE</h3><div class="detail-table"><div><span>Ready</span><b>12 P-40</b><em>launchable</em></div><div><span>Readying</span><b>12 P-39 · 5 B-25</b><em>arming / preparing</em></div><div><span>Just Landed</span><b>4 Catalina</b><em>needs Readying Factor</em></div><div><span>In Flight</span><b>none</b><em>no active sorties</em></div></div></div><div class="detail-section"><h3>AVAILABLE OPERATIONS</h3><div class="detail-actions"><button class="primary-action" data-action="operations"><span>▦</span> Open operations chart <b>→</b></button><button class="secondary-action" data-action="close-modal"><span>×</span> Close <b>→</b></button></div></div></div>` : `<div class="modal-body"><div class="detail-hero"><span class="large-unit-icon carrier">CV</span><div><strong>Carrier task force</strong><small>${unit.detail || 'Allied task force'} · source coordinate ${unit.location || 'unknown'}</small></div><span class="condition-pill">${unit.condition || 'OWN'}</span></div><div class="detail-section"><h3>SHIP COMPOSITION</h3><div class="detail-table"><div><span>Carrier</span><b>CV Lexington</b><em>LF 11 / 3 · damage 0</em></div><div><span>Cruisers</span><b>Pensacola · Minneapolis · San Francisco · Indianapolis</b><em>4 capital ships</em></div><div><span>Screen</span><b>10 destroyers</b><em>MF 2 · operational</em></div></div></div><div class="detail-section"><h3>AIR OPERATIONS</h3><div class="detail-grid"><div><small>READY</small><b>8 F4F</b></div><div><small>READYING</small><b>12 SBD</b></div><div><small>JUST LANDED</small><b>4 TBD</b></div><div><small>LAUNCH FACTOR</small><b>11 / 3</b></div></div></div><div class="detail-section"><h3>AVAILABLE OPERATIONS</h3><div class="detail-actions"><button class="primary-action" data-action="operations"><span>▦</span> Manage air operations <b>→</b></button><button class="secondary-action" data-action="plot"><span>⌁</span> Plot movement <b>→</b></button><button class="secondary-action" data-action="close-modal"><span>×</span> Close <b>→</b></button></div></div></div>`;
  return modalShell(title, `${unit.eyebrow || 'UNIT DETAILS'} · source state preview`, body);
}

function modalShell(title, subtitle, body) {
  return `<div class="modal-head"><div><p class="eyebrow">COMMAND VIEW</p><h2 id="modalTitle">${title}</h2><p>${subtitle}</p></div><button class="modal-close" data-action="close-modal" aria-label="Close">×</button></div>${body}`;
}

function operationsModal() {
  return modalShell('Operations chart', 'Task Force 7 · CV Enterprise · air operations phase', `<div class="modal-body"><div class="operations-grid"><div class="ops-box"><h3>READY · 10</h3><div class="plane-token"><span>F4F Wildcat</span><b>6</b></div><div class="plane-token"><span>SBD Dauntless</span><b>4</b></div></div><div class="ops-box"><h3>READYING · 8</h3><div class="plane-token"><span>SBD Dauntless</span><b>8</b></div></div><div class="ops-box"><h3>JUST LANDED · 4</h3><div class="plane-token"><span>TBD Devastator</span><b>4</b></div></div><div class="ops-box"><h3>IN FLIGHT · 4</h3><div class="plane-token"><span>Formation 18</span><b>4</b></div></div></div><div class="launch-planner"><h3>Launch planner <span class="condition-pill">preview</span></h3><div class="launch-controls"><button class="choice ${state.launchMode === 'minimum' ? 'active' : ''}" data-launch="minimum"><strong>Minimum launch</strong><small>1-3 factors · full MF</small></button><button class="choice ${state.launchMode === 'normal' ? 'active' : ''}" data-launch="normal"><strong>Normal launch</strong><small>4-11 factors · half MF</small></button><button class="choice ${state.launchMode === 'maximum' ? 'active' : ''}" data-launch="maximum"><strong>Maximum launch</strong><small>12-22 factors · no movement</small></button></div><div class="formula">6 F4F + 4 SBD · normal launch · 10 / 11 LF used · formation MF 2 · safe return by 1600</div><div class="modal-actions"><button class="ghost-button" data-action="close-modal">Cancel</button><button class="primary-button" data-action="confirm-launch">Confirm launch <span>→</span></button></div></div></div>`);
}

function interactiveOperationsModal() {
  const selected = state.formationSelection;
  const total = selected.wildcat + selected.dauntless + selected.devastator;
  return modalShell('Air operations tracker', 'Task Force 7 · CV Enterprise · air operations phase', `<div class="modal-body"><div class="tracker-toolbar"><span>Aircraft combat values</span><small>Values are shown before armament and attack selection</small></div><div class="air-table-wrap"><table class="air-combat-table"><thead><tr><th rowspan="2">Aircraft</th><th rowspan="2">Factors</th><th rowspan="2">A2A</th><th colspan="6">vs Base</th><th colspan="7">vs Ship</th><th rowspan="2">Move</th><th rowspan="2">Range</th><th rowspan="2">Armament</th></tr><tr><th colspan="2">High</th><th colspan="2">Low</th><th colspan="2">Dive</th><th colspan="2">High</th><th colspan="2">Low</th><th colspan="2">Dive</th><th>Torpedo</th></tr><tr class="table-subhead"><th></th><th></th><th></th><th>GP</th><th>AP</th><th>GP</th><th>AP</th><th>GP</th><th>AP</th><th>GP</th><th>AP</th><th>GP</th><th>AP</th><th>GP</th><th>AP</th><th>TORP</th><th></th><th></th><th></th></tr></thead><tbody><tr class="status-row"><th colspan="19">READY · select aircraft for formation</th></tr>${aircraftTableRow('wildcat', 'F4F Wildcat', 6, ['9','0','0','4','0','0','0','0','1','0','0','0','0'], '8', '6 / 6', selected.wildcat)}${aircraftTableRow('dauntless', 'SBD Dauntless', 4, ['3','1','1','5','1','6','2','0','0','2','5','2','7'], '9', '6 / 6', selected.dauntless)}<tr class="status-row"><th colspan="19">READYING · aircraft available after readiness move</th></tr>${aircraftTableRow('devastator', 'TBD Devastator', 4, ['2','1','1','5','2','0','0','0','0','1','5','0','0'], '6', '5 / 5', 0)}<tr class="status-row"><th colspan="19">JUST LANDED / IN FLIGHT · tracked below</th></tr><tr class="summary-row"><td colspan="19">Formation 18 · 10 SBD armed GP · 6 F4F escort · landing window 1400</td></tr></tbody></table></div><div class="formation-planner"><div class="formation-planner-head"><h3>Build Air Formation</h3><span class="condition-pill">${total} selected · ${total ? 'ready to launch' : 'select aircraft'}</span></div><div class="formation-controls"><label>Formation number <select id="formationNumber"><option>19</option><option>20</option><option>21</option></select></label><label>Selected factors <strong>${total} / 11 LF</strong></label></div><div class="formation-profile"><span>SELECTED PROFILE</span><strong>${selected.wildcat} F4F ${state.formationArmament.wildcat} · ${selected.dauntless} SBD ${state.formationArmament.dauntless}</strong><small>Armament choices determine the legal attack values used when the formation attacks.</small></div><div class="launch-controls"><button class="choice ${state.launchMode === 'minimum' ? 'active' : ''}" data-launch="minimum"><strong>Minimum launch</strong><small>1-3 factors · full MF</small></button><button class="choice ${state.launchMode === 'normal' ? 'active' : ''}" data-launch="normal"><strong>Normal launch</strong><small>4-11 factors · half MF</small></button><button class="choice ${state.launchMode === 'maximum' ? 'active' : ''}" data-launch="maximum"><strong>Maximum launch</strong><small>12-22 factors · no movement</small></button></div><div class="modal-actions"><button class="ghost-button" data-action="close-modal">Cancel</button><button class="primary-button" data-action="create-formation" ${total ? '' : 'disabled'}>Create Air Formation <span>→</span></button></div></div></div>`);
}

function aircraftTableRow(key, name, factors, values, movement, range, selectedCount) {
  const catalogValues = {
    wildcat: ['9','0','0','4','0','0','0','0','0','1','0','0','0','0'],
    dauntless: ['3','3','1','5','1','6','2','0','0','2','5','2','7','0'],
    devastator: ['2','3','1','5','2','0','0','0','0','1','5','0','0','6']
  };
  const cells = (catalogValues[key] || values).map(value => `<td class="combat-value">${value}</td>`).join('');
  const armament = state.formationArmament[key] || (key === 'dauntless' ? 'GP' : 'None');
  return `<tr class="aircraft-row ${selectedCount ? 'selected' : ''}"><td><button class="aircraft-choice" data-aircraft-select="${key}"><span class="plane-dot ${key === 'wildcat' ? 'fighter' : key === 'devastator' ? 'torpedo' : 'bomber'}"></span><strong>${name}</strong></button></td><td><b>${factors}</b></td>${cells}<td>${movement}</td><td>${range}</td><td><button class="armament-cycle" data-armament="${key}">${armament}</button></td></tr>`;
}

function legacyInteractiveOperationsModal() {
  const selected = state.formationSelection;
  const total = selected.wildcat + selected.dauntless;
  return modalShell('Operations chart', 'Task Force 7 · CV Enterprise · air operations phase', `<div class="modal-body"><div class="operations-grid"><div class="ops-box"><h3>READY · select for formation</h3><button class="plane-token selectable ${selected.wildcat ? 'selected' : ''}" data-aircraft-select="wildcat"><span>F4F Wildcat <small>6 available</small></span><b>${selected.wildcat}</b></button><button class="plane-token selectable ${selected.dauntless ? 'selected' : ''}" data-aircraft-select="dauntless"><span>SBD Dauntless <small>4 available</small></span><b>${selected.dauntless}</b></button></div><div class="ops-box"><h3>READYING · queue</h3><button class="plane-token selectable" data-action="queue-ready"><span>SBD Dauntless <small>8 waiting</small></span><b>+1</b></button><p class="ops-hint">Select a row to queue a readiness move.</p></div><div class="ops-box"><h3>JUST LANDED · queue</h3><button class="plane-token selectable" data-action="queue-ready"><span>TBD Devastator <small>4 landed</small></span><b>+1</b></button><p class="ops-hint">Ready Factor remaining: 8</p></div><div class="ops-box"><h3>IN FLIGHT · 4</h3><div class="plane-token"><span>Formation 18</span><b>1400</b></div></div></div><div class="launch-planner"><h3>Build Air Formation <span class="condition-pill">${total} selected</span></h3><div class="formation-controls"><label>Formation number <select id="formationNumber"><option>19</option><option>20</option><option>21</option></select></label><label>Selected factors <strong>${total} / 11 LF</strong></label></div><div class="armament-list"><div><span>F4F Wildcat · ${selected.wildcat}</span><button class="armament-cycle" data-armament="wildcat">${state.formationArmament.wildcat}</button></div><div><span>SBD Dauntless · ${selected.dauntless}</span><button class="armament-cycle" data-armament="dauntless">${state.formationArmament.dauntless}</button></div></div><div class="launch-controls"><button class="choice ${state.launchMode === 'minimum' ? 'active' : ''}" data-launch="minimum"><strong>Minimum launch</strong><small>full MF</small></button><button class="choice ${state.launchMode === 'normal' ? 'active' : ''}" data-launch="normal"><strong>Normal launch</strong><small>half MF</small></button><button class="choice ${state.launchMode === 'maximum' ? 'active' : ''}" data-launch="maximum"><strong>Maximum launch</strong><small>no movement</small></button></div><div class="formula">${selected.wildcat} F4F (${state.formationArmament.wildcat}) + ${selected.dauntless} SBD (${state.formationArmament.dauntless}) · formation ${state.formationNumber} · safe return by 1600</div><div class="modal-actions"><button class="ghost-button" data-action="close-modal">Cancel</button><button class="primary-button" data-action="create-formation" ${total ? '' : 'disabled'}>Create Air Formation <span>→</span></button></div></div></div>`);
}

function combatModal() {
  return modalShell('Air strike at BB15', 'Allied Air Formation 18 vs Japanese Task Force contact · daylight', `<div class="combat-body"><div class="combat-stepper"><div class="combat-step done"><span>01</span>Air-to-air</div><div class="combat-step done"><span>02</span>Anti-aircraft</div><div class="combat-step active"><span>03</span>Air attack</div><div class="combat-step"><span>04</span>Surface</div></div><div class="combat-stat-row"><span>Attack</span><b>8 SBD Dauntless · dive bombing · AP</b></div><div class="combat-stat-row"><span>Target</span><b>CV Shokaku · observed C3</b></div><div class="combat-stat-row"><span>Base BHT</span><b>7</b></div><div class="combat-stat-row"><span>Modifiers</span><b class="modifier">+2 crippled ship · −2 clouds</b></div><div class="combat-stat-row"><span>Final BHT</span><b>7</b></div><div class="formula">BHT 7 × 8 attacking factors → Result Number 2<br>Die roll: <strong>5</strong> → Result Number + 1</div><div class="result-grid"><div class="result-box"><small>DIE</small><b>5</b></div><div class="result-box"><small>RESULT NUMBER</small><b>2</b></div><div class="result-box"><small>HITS</small><b>3</b></div><div class="result-box"><small>RF USED</small><b>1</b></div></div><div class="combat-result"><strong>3 hits on CV Shokaku</strong><p>3 aircraft eliminated from Ready / Just Landed boxes. Ship damage: 7 → 10 of 12. Aircraft may continue to assigned landing window.</p></div><div class="modal-actions"><button class="ghost-button" data-action="close-modal">Close review</button><button class="primary-button" data-action="resolve-combat">Apply result <span>→</span></button></div></div>`);
}

function scoreModal() {
  return modalShell('Victory Point ledger', 'Turn 14 · all scoring events recorded in order', `<div class="modal-body"><div class="result-grid"><div class="result-box"><small>ALLIED</small><b class="text-green">62</b></div><div class="result-box"><small>JAPANESE</small><b>48</b></div><div class="result-box"><small>DIFFERENCE</small><b>+14</b></div></div><div class="ledger-row"><span>1200</span><div><strong>Sunk: IJN DD Arashi</strong><small>Surface attack · ship value</small></div><b>+8</b></div><div class="ledger-row"><span>1100</span><div><strong>Aircraft eliminated: 3 Val</strong><small>Air-to-air combat · normal loss</small></div><b>+6</b></div><div class="ledger-row"><span>1000</span><div><strong>Transport unload</strong><small>AP 3 · turn 2 of 8</small></div><b>+3</b></div><div class="ledger-row"><span>0900</span><div><strong>Base LF at zero or less</strong><small>Rabaul · 1 turn</small></div><b>+2</b></div></div>`);
}

function rulesModal() {
  return modalShell('Combat quick reference', 'The calculation chain used by every attack', `<div class="modal-body"><div class="combat-stat-row"><span>1 · Choose attack</span><b>Weapon + target + aircraft</b></div><div class="combat-stat-row"><span>2 · Calculate BHT</span><b>Base value + modifiers</b></div><div class="combat-stat-row"><span>3 · Find Result Number</span><b>BHT row × attack-factor range</b></div><div class="combat-stat-row"><span>4 · Roll die</span><b>1/2: −2/−1 · 3/4: 0 · 5/6: +1/+2</b></div><div class="combat-stat-row"><span>5 · Apply hits</span><b>Aircraft, ships, bases, Victory Points</b></div><div class="formula">Attack-factor ranges: 1-2 · 3-4 · 5-6 · 7-8 · 9-10 · 11-12 · 13-15 · 16-20 · 21-24 · 25-30 · 31-35 · 36-40 · 41-45 · 46+</div><p class="muted-copy">BHT is a table row, not a hit count. The combat log keeps every intermediate value visible for review.</p></div>`);
}

function logModal() {
  return modalShell('Event log', 'Latest events · filtered to this turn', `<div class="modal-body"><div class="ledger-row"><span>12:02</span><div><strong>Air contact observed at BB15</strong><small>Formation 18 · Condition 2 · cloud modifier applied</small></div><b>INTEL</b></div><div class="ledger-row"><span>12:01</span><div><strong>Formation 18 moved to BB15</strong><small>Low altitude · 2 movement points remaining</small></div><b>MOVE</b></div><div class="ledger-row"><span>12:00</span><div><strong>Weather phase complete</strong><small>Wind shifted NE · storm front unchanged</small></div><b>WX</b></div></div>`);
}

function renderOperationsCombatDetails() {
  const armamentList = $('.armament-list');
  if (!armamentList) return;
  const profiles = {
    wildcat: { name: 'F4F Wildcat', role: 'fighter / escort', movement: '8', range: '6', values: { None: '9 A2A · 4 low GP', GP: '9 A2A · 4 low GP' } },
    dauntless: { name: 'SBD Dauntless', role: 'dive bomber', movement: '9', range: '6', values: { None: '3 A2A · no bombing', GP: '3 A2A · 6 dive GP / 2 dive AP', AP: '3 A2A · 6 dive GP / 2 dive AP' } }
  };
  const panel = document.createElement('div');
  panel.className = 'operations-combat-details';
  panel.innerHTML = `<div class="operations-combat-heading"><span>COMBAT VALUES BY ARMAMENT</span><small>Choose an armament to update the formation profile</small></div>${Object.entries(profiles).map(([key, profile]) => `<div class="operations-aircraft"><div><strong>${profile.name}</strong><small>${profile.role} · MF ${profile.movement} · range ${profile.range}</small></div><b>${profile.values[state.formationArmament[key]] || profile.values.None}</b><em>${state.formationArmament[key]}</em></div>`).join('')}`;
  armamentList.parentNode.insertBefore(panel, armamentList);
}

function advancePhase() {
  state.phaseIndex = Math.min(state.phaseIndex + 1, state.phaseNames.length - 1);
  $('#phaseLabel').textContent = state.phaseNames[state.phaseIndex];
  $$('.phase-item').forEach((item, index) => item.classList.toggle('active', index === state.phaseIndex));
  $('#commandText').innerHTML = `<b>${state.phaseNames[state.phaseIndex]}</b> · The interface is previewing the next decision point.`;
  toast(`Advanced to ${state.phaseNames[state.phaseIndex].toLowerCase()}.`);
}

function handleAction(action) {
  if (action === 'operations') openModal('operations');
  else if (action === 'combat') openModal('combat');
  else if (action === 'score') openModal('score');
  else if (action === 'rules' || action === 'help') openModal('rules');
  else if (action === 'log') openModal('log');
  else if (action === 'close-modal') $('#modalBackdrop').hidden = true;
  else if (action === 'advance') advancePhase();
  else if (action === 'confirm-launch') { $('#modalBackdrop').hidden = true; toast('Launch committed: 10 LF used. Formation 19 is airborne.'); }
  else if (action === 'create-formation') { $('#modalBackdrop').hidden = true; toast(`Air Formation ${state.formationNumber} created with ${state.formationSelection.wildcat + state.formationSelection.dauntless + state.formationSelection.devastator} selected factors.`); state.formationSelection = { wildcat: 0, dauntless: 0, devastator: 0 }; }
  else if (action === 'queue-ready') toast('Readiness move queued. One Readying Factor reserved.');
  else if (action === 'resolve-combat') { $('#modalBackdrop').hidden = true; toast('Combat result applied. 3 hits recorded on CV Shokaku.'); }
  else if (action === 'confirm') { toast('Air operations phase confirmed. Movement plotting is now available.'); advancePhase(); }
  else if (action === 'undo') toast('No uncommitted action to undo.');
  else if (action === 'plot') toast('Movement plotting will unlock after Air Operations is confirmed.');
  else if (action === 'inspect') toast('Detailed ship inspection opened in the operations chart.');
  else if (action === 'save') toast('Mock save created locally.');
  else if (action === 'clear-selection') { toast('Selection cleared.'); }
  else if (action === 'zoom-in') { state.zoom = Math.min(2.5, state.zoom + .1); applyMapZoom(); toast(`Map zoom ${Math.round(state.zoom * 100)}%.`); }
  else if (action === 'zoom-out') { state.zoom = Math.max(.5, state.zoom - .1); applyMapZoom(); toast(`Map zoom ${Math.round(state.zoom * 100)}%.`); }
}

function handlePieceAction(action) {
  const unitId = state.pendingPiece;
  if (action === 'details') openModal('details');
  if (action === 'move') { $('#modalBackdrop').hidden = true; toast('Move is phase-gated in this mockup; the action is available during the applicable movement phase.'); }
  if (action === 'land') { $('#modalBackdrop').hidden = true; toast('Landing requires a friendly base or plane-carrying task force in the selected hex.'); }
  if (action === 'combat') { openModal('combat'); }
}

function bindDynamicActions() {
  $$('[data-action]').forEach(button => { if (!button.dataset.bound) { button.dataset.bound = 'true'; button.addEventListener('click', () => handleAction(button.dataset.action)); } });
  $$('[data-launch]').forEach(button => button.addEventListener('click', () => { state.launchMode = button.dataset.launch; $$('.choice').forEach(choice => choice.classList.toggle('active', choice.dataset.launch === state.launchMode)); toast(`${button.textContent.trim().split(' ')[0]} launch selected.`); }));
  $$('[data-aircraft-select]').forEach(button => button.addEventListener('click', () => { const type = button.dataset.aircraftSelect; state.formationSelection[type] = state.formationSelection[type] ? 0 : (type === 'wildcat' ? 2 : 4); openModal('operations'); }));
  $$('[data-armament]').forEach(button => button.addEventListener('click', () => { const type = button.dataset.armament; const options = type === 'wildcat' ? ['None', 'GP'] : type === 'devastator' ? ['Torpedo', 'GP', 'None'] : ['GP', 'AP', 'None']; const index = options.indexOf(state.formationArmament[type]); state.formationArmament[type] = options[(index + 1) % options.length]; openModal('operations'); }));
  $$('[data-piece-action]').forEach(button => button.addEventListener('click', () => handlePieceAction(button.dataset.pieceAction)));
  const formationNumber = $('#formationNumber');
  if (formationNumber && !formationNumber.dataset.bound) { formationNumber.dataset.bound = 'true'; formationNumber.value = String(state.formationNumber); formationNumber.addEventListener('change', () => { state.formationNumber = Number(formationNumber.value); }); }
}

bindDynamicActions();
renderScenario('one');
renderUnit('allied-tf1');
$$('[data-unit]:not(.map-unit)').forEach(button => button.addEventListener('click', () => renderUnit(button.dataset.unit)));
$$('[data-contact]:not(.map-unit)').forEach(button => button.addEventListener('click', () => renderUnit(button.dataset.contact)));
$$('[data-map-piece]').forEach(button => button.addEventListener('click', () => { state.pendingPiece = button.dataset.mapPiece; openModal('piece-menu'); }));
$$('[data-board]').forEach(button => button.addEventListener('click', () => {
  $$('[data-board]').forEach(item => item.classList.toggle('active', item === button));
  renderScenario(button.dataset.board);
  const firstAllied = scenarios[button.dataset.board].forces.find(force => force.side === 'A');
  renderUnit(firstAllied.id);
  toast(`${button.textContent} loaded from main.py scenario setup.`);
}));
$$('[data-overlay]').forEach(button => button.addEventListener('click', () => { state.overlay = button.dataset.overlay; $$('[data-overlay]').forEach(item => item.classList.toggle('active', item === button)); toast(`${button.textContent} overlay ${state.overlay === 'contacts' ? 'enabled' : 'selected'}.`); }));
$('#modalBackdrop').addEventListener('click', event => { if (event.target.id === 'modalBackdrop') $('#modalBackdrop').hidden = true; });
window.addEventListener('keydown', event => { if (event.key === 'Escape') $('#modalBackdrop').hidden = true; if (event.key.toLowerCase() === 'o') openModal('operations'); if (event.key === '?') openModal('rules'); if (event.key.toLowerCase() === 'l') openModal('log'); });
