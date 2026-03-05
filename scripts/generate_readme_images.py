from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

out = Path("images")
out.mkdir(parents=True, exist_ok=True)

# 1) Architecture diagram
fig, ax = plt.subplots(figsize=(8, 10))
ax.axis("off")
boxes = [
    (0.5, 0.9, "User Interface Layer"),
    (0.5, 0.75, "Flask Backend API"),
    (0.25, 0.55, "AI/ML Layer\nRandom Forest + XGBoost"),
    (0.75, 0.55, "PostgreSQL Database"),
    (0.75, 0.35, "BI Dashboard"),
    (0.5, 0.15, "Deployment Layer"),
]
for x, y, t in boxes:
    ax.add_patch(plt.Rectangle((x - 0.16, y - 0.05), 0.32, 0.1, fill=False, lw=2, ec="#2f855a"))
    ax.text(x, y, t, ha="center", va="center", fontsize=11)

def arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.8))

arrow(0.5, 0.85, 0.5, 0.8)
arrow(0.5, 0.70, 0.28, 0.60)
arrow(0.5, 0.70, 0.72, 0.60)
arrow(0.75, 0.50, 0.75, 0.40)
arrow(0.75, 0.30, 0.52, 0.20)
ax.text(0.5, 0.97, "EcoPackAI System Architecture", ha="center", fontsize=14, fontweight="bold")
fig.savefig(out / "architecture_new.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# Data used for dashboard-like visuals
materials = [
    "Starch Film", "Leaf Wrap", "Tissue Paper", "Thin Paper", "Aluminum Can",
    "Steel Tin", "Bagasse Bowl", "Molded Pulp", "Hemp Board", "Glass Jar", "Metal Drum", "Palm Leaf"
]
scores = np.array([0.96, 0.96, 0.93, 0.92, 0.65, 0.55, 0.53, 0.52, 0.36, 0.33, 0.33, 0.31])
usage_vals = np.array([2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1])

# 2) Main dashboard composite
fig, axs = plt.subplots(2, 2, figsize=(14, 8))
fig.suptitle("EcoPackAI - Sustainable Packaging Intelligence", fontsize=16, fontweight="bold")

axs[0, 0].bar(materials, usage_vals, color="#2a9d8f")
axs[0, 0].set_title("Material Usage Ranking")
axs[0, 0].tick_params(axis="x", rotation=50)

axs[0, 1].barh(materials[::-1], scores[::-1], color="#4a90e2")
axs[0, 1].set_title("Sustainability Ranking")
axs[0, 1].set_xlim(0, 1)

axs[1, 0].plot(materials, scores, marker="o", color="#8e44ad")
axs[1, 0].fill_between(range(len(scores)), scores, color="#d7bde2", alpha=0.6)
axs[1, 0].set_title("Recommendation Trends")
axs[1, 0].tick_params(axis="x", rotation=50)
axs[1, 0].set_ylim(0.2, 1.0)

axs[1, 1].pie([26, 74], labels=["Eco Friendly", "Standard"], autopct="%1.0f%%", colors=["#7fbf7f", "#d95f59"])
axs[1, 1].set_title("Material Distribution")

fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(out / "dashboard-main.png", dpi=200)
plt.close(fig)

# 3) Material distribution chart
fig, ax = plt.subplots(figsize=(10, 6))
ax.pie([26, 74], labels=["Eco Friendly", "Standard"], autopct="%1.0f%%", colors=["#7fbf7f", "#d95f59"])
ax.set_title("Material Distribution")
fig.savefig(out / "material-distribution.png", dpi=200)
plt.close(fig)

# 4) Recommendation trends chart
fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(materials, scores, marker="o", color="#8e44ad", lw=2)
ax.fill_between(range(len(scores)), scores, color="#d7bde2", alpha=0.5)
ax.set_ylim(0.2, 1.0)
ax.set_ylabel("Suitability Score")
ax.set_title("Recommendation Trends")
ax.tick_params(axis="x", rotation=45)
fig.tight_layout()
fig.savefig(out / "recommendation-trends.png", dpi=200)
plt.close(fig)

# 5) Model metric snapshots
fig, ax = plt.subplots(figsize=(7, 3.8))
ax.axis("off")
ax.text(0.02, 0.75, "Cost MAE: 0.5789", fontsize=18)
ax.text(0.02, 0.50, "Cost RMSE: 0.7784", fontsize=18)
ax.text(0.02, 0.25, "Cost R²: 0.8708", fontsize=18)
fig.savefig(out / "model-metrics-cost.png", dpi=220, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 3.8))
ax.axis("off")
ax.text(0.02, 0.75, "CO₂ MAE: 0.4326", fontsize=18)
ax.text(0.02, 0.50, "CO₂ RMSE: 0.6520", fontsize=18)
ax.text(0.02, 0.25, "CO₂ R²: 0.9460", fontsize=18)
fig.savefig(out / "model-metrics-co2.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# 6) Best material output
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.axis("off")
ax.text(0.03, 0.65, "Best Material: Corn Peanuts", fontsize=24, fontfamily="monospace")
ax.text(0.03, 0.35, "Final Score: 0.27214285714285713", fontsize=24, fontfamily="monospace")
fig.savefig(out / "best-material-output.png", dpi=220, bbox_inches="tight")
plt.close(fig)

print("Generated README images in images/")
