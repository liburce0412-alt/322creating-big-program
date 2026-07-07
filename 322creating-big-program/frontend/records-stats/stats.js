const MOCK_STATS = {
    by_category: {
        '学习': 210,
        '运动': 40,
        '娱乐': 60,
        '其他': 30
    },
    by_date: [
        { date: '07-01', total: 90 },
        { date: '07-02', total: 120 },
        { date: '07-03', total: 80 },
        { date: '07-04', total: 180 },
        { date: '07-05', total: 0 }
    ]
};

let pieChartInstance, barChartInstance;

async function fetchStats() {
    try {
        const data = await fetchWithAuth('/api/time-records/stats');
        renderCharts(data);
    } catch (e) {
        console.warn('使用模拟统计数据');
        renderCharts(MOCK_STATS);
    }
}

function renderCharts(stats) {
    if (pieChartInstance) pieChartInstance.destroy();
    if (barChartInstance) barChartInstance.destroy();

    const categories = Object.keys(stats.by_category);
    const values = Object.values(stats.by_category);
    const hasCategoryData = values.some(v => v > 0);

    // 饼图
    if (hasCategoryData) {
        document.getElementById('pieEmpty').style.display = 'none';
        const ctx1 = document.getElementById('pieChart').getContext('2d');
        pieChartInstance = new Chart(ctx1, {
            type: 'pie',
            data: {
                labels: categories,
                datasets: [{
                    data: values,
                    backgroundColor: ['#0984e3', '#00b894', '#fdcb6e', '#b2bec3'],
                    borderColor: 'white',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    } else {
        document.getElementById('pieEmpty').style.display = 'block';
        document.getElementById('pieChart').style.display = 'none';
    }

    // 柱状图
    const dates = stats.by_date.map(d => d.date);
    const totals = stats.by_date.map(d => d.total);
    const hasDailyData = totals.some(v => v > 0);
    if (hasDailyData) {
        document.getElementById('barEmpty').style.display = 'none';
        const ctx2 = document.getElementById('barChart').getContext('2d');
        barChartInstance = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [{
                    label: '专注时长 (分钟)',
                    data: totals,
                    backgroundColor: 'rgba(91,141,239,0.7)',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true } }
            }
        });
    } else {
        document.getElementById('barEmpty').style.display = 'block';
        document.getElementById('barChart').style.display = 'none';
    }
}

fetchStats();