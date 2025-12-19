from dataclasses import dataclass
from datetime import datetime
from src.constants import MODEL_FILE_NAME, MODEL_BUCKET_NAME

@dataclass
class VehiclePredictorConfig:
    model_file_path: str = MODEL_FILE_NAME
    model_bucket_name: str = MODEL_BUCKET_NAME