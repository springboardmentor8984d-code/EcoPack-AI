import joblib
import os
import onnxmltools
from onnxmltools.convert.common.data_types import FloatTensorType
import xgboost as xgb

def convert_models():
    # Load models
    models_dir = os.path.join('models')
    cost_model = joblib.load(os.path.join(models_dir, 'cost_model.pkl'))
    co2_model = joblib.load(os.path.join(models_dir, 'co2_model.pkl'))
    features = joblib.load(os.path.join(models_dir, 'features.pkl'))
    
    # Define input type (None implies dynamic batch size)
    initial_type = [('float_input', FloatTensorType([None, len(features)]))]
    
    # Convert Cost Model
    print(f"Converting Cost Model... (features: {features})")
    cost_booster = cost_model.get_booster()
    # Clear feature names to avoid "f%d" pattern error
    cost_booster.feature_names = None
    
    cost_onnx = onnxmltools.convert_xgboost(cost_booster, initial_types=initial_type)
    onnxmltools.utils.save_model(cost_onnx, os.path.join(models_dir, 'cost_model.onnx'))
    
    # Convert CO2 Model
    print("Converting CO2 Model...")
    co2_booster = co2_model.get_booster()
    co2_booster.feature_names = None
    
    co2_onnx = onnxmltools.convert_xgboost(co2_booster, initial_types=initial_type)
    onnxmltools.utils.save_model(co2_onnx, os.path.join(models_dir, 'co2_model.onnx'))
    
    print("Models converted to ONNX successfully.")
    
    # Verification
    cost_size = os.path.getsize(os.path.join(models_dir, 'cost_model.onnx'))
    co2_size = os.path.getsize(os.path.join(models_dir, 'co2_model.onnx'))
    print(f"Cost Model Size: {cost_size/1024:.2f} KB")
    print(f"CO2 Model Size: {co2_size/1024:.2f} KB")

if __name__ == "__main__":
    convert_models()
