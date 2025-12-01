import sys
import numpy as np
from typing import Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from src.logger import logging
from src.exception import CustomException
from src.utils.main_utils import load_numpy_array, save_object, load_object
from src.entity.estimator import ModelWrapper
from src.entity.config_entity import ModelTrainerConfig
from src.entity.artifact_entity import DataTransformationArtifact, ModelTrainerArtifact, ClassificationMetricsArtifact

class ModelTrainer:
    """
    Trains a classification model using transformed data, evaluates performance,
    and saves the final model if performance meets the required threshold.
    
    This component handles:
    - Loading transformed numpy arrays
    - Training a RandomForest classifier
    - Producing evaluation metrics
    - Wrapping model + preprocessing into a single deployable object
    - Saving the trained model artifact
    """
    def __init__(self, data_transformation_artifact: DataTransformationArtifact, model_trainer_config: ModelTrainerConfig):
        """
        Initialize ModelTrainer with transformation artifacts and trainer config.

        Args:
            data_transformation_artifact (DataTransformationArtifact):
                Contains file paths for transformed train/test arrays and preprocessing object.
            
            model_trainer_config (ModelTrainerConfig):
                Contains hyperparameters for model training and save locations.
        """
        try:
            self.data_transformation_artifact = data_transformation_artifact
            self.model_trainer_config = model_trainer_config
        except Exception as e:
            raise CustomException(e, sys) from e

    def get_model_object_and_report(self, train: np.array, test: np.array) -> Tuple[object, object]:
        """
        Train the RandomForest model and compute performance metrics.

        Steps:
        - Split train/test arrays into features and targets
        - Train RandomForestClassifier with config hyperparameters
        - Predict on test data
        - Compute accuracy, F1-score, precision, recall
        - Return trained model & metric artifact

        Args:
            train (np.array): Transformed training array with features + target.
            test (np.array): Transformed testing array with features + target.

        Returns:
            Tuple[object, ClassificationMetricArtifact]:
                trained model object, metric artifact containing evaluation scores.
        """
        try:
            logging.info("training RandomForestClassifier with specifies parameters")

            # splitting datasets with features and targets
            x_train, y_train, x_test, y_test = train[:, :-1], train[:, -1], test[:, :-1], test[:, -1]
            
            logging.info("initialising RandomForestClassifier with specified parameters")
            model = RandomForestClassifier(
                n_estimators= self.model_trainer_config._n_estimators,
                min_samples_split= self.model_trainer_config._min_samples_split,
                min_samples_leaf= self.model_trainer_config._min_samples_leaf,
                max_depth= self.model_trainer_config._max_depth,
                criterion= self.model_trainer_config._criterion,
                random_state= self.model_trainer_config._random_state
            )

            logging.info("model initialised; starting training...")
            model.fit(x_train, y_train)
            logging.info("training completed.")

            # prediction and evaluation metrics
            y_pred = model.predict(x_test)

            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)

            metric_artifact = ClassificationMetricsArtifact(
                accuracy= accuracy,
                f1_score= f1,
                precision_score= precision,
                recall_score= recall
            )

            return model, metric_artifact
        except Exception as e:
            raise CustomException(e, sys) from e

    def initiate_model_trainer(self) -> ModelTrainerArtifact:
        """
        Orchestrates the complete model training pipeline.

        Steps:
        - Load transformed train/test numpy arrays
        - Train model and compute metrics
        - Load preprocessing object
        - Validate model performance against expected accuracy threshold
        - Save final packed model (preprocessor + trained model)
        - Return ModelTrainerArtifact containing model path & evaluation metrics

        Returns:
            ModelTrainerArtifact: 
                File path of the trained model and evaluation metrics.
        """
        try:
            logging.info("Starting model training...")
            logging.info("loading train and test files...")
            train_arr = load_numpy_array(self.data_transformation_artifact.transformed_train_file_path)
            test_arr = load_numpy_array(self.data_transformation_artifact.transformed_test_file_path)
            logging.info("loaded train and test files.")

            # model training and metrics
            trained_model, trained_model_metrics = self.get_model_object_and_report(train_arr, test_arr)

            # loading preprocessing object 
            preprocessing_obj = load_object(self.data_transformation_artifact.transformed_object_file_path)

            logging.info("checking if accuracy of model beats the threshold")
            if accuracy_score(train_arr[:, -1], trained_model.predict(train_arr[:, :-1])) < self.model_trainer_config.expected_accuracy:
                raise Exception("Model failed to reach the threshold")
            
            logging.info("Model beats the threshold, saving the model...")
            new_model = ModelWrapper(preprocessing_obj, trained_model)
            save_object(self.model_trainer_config.trained_model_file_path, new_model)
            logging.info("Model saved.")

            logging.info("model training completed.")
            return ModelTrainerArtifact(
                self.model_trainer_config.trained_model_file_path,
                trained_model_metrics
            )
        except Exception as e:
            raise CustomException(e, sys) from e