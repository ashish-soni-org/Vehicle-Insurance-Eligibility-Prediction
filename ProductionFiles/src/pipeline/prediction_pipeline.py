import sys
import numpy as np
from pandas import DataFrame
from typing import Dict, Union

from src.exception import CustomException
from src.entity.config_entity import VehiclePredictorConfig
from src.entity.s3_estimator import CloudModelWrapper
from src.logger import logging

class VehicleData:
    """
    Container for a single vehicle insurance datapoint.

    This class holds all raw input features required by the model
    and provides utilities to convert them into a dictionary or
    pandas DataFrame format, which is required by the prediction pipeline.
    """
    
    def __init__(self, Gender: str, Age: int, Driving_License: int, Region_Code: int, Previously_Insured: int, Annual_Premium: float, Policy_Sales_Channel: int, Vintage: int, Vehicle_Age_lt_1_Year: int, Vehicle_Age_gt_2_Years: int, Vehicle_Damage_Yes: int):
        """
        Initialize the VehicleData object with all feature values.

        Parameters
        ----------
        Gender : str or int
            Gender of the customer (e.g., 'Male', 'Female' or encoded).
        Age : int
            Age of the customer.
        Driving_License : int
            Whether customer holds a driving license (1/0).
        Region_Code : int or float
            Encoded region of the customer.
        Previously_Insured : int
            Whether customer already holds insurance (1/0).
        Annual_Premium : float
            Premium amount paid by the customer.
        Policy_Sales_Channel : int
            Channel ID through which the policy was sold.
        Vintage : int
            Number of days customer has been associated with the company.
        Vehicle_Age_lt_1_Year : int
            Whether vehicle age is less than 1 year (1/0).
        Vehicle_Age_gt_2_Years : int
            Whether vehicle age is greater than 2 years (1/0).
        Vehicle_Damage_Yes : int
            Whether the customer previously had vehicle damage (1/0).
        """
        try:
            self.Gender = Gender
            self.Age = Age
            self.Driving_License = Driving_License
            self.Region_Code = Region_Code
            self.Previously_Insured = Previously_Insured
            self.Annual_Premium = Annual_Premium
            self.Policy_Sales_Channel = Policy_Sales_Channel
            self.Vintage = Vintage
            self.Vehicle_Age_lt_1_Year = Vehicle_Age_lt_1_Year
            self.Vehicle_Age_gt_2_Years = Vehicle_Age_gt_2_Years
            self.Vehicle_Damage_Yes = Vehicle_Damage_Yes

        except Exception as e:
            raise CustomException(e, sys) from e

    def get_vehicle_data_as_dict(self) -> Dict[str, Union[str, int, float]]:
        """
        Convert the stored vehicle feature inputs into a dictionary.

        Returns
        -------
        dict
            Dictionary mapping each feature name to a list
            containing its corresponding value.
        """
        try:
            input_data = {
                "Gender": [self.Gender],
                "Age": [self.Age],
                "Driving_License": [self.Driving_License],
                "Region_Code": [self.Region_Code],
                "Previously_Insured": [self.Previously_Insured],
                "Annual_Premium": [self.Annual_Premium],
                "Policy_Sales_Channel": [self.Policy_Sales_Channel],
                "Vintage": [self.Vintage],
                "Vehicle_Age_lt_1_Year": [self.Vehicle_Age_lt_1_Year],
                "Vehicle_Age_gt_2_Years": [self.Vehicle_Age_gt_2_Years],
                "Vehicle_Damage_Yes": [self.Vehicle_Damage_Yes]
            }

            return input_data

        except Exception as e:
            raise CustomException(e, sys) from e

    def get_vehicle_input_dataframe(self) -> DataFrame:
        """
        Convert the stored vehicle feature inputs into a pandas DataFrame.

        Returns
        -------
        pandas.DataFrame
            DataFrame containing a single row representing the input features.
        """
        try:
            vehicle_input_dict = self.get_vehicle_data_as_dict()
            return DataFrame(vehicle_input_dict)

        except Exception as e:
            raise CustomException(e, sys) from e


class VehicleDataClassifier:
    """
    Predicts insurance response using the trained model stored in S3.

    This class loads the prediction model using S3 configuration metadata
    and exposes a simple `.predict()` method to classify input features.
    """
    
    def __init__(self, prediction_pipeline_config: VehiclePredictorConfig = VehiclePredictorConfig()):
        """
        Initialize the classifier with model configuration.

        Parameters
        ----------
        prediction_pipeline_config : VehiclePredictorConfig
            Configuration containing S3 bucket name and model path.
        """
        try:
            self.prediction_pipeline_config = prediction_pipeline_config

        except Exception as e:
            raise CustomException(e, sys) from e

    def predict(self, dataframe: DataFrame) -> np.ndarray:
        """
        Run prediction on the given DataFrame using the model loaded from S3.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            A dataframe containing one or more rows of model input features.

        Returns
        -------
        str or numpy.ndarray
            Predicted class or array of predictions from the model.
        """
        try:
            logging.info("Predicting the results for the provided inputs...")
            model = CloudModelWrapper(
                bucket_name=self.prediction_pipeline_config.model_bucket_name,
                model_path=self.prediction_pipeline_config.model_file_path,
            )
            result =  model.predict(dataframe)

            logging.info(f"prediction completed. Prediction: {result}")
            return result

        except Exception as e:
            raise CustomException(e, sys) from e