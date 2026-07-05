/**
 * api.js —— 统一的 fetch 封装
 *
 * 所有前端 API 请求都通过此模块发出，自动：
 *   - 携带 JWT token（从 localStorage 读取）
 *   - 处理 401 过期跳转登录页
 *   - JSON 解析 & 错误统一处理
 */

const API_BASE = '/api';

const api = {
    /**
     * 通用请求
     * @param {string} method - GET | POST | PUT | DELETE
     * @param {string} path   - 接口路径（如 '/user/profile'）
     * @param {object} body   - 请求体（仅 POST/PUT）
     * @returns {Promise<object>} 解析后的 JSON
     */
    async request(method, path, body = null) {
        const headers = { 'Content-Type': 'application/json' };
        const token = localStorage.getItem('campus_token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const opts = { method, headers };
        if (body && (method === 'POST' || method === 'PUT')) {
            opts.body = JSON.stringify(body);
        }

        let url = API_BASE + path;

        // GET 请求的参数拼接到 URL
        if (method === 'GET' && body) {
            const params = new URLSearchParams(body).toString();
            if (params) url += '?' + params;
        }

        const resp = await fetch(url, opts);

        // 401 未登录 → 强制跳转
        if (resp.status === 401) {
            localStorage.removeItem('campus_token');
            localStorage.removeItem('campus_user');
            if (window.location.pathname !== '/login.html' &&
                window.location.pathname !== '/register.html' &&
                window.location.pathname !== '/' &&
                !window.location.pathname.endsWith('login.html') &&
                !window.location.pathname.endsWith('register.html')) {
                window.location.href = 'login.html';
            }
            throw new Error('登录已过期，请重新登录');
        }

        const data = await resp.json();

        if (!resp.ok) {
            throw new Error(data.error || `请求失败 (${resp.status})`);
        }

        return data;
    },

    get(path, params = null)    { return this.request('GET', path, params); },
    post(path, body = {})       { return this.request('POST', path, body); },
    put(path, body = {})        { return this.request('PUT', path, body); },
    del(path, body = null)      { return this.request('DELETE', path, body); },

    // ---- 认证 ----
    login(username, password)       { return this.post('/login', { username, password }); },
    register(username, password)   { return this.post('/register', { username, password }); },

    // ---- 用户 ----
    getProfile()                    { return this.get('/user/profile'); },
    getAchievements()               { return this.get('/user/achievements'); },
    getAllAchievements()            { return this.get('/user/achievements/all'); },

    // ---- 时间记录 ----
    getTimeRecords(params)          { return this.get('/time-records', params); },
    addTimeRecord(data)             { return this.post('/time-records', data); },
    deleteTimeRecord(id)            { return this.del(`/time-records/${id}`); },
    getTimeStats()                  { return this.get('/time-records/stats'); },
    undoRecord()                    { return this.post('/time-records/undo'); },
    redoRecord()                    { return this.post('/time-records/redo'); },

    // ---- 番茄钟 ----
    completePomodoro(durationMin)   { return this.post('/pomodoro/complete', { duration_min: durationMin }); },
    getPomodoroHistory(page, limit) { return this.get('/pomodoro/history', { page, limit }); },
    getPomodoroStats()              { return this.get('/pomodoro/stats'); },

    // ---- AI ----
    getAiModels()                   { return this.get('/ai/models'); },
    generateReport(model)           { return this.get('/ai/report', { model }); },
    getReports()                    { return this.get('/ai/reports'); },
    getReportDetail(id)             { return this.get(`/ai/reports/${id}`); },
    getChatHistory()                { return this.get('/ai/chat-history'); },
    sendChatMessage(message)        { return this.post('/ai/chat', { message }); },

    // ---- 搜索 ----
    search(keyword)                 { return this.get('/search', { q: keyword }); },
};
