/**
 * API 请求封装
 * 自动附带 JWT Token，统一处理错误
 */
const API_BASE = '/api';

const api = {
    /**
     * 发送 HTTP 请求
     */
    async request(method, path, data = null, options = {}) {
        const url = `${API_BASE}${path}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        const token = localStorage.getItem('token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = { method, headers, ...options };

        if (data && method !== 'GET') {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, config);
            const result = await response.json();

            if (result.code === 401) {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/frontend/login.html';
                return null;
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            return { code: 500, message: '网络请求失败，请检查连接' };
        }
    },

    get(path, params = {}) {
        const query = new URLSearchParams(params).toString();
        const fullPath = query ? `${path}?${query}` : path;
        return this.request('GET', fullPath);
    },

    post(path, data) { return this.request('POST', path, data); },
    put(path, data) { return this.request('PUT', path, data); },
    delete(path) { return this.request('DELETE', path); },
};

// ========== 认证相关 ==========
const AuthAPI = {
    register: (data) => api.post('/auth/register', data),
    login: (data) => api.post('/auth/login', data),
    getMe: () => api.get('/auth/me'),
    updateProfile: (data) => api.put('/auth/profile', data),
};

// ========== 番茄钟相关 ==========
const PomodoroAPI = {
    start: (data) => api.post('/pomodoro/start', data),
    pause: (id) => api.post(`/pomodoro/pause/${id}`),
    resume: (id) => api.post(`/pomodoro/resume/${id}`),
    complete: (id) => api.post(`/pomodoro/complete/${id}`),
    abandon: (id) => api.post(`/pomodoro/abandon/${id}`),
    current: () => api.get('/pomodoro/current'),
    list: (params) => api.get('/pomodoro/list', params),
    stats: () => api.get('/pomodoro/stats'),
};

// ========== 成就相关 ==========
const AchievementAPI = {
    list: (params) => api.get('/achievement/list', params),
    user: () => api.get('/achievement/user'),
    check: () => api.post('/achievement/check'),
    stats: () => api.get('/achievement/stats'),
};

// ========== AI 相关 ==========
const AIAPI = {
    generateReport: (data) => api.post('/ai/report/generate', data),
    listReports: (params) => api.get('/ai/report/list', params),
    getReport: (id) => api.get(`/ai/report/${id}`),
    deleteReport: (id) => api.delete(`/ai/report/${id}`),
    sendMessage: (data) => api.post('/ai/chat/send', data),
    chatHistory: (params) => api.get('/ai/chat/history', params),
    clearChat: () => api.delete('/ai/chat/clear'),
    insights: () => api.get('/ai/insights'),
};

// ========== 时间记录相关 ==========
const TimeAPI = {
    create: (data) => api.post('/time/record', data),
    list: (params) => api.get('/time/records', params),
    update: (id, data) => api.put(`/time/record/${id}`, data),
    delete: (id) => api.delete(`/time/record/${id}`),
    stats: () => api.get('/time/stats'),
};
