/**
 * auth.js —— 登录状态管理
 *
 * 负责：
 *   - localStorage 存取 token & user
 *   - 登录/登出/注册
 *   - 检查登录态
 *   - 渲染导航栏
 */

const auth = {
    /**
     * 获取当前用户信息（从 localStorage）
     */
    getUser() {
        const raw = localStorage.getItem('campus_user');
        return raw ? JSON.parse(raw) : null;
    },

    /**
     * 获取 token
     */
    getToken() {
        return localStorage.getItem('campus_token');
    },

    /**
     * 是否已登录
     */
    isLoggedIn() {
        return !!this.getToken();
    },

    /**
     * 保存登录信息
     */
    saveSession(token, user) {
        localStorage.setItem('campus_token', token);
        localStorage.setItem('campus_user', JSON.stringify(user));
    },

    /**
     * 登录
     */
    async login(username, password) {
        const data = await api.login(username, password);
        this.saveSession(data.token, data.user);
        return data;
    },

    /**
     * 注册
     */
    async register(username, password) {
        const data = await api.register(username, password);
        this.saveSession(data.token, data.user);
        return data;
    },

    /**
     * 登出
     */
    logout() {
        localStorage.removeItem('campus_token');
        localStorage.removeItem('campus_user');
        window.location.href = '/login.html';
    },

    /**
     * 要求登录，未登录则跳转
     */
    requireLogin() {
        if (!this.isLoggedIn()) {
            window.location.href = '/login.html';
            return false;
        }
        return true;
    },

    /**
     * 渲染顶部导航栏（插入到 <nav id="navbar"> 中）
     */
    async renderNavbar() {
        const navEl = document.getElementById('navbar');
        if (!navEl) return;

        const user = this.getUser();
        const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';

        const navItems = [
            { href: 'dashboard.html',    icon: '🏠', label: '首页' },
            { href: 'pomodoro.html',     icon: '🍅', label: '番茄钟' },
            { href: 'records.html',      icon: '📝', label: '时间记录' },
            { href: 'stats.html',        icon: '📊', label: '统计' },
            { href: 'ai-report.html',    icon: '🤖', label: 'AI 分析' },
            { href: 'achievements.html', icon: '🏆', label: '成就' },
        ];

        const navHTML = navItems.map(item =>
            `<a href="${item.href}" class="${currentPage === item.href ? 'active' : ''}">${item.icon} ${item.label}</a>`
        ).join('');

        // 获取最新用户信息（等级可能发生变化）
        let profile = null;
        try {
            profile = await api.getProfile();
            // 更新本地存储
            localStorage.setItem('campus_user', JSON.stringify(profile));
        } catch (e) {
            profile = user;
        }

        navEl.innerHTML = `
            <div class="navbar-brand">
                <span class="logo-icon">🎓</span> 校园达人
            </div>
            <ul class="navbar-nav">${navHTML}</ul>
            <div class="navbar-user">
                <span class="username">${profile ? profile.username : (user ? user.username : '')}</span>
                <span class="level-badge">Lv.${profile ? profile.level : (user ? user.level : 1)}</span>
                <button class="btn-logout" onclick="auth.logout()">退出</button>
            </div>
        `;
    }
};
