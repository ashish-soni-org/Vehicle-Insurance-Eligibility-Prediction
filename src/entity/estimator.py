import sys
import pandas as pd
from sklearn.pipeline import Pipeline

from src.exception import CustomException
from src.logger import logging

class TargetValueMapping:
    """
    Utility class for mapping target class labels between human-readable form
    and machine-learning-friendly numerical values.

    Example:
        yes → 0
        no  → 1

    Used during training and inference to ensure consistent label encoding.
    """

    def __init__(self) -> None:
        """
        Initialize default mappings for target labels.

        Attributes:
            yes (int): Encoded value for label 'yes'.
            no (int): Encoded value for label 'no'.
        """
        self.yes: int = 0
        self.no: int = 1

    def _asdict(self) -> dict:
        """
        Return the mapping as a Python dictionary.

        Returns:
            dict: Mapping between label names and encoded integers.
        """
        return self.__dict__

    def reverse_mapping(self) -> dict:
        """
        Reverse the label-to-integer mapping.

        Useful for converting model predictions (integers)
        back into human-readable labels.

        Returns:
            dict: Mapping between encoded integers and original label names.
        """
        mapping_response = self._asdict()
        return dict(zip(mapping_response.values(), mapping_response.keys()))

class ModelWrapper:
    """
    Wrapper class for bundling the preprocessing pipeline and trained model
    into a single deployable object.

    This ensures that:
    - Preprocessing is applied exactly as during training
    - Predictions remain consistent and reproducible
    - The saved model can be used directly for inference
    """

    def __init__(self, preprocessing_object: Pipeline, trained_model_object: object):
        """
        Initialize MyModel with preprocessing and trained model.

        Args:
            preprocessing_object (Pipeline):
                The fitted preprocessing pipeline used during training.
            
            trained_model_object (object):
                The trained ML model (e.g., RandomForestClassifier).
        """
        self.preprocessing_object = preprocessing_object
        self.trained_model_object = trained_model_object

    def predict(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Apply preprocessing and generate predictions on input data.

        Steps:
            1. Apply the saved preprocessing pipeline to input features.
            2. Pass transformed data to the trained model.
            3. Return model predictions.

        Args:
            dataframe (pd.DataFrame):
                Raw input features expected by the model.

        Returns:
            np.array:
                Array of model predictions (encoded target values).
        """
        try:
            logging.info("Starting prediction process...")

            # apply scaling transformation using pre-trained preprocessing object
            transformed_feature = self.preprocessing_object.transform(dataframe)

            # perform prediction using the trained model
            logging.info("using the trained model to get predictions...")
            predictions = self.trained_model_object.predict(transformed_feature)

            return predictions
        except Exception as e:
            raise CustomException(e, sys) from e

    def __repr__(self):
        """
        Provide an unambiguous string representation of the underlying model.

        Returns:
            str: String showing the model class name.
        """
        return f"{type(self.trained_model_object).__name__}()"

    def __str__(self):
        """
        Provide a readable string representation of the model.

        Returns:
            str: String showing the model class name.
        """
        return f"{type(self.trained_model_object).__name__}()"