/**
 * utils.js —— 通用工具函数
 */

const utils = {
    /**
     * Toast 消息提示
     * @param {string} message - 消息内容
     * @param {string} type    - 'success' | 'error' | 'info'
     * @param {number} duration - 显示时长（毫秒）
     */
    toast(message, type = 'info', duration = 3000) {
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
            if (toast.parentNode) toast.remove();
        }, duration);
    },

    /**
     * 显示加载状态
     */
    showLoading(selector) {
        const el = document.querySelector(selector);
        if (el) el.innerHTML = '<div class="flex-center"><span class="spinner"></span></div>';
    },

    /**
     * 格式化分钟数为 "X小时Y分钟"
     */
    formatMinutes(minutes) {
        if (!minutes || minutes <= 0) return '0 分钟';
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        if (h > 0 && m > 0) return `${h} 小时 ${m} 分钟`;
        if (h > 0) return `${h} 小时`;
        return `${m} 分钟`;
    },

    /**
     * 格式化日期
     */
    formatDate(dateStr, withTime = false) {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        if (withTime) {
            const h = String(d.getHours()).padStart(2, '0');
            const min = String(d.getMinutes()).padStart(2, '0');
            return `${y}-${m}-${day} ${h}:${min}`;
        }
        return `${y}-${m}-${day}`;
    },

    /**
     * 获取今天日期字符串
     */
    today() {
        return new Date().toISOString().split('T')[0];
    },

    /**
     * 获取相对时间描述
     */
    timeAgo(dateStr) {
        const now = Date.now();
        const then = new Date(dateStr).getTime();
        const diff = Math.floor((now - then) / 1000);

        if (diff < 60) return '刚刚';
        if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`;
        if (diff < 604800) return `${Math.floor(diff / 86400)} 天前`;
        return this.formatDate(dateStr);
    },

    /**
     * 防抖
     */
    debounce(fn, delay = 300) {
        let timer;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    },

    /**
     * Canvas 画饼图
     * @param {string} canvasId - canvas 元素 ID
     * @param {Array} data      - [{label, value, color}]
     */
    drawPieChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        const cx = w / 2, cy = h / 2, r = Math.min(cx, cy) - 20;

        ctx.clearRect(0, 0, w, h);

        const total = data.reduce((sum, d) => sum + d.value, 0);
        if (total === 0) {
            ctx.fillStyle = '#999';
            ctx.font = '16px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('暂无数据', cx, cy);
            return;
        }

        let angle = -Math.PI / 2;
        const colors = ['#4A90D9', '#5CB85C', '#F5A623', '#D9534F', '#5BC0DE',
                         '#9B59B6', '#E67E22', '#1ABC9C', '#E74C3C', '#3498DB'];

        data.forEach((item, i) => {
            const slice = (item.value / total) * Math.PI * 2;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, r, angle, angle + slice);
            ctx.closePath();
            ctx.fillStyle = item.color || colors[i % colors.length];
            ctx.fill();

            // 标签
            const mid = angle + slice / 2;
            const lx = cx + Math.cos(mid) * (r + 30);
            const ly = cy + Math.sin(mid) * (r + 30);
            ctx.fillStyle = '#333';
            ctx.font = '12px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(`${item.label}(${Math.round(item.value/total*100)}%)`, lx, ly);

            angle += slice;
        });
    },

    /**
     * Canvas 画柱状图
     * @param {string} canvasId
     * @param {Array} data - [{label, value}]
     */
    drawBarChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        const padding = { top: 20, right: 20, bottom: 50, left: 50 };
        const chartW = w - padding.left - padding.right;
        const chartH = h - padding.top - padding.bottom;

        ctx.clearRect(0, 0, w, h);

        if (!data || data.length === 0) {
            ctx.fillStyle = '#999';
            ctx.font = '16px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('暂无数据', w/2, h/2);
            return;
        }

        const maxVal = Math.max(...data.map(d => d.value), 1);
        const barWidth = chartW / data.length * 0.6;
        const gap = chartW / data.length * 0.4;

        // Y 轴
        ctx.strokeStyle = '#ccc';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + chartH * (1 - i / 4);
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(w - padding.right, y);
            ctx.stroke();
            ctx.fillStyle = '#999';
            ctx.font = '11px sans-serif';
            ctx.textAlign = 'right';
            ctx.fillText(Math.round(maxVal * i / 4), padding.left - 8, y + 4);
        }

        // 柱状条
        data.forEach((item, i) => {
            const barH = (item.value / maxVal) * chartH;
            const x = padding.left + i * (barWidth + gap) + gap / 2;
            const y = padding.top + chartH - barH;

            ctx.fillStyle = '#4A90D9';
            ctx.fillRect(x, y, barWidth, barH);

            // X 轴标签
            ctx.fillStyle = '#333';
            ctx.font = '11px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(item.label, x + barWidth / 2, h - padding.bottom + 20);
        });
    },

    /**
     * 生成随机颜色
     */
    randomColor() {
        const colors = ['#4A90D9', '#5CB85C', '#F5A623', '#D9534F', '#5BC0DE',
                        '#9B59B6', '#E67E22', '#1ABC9C'];
        return colors[Math.floor(Math.random() * colors.length)];
    }
};
