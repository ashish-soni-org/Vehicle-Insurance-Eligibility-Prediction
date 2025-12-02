import sys

from src.logger import logging
from src.exception import CustomException

from src.components.data_ingestion import DataIngestion
from src.components.data_validation import DataValidation
from src.components.data_transformation import DataTransformation
from src.components.model_trainer import ModelTrainer
from src.components.model_evaluation import ModelEvaluation
from src.components.model_pusher import ModelPusher

from src.entity.config_entity import DataIngestionConfig, DataValidationConfig, DataTransformationConfig, ModelTrainerConfig, ModelEvaluationConfig, ModelPusherConfig
from src.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact, DataTransformationArtifact, ModelTrainerArtifact, ModelEvaluationArtifact, ModelPusherArtifact

class TrainPipeline:
    """
    Orchestrates the end-to-end machine learning training workflow.

    This pipeline coordinates all stages of the ML lifecycle, including:
        - Data ingestion from the feature store
        - Data validation and schema checks
        - Data transformation and preprocessing
        - Model training
        - Model evaluation against the existing model
        - Model pushing to production (if accepted)

    Each stage produces an artifact object that is passed to the next component,
    ensuring a modular, traceable, and reproducible pipeline execution.
    """    
    def __init__(self):
        """
        Initialize the TrainPipeline with configuration objects for each pipeline stage.

        All components (ingestion, validation, transformation, training, evaluation,
        and pusher) receive their respective configuration classes, which define 
        file paths, schema details, hyperparameters, thresholds, and output locations.
        """
        self.data_ingestion_config = DataIngestionConfig()
        self.data_validation_config = DataValidationConfig()
        self.data_transformation_config = DataTransformationConfig()
        self.model_trainer_config = ModelTrainerConfig()
        self.model_evaluation_config = ModelEvaluationConfig()
        self.model_pushing_config = ModelPusherConfig()

    def start_data_ingestion(self) -> DataIngestionArtifact:
        """
        Execute the data ingestion stage of the pipeline.

        This step:
            - Connects to MongoDB
            - Exports raw data into the feature store
            - Splits data into training and testing sets
            - Produces a DataIngestionArtifact containing the file paths

        Returns
        -------
        DataIngestionArtifact
            Artifact containing paths to the ingested training and testing datasets.
        """
        try:
            logging.info("------------------------------------------------------------------------------------------------")
            logging.info("Starting first phase of pipeline: Data Ingestion...")
            data_ingestion = DataIngestion(self.data_ingestion_config)
            data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
            logging.info("first phase of pipeline completed: Data Ingestion")
            
            return data_ingestion_artifact
        except Exception as e:
            raise CustomException(e, sys) from e

    def start_data_validation(self, data_ingestion_artifact: DataIngestionArtifact) -> DataValidationArtifact:
        """
        Perform schema validation, dataset integrity checks, and drift detection.

        Parameters
        ----------
        data_ingestion_artifact : DataIngestionArtifact
            Contains file paths of the ingested train and test datasets.

        Returns
        -------
        DataValidationArtifact
            Artifact containing validation status, schema reports, and drift reports.
        """
        try:
            logging.info("------------------------------------------------------------------------------------------------")
            logging.info("Starting second phase of pipeline: Data Validation...")
            data_validation = DataValidation(data_ingestion_artifact, self.data_validation_config)
            data_validation_artifact = data_validation.initiate_data_validation()
            logging.info("second phase of pipeline completed: Data Validation")

            return data_validation_artifact
        except Exception as e:
            raise CustomException(e, sys) from e

    def start_data_transformation(self, data_ingestion_artifact : DataIngestionArtifact, data_validation_artifact : DataValidationArtifact) -> DataTransformationArtifact:
        """
        Transform the validated dataset into numerical format suitable for model training.

        This step applies:
            - Missing value handling
            - Encoding and scaling
            - Feature engineering
            - Train-test transformation synchronization
            - Pipeline object creation and saving

        Parameters
        ----------
        data_ingestion_artifact : DataIngestionArtifact
            Paths to ingested train and test datasets.
        data_validation_artifact : DataValidationArtifact
            Validation outputs ensuring schema correctness.

        Returns
        -------
        DataTransformationArtifact
            Artifact containing transformed arrays and the preprocessing object.
        """
        try:
            logging.info("------------------------------------------------------------------------------------------------")
            logging.info("Starting third phase of pipeline: Data Transformation...")
            data_transformation = DataTransformation(data_ingestion_artifact, data_validation_artifact, self.data_transformation_config)
            data_transformation_artifact = data_transformation.initiate_data_transformation()
            logging.info("third phase of pipeline completed: Data Transformation")

            return data_transformation_artifact
        except Exception as e:
            raise CustomException(e, sys) from e

    def start_model_trainer(self, data_transformation_artifact: DataTransformationArtifact) -> ModelTrainerArtifact:
        """
        Train the machine learning model using the transformed data.

        This includes:
            - Selecting the algorithm
            - Hyperparameter tuning (if configured)
            - Training the model
            - Saving the trained model

        Parameters
        ----------
        data_transformation_artifact : DataTransformationArtifact
            Artifact containing transformed train/test arrays and preprocessing path.

        Returns
        -------
        ModelTrainerArtifact
            Artifact containing trained model path and training metrics.
        """
        try:
            logging.info("------------------------------------------------------------------------------------------------")
            logging.info("Starting fourth phase of pipeline: Model Training...")
            model_trainer = ModelTrainer(data_transformation_artifact, self.model_trainer_config)
            model_trainer_artifact = model_trainer.initiate_model_trainer()
            logging.info("fourth phase of pipeline completed: Model Training")

            return model_trainer_artifact
        except Exception as e:
            raise CustomException(e, sys) from e

    def start_model_evaluation(self, data_ingestion_artifact: DataIngestionArtifact, model_trainer_artifact: ModelTrainerArtifact) -> ModelEvaluationArtifact:
        """
        Evaluate the newly trained model against the existing production model.

        This step determines whether the new model performs better than the current 
        one based on a defined metric threshold.

        Parameters
        ----------
        data_ingestion_artifact : DataIngestionArtifact
            Contains raw train/test file paths.
        model_trainer_artifact : ModelTrainerArtifact
            Contains trained model and accuracy metrics.

        Returns
        -------
        ModelEvaluationArtifact
            Artifact indicating whether the new model is accepted.
        """
        try:
            logging.info("------------------------------------------------------------------------------------------------")
            logging.info("Starting fifth phase of pipeline: Model Evaluation...")
            model_evaluation = ModelEvaluation(self.model_evaluation_config, data_ingestion_artifact, model_trainer_artifact)
            model_evaluation_artifact = model_evaluation.initiate_model_evaluation()
            logging.info("fifth phase of pipeline completed: Model Evaluation")
            
            return model_evaluation_artifact
        except Exception as e:
            raise CustomException(e, sys) from e

    def start_model_pushing(self, model_evaluation_artifact: ModelEvaluationArtifact) -> ModelPusherArtifact:
        """
        Push the accepted model to production or saved model directory.

        This includes:
            - Copying the trained model to the deployment directory
            - Versioning or archiving previous models (depending on config)

        Parameters
        ----------
        model_evaluation_artifact : ModelEvaluationArtifact
            Evaluation output indicating model acceptance status.

        Returns
        -------
        ModelPusherArtifact
            Artifact containing the final deployed model path.
        """
        try:
            logging.info("------------------------------------------------------------------------------------------------")
            logging.info("Starting sixth phase of pipeline: Model Pushing...")
            model_pusher = ModelPusher(model_evaluation_artifact, self.model_pushing_config)
            model_pusher_artifact = model_pusher.initiate_model_pusher()
            logging.info("sixth phase of pipeline completed: Model Pushing")
            
            return model_pusher_artifact
        except Exception as e:
            raise CustomException(e, sys) from e

    def run_pipeline(self) -> None:
        """
        Execute the full end-to-end machine learning training pipeline.

        This function sequentially triggers:
            1. Data Ingestion
            2. Data Validation
            3. Data Transformation
            4. Model Training
            5. Model Evaluation
            6. Model Pushing (only if the model is accepted)
        """
        try:
            data_ingestion_artifact = self.start_data_ingestion()
            data_validation_artifact = self.start_data_validation(data_ingestion_artifact)
            data_transformation_artifact = self.start_data_transformation(data_ingestion_artifact, data_validation_artifact)
            model_trainer_artifact = self.start_model_trainer(data_transformation_artifact)
            model_evaluation_artifact = self.start_model_evaluation(data_ingestion_artifact, model_trainer_artifact)

            if not model_evaluation_artifact.is_model_accepted:
                logging.info("Model not accepted")
                return None

            model_pusher_artifact = self.start_model_pushing(model_evaluation_artifact)
        except Exception as e:
            raise CustomException(e, sys) from e
