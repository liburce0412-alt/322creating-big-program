/**
 * 认证中间件 — 检查登录状态
 */

/**
 * 检查是否已登录，未登录则跳转登录页
 */
function requireAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/frontend/login.html';
        return false;
    }
    return true;
}

/**
 * 获取当前用户信息
 */
function getCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem('user') || 'null');
    } catch {
        return null;
    }
}

/**
 * 退出登录
 */
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/frontend/login.html';
}

/**
 * 更新导航栏激活状态
 */
function setActiveNav() {
    const path = window.location.pathname;
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        link.classList.remove('active');
        if (path.includes(link.getAttribute('href')?.replace('/frontend/', ''))) {
            link.classList.add('active');
        }
    });
}

// 页面加载时自动执行
document.addEventListener('DOMContentLoaded', () => {
    setActiveNav();

    // 为退出按钮绑定事件
    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }

    // 显示当前用户名
    const userEl = document.getElementById('current-user');
    if (userEl) {
        const user = getCurrentUser();
        if (user) {
            userEl.textContent = user.username;
        }
    }
});
