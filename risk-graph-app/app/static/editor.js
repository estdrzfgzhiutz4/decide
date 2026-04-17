let state = { scenario: null, selected: null, path: '' };

const $ = (id) => document.getElementById(id);

function uid(prefix) {
  return `${prefix}_${Math.random().toString(36).slice(2, 7)}`;
}

function slugify(text, fallback = 'item') {
  const s = (text || '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  return s || fallback;
}

async function api(path, method = 'GET', body = null) {
  const res = await fetch(path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : null,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(JSON.stringify(data));
  return data;
}

function setStatus(obj) {
  $('status').textContent = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
}

function renderScenarioForm() {
  const s = state.scenario;
  $('scenarioForm').innerHTML = `
    <label>Name<input id="sc_name" value="${s.scenario_name || ''}"></label>
    <label>Description<textarea id="sc_desc">${s.description || ''}</textarea></label>
    <label>Mode
      <select id="sc_mode">
        <option value="strict" ${s.mode === 'strict' ? 'selected' : ''}>strict</option>
        <option value="draft" ${s.mode === 'draft' ? 'selected' : ''}>draft</option>
      </select>
    </label>
    <label>catastrophic_weight<input id="sw_cat" type="number" value="${s.scoring.catastrophic_weight}"></label>
    <label>positive_weight<input id="sw_pos" type="number" value="${s.scoring.positive_weight}"></label>
    <label>harm_weight<input id="sw_harm" type="number" value="${s.scoring.harm_weight}"></label>
    <label>uncertainty_weight<input id="sw_unc" type="number" value="${s.scoring.uncertainty_weight}"></label>
    <label>reversibility_weight<input id="sw_rev" type="number" value="${s.scoring.reversibility_weight}"></label>
    <button class="small" id="applyScenario">Apply scenario fields</button>
  `;
  $('applyScenario').onclick = () => {
    s.scenario_name = $('sc_name').value;
    s.description = $('sc_desc').value;
    s.mode = $('sc_mode').value;
    s.scoring = {
      catastrophic_weight: Number($('sw_cat').value || 0),
      positive_weight: Number($('sw_pos').value || 0),
      harm_weight: Number($('sw_harm').value || 0),
      uncertainty_weight: Number($('sw_unc').value || 0),
      reversibility_weight: Number($('sw_rev').value || 0),
    };
    refreshLists();
  };
}

function refreshLists() {
  const s = state.scenario;
  $('currentPath').textContent = state.path;

  const nodeFilter = $('nodeFilter').value?.toLowerCase() || '';
  $('nodesList').innerHTML = '';
  s.nodes
    .filter((n) => `${n.id} ${n.label}`.toLowerCase().includes(nodeFilter))
    .forEach((n, i) => {
      const li = document.createElement('li');
      li.textContent = `${n.id || '(no id)'} [${n.type || '?'}] ${n.label || ''} ${n.draft_status === 'complete' ? '' : `(${n.draft_status})`}`;
      li.onclick = () => { state.selected = { kind: 'node', index: i }; renderSelected(); };
      $('nodesList').appendChild(li);
    });

  const edgeFilter = $('edgeFilter').value?.toLowerCase() || '';
  $('edgesList').innerHTML = '';
  s.edges
    .filter((e) => `${e.id} ${e.from} ${e.to}`.toLowerCase().includes(edgeFilter))
    .forEach((e, i) => {
      const li = document.createElement('li');
      li.textContent = `${e.id || '(no id)'}: ${e.from || '?'} -> ${e.to || '?'} ${e.transition_kind || '?'} ${e.draft_status === 'complete' ? '' : `(${e.draft_status})`}`;
      li.onclick = () => { state.selected = { kind: 'edge', index: i }; renderSelected(); };
      $('edgesList').appendChild(li);
    });

  $('variablesList').innerHTML = '';
  Object.entries(s.variables || {}).forEach(([k, v]) => {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${k}</strong> = ${JSON.stringify(v)} <button data-k="${k}">x</button>`;
    li.querySelector('button').onclick = (ev) => {
      delete s.variables[ev.target.dataset.k];
      refreshLists();
    };
    $('variablesList').appendChild(li);
  });
}

function parseValue(raw) {
  if (raw === 'true') return true;
  if (raw === 'false') return false;
  if (raw !== '' && !isNaN(Number(raw))) return Number(raw);
  return raw;
}

function renderSelected() {
  const sel = state.selected;
  if (!sel) return;
  const s = state.scenario;

  if (sel.kind === 'node') {
    const n = s.nodes[sel.index];
    $('itemForm').innerHTML = `
      <h4>Node</h4>
      <label>id<input id="n_id" value="${n.id || ''}"></label>
      <label>label<input id="n_label" value="${n.label || ''}"></label>
      <label>type<select id="n_type">${['decision','event','actor','outcome','terminal_positive','terminal_failure'].map(t=>`<option ${n.type===t?'selected':''}>${t}</option>`).join('')}</select></label>
      <label>harm<input id="n_harm" type="number" value="${n.harm ?? 0}"></label>
      <label><input id="n_terminal" type="checkbox" ${n.terminal?'checked':''}> terminal</label>
      <label><input id="n_positive" type="checkbox" ${n.positive?'checked':''}> positive</label>
      <label><input id="n_failure" type="checkbox" ${n.failure?'checked':''}> failure</label>
      <label>notes<textarea id="n_notes">${n.notes || ''}</textarea></label>
      <label>tags (comma separated)<input id="n_tags" value="${(n.tags||[]).join(',')}"></label>
      <label>draft_status<select id="n_ds">${['complete','incomplete','guessed'].map(t=>`<option ${n.draft_status===t?'selected':''}>${t}</option>`).join('')}</select></label>
      <label>draft_note<textarea id="n_dn">${n.draft_note || ''}</textarea></label>
      <button id="nodeAutoId">Auto id from label</button>
      <button id="nodeDup">Duplicate</button>
      <button id="nodeMarkGuess">Mark guessed</button>
      <button id="nodeMarkIncomplete">Mark incomplete</button>
      <button id="nodeClearDraft">Clear draft flag</button>
      <button id="nodeApply">Apply</button>
      <button id="nodeDelete">Delete</button>
    `;
    $('nodeAutoId').onclick = ()=> $('n_id').value = slugify($('n_label').value, 'node');
    $('nodeDup').onclick = ()=> { s.nodes.push({...n, id: uid(n.id || 'node')}); refreshLists(); };
    $('nodeMarkGuess').onclick = ()=> { n.draft_status='guessed'; renderSelected(); refreshLists(); };
    $('nodeMarkIncomplete').onclick = ()=> { n.draft_status='incomplete'; renderSelected(); refreshLists(); };
    $('nodeClearDraft').onclick = ()=> { n.draft_status='complete'; n.draft_note=''; renderSelected(); refreshLists(); };
    $('nodeApply').onclick = () => {
      n.id = $('n_id').value;
      n.label = $('n_label').value;
      n.type = $('n_type').value;
      n.harm = Number($('n_harm').value || 0);
      n.terminal = $('n_terminal').checked;
      n.positive = $('n_positive').checked;
      n.failure = $('n_failure').checked;
      n.notes = $('n_notes').value || null;
      n.tags = $('n_tags').value ? $('n_tags').value.split(',').map(x=>x.trim()).filter(Boolean) : [];
      n.draft_status = $('n_ds').value;
      n.draft_note = $('n_dn').value || null;
      if (!n.id) n.id = slugify(n.label, 'node');
      refreshLists();
    };
    $('nodeDelete').onclick = () => { s.nodes.splice(sel.index, 1); state.selected = null; $('itemForm').innerHTML=''; refreshLists(); };
  }

  if (sel.kind === 'edge') {
    const e = s.edges[sel.index];
    const nodeOpts = s.nodes.map(n=>`<option value="${n.id}" ${e.from===n.id?'selected':''}>${n.id}</option>`).join('');
    const nodeOptsTo = s.nodes.map(n=>`<option value="${n.id}" ${e.to===n.id?'selected':''}>${n.id}</option>`).join('');
    $('itemForm').innerHTML = `
      <h4>Edge</h4>
      <label>id<input id="e_id" value="${e.id || ''}"></label>
      <label>from<select id="e_from"><option value=""></option>${nodeOpts}</select></label>
      <label>to<select id="e_to"><option value=""></option>${nodeOptsTo}</select></label>
      <label>probability<input id="e_prob" type="number" step="0.01" value="${e.probability ?? ''}"></label>
      <label>transition_kind<select id="e_kind"><option value=""></option>${['branch','fork','escalate','resolve'].map(k=>`<option ${e.transition_kind===k?'selected':''}>${k}</option>`).join('')}</select></label>
      <label>uncertainty<input id="e_unc" type="number" step="0.01" value="${e.uncertainty ?? 0}"></label>
      <label>reversibility_cost<input id="e_rev" type="number" step="0.01" value="${e.reversibility_cost ?? 0}"></label>
      <label>notes<textarea id="e_notes">${e.notes || ''}</textarea></label>
      <label>draft_status<select id="e_ds">${['complete','incomplete','guessed'].map(t=>`<option ${e.draft_status===t?'selected':''}>${t}</option>`).join('')}</select></label>
      <label>draft_note<textarea id="e_dn">${e.draft_note || ''}</textarea></label>
      <label>active_if (JSON array)<textarea id="e_cond">${JSON.stringify(e.active_if || [], null, 2)}</textarea></label>
      <label>effects (JSON array)<textarea id="e_fx">${JSON.stringify(e.effects || [], null, 2)}</textarea></label>
      <button id="edgeAutoId">Auto id</button>
      <button id="edgeDup">Duplicate</button>
      <button id="edgeMarkGuess">Mark guessed</button>
      <button id="edgeMarkIncomplete">Mark incomplete</button>
      <button id="edgeClearDraft">Clear draft flag</button>
      <button id="edgeApply">Apply</button>
      <button id="edgeDelete">Delete</button>
    `;
    $('edgeAutoId').onclick = ()=> $('e_id').value = slugify(`${$('e_from').value}_${$('e_to').value}`, 'edge');
    $('edgeDup').onclick = ()=> { s.edges.push({...e, id: uid(e.id || 'edge')}); refreshLists(); };
    $('edgeMarkGuess').onclick = ()=> { e.draft_status='guessed'; renderSelected(); refreshLists(); };
    $('edgeMarkIncomplete').onclick = ()=> { e.draft_status='incomplete'; renderSelected(); refreshLists(); };
    $('edgeClearDraft').onclick = ()=> { e.draft_status='complete'; e.draft_note=''; renderSelected(); refreshLists(); };
    $('edgeApply').onclick = () => {
      e.id = $('e_id').value || slugify(`${$('e_from').value}_${$('e_to').value}`, 'edge');
      e.from = $('e_from').value;
      e.to = $('e_to').value;
      e.probability = $('e_prob').value === '' ? null : Number($('e_prob').value);
      e.transition_kind = $('e_kind').value;
      e.uncertainty = Number($('e_unc').value || 0);
      e.reversibility_cost = Number($('e_rev').value || 0);
      e.notes = $('e_notes').value || null;
      e.draft_status = $('e_ds').value;
      e.draft_note = $('e_dn').value || null;
      e.active_if = JSON.parse($('e_cond').value || '[]');
      e.effects = JSON.parse($('e_fx').value || '[]');
      refreshLists();
    };
    $('edgeDelete').onclick = () => { s.edges.splice(sel.index, 1); state.selected = null; $('itemForm').innerHTML=''; refreshLists(); };
  }
}

function addNode(type) {
  state.scenario.nodes.push({
    id: uid(type), label: '', type,
    harm: 0, terminal: type.startsWith('terminal_'),
    positive: type === 'terminal_positive',
    failure: type === 'terminal_failure',
    notes: null, tags: [], draft_status: 'incomplete', draft_note: null,
  });
  refreshLists();
}

function addEdge() {
  state.scenario.edges.push({
    id: uid('edge'), from: '', to: '', probability: null, transition_kind: '',
    active_if: [], effects: [], uncertainty: 0, reversibility_cost: 0,
    notes: null, draft_status: 'incomplete', draft_note: null,
  });
  refreshLists();
}

async function boot() {
  const init = await api('/api/scenario');
  state.scenario = init.scenario;
  state.path = init.path;
  renderScenarioForm();
  refreshLists();

  $('loadBtn').onclick = async () => {
    const p = prompt('Scenario path', state.path);
    if (!p) return;
    const out = await api('/api/scenario/load', 'POST', { path: p });
    state.scenario = out.scenario;
    state.path = out.path;
    state.selected = null;
    $('itemForm').innerHTML = '';
    renderScenarioForm();
    refreshLists();
    setStatus('Loaded.');
  };

  $('saveBtn').onclick = async () => {
    try {
      const out = await api('/api/scenario/save', 'POST', { scenario: state.scenario, path: state.path });
      setStatus(out);
    } catch (e) { setStatus(`Save failed: ${e.message}`); }
  };

  $('saveDraftBtn').onclick = async () => {
    const out = await api('/api/scenario/save-draft', 'POST', { scenario: state.scenario, path: state.path });
    setStatus(out);
  };

  $('validateBtn').onclick = async () => {
    const mode = prompt('Validation mode (strict|draft)', state.scenario.mode || 'draft') || 'draft';
    const out = await api('/api/validate', 'POST', { scenario: state.scenario, mode });
    setStatus(out);
  };

  $('evaluateBtn').onclick = async () => {
    const out = await api('/api/evaluate', 'POST', { scenario: state.scenario });
    setStatus(out);
  };

  $('renderBtn').onclick = async () => {
    const out = await api('/api/render', 'POST', { scenario: state.scenario });
    $('previewWrap').innerHTML = `<img src="/api/preview.svg?ts=${Date.now()}" alt="preview" />`;
    setStatus(out);
  };

  $('addVarBtn').onclick = () => {
    const key = prompt('Variable name');
    if (!key) return;
    const value = prompt('Variable value (true/false/number/string)', '');
    state.scenario.variables[key] = parseValue(value || '');
    refreshLists();
  };

  $('addDecisionBtn').onclick = () => addNode('decision');
  $('addEventBtn').onclick = () => addNode('event');
  $('addOutcomeBtn').onclick = () => addNode('outcome');
  $('addPositiveBtn').onclick = () => addNode('terminal_positive');
  $('addFailureBtn').onclick = () => addNode('terminal_failure');
  $('addEdgeBtn').onclick = () => addEdge();
  $('nodeFilter').oninput = refreshLists;
  $('edgeFilter').oninput = refreshLists;
}

boot().catch((e) => setStatus(`Init failed: ${e.message}`));
