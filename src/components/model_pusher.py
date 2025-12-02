import sys

from src.logger import logging
from src.exception import CustomException
from src.entity.s3_estimator import CloudModelWrapper
from src.entity.config_entity import ModelPusherConfig 
from src.cloud_storage.aws_storage import SimpleStorageService
from src.entity.artifact_entity import ModelEvaluationArtifact, ModelPusherArtifact

class ModelPusher:
    """
    Handles uploading the newly trained and validated model to S3.
    This component runs only when the new model has been accepted
    during model evaluation.
    """
    def __init__(self, model_evaluation_artifact: ModelEvaluationArtifact, model_pusher_config: ModelPusherConfig):
        """
        Initialize the ModelPusher component.

        Args:
            model_evaluation_artifact (ModelEvaluationArtifact):
                Contains trained model path and whether it was accepted.
            model_pusher_config (ModelPusherConfig):
                Contains S3 bucket name and key path for saving the model.
        """
        self.s3 = SimpleStorageService()
        self.model_evaluation_artifact = model_evaluation_artifact
        self.model_pusher_config = model_pusher_config
        self.cloud_model_wrapper = CloudModelWrapper(
            self.model_pusher_config.bucket_name,
            self.model_pusher_config.s3_model_key_path
        )

    def initiate_model_pusher(self):
        """
        Upload the newly trained model to the configured S3 location.

        Steps:
            1. Load the model produced during training.
            2. Upload the model file to S3 using Prej1Estimator.
            3. Create and return ModelPusherArtifact describing upload results.

        Returns:
            ModelPusherArtifact: Contains S3 bucket name and the model upload path.
        """
        logging.info("Starting model pushing...")
        try:

            logging.info("Uploading new model to S3 bucket...")
            self.cloud_model_wrapper.save_model(self.model_evaluation_artifact.trained_model_path)
            model_pusher_artifact = ModelPusherArtifact(
                self.model_pusher_config.bucket_name,
                self.model_pusher_config.s3_model_key_path
            )
            logging.info("model uploaded to S3 bucket.")
            
            logging.info(f"model pushing completed, Model Pusher Artifact: {model_pusher_artifact}")
            return model_pusher_artifact
        except Exception as e:
            raise CustomException(e, sys) from e