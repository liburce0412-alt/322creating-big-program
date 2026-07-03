const API = window.location.origin + '/api';
async function api(path, method, body) {
  const opts = { method, headers: {}};
  const token = getToken();
  if (token) opts.headers.Authorization = 'Bearer ' + token;
  if (body) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
  const res = await fetch(API + path, opts);
  if (!res.ok) { const err = await res.json(); throw new Error(err.error || res.statusText); }
  return res.json();
}
