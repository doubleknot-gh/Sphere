'use strict';
const $ = (id) => document.getElementById(id);
let token = sessionStorage.getItem('sphere_token') || '';
let me = null, members = [], page = 0, editTarget = null, fileVersion = 0;
let expiresAt = 0;
const pageSize = 30;
const show = (id, visible) => { $(id).hidden = !visible; };
function feedback(message, error = false) {
  $('edit-feedback').hidden = !$('edit-dialog').open;
  $('edit-feedback').textContent = message;
  $('feedback').textContent = message;
  $('feedback').classList.toggle('error', error);
  show('feedback', true);
}
function clearFeedback() { show('feedback', false); show('edit-feedback', false); }
function logout(message = '') {
  token = ''; me = null; members = []; expiresAt = 0; editTarget = null;
  sessionStorage.removeItem('sphere_token');
  if ($('edit-dialog').open) $('edit-dialog').close();
  for (const id of ['login-form', 'password-form', 'message-form', 'add-form', 'notice-form', 'edit-form', 'upload-form']) $(id).reset();
  $('upload-file').value = ''; fileVersion++;
  show('upload-mapping', false);
  for (const id of ['card-name', 'card-sid', 'card-club', 'messages', 'members-body', 'stats', 'notice-banner', 'notice-content', 'preview-table', 'club-counts-body', 'club-count-summary']) $(id).replaceChildren();
  show('notice-banner', false); show('admin-nav', false);
  show('login-view', true); show('app-view', false); show('logout', false);
  clearFeedback();
  if (message) feedback(message, true);
}
function setToken(value) {
  token = value; sessionStorage.setItem('sphere_token', token);
  try { expiresAt = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))).exp * 1000; }
  catch { expiresAt = 0; }
}
async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  let response;
  try { response = await fetch(path, {...options, headers, cache: 'no-store'}); }
  catch { throw new Error('서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.'); }
  let data;
  try { data = await response.json(); } catch { data = {}; }
  if (!response.ok) {
    if (response.status === 401 && path !== '/token') logout('로그인이 만료되었습니다. 다시 로그인해주세요.');
    let message = data.detail;
    if (Array.isArray(message)) message = '입력한 정보를 확인해주세요.';
    if (path === '/token' && response.status === 401) message = '학번 또는 비밀번호가 올바르지 않습니다.';
    if (message === 'Incorrect current password') message = '현재 비밀번호가 올바르지 않습니다.';
    throw new Error(message || `요청에 실패했습니다 (${response.status}).`);
  }
  return data;
}
const jsonRequest = (method, data) => ({method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});
function run(control, task) {
  return async (event) => {
    if (event) event.preventDefault();
    const button = control.tagName === 'FORM' ? control.querySelector('button[type="submit"]') : control;
    if (button.disabled) return;
    button.disabled = true; clearFeedback();
    try { await task(event); } catch (error) { feedback(error.message, true); }
    finally { button.disabled = false; }
  };
}
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function openCard() {
  show('card-view', true); show('admin-view', false);
  $('card-nav').setAttribute('aria-current', 'page'); $('admin-nav').removeAttribute('aria-current');
}
function renderCard() {
  $('greeting').textContent = `${me.name}님의 SPHERE`;
  $('card-name').textContent = me.name;
  $('card-sid').textContent = me.student_id;
  $('card-club').textContent = me.club || '소속 없음';
  $('card-status').textContent = me.status === 'active' ? '활동 회원' : '비활동 회원';
  $('card-status').classList.toggle('inactive', me.status !== 'active');
  show('admin-nav', me.role === 'admin');
}
async function loadNotice() {
  const data = await api('/notice');
  $('notice-banner').textContent = data.content;
  $('notice-content').value = data.content;
  show('notice-banner', Boolean(data.content));
}
async function loadMessages() {
  const data = await api('/messages');
  $('messages').replaceChildren();
  if (!data.length) $('messages').append(node('p', '아직 메시지가 없습니다. 첫 이야기를 남겨보세요.', 'muted'));
  for (const item of data) {
    const article = node('article', undefined, 'message');
    article.append(node('strong', item.name), node('small', `${item.role === 'admin' ? '관리자' : item.club || '회원'} · ${new Date(item.created_at).toLocaleString('ko-KR')}`), node('p', item.message));
    if (item.can_delete) {
      const button = node('button', '삭제');
      button.addEventListener('click', run(button, async () => {
        if (!confirm('이 메시지를 삭제할까요?')) return;
        await api(`/messages/${item.id}`, {method: 'DELETE'}); await loadMessages();
      }));
      article.append(button);
    }
    $('messages').append(article);
  }
}
async function enterApp() {
  me = await api('/members/me'); renderCard(); openCard();
  show('login-view', false); show('app-view', true); show('logout', true);
  $('login-form').reset();
  const results = await Promise.allSettled([loadNotice(), loadMessages()]);
  const failed = results.find(result => result.status === 'rejected');
  if (failed) feedback(failed.reason.message, true);
}
$('login-form').addEventListener('submit', run($('login-form'), async () => {
  const form = new FormData($('login-form'));
  const data = await api('/token', {method: 'POST', body: new URLSearchParams(form)});
  setToken(data.access_token);
  try { await enterApp(); } catch (error) { logout(); throw error; }
}));
$('logout').addEventListener('click', () => logout());
$('card-nav').addEventListener('click', openCard);
$('refresh-card').addEventListener('click', run($('refresh-card'), async () => {
  me = await api('/members/me'); renderCard(); await loadNotice(); feedback('회원 정보를 갱신했습니다.');
}));
$('password-form').addEventListener('submit', run($('password-form'), async () => {
  const data = Object.fromEntries(new FormData($('password-form')));
  if (data.new_password !== data.confirm_password) throw new Error('새 비밀번호가 일치하지 않습니다.');
  await api('/members/me/password', jsonRequest('PUT', {current_password: data.current_password, new_password: data.new_password}));
  $('password-form').reset(); feedback('비밀번호를 변경했습니다.');
}));
$('refresh-chat').addEventListener('click', run($('refresh-chat'), loadMessages));
$('message-form').addEventListener('submit', run($('message-form'), async () => {
  const message = new FormData($('message-form')).get('message').trim();
  if (!message) throw new Error('메시지를 입력해주세요.');
  await api('/messages', jsonRequest('POST', {message})); $('message-form').reset(); await loadMessages();
}));
function filteredMembers() {
  const query = $('member-search').value.trim().toLowerCase();
  const status = $('status-filter').value;
  return members.filter(m => (!status || m.status === status) && [m.name, m.student_id, m.club || ''].some(v => v.toLowerCase().includes(query)));
}
function renderMembers() {
  const filtered = filteredMembers();
  page = Math.max(0, Math.min(page, Math.ceil(filtered.length / pageSize) - 1));
  $('result-count').textContent = `검색 결과 ${filtered.length}명`;
  $('members-body').replaceChildren();
  for (const member of filtered.slice(page * pageSize, (page + 1) * pageSize)) {
    const row = node('tr');
    for (const value of [member.name, member.student_id, member.club || '-', member.status === 'active' ? '활동' : '비활동', member.role === 'admin' ? '관리자' : '회원']) row.append(node('td', value));
    const cell = node('td'); const button = node('button', '관리');
    button.addEventListener('click', () => openEdit(member)); cell.append(button); row.append(cell); $('members-body').append(row);
  }
  if (!filtered.length) { const cell = node('td', '표시할 회원이 없습니다.'); cell.colSpan = 6; const row = node('tr'); row.append(cell); $('members-body').append(row); }
  $('page-info').textContent = `${page + 1} / ${Math.max(1, Math.ceil(filtered.length / pageSize))}`;
  $('prev-page').disabled = page === 0; $('next-page').disabled = (page + 1) * pageSize >= filtered.length;
}
function renderClubCounts() {
  const result = SphereClubs.countMemberships(members);
  $('club-counts-body').replaceChildren();
  $('club-count-summary').textContent = `동아리 ${result.clubs.length}개 · 중복 가입 포함 연인원 ${result.total}명 · 소속 없는 회원 ${result.unassigned}명 제외`;
  for (const club of result.clubs) {
    const row = node('tr');
    for (const value of [club.name, `${club.total}명`, `${club.active}명`, `${club.inactive}명`]) row.append(node('td', value));
    $('club-counts-body').append(row);
  }
  if (!result.clubs.length) {
    const row = node('tr'), cell = node('td', '등록된 동아리가 없습니다.');
    cell.colSpan = 4; row.append(cell); $('club-counts-body').append(row);
  }
}
async function loadMembers() {
  members = await api('/admin/members');
  const clubCounts = SphereClubs.countMemberships(members);
  $('stats').replaceChildren();
  for (const [label, value] of [['전체 회원', members.length], ['활동 회원', members.filter(m => m.status === 'active').length], ['동아리', clubCounts.clubs.length], ['관리자', members.filter(m => m.role === 'admin').length]]) {
    const box = node('div', undefined, 'stat'); box.append(node('span', label), node('strong', String(value))); $('stats').append(box);
  }
  renderMembers();
  renderClubCounts();
}
$('admin-nav').addEventListener('click', run($('admin-nav'), async () => {
  if (me?.role !== 'admin') return;
  await loadMembers(); show('card-view', false); show('admin-view', true);
  $('admin-nav').setAttribute('aria-current', 'page'); $('card-nav').removeAttribute('aria-current');
}));
$('reload-members').addEventListener('click', run($('reload-members'), loadMembers));
$('reload-clubs').addEventListener('click', run($('reload-clubs'), loadMembers));
for (const id of ['member-search', 'status-filter']) $(id).addEventListener('input', () => { page = 0; renderMembers(); });
$('prev-page').addEventListener('click', () => { page--; renderMembers(); });
$('next-page').addEventListener('click', () => { page++; renderMembers(); });
for (const button of document.querySelectorAll('[data-panel]')) button.addEventListener('click', () => {
  for (const section of document.querySelectorAll('.admin-panel')) section.hidden = section.id !== button.dataset.panel;
  for (const tab of document.querySelectorAll('[data-panel]')) tab.setAttribute('aria-pressed', String(tab === button));
});
$('export-members').addEventListener('click', () => {
  const escape = value => {
    let text = String(value ?? '');
    if (/^[=+@\-\t\r]/.test(text)) text = "'" + text;
    return '"' + text.replaceAll('"', '""') + '"';
  };
  const rows = [['이름', '학번', '소속', '상태', '권한'], ...filteredMembers().map(m => [m.name, m.student_id, m.club, m.status, m.role])];
  const url = URL.createObjectURL(new Blob(['\ufeff' + rows.map(row => row.map(escape).join(',')).join('\r\n')], {type: 'text/csv;charset=utf-8'}));
  const a = node('a'); a.href = url; a.download = 'sphere-members.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$('upload-file').addEventListener('change', async () => {
  const version = ++fileVersion; show('upload-mapping', false); clearFeedback();
  const file = $('upload-file').files[0]; if (!file) return;
  try {
    if (file.size > 10 * 1024 * 1024) throw new Error('10MB 이하의 파일을 선택해주세요.');
    const form = new FormData(); form.append('file', file);
    const data = await api('/admin/import-preview', {method: 'POST', body: form});
    if (version !== fileVersion || !me) return;
    $('preview-table').replaceChildren(); const head = node('thead'), heading = node('tr'), body = node('tbody');
    for (const title of data.columns) heading.append(node('th', title || '(빈 제목)'));
    head.append(heading);
    for (const row of data.rows) { const tr = node('tr'); for (const value of row) tr.append(node('td', value)); body.append(tr); }
    $('preview-table').append(head, body);
    for (const [id, preferred, pattern] of [['name-column', 0, /이름|성명|name/i], ['sid-column', 1, /학번|student|^id$/i], ['club-column', 2, /소속|동아리|club/i]]) {
      const select = $(id); select.replaceChildren();
      data.columns.forEach((label, i) => { const option = node('option', `${i + 1}열 · ${label || '(빈 제목)'}`); option.value = i; select.append(option); });
      const matched = data.columns.findIndex(label => pattern.test(label)); select.value = matched >= 0 ? matched : Math.min(preferred, data.columns.length - 1);
    }
    $('upload-count').textContent = `첫 행을 제목으로 제외하면 ${data.count}행입니다. 아래는 상위 5행 미리보기입니다.`;
    show('upload-mapping', true);
  } catch (error) { if (version === fileVersion) feedback(error.message, true); }
});
$('upload-form').addEventListener('submit', run($('upload-form'), async () => {
  const file = $('upload-file').files[0]; if (!file) throw new Error('파일을 선택해주세요.');
  const form = new FormData($('upload-form'));
  const indices = ['name_column', 'sid_column', 'club_column'].map(key => form.get(key));
  if (new Set(indices).size !== 3) throw new Error('이름·학번·소속을 서로 다른 열에 연결해주세요.');
  form.set('has_header', String($('upload-form').elements.has_header.checked)); form.append('file', file);
  const data = await api('/admin/import-members', {method: 'POST', body: form});
  show('upload-mapping', false); $('upload-file').value = ''; await loadMembers(); feedback(data.message);
}));
$('add-form').addEventListener('submit', run($('add-form'), async () => {
  const data = Object.fromEntries([...new FormData($('add-form'))].map(([key, value]) => [key, value.trim()]));
  if (Object.values(data).some(v => !v)) throw new Error('모든 정보를 입력해주세요.');
  await api('/admin/members', jsonRequest('POST', data)); $('add-form').reset(); await loadMembers(); feedback('회원 등록 또는 소속 추가를 완료했습니다.');
}));
$('notice-form').addEventListener('submit', run($('notice-form'), async () => {
  const data = await api('/admin/notice', jsonRequest('PUT', {content: $('notice-content').value}));
  await loadNotice(); feedback(data.message);
}));
function openEdit(member) {
  show('edit-feedback', false);
  editTarget = {...member}; $('edit-name').textContent = member.name;
  for (const field of ['sid', 'club', 'status', 'role']) $('edit-' + field).value = member[field === 'sid' ? 'student_id' : field] || '';
  $('edit-dialog').showModal();
}
$('close-edit').addEventListener('click', () => $('edit-dialog').close());
$('edit-form').addEventListener('submit', run($('edit-form'), async () => {
  const data = Object.fromEntries(new FormData($('edit-form')));
  if (!data.student_id.trim() || !data.club.trim()) throw new Error('학번과 소속을 입력해주세요.');
  if (editTarget.student_id === me.student_id && (data.student_id !== me.student_id || data.role !== me.role)) throw new Error('현재 로그인한 계정의 학번·권한 변경은 다른 관리자에게 요청해주세요.');
  try {
    for (const field of ['club', 'status', 'role']) {
      if (data[field] === editTarget[field]) continue;
      await api(`/admin/members/${encodeURIComponent(editTarget.student_id)}/${field}?${new URLSearchParams({[field]: data[field]})}`, {method: 'PATCH'});
      editTarget[field] = data[field];
    }
    if (data.student_id !== editTarget.student_id) {
      await api(`/admin/members/${encodeURIComponent(editTarget.student_id)}/id?${new URLSearchParams({new_id: data.student_id})}`, {method: 'PATCH'});
      editTarget.student_id = data.student_id;
    }
    $('edit-dialog').close(); await loadMembers(); feedback('회원 정보를 저장했습니다.');
  } catch (error) { if (token) await loadMembers(); throw error; }
}));
$('reset-password').addEventListener('click', run($('reset-password'), async () => {
  if (!confirm(`${editTarget.name}님의 비밀번호를 1234로 초기화할까요?`)) return;
  await api(`/admin/members/${encodeURIComponent(editTarget.student_id)}/reset-password`, {method: 'PATCH'});
  $('edit-dialog').close(); feedback('비밀번호를 1234로 초기화했습니다.');
}));
$('delete-member').addEventListener('click', run($('delete-member'), async () => {
  if (editTarget.student_id === me.student_id) throw new Error('현재 로그인한 계정은 여기서 삭제할 수 없습니다.');
  if (!confirm(`${editTarget.name} (${editTarget.student_id}) 회원을 삭제할까요? 복구할 수 없습니다.`)) return;
  await api(`/admin/members/${encodeURIComponent(editTarget.student_id)}`, {method: 'DELETE'});
  $('edit-dialog').close(); await loadMembers(); feedback('회원을 삭제했습니다.');
}));
setInterval(() => {
  $('clock').textContent = new Date().toLocaleString('ko-KR');
  if (token && expiresAt) {
    const remaining = Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000));
    $('expiry').textContent = `자동 로그아웃 ${Math.floor(remaining / 60)}:${String(remaining % 60).padStart(2, '0')}`;
    if (!remaining) logout('로그인 시간이 만료되었습니다. 다시 로그인해주세요.');
  }
}, 1000);
if (token) {
  setToken(token);
  enterApp().catch(error => {
    if (token) { show('app-view', false); show('login-view', true); feedback(error.message, true); }
  });
}
