/**
 * api.js — 统一的 fetch 封装
 */
const API_BASE = '/api';
const api = {
    async request(method, path, body = null) {
        const headers = { 'Content-Type': 'application/json' };
        const token = localStorage.getItem('campus_token');
        if (token) { headers['Authorization'] = 'Bearer ' + token; }
        const opts = { method, headers };
        if (body && (method === 'POST' || method === 'PUT')) { opts.body = JSON.stringify(body); }
        let url = API_BASE + path;
        if (method === 'GET' && body) { body._t = Date.now(); const params = new URLSearchParams(body).toString(); if (params) url += '?' + params; }
        const resp = await fetch(url, opts);
        if (resp.status === 401) { localStorage.removeItem('campus_token'); localStorage.removeItem('campus_user'); if (window.location.pathname !== '/login.html' && window.location.pathname !== '/register.html' && window.location.pathname !== '/' && !window.location.pathname.endsWith('login.html') && !window.location.pathname.endsWith('register.html')) { window.location.href = 'login.html'; } throw new Error('登录已过期，请重新登录'); }
        const data = await resp.json();
        if (!resp.ok) { throw new Error(data.error || '请求失败 (' + resp.status + ')'); }
        return data;
    },
    get(path, params) { return this.request('GET', path, params); },
    post(path, body) { return this.request('POST', path, body); },
    put(path, body) { return this.request('PUT', path, body); },
    del(path, body) { return this.request('DELETE', path, body); },
    login(username, password) { return this.post('/login', { username, password }); },
    register(username, password) { return this.post('/register', { username, password }); },
    getProfile() { return this.get('/user/profile'); },
    getAchievements() { return this.get('/user/achievements'); },
    getAllAchievements() { return this.get('/user/achievements/all'); },
    getTimeRecords(params) { return this.get('/time-records', params); },
    addTimeRecord(data) { return this.post('/time-records', data); },
    deleteTimeRecord(id) { return this.del('/time-records/' + id); },
    getTimeStats() { return this.get('/time-records/stats'); },
    undoRecord() { return this.post('/time-records/undo'); },
    redoRecord() { return this.post('/time-records/redo'); },
    completePomodoro(d) { return this.post('/pomodoro/complete', { duration_min: d }); },
    getPomodoroHistory(p, l) { return this.get('/pomodoro/history', { page: p, limit: l }); },
    getPomodoroStats() { return this.get('/pomodoro/stats'); },
    getAiModels() { return this.get('/ai/models'); },
    generateReport(m) { return this.get('/ai/report', { model: m }); },
    getReports() { return this.get('/ai/reports'); },
    getReportDetail(id) { return this.get('/ai/reports/' + id); },
    getChatHistory() { return this.get('/ai/chat-history'); },
    sendChatMessage(msg, k) { var d = { message: msg }; if (k) d.api_key = k; return this.post('/ai/chat', d); },
    search(keyword) { return this.get('/search', { q: keyword }); },
    getAdminUsers() { return this.get('/admin/users'); },
    promoteAdmin(id) { return this.post('/admin/users/' + id + '/promote'); },
    demoteAdmin(id) { return this.post('/admin/users/' + id + '/demote'); },
    deleteUser(id) { return this.del('/admin/users/' + id); },
};