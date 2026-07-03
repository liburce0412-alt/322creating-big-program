function getToken() { return localStorage.getItem('token'); }
function setToken(t) { localStorage.setItem('token', t); }
function clearToken() { localStorage.removeItem('token'); }
function getUser() { const u = localStorage.getItem('user'); return u ? JSON.parse(u) : null; }
function setUser(u) { localStorage.setItem('user', JSON.stringify(u)); }

async function login() {
  const u = document.getElementById('username').value;
  const p = document.getElementById('password').value;
  const msg = document.getElementById('msg');
  try {
    const res = await api('/login', 'POST', {username:u, password:p});
    setToken(res.token); setUser(res.user);
    location.href = 'dashboard.html';
  } catch(e) { msg.textContent = e.message; }
}

async function register() {
  const u = document.getElementById('username').value;
  const p = document.getElementById('password').value;
  const msg = document.getElementById('msg');
  try {
    const res = await api('/register', 'POST', {username:u, password:p});
    setToken(res.token); setUser(res.user);
    location.href = 'dashboard.html';
  } catch(e) { msg.textContent = e.message; }
}

async function doRegister() {
  const u = document.getElementById('username').value;
  const p = document.getElementById('password').value;
  const c = document.getElementById('confirm').value;
  const msg = document.getElementById('msg');
  if (p !== c) { msg.textContent = '?????'; return; }
  try {
    const res = await api('/register', 'POST', {username:u, password:p});
    setToken(res.token); setUser(res.user);
    location.href = 'dashboard.html';
  } catch(e) { msg.textContent = e.message; }
}

function logout() { clearToken(); location.href = 'login.html'; }
