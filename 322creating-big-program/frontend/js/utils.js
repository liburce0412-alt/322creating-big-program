/**
 * 通用工具函数
 */

/**
 * 显示 Toast 通知
 */
function showToast(message, type = 'info', duration = 3000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * 格式化时长（秒 → 可读文本）
 */
function formatDuration(seconds) {
    if (!seconds || seconds <= 0) return '0 分钟';
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
        return `${hours} 小时 ${mins > 0 ? mins + ' 分钟' : ''}`;
    }
    return `${mins} 分钟`;
}

/**
 * 格式化时间（秒 → MM:SS）
 */
function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

/**
 * 格式化日期
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const h = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${day} ${h}:${min}`;
}

/**
 * 获取状态标签
 */
function getStatusBadge(status) {
    const map = {
        'running': '<span style="color:#10B981">● 进行中</span>',
        'paused': '<span style="color:#F59E0B">⏸ 已暂停</span>',
        'completed': '<span style="color:#4F46E5">✓ 已完成</span>',
        'abandoned': '<span style="color:#EF4444">✗ 已放弃</span>',
        'pending': '<span style="color:#64748B">○ 待开始</span>',
    };
    return map[status] || status;
}

/**
 * 防抖
 */
function debounce(fn, delay = 300) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

/**
 * 获取今天的日期字符串
 */
function todayStr() {
    return new Date().toISOString().split('T')[0];
}
