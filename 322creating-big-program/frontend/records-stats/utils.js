// 获取存储的 token
function getToken() {
    return localStorage.getItem('token');
}

// 带认证的 fetch 封装
async function fetchWithAuth(url, options = {}) {
    const token = getToken();
    if (token) {
        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };
    }
    const response = await fetch(url, options);
    if (!response.ok) {
        const error = new Error('请求失败');
        error.status = response.status;
        throw error;
    }
    return response.json();
}

// 显示顶部提示（适用于多数页面）
function showGlobalAlert(message, type = 'error') {
    const alertBox = document.getElementById('alertBox');
    if (!alertBox) return;
    alertBox.textContent = message;
    alertBox.className = `alert alert-${type}`;
    alertBox.style.display = 'flex';
    setTimeout(() => {
        alertBox.style.display = 'none';
    }, 3000);
}