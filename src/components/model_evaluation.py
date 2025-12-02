import sys
import pandas as pd
from typing import Optional
from sklearn.metrics import f1_score
from dataclasses import dataclass

from src.logger import logging
from src.constants import TARGET_COLUMN
from src.exception import CustomException
from src.utils.main_utils import load_object
from src.entity.s3_estimator import CloudModelWrapper
from src.entity.config_entity import ModelEvaluationConfig
from src.entity.artifact_entity import DataIngestionArtifact, ModelTrainerArtifact, ModelEvaluationArtifact

@dataclass
class EvaluateModelResponse:
    trained_model_f1_score: float
    best_model_f1_score: float
    is_model_accepted: bool
    difference: float

class ModelEvaluation:
    """
    Handles comparison between the newly trained model and the currently
    deployed (production) model stored in S3. Determines whether the 
    newly trained model should replace the existing production model.
    """
    def __init__(self, model_evaluation_config: ModelEvaluationConfig, data_ingestion_artifact: DataIngestionArtifact, model_trainer_artifact: ModelTrainerArtifact):
        """
        Initialize the ModelEvaluation component.

        Args:
            model_evaluation_config (ModelEvaluationConfig): Config containing S3 paths and bucket information.
            data_ingestion_artifact (DataIngestionArtifact): Contains test dataset path.
            model_trainer_artifact (ModelTrainerArtifact): Contains trained model path and metrics.
        """
        try:
            self.model_evaluation_config = model_evaluation_config
            self.data_ingestion_artifact = data_ingestion_artifact
            self.model_trainer_artifact = model_trainer_artifact
        except Exception as e:
            raise CustomException(e, sys) from e

    def get_best_model(self) -> Optional[CloudModelWrapper]:
        """
        Fetch the currently deployed model from S3 if it exists.

        Returns:
            Optional[CloudModelWrapper]: Loaded production model wrapper if present; otherwise None.
        """
        try:
            bucket_name = self.model_evaluation_config.bucket_name
            model_path = self.model_evaluation_config.s3_model_key_path
            cloud_model_wrapper = CloudModelWrapper(bucket_name, model_path)

            if cloud_model_wrapper.is_model_present(model_path):
                return cloud_model_wrapper
            
            return None
        except Exception as e:
            raise CustomException(e, sys) from e

    def _map_gender_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Converts the 'Gender' column from categorical strings to numeric binary values.

        Mapping:
            Female -> 0
            Male   -> 1

        Parameters
        ----------
        dataframe : pd.DataFrame
            Input DataFrame.

        Returns
        -------
        pd.DataFrame
            Updated DataFrame with mapped 'Gender' column.
        """
        logging.info("mapping 'Gender' column to binary values")
        dataframe['Gender'] = dataframe['Gender'].map({'Female': 0, 'Male': 1}).astype(int)
        return dataframe

    def _create_dummy_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Generates one-hot encoded dummy variables for categorical features.

        Notes
        -----
        drop_first=True is used to avoid multicollinearity.

        Parameters
        ----------
        dataframe : pd.DataFrame

        Returns
        -------
        pd.DataFrame
            DataFrame with new dummy variables.
        """
        logging.info("creating dummy variables for categorical features")
        dataframe = pd.get_dummies(dataframe, drop_first= True)
        return dataframe

    def _rename_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Renames specific columns (mainly vehicle age categories) and ensures
        appropriate integer datatypes for the newly created dummy columns.

        Parameters
        ----------
        dataframe : pd.DataFrame

        Returns
        -------
        pd.DataFrame
            Updated DataFrame with consistent naming and datatypes.
        """
        logging.info("renaming specific columns and casting to int")
        dataframe = dataframe.rename(columns= {
            "Vehicle_Age_< 1 Year": "Vehicle_Age_lt_1_Year",
            "Vehicle_Age_> 2 Years": "Vehicle_Age_gt_2_Years"
        })
        for col in ["Vehicle_Age_lt_1_Year", "Vehicle_Age_gt_2_Years", "Vehicle_Damage_Yes"]:
            if col in dataframe.columns:
                dataframe[col] = dataframe[col].astype('int')

        return dataframe

    def _drop_id_column(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Drops the 'id' column (or any user-specified ID columns) from the dataset.

        Parameters
        ----------
        dataframe : pd.DataFrame

        Returns
        -------
        pd.DataFrame
            DataFrame without the ID column.
        """
        logging.info("dropping 'id' column")
        if "_id" in dataframe:
            return dataframe.drop("_id", axis= 1)
        
    def evaluate_model(self) -> EvaluateModelResponse:
        """
        Compare the performance of the newly trained model with the 
        production model (if present).

        Steps:
            1. Load test data.
            2. Apply preprocessing identical to training pipeline.
            3. Predict using the newly trained model.
            4. Predict using production model (if exists).
            5. Compute F1-scores and determine whether to accept new model.

        Returns:
            EvaluateModelResponse: Evaluation results encapsulated in a dataclass.
        """
        try:
            test_df = pd.read_csv(self.data_ingestion_artifact.test_file_path)
            x, y = test_df.drop(TARGET_COLUMN, axis= 1), test_df[TARGET_COLUMN]

            logging.info("test data loaded; transforming for predictions...")

            x = self._map_gender_columns(x)
            x = self._drop_id_column(x)
            x = self._create_dummy_columns(x)
            x = self._rename_columns(x)

            trained_model = load_object(self.model_trainer_artifact.trained_model_file_path)
            logging.info("trained model loaded/exists")
            trained_model_f1_score = self.model_trainer_artifact.metric_artifact.f1_score
            logging.info(f"f1_score for trained model: {trained_model_f1_score}")

            best_model_f1_score = None
            best_model = self.get_best_model()
            if best_model is not None:
                logging.info(f"computing f1_score for production model...")
                y_hat_best_model = best_model.predict(x)
                best_model_f1_score = f1_score(y, y_hat_best_model)
                logging.info(f"f1_score for production model: {best_model_f1_score}, f1_score for new trained model: {trained_model_f1_score}")

            tmp_best_model_score = 0 if best_model_f1_score is None else best_model_f1_score
            result = EvaluateModelResponse(
                trained_model_f1_score,
                best_model_f1_score,
                is_model_accepted= trained_model_f1_score > tmp_best_model_score,
                difference= trained_model_f1_score - tmp_best_model_score
            )

            logging.info(f"Result: {result}")
            return result
        except Exception as e:
            raise CustomException(e, sys) from e

    def initiate_model_evaluation(self):
        """
        Execute the model evaluation pipeline and generate a ModelEvaluationArtifact.

        Returns:
            ModelEvaluationArtifact: Final evaluation output including:
                - acceptance flag
                - path of S3 production model
                - path of newly trained model
                - accuracy change
        """
        logging.info("Starting model evaluation...")
        try:
            evaluate_model_response = self.evaluate_model()
            s3_model_path = self.model_evaluation_config.s3_model_key_path

            model_evaluation_artifact = ModelEvaluationArtifact(
                is_model_accepted= evaluate_model_response.is_model_accepted,
                s3_model_path= s3_model_path,
                trained_model_path= self.model_trainer_artifact.trained_model_file_path,
                chaged_accuracy= evaluate_model_response.difference
            )

            logging.info(f"model evaluation completed, Model Evaluation Artifact: {model_evaluation_artifact}")
            return model_evaluation_artifact
        except Exception as e:
            raise CustomException(e, sys) from e