import joblib

model = joblib.load("co2_model.pkl")

# Save in stable format
model.save_model("co2_model.json")

print("Model converted successfully!")