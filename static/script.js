document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("productForm");
    const resultsSection = document.getElementById("resultsSection");
    const resultBody = document.getElementById("resultBody");

    form.addEventListener("submit", function (e) {

        e.preventDefault();

        const data = {
            product_category: document.getElementById("product_category").value.trim().toLowerCase(),
            fragility: document.getElementById("fragility").value,
            shipping_type: document.getElementById("shipping_type").value,
            sustainability_priority: document.getElementById("sustainability_priority").value
        };

        if (!data.product_category || !data.fragility ||
            !data.shipping_type || !data.sustainability_priority) {
            alert("Please fill all fields.");
            return;
        }

        fetch("/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {

            resultBody.innerHTML = "";

            result.recommended_materials.forEach((item, index) => {

                let rankClass = "";
                if (index === 0) rankClass = "rank-1";
                else if (index === 1) rankClass = "rank-2";
                else if (index === 2) rankClass = "rank-3";

                const row = `
                    <tr>
                        <td class="${rankClass}">#${index + 1}</td>
                        <td>${item.material}</td>
                        <td>${item.predicted_cost.toFixed(2)}</td>
                        <td>${item.predicted_co2.toFixed(2)}</td>
                        <td>${item.suitability_score.toFixed(2)}</td>
                    </tr>
                `;

                resultBody.innerHTML += row;
            });

            resultsSection.style.display = "block";

        })
        .catch(error => {
            console.error("Error:", error);
        });

    });

});