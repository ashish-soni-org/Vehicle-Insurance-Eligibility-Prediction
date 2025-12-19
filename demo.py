from src.pipeline.training_pipeline import TrainPipeline
from dotenv import load_dotenv

# 1. This MUST come first
load_dotenv()

if __name__ == "__main__":
    pipeline = TrainPipeline()
    pipeline.run_pipeline()
