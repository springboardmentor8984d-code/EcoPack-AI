let chartInstance = null;

function getValue(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
}

function getRecommendation() {

    fetch("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            product_category: getValue("product_category"),
            fragility: getValue("fragility"),
            shipping_type: getValue("shipping_type"),
            sustainability_priority: getValue("sustainability_priority")
        })
    })
    .then(response => response.json())
    .then(data => {

        if (!data.recommended_materials || data.recommended_materials.length === 0) {
            alert("No recommendations found.");
            return;
        }

        const recommendations = data.recommended_materials;

        // Show dashboard section
        const dashboard = document.getElementById("dashboard");
        if (dashboard) {
            dashboard.classList.remove("hidden");
        }

        // ===== TOP CARD VALUES =====
        const top = recommendations[0];

        const costVal = document.getElementById("saveVal");
        const co2Val = document.getElementById("co2Val");

        if (costVal) costVal.innerText = "₹ " + top.cost_savings.toFixed(2);
        if (co2Val) co2Val.innerText = top.co2_reduction.toFixed(2) + " %";

        // ===== TABLE =====
        const table = document.getElementById("tableBody");
        if (table) {
            table.innerHTML = "";

            recommendations.forEach((r, index) => {
                table.innerHTML += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${r.material}</td>
                        <td>₹ ${r.cost.toFixed(2)}</td>
                        <td>${r.co2.toFixed(2)}</td>
                        <td>${r.score.toFixed(3)}</td>
                    </tr>
                `;
            });
        }

        // ===== BAR CHART =====
        const chartCanvas = document.getElementById("suitabilityChart");

        if (chartCanvas) {

            const ctx = chartCanvas.getContext("2d");

            if (chartInstance) {
                chartInstance.destroy();
            }

            chartInstance = new Chart(ctx, {
                type: "bar",
                data: {
                    labels: recommendations.map(r => r.material),
                    datasets: [{
                        label: "Suitability Score",
                        data: recommendations.map(r => r.score),
                        backgroundColor: "#2ecc71"
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: true
                        }
                    }
                }
            });
        }

    })
    .catch(error => {
        alert("Connection Error");
        console.error(error);
    });
}