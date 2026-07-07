// stats.js —— 时间统计（前后端联调版）
if (!localStorage.getItem("campus_token")) { window.location.href = "/login.html"; }

let pieChartInstance, barChartInstance;

function getToken() {
    return localStorage.getItem("campus_token");
}

async function fetchWithAuth(url, options = {}) {
    const token = getToken();
    if (token) { options.headers = { ...options.headers, "Authorization": "Bearer " + token }; }
    const resp = await fetch(url, options);
    if (!resp.ok) {
        if (resp.status === 401) { localStorage.removeItem("campus_token"); window.location.href = "/login.html"; }
        throw new Error("API Error");
    }
    return resp.json();
}

async function fetchStats() {
    try {
        const data = await fetchWithAuth("/api/time-records/stats");
        renderCharts(data);
    } catch (e) {
        console.error("Failed to load stats:", e);
    }
}

function renderCharts(stats) {
    if (pieChartInstance) pieChartInstance.destroy();
    if (barChartInstance) barChartInstance.destroy();
    document.getElementById("pieChart").style.display = "block";
    document.getElementById("barChart").style.display = "block";
    document.getElementById("pieEmpty").style.display = "none";
    document.getElementById("barEmpty").style.display = "none";

    var categories = [];
    var values = [];
    if (stats.by_category) {
        stats.by_category.forEach(function(item) {
            categories.push(item.category);
            values.push(item.total_min);
        });
    }

    var hasCategoryData = values.some(function(v) { return v > 0; });
    if (hasCategoryData) {
        var ctx = document.getElementById("pieChart").getContext("2d");
        pieChartInstance = new Chart(ctx, {
            type: "pie",
            data: {
                labels: categories,
                datasets: [{ data: values, backgroundColor: ["#0984e3","#00b894","#fdcb6e","#b2bec3","#e17055","#6c5ce7"], borderColor: "white", borderWidth: 2 }]
            },
            options: { responsive: true, plugins: { legend: { position: "bottom" } } }
        });
    } else {
        document.getElementById("pieEmpty").style.display = "block";
        document.getElementById("pieChart").style.display = "none";
    }

    var dates = [];
    var totals = [];
    if (stats.by_date) {
        stats.by_date.forEach(function(d) {
            dates.push(d.date);
            totals.push(d.total_min);
        });
    }
    var hasDaily = totals.some(function(v) { return v > 0; });
    if (hasDaily) {
        var ctx2 = document.getElementById("barChart").getContext("2d");
        barChartInstance = new Chart(ctx2, {
            type: "bar",
            data: {
                labels: dates,
                datasets: [{ label: "专注时长 (分钟)", data: totals, backgroundColor: "rgba(91,141,239,0.7)", borderRadius: 8 }]
            },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });
    } else {
        document.getElementById("barEmpty").style.display = "block";
        document.getElementById("barChart").style.display = "none";
    }
}

fetchStats();
