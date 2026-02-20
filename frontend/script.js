let latestResults = [];
let latestTop10 = [];
let latestMeta = {};
let history = []; // stores only the displayed (top 3) recommendations per run

const baseLayout = (title, xTitle, yTitle) => ({
    title,
    margin: { l: 80, r: 30, b: 90, t: 60 },
    xaxis: { title: { text: xTitle, standoff: 14 }, automargin: true },
    yaxis: { title: { text: yTitle, standoff: 14 }, automargin: true },
    legend: { orientation: "h", x: 0, y: 1.18 }
});

// Load persisted history on page load
document.addEventListener("DOMContentLoaded", () => {
    loadHistory();
    
    // ===============================
    // FORM SUBMIT
    // ===============================
    const form = document.getElementById("recommendationForm");
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        // Save form values to localStorage
        const formData = {
            product_category: document.getElementById("product_category").value,
            fragility: document.getElementById("fragility").value,
            shipping_type: document.getElementById("shipping_type").value,
            sustainability_priority: document.getElementById("sustainability_priority").value
        };
        localStorage.setItem("ecopackFormData", JSON.stringify(formData));

        const payload = formData;

        try {
            const res = await fetch(`${API_BASE_URL}/recommend`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            latestResults = data.recommended_materials || [];
            latestTop10 = data.top10 && data.top10.length ? data.top10 : latestResults;
            latestMeta = data.inputs || {};

            if (latestResults.length === 0) return;

            history.push(latestResults);

            updateTable(latestResults);
            updateMetrics(latestResults);
            drawMaterialComparison(latestResults);
            enableExports();
        } catch (err) {
            console.error("Error fetching recommendations:", err);
        }
    });
    
    // ===============================
    // CLEAR FORM
    // ===============================
    document.getElementById("clearFormBtn").addEventListener("click", () => {
        form.reset();
        localStorage.removeItem("ecopackFormData");
        clearRecommendationResults();
    });
    
    // ===============================
    // RESTORE FORM VALUES
    // ===============================
    const savedFormData = localStorage.getItem("ecopackFormData");
    if (savedFormData) {
        try {
            const formData = JSON.parse(savedFormData);
            document.getElementById("product_category").value = formData.product_category || "";
            document.getElementById("fragility").value = formData.fragility || "";
            document.getElementById("shipping_type").value = formData.shipping_type || "";
            document.getElementById("sustainability_priority").value = formData.sustainability_priority || "";
        } catch (err) {
            console.error("Error restoring form data:", err);
        }
    }
    
    // Setup chart mode button listeners
    document.querySelectorAll(".chart-mode-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".chart-mode-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const mode = btn.dataset.chartMode;

            if (mode === "material_comparison") drawMaterialComparison(latestResults);
            if (mode === "ranking_display") drawRankingDisplay();
        });
    });
    
    // Setup clickable info card listeners
    document.querySelectorAll(".clickable-card").forEach(card => {
        card.addEventListener("click", () => {
            const mode = card.dataset.chartMode;
            
            if (mode === "co2_reduction") openCO2Modal();
            if (mode === "cost_savings") openCostSavingsModal();
        });
    });
    
    // Setup modal event listeners
    document.getElementById("co2ModalClose").addEventListener("click", closeCO2Modal);
    document.getElementById("costModalClose").addEventListener("click", closeCostSavingsModal);

    // Close modal when clicking outside
    document.getElementById("co2Modal").addEventListener("click", (e) => {
        if (e.target.id === "co2Modal") closeCO2Modal();
    });

    document.getElementById("costModal").addEventListener("click", (e) => {
        if (e.target.id === "costModal") closeCostSavingsModal();
    });
});

// ===============================
// HISTORY LOAD
// ===============================
async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE_URL}/history`);
        const data = await res.json();
        const rawHistory = data.history || [];
        // keep only top 3 per run for charting
        history = rawHistory.map(run => run.slice(0, 3));

        if (history.length > 0) {
            const lastRunTop3 = history[history.length - 1];
            const lastRunFull = rawHistory[rawHistory.length - 1] || [];
            latestResults = lastRunTop3;
            latestTop10 = lastRunFull.slice(0, 10);
            latestMeta = {};
            updateTable(latestResults);
            updateMetrics(latestResults);
            drawMaterialComparison(latestResults);
        }
    } catch (err) {
        console.error("Failed to load history", err);
    }
}

// ===============================
// TABLE
// ===============================
function updateTable(data) {
    const tbody = document.getElementById("resultsTable");
    tbody.innerHTML = "";

    data.forEach(item => {
        tbody.innerHTML += `
            <tr>
                <td>${item.material}</td>
                <td>${item.predicted_cost.toFixed(2)}</td>
                <td>${item.predicted_co2.toFixed(2)}</td>
                <td>${item.suitability_score.toFixed(2)}</td>
            </tr>
        `;
    });
}

// ===============================
// METRICS
// ===============================
function updateMetrics(data) {
    const baselineCO2 = 10;
    const baselineCost = 10;

    const avgCO2 = data.reduce((s, d) => s + d.predicted_co2, 0) / data.length;
    const avgCost = data.reduce((s, d) => s + d.predicted_cost, 0) / data.length;

    const co2Reduction = ((baselineCO2 - avgCO2) / baselineCO2) * 100;
    const costSavings = baselineCost - avgCost;

    // Calculate average across all historical runs
    let avgCO2Reduction = 0;
    let avgCostSavings = 0;

    if (history.length > 0) {
        const reductions = history.map(run => {
            const runAvgCO2 = run.reduce((s, d) => s + d.predicted_co2, 0) / run.length;
            return ((baselineCO2 - runAvgCO2) / baselineCO2) * 100;
        });
        avgCO2Reduction = reductions.reduce((a, b) => a + b, 0) / reductions.length;

        const savings = history.map(run => {
            const runAvgCost = run.reduce((s, d) => s + d.predicted_cost, 0) / run.length;
            return baselineCost - runAvgCost;
        });
        avgCostSavings = savings.reduce((a, b) => a + b, 0) / savings.length;
    } else {
        avgCO2Reduction = co2Reduction;
        avgCostSavings = costSavings;
    }

    document.getElementById("co2ReductionValue").innerText =
        `${avgCO2Reduction.toFixed(2)}%`;
    document.getElementById("co2ReductionSubtext").innerText =
        `Average across ${history.length} runs`;

    document.getElementById("costSavingsValue").innerText =
        avgCostSavings.toFixed(2);
    document.getElementById("costSavingsSubtext").innerText =
        `Average across ${history.length} runs`;
}

// ===============================
// MODAL MANAGEMENT
// ===============================
function openCO2Modal() {
    const modal = document.getElementById("co2Modal");
    modal.classList.add("active");
    setTimeout(() => drawCO2ReductionChartInModal(), 100);
}

function closeCO2Modal() {
    const modal = document.getElementById("co2Modal");
    modal.classList.remove("active");
}

function openCostSavingsModal() {
    const modal = document.getElementById("costModal");
    modal.classList.add("active");
    setTimeout(() => drawCostSavingsChartInModal(), 100);
}

function closeCostSavingsModal() {
    const modal = document.getElementById("costModal");
    modal.classList.remove("active");
}

// ===============================
// BAR CHART – MATERIAL COMPARISON
// ===============================
function drawMaterialComparison(data) {
    const pool = history.flat().length ? history.flat() : data;
    const byMaterial = {};
    pool.forEach(d => {
        if (!byMaterial[d.material]) byMaterial[d.material] = { total: 0, count: 0 };
        byMaterial[d.material].total += d.suitability_score;
        byMaterial[d.material].count += 1;
    });

    const materials = Object.keys(byMaterial);
    const avgScores = materials.map(m => byMaterial[m].total / byMaterial[m].count);

    Plotly.newPlot("primaryChartCanvas", [{
        x: materials,
        y: avgScores,
        type: "bar"
    }], baseLayout("Material Comparison", "Material", "Avg Suitability Score"));
}


// ===============================
// HORIZONTAL BAR – RANKING
// ===============================
function drawRankingDisplay() {
    const pool = history.flat().length ? history.flat() : latestResults;
    const byMaterial = {};
    pool.forEach(d => {
        if (!byMaterial[d.material]) byMaterial[d.material] = { total: 0, count: 0 };
        byMaterial[d.material].total += d.suitability_score;
        byMaterial[d.material].count += 1;
    });
    const materials = Object.keys(byMaterial);
    const avgScores = materials.map(m => byMaterial[m].total / byMaterial[m].count);

    Plotly.newPlot("primaryChartCanvas", [{
        y: materials,
        x: avgScores,
        type: "bar",
        orientation: "h"
    }], baseLayout("Sustainability Ranking", "Avg Suitability Score", "Material"));
}

// ===============================
// CO2 REDUCTION CHART
// ===============================
function drawCO2ReductionChart() {
    const baselineCO2 = 10;
    const pool = history.flat().length ? history.flat() : latestResults;
    
    if (pool.length === 0) {
        Plotly.purge("primaryChartCanvas");
        return;
    }

    const byMaterial = {};
    pool.forEach(d => {
        if (!byMaterial[d.material]) byMaterial[d.material] = { total: 0, count: 0 };
        byMaterial[d.material].total += d.predicted_co2;
        byMaterial[d.material].count += 1;
    });

    const materials = Object.keys(byMaterial);
    const avgCO2s = materials.map(m => byMaterial[m].total / byMaterial[m].count);
    const reductions = avgCO2s.map(co2 => ((baselineCO2 - co2) / baselineCO2) * 100);

    Plotly.newPlot("primaryChartCanvas", [{
        x: materials,
        y: reductions,
        type: "bar",
        marker: { color: "#2f9d78" }
    }], baseLayout("CO2 Reduction %", "Material", "Reduction %"));
}

// ===============================
// COST SAVINGS CHART
// ===============================
function drawCostSavingsChart() {
    const baselineCost = 10;
    const pool = history.flat().length ? history.flat() : latestResults;
    
    if (pool.length === 0) {
        Plotly.purge("primaryChartCanvas");
        return;
    }

    const byMaterial = {};
    pool.forEach(d => {
        if (!byMaterial[d.material]) byMaterial[d.material] = { total: 0, count: 0 };
        byMaterial[d.material].total += d.predicted_cost;
        byMaterial[d.material].count += 1;
    });

    const materials = Object.keys(byMaterial);
    const avgCosts = materials.map(m => byMaterial[m].total / byMaterial[m].count);
    const savings = avgCosts.map(cost => baselineCost - cost);

    Plotly.newPlot("primaryChartCanvas", [{
        x: materials,
        y: savings,
        type: "bar",
        marker: { color: "#ef9b33" }
    }], baseLayout("Cost Savings", "Material", "Savings ($)"));
}

// ===============================
// CO2 REDUCTION TREND CHART (MODAL)
// ===============================
function drawCO2ReductionChartInModal() {
    const baselineCO2 = 10;
    
    if (history.length === 0) {
        return;
    }

    // Calculate CO2 reduction % for each run
    const runNumbers = [];
    const reductionValues = [];

    history.forEach((run, runIndex) => {
        const avgCO2 = run.reduce((s, d) => s + d.predicted_co2, 0) / run.length;
        const reduction = ((baselineCO2 - avgCO2) / baselineCO2) * 100;
        runNumbers.push(`Run ${runIndex + 1}`);
        reductionValues.push(reduction);
    });

    Plotly.newPlot("co2ChartCanvas", [{
        x: runNumbers,
        y: reductionValues,
        type: "scatter",
        mode: "lines+markers",
        line: { color: "#2f9d78", width: 3 },
        marker: { size: 8, color: "#2f9d78" },
        fill: "tozeroy",
        fillcolor: "rgba(47, 157, 120, 0.2)"
    }], {
        title: "CO₂ Reduction Trend Over Time",
        xaxis: { title: "Recommendation Runs" },
        yaxis: { title: "CO₂ Reduction (%)" },
        margin: { l: 80, r: 30, b: 80, t: 60 },
        hovermode: "x unified"
    });
}

// ===============================
// COST SAVINGS TREND CHART (MODAL)
// ===============================
function drawCostSavingsChartInModal() {
    const baselineCost = 10;
    
    if (history.length === 0) {
        return;
    }

    // Calculate cost savings for each run
    const runNumbers = [];
    const savingsValues = [];

    history.forEach((run, runIndex) => {
        const avgCost = run.reduce((s, d) => s + d.predicted_cost, 0) / run.length;
        const savings = baselineCost - avgCost;
        runNumbers.push(`Run ${runIndex + 1}`);
        savingsValues.push(savings);
    });

    Plotly.newPlot("costChartCanvas", [{
        x: runNumbers,
        y: savingsValues,
        type: "scatter",
        mode: "lines+markers",
        line: { color: "#ef9b33", width: 3 },
        marker: { size: 8, color: "#ef9b33" },
        fill: "tozeroy",
        fillcolor: "rgba(239, 155, 51, 0.2)"
    }], {
        title: "Cost Savings Trend Over Time",
        xaxis: { title: "Recommendation Runs" },
        yaxis: { title: "Cost Savings ($)" },
        margin: { l: 80, r: 30, b: 80, t: 60 },
        hovermode: "x unified"
    });
}

// ===============================
// EXPORTS
// ===============================
function enableExports() {
    document.getElementById("exportPdfBtn").disabled = false;
    document.getElementById("exportExcelBtn").disabled = false;
}

document.getElementById("exportExcelBtn").addEventListener("click", () => {
    const exportData = (latestTop10.length ? latestTop10 : latestResults).slice(0, 10);
    const metaRows = [
        { Field: "Category", Value: latestMeta.product_category || "-" },
        { Field: "Fragility", Value: latestMeta.fragility || "-" },
        { Field: "Shipping", Value: latestMeta.shipping_type || "-" },
        { Field: "Priority", Value: latestMeta.sustainability_priority || "-" }
    ];

    const wsMeta = XLSX.utils.json_to_sheet(metaRows);
    const wsData = XLSX.utils.json_to_sheet(exportData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, wsMeta, "Inputs");
    XLSX.utils.book_append_sheet(wb, wsData, "Top10 Ranking");
    XLSX.writeFile(wb, "EcoPackAI_Ranking.xlsx");
});

document.getElementById("exportPdfBtn").addEventListener("click", () => {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    doc.text("EcoPackAI – Sustainability Report", 14, 14);
    doc.text(`Category: ${latestMeta.product_category || "-"}`, 14, 22);
    doc.text(`Fragility: ${latestMeta.fragility || "-"}`, 14, 28);
    doc.text(`Shipping: ${latestMeta.shipping_type || "-"}`, 14, 34);
    doc.text(`Priority: ${latestMeta.sustainability_priority || "-"}`, 14, 40);

    const exportData = (latestTop10.length ? latestTop10 : latestResults).slice(0, 10);

    doc.autoTable({
        startY: 46,
        head: [["Material", "Cost", "CO₂", "Score"]],
        body: exportData.map(d => [
            d.material,
            d.predicted_cost.toFixed(2),
            d.predicted_co2.toFixed(2),
            d.suitability_score.toFixed(2)
        ])
    });

    doc.save("EcoPackAI_Report.pdf");
});

// ===============================
// CLEAR HISTORY
// ===============================
document.getElementById("clearHistoryBtn").addEventListener("click", () => {
    clearHistory();
});

async function clearHistory() {
    try {
        await fetch(`${API_BASE_URL}/history/clear`, { method: "POST" });
    } catch (err) {
        console.error("Failed to clear server history", err);
    }

    history = [];
    latestResults = [];
    latestTop10 = [];
    latestMeta = {};

    const tbody = document.getElementById("resultsTable");
    tbody.innerHTML = `<tr><td colspan="4">History cleared. Submit new recommendation.</td></tr>`;

    document.getElementById("co2ReductionValue").innerText = "-";
    document.getElementById("co2ReductionSubtext").innerText = "Run recommendation";
    document.getElementById("costSavingsValue").innerText = "-";
    document.getElementById("costSavingsSubtext").innerText = "Run recommendation";

    Plotly.purge("primaryChartCanvas");
}

// ===============================
// CLEAR RECOMMENDATION RESULTS
// ===============================
function clearRecommendationResults() {
    // Clear current recommendation rows but keep historical metrics/cards intact
    latestResults = [];
    latestTop10 = [];
    latestMeta = {};

    const tbody = document.getElementById("resultsTable");
    tbody.innerHTML = `<tr><td colspan="4">Submit details to view recommendations</td></tr>`;

    // Disable export buttons since table has been cleared
    document.getElementById("exportPdfBtn").disabled = true;
    document.getElementById("exportExcelBtn").disabled = true;
}
