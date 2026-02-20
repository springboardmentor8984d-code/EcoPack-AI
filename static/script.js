let chartInstance = null;

function getValue(id){
    const el = document.getElementById(id);
    return el ? el.value : "";
}

function getRecommendation(){

    fetch("/recommend",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            category: getValue("category"),
            weight: getValue("weight"),
            fragility: getValue("fragility"),
            shipping: getValue("shipping"),
            distance: getValue("distance"),
            quantity: getValue("quantity")
        })
    })
    .then(response => response.json())
    .then(data => {

        if(data.error){
            alert("Server Error: " + data.error);
            return;
        }

        const dashboard = document.getElementById("dashboard");
        if(dashboard){
            dashboard.classList.remove("hidden");
        }

        const costVal = document.getElementById("saveVal");
        const co2Val = document.getElementById("co2Val");

        if(costVal) costVal.innerText = "₹" + data.estimated_cost;
        if(co2Val) co2Val.innerText = data.estimated_co2;

        const table = document.getElementById("tableBody");
        if(table){
            table.innerHTML = "";
            data.recommendations.forEach((r, index) => {
                table.innerHTML += `
                    <tr>
                        <td>${index+1}</td>
                        <td>${r.material}</td>
                        <td>${r.cost}</td>
                        <td>${r.co2}</td>
                        <td>${r.suitability}</td>
                    </tr>
                `;
            });
        }

        const chartCanvas = document.getElementById("suitabilityChart");
        if(chartCanvas){

            const ctx = chartCanvas.getContext("2d");

            if(chartInstance){
                chartInstance.destroy();
            }

            chartInstance = new Chart(ctx, {
                type: "bar",
                data: {
                    labels: data.recommendations.map(r => r.material),
                    datasets: [{
                        label: "Suitability %",
                        data: data.recommendations.map(r => r.suitability),
                        backgroundColor: "#2ecc71"
                    }]
                },
                options: {
                    responsive: true
                }
            });
        }

    })
    .catch(error => {
        alert("Connection Error");
        console.log(error);
    });
}

