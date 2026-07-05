// records.js —— 时间记录 CRUD（前后端联调版）
if (!localStorage.getItem("campus_token")) { window.location.href = "/login.html"; }

let records = [];
let currentCategory = "";

const recordList = document.getElementById("recordList");
const filterTabs = document.getElementById("filterTabs");
const searchInput = document.getElementById("searchInput");

function getToken() {
    return localStorage.getItem("campus_token");
}

async function fetchWithAuth(url, options = {}) {
    const token = getToken();
    if (token) {
        options.headers = { ...options.headers, "Authorization": "Bearer " + token };
    }
    const resp = await fetch(url, options);
    if (!resp.ok) {
        const err = new Error("API Error: " + resp.status);
        if (resp.status === 401) { localStorage.removeItem("campus_token"); window.location.href = "/login.html"; }
        throw err;
    }
    return resp.json();
}

async function fetchRecords() {
    try {
        const params = new URLSearchParams();
        if (currentCategory) params.append("category", currentCategory);
        const data = await fetchWithAuth("/api/time-records?" + params.toString());
        records = data.records || [];
    } catch (e) {
        console.error("Failed to load records:", e);
        records = [];
    }
    renderRecords();
}

function renderRecords() {
    recordList.innerHTML = "";
    if (records.length === 0) {
        recordList.innerHTML = "<div class=\"empty-state\"><i class=\"fas fa-clock\" style=\"font-size:48px;opacity:0.3;\"></i><p>暂无记录</p></div>";
        return;
    }
    records.forEach(function(rec) {
        const card = document.createElement("div");
        card.className = "record-card";
        card.innerHTML = [
            "<div class=\"record-info\">",
            "<span class=\"category-badge " + rec.category + "\">" + rec.category + "</span>",
            "<span class=\"record-desc\">" + (rec.description || "-") + "</span>",
            "<span class=\"record-time\">" + rec.duration_min + "分钟 · " + new Date(rec.created_at).toLocaleString() + "</span>",
            "</div>",
            "<div class=\"record-actions\">",
            "<button class=\"btn btn-sm btn-danger delete-btn\" data-id=\"" + rec.id + "\"><i class=\"fas fa-trash\"></i></button>",
            "</div>"
        ].join("");
        recordList.appendChild(card);
    });
    document.querySelectorAll(".delete-btn").forEach(function(btn) {
        btn.addEventListener("click", async function(e) {
            await deleteRecord(e.currentTarget.dataset.id);
        });
    });
}

async function deleteRecord(id) {
    try {
        await fetchWithAuth("/api/time-records/" + id, { method: "DELETE" });
        showGlobalAlert("删除成功", "success");
    } catch (e) {
        showGlobalAlert("删除失败: " + e.message, "error");
    }
    fetchRecords();
}

document.getElementById("recordForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const category = document.getElementById("category").value;
    const description = document.getElementById("description").value.trim();
    const duration = document.getElementById("duration").value;
    if (!category || !description || !duration) return;
    try {
        await fetchWithAuth("/api/time-records", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ category: category, description: description, duration_min: parseInt(duration) })
        });
        showGlobalAlert("记录添加成功", "success");
    } catch (e) {
        showGlobalAlert("添加失败: " + e.message, "error");
    }
    document.getElementById("recordForm").reset();
    fetchRecords();
});

filterTabs.addEventListener("click", function(e) {
    if (e.target.classList.contains("filter-tab")) {
        currentCategory = e.target.dataset.category;
        document.querySelectorAll(".filter-tab").forEach(function(t) { t.classList.remove("active"); });
        e.target.classList.add("active");
        fetchRecords();
    }
});

document.getElementById("searchBtn").addEventListener("click", async function() {
    const q = searchInput.value.trim();
    if (!q) return;
    try {
        const data = await fetchWithAuth("/api/search?q=" + encodeURIComponent(q));
        records = data.results || [];
    } catch (e) {
        records = [];
    }
    renderRecords();
});

document.getElementById("undoBtn").addEventListener("click", async function() {
    try {
        await fetchWithAuth("/api/time-records/undo", { method: "POST" });
        showGlobalAlert("撤销成功", "success");
    } catch (e) {
        showGlobalAlert("撤销失败: " + e.message, "error");
    }
    fetchRecords();
});

document.getElementById("redoBtn").addEventListener("click", async function() {
    try {
        await fetchWithAuth("/api/time-records/redo", { method: "POST" });
        showGlobalAlert("重做成功", "success");
    } catch (e) {
        showGlobalAlert("重做失败: " + e.message, "error");
    }
    fetchRecords();
});

fetchRecords();
