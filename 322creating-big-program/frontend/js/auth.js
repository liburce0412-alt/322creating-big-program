/**
 * auth.js —— 登录状态管理 + 响应式导航栏渲染
 *
 * 负责：
 *   - localStorage 存取 token & user
 *   - 登录/登出/注册
 *   - 检查登录态
 *   - 渲染导航栏（桌面横向 + 移动端汉堡抽屉）
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
        window.location.href = 'login.html';
    },

    /**
     * 要求登录，未登录则跳转
     */
    requireLogin() {
        if (!this.isLoggedIn()) {
            window.location.href = 'login.html';
            return false;
        }
        return true;
    },

    /**
     * 渲染顶部导航栏（插入到 <nav id="navbar"> 中）
     * 桌面端：横向排列所有链接
     * 移动端：显示汉堡按钮，点击弹出侧滑抽屉
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
        // admin check
        try { var p = await api.getProfile(); if (p) { localStorage.setItem("campus_user", JSON.stringify(p)); } } catch(e) {}
        const _cu = JSON.parse(localStorage.getItem("campus_user") || "{}");
        if (_cu.is_admin) navItems.push({ href: "admin.html", icon: "⚙️", label: "管理后台" });
        // 构建桌面端导航链接 HTML
        const desktopNav = navItems.map(item =>
            `<li><a href="${item.href}" class="${currentPage === item.href ? 'active' : ''}">${item.icon} ${item.label}</a></li>`
        ).join('');

        // 构建移动端抽屉链接 HTML
        const drawerNav = navItems.map(item =>
            `<li><a href="${item.href}" class="${currentPage === item.href ? 'active' : ''}">${item.icon} ${item.label}</a></li>`
        ).join('');

        // 获取最新用户信息（等级可能发生变化）
        let profile = null;
        try {
            profile = await api.getProfile();
            localStorage.setItem('campus_user', JSON.stringify(profile));
        } catch (e) {
            profile = user;
        }

        const displayName = profile ? profile.username : (user ? user.username : '');
        const displayLevel = profile ? profile.level : (user ? user.level : 1);

        // 渲染导航栏
        navEl.innerHTML = `
            <button class="nav-toggle" id="nav-toggle" aria-label="菜单" style="display:inline-flex;align-items:center;gap:6px;padding:6px 14px;width:auto;border-radius:8px;background:var(--primary);color:white;border:none;cursor:pointer;font-size:0.85rem;">
                ☰ 菜单
            </button>
            <div class="navbar-brand">
                <span class="logo-icon">🎓</span> 校园达人
            </div>
            <ul class="navbar-nav">${desktopNav}</ul>
            <div class="navbar-user">
                <span class="username">${displayName}</span>
                <span class="level-badge">Lv.${displayLevel}</span>
                <button class="btn-logout" onclick="auth.logout()">退出</button>
            </div>
        `;

        // 创建移动端抽屉（插入到 body）
        this._renderDrawer(displayName, displayLevel, drawerNav, currentPage);

        // 绑定汉堡按钮事件
        this._bindDrawerEvents();
    },

    /**
     * 渲染移动端抽屉菜单
     */
    _renderDrawer(username, level, navHTML, currentPage) {
        // 移除旧抽屉
        const oldOverlay = document.getElementById('nav-drawer-overlay');
        const oldDrawer = document.getElementById('nav-drawer');
        if (oldOverlay) oldOverlay.remove();
        if (oldDrawer) oldDrawer.remove();

        const overlay = document.createElement('div');
        overlay.id = 'nav-drawer-overlay';
        overlay.className = 'nav-drawer-overlay';

        const drawer = document.createElement('div');
        drawer.id = 'nav-drawer';
        drawer.className = 'nav-drawer';

        drawer.innerHTML = `
            <div class="drawer-header">
                <span class="drawer-title">🎓 校园达人</span>
                <button class="drawer-close" id="drawer-close">✕</button>
            </div>
            <ul class="drawer-nav">${navHTML}</ul>
            <div class="drawer-user">
                <span>👤 ${username}</span>
                <span class="level-badge" style="margin-left:auto;">Lv.${level}</span>
            </div>
        `;

        document.body.appendChild(overlay);
        document.body.appendChild(drawer);
    },

    /**
     * 绑定抽屉开关事件
     */
    _bindDrawerEvents() {
        const toggle = document.getElementById('nav-toggle');
        const overlay = document.getElementById('nav-drawer-overlay');
        const drawer = document.getElementById('nav-drawer');
        const closeBtn = document.getElementById('drawer-close');

        if (!toggle || !overlay || !drawer) return;

        const openDrawer = () => {
            toggle.classList.add('active');
            overlay.classList.add('open');
            drawer.classList.add('open');
            document.body.style.overflow = 'hidden';
        };

        const closeDrawer = () => {
            toggle.classList.remove('active');
            overlay.classList.remove('open');
            drawer.classList.remove('open');
            document.body.style.overflow = '';
        };

        // 移除旧事件（避免重复绑定）
        toggle.replaceWith(toggle.cloneNode(true));
        overlay.replaceWith(overlay.cloneNode(true));
        closeBtn?.replaceWith(closeBtn.cloneNode(true));

        const newToggle = document.getElementById('nav-toggle');
        const newOverlay = document.getElementById('nav-drawer-overlay');
        const newCloseBtn = document.getElementById('drawer-close');

        newToggle?.addEventListener('click', () => {
            const drawerEl = document.getElementById('nav-drawer');
            if (drawerEl?.classList.contains('open')) {
                closeDrawer();
            } else {
                openDrawer();
            }
        });

        newOverlay?.addEventListener('click', closeDrawer);
        newCloseBtn?.addEventListener('click', closeDrawer);

        // 抽屉内链接点击后自动关闭
        const drawerLinks = document.querySelectorAll('#nav-drawer .drawer-nav a');
        drawerLinks.forEach(link => {
            link.addEventListener('click', () => {
                setTimeout(closeDrawer, 200);
            });
        });

        // ESC 关闭
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeDrawer();
        });
    }
};
