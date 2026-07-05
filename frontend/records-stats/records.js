// 模拟数据
const MOCK_RECORDS = [
    { id: 1, category: '学习', description: '复习高等数学', duration_min: 90, created_at: '2026-07-04T10:30' },
    { id: 2, category: '运动', description: '跑步5公里', duration_min: 40, created_at: '2026-07-04T07:00' },
    { id: 3, category: '娱乐', description: '看纪录片', duration_min: 60, created_at: '2026-07-03T20:00' },
    { id: 4, category: '学习', description: '算法练习', duration_min: 120, created_at: '2026-07-03T14:00' }
];

let records = [];
let currentCategory = '';
let undoStack = [];

const recordList = document.getElementById('recordList');
const filterTabs = document.getElementById('filterTabs');
const searchInput = document.getElementById('searchInput');

// 获取记录
async function fetchRecords() {
    try {
        const params = new URLSearchParams();
        if (currentCategory) params.append('category', currentCategory);
        const data = await fetchWithAuth(`/api/time-records?${params}`);
        records = data.records || data;
    } catch (e) {
        console.warn('使用模拟数据');
        records = currentCategory
            ? MOCK_RECORDS.filter(r => r.category === currentCategory)
            : [...MOCK_RECORDS];
    }
    renderRecords();
}

// 渲染列表
function renderRecords() {
    recordList.innerHTML = '';
    if (records.length === 0) {
        recordList.innerHTML = '<div class="empty-state"><i class="fas fa-clock" style="font-size:48px;opacity:0.3;"></i><p>暂无记录</p></div>';
        return;
    }
    records.forEach(rec => {
        const card = document.createElement('div');
        card.className = 'record-card';
        card.innerHTML = `
            <div class="record-info">
                <span class="category-badge ${rec.category}">${rec.category}</span>
                <span class="record-desc">${rec.description}</span>
                <span class="record-time">${rec.duration_min}分钟 · ${new Date(rec.created_at).toLocaleString()}</span>
            </div>
            <div class="record-actions">
                <button class="btn btn-sm btn-danger delete-btn" data-id="${rec.id}"><i class="fas fa-trash"></i></button>
            </div>
        `;
        recordList.appendChild(card);
    });

    // 绑定删除事件
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = e.currentTarget.dataset.id;
            await deleteRecord(id);
        });
    });
}

// 删除记录
async function deleteRecord(id) {
    try {
        await fetchWithAuth(`/api/time-records/${id}`, { method: 'DELETE' });
        showGlobalAlert('删除成功', 'success');
    } catch (e) {
        // 模拟删除
        records = records.filter(r => r.id != id);
        showGlobalAlert('删除成功（模拟）', 'success');
    }
    fetchRecords();
}

// 添加记录
document.getElementById('recordForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const category = document.getElementById('category').value;
    const description = document.getElementById('description').value.trim();
    const duration = document.getElementById('duration').value;
    if (!category || !description || !duration) return;

    const body = { category, description, duration_min: parseInt(duration) };
    try {
        await fetchWithAuth('/api/time-records', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        showGlobalAlert('记录添加成功', 'success');
    } catch (e) {
        // 模拟添加
        const newRec = { id: Date.now(), ...body, created_at: new Date().toISOString() };
        records.unshift(newRec);
        showGlobalAlert('记录添加成功（模拟）', 'success');
    }
    document.getElementById('recordForm').reset();
    fetchRecords();
});

// 类别筛选
filterTabs.addEventListener('click', (e) => {
    if (e.target.classList.contains('filter-tab')) {
        currentCategory = e.target.dataset.category;
        document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
        e.target.classList.add('active');
        fetchRecords();
    }
});

// 关键词搜索
document.getElementById('searchBtn').addEventListener('click', async () => {
    const q = searchInput.value.trim();
    if (!q) return;
    try {
        const data = await fetchWithAuth(`/api/search?q=${encodeURIComponent(q)}`);
        records = data.records || data;
    } catch (e) {
        records = MOCK_RECORDS.filter(r => r.description.includes(q));
    }
    renderRecords();
});

// 撤销
document.getElementById('undoBtn').addEventListener('click', async () => {
    try {
        await fetchWithAuth('/api/time-records/undo', { method: 'POST' });
        showGlobalAlert('撤销成功', 'success');
    } catch (e) {
        if (records.length > 0) {
            undoStack.push(records.shift());
            renderRecords();
            showGlobalAlert('撤销（模拟）', 'success');
        }
    }
    fetchRecords();
});

// 重做
document.getElementById('redoBtn').addEventListener('click', async () => {
    try {
        await fetchWithAuth('/api/time-records/redo', { method: 'POST' });
        showGlobalAlert('重做成功', 'success');
    } catch (e) {
        if (undoStack.length > 0) {
            records.unshift(undoStack.pop());
            renderRecords();
            showGlobalAlert('重做（模拟）', 'success');
        }
    }
});

// 初始化
fetchRecords();