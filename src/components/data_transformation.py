import sys
import numpy as np
import pandas as pd
from imblearn.combine import SMOTEENN
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.compose import ColumnTransformer

from src.exception import CustomException
from src.logger import logging
from src.utils.main_utils import read_yaml_file, save_object, save_numpy_array
from src.constants import SCHEMA_FILE_PATH, TARGET_COLUMN
from src.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact, DataTransformationArtifact
from src.entity.config_entity import DataTransformationConfig

class DataTransformation:
    """
    Handles all preprocessing and feature engineering steps required before model training.
    
    Responsibilities:
    - Read raw train/test data.
    - Apply custom transformations (mapping, dummy variables, renaming, dropping ID columns).
    - Scale numerical features using StandardScaler / MinMaxScaler.
    - Handle imbalanced data using SMOTEENN.
    - Save transformation pipeline and transformed datasets.
    """

    def __init__(self, data_ingestion_artifact: DataIngestionArtifact, data_validation_artifact: DataValidationArtifact, data_transformation_config: DataTransformationConfig):
        """
        Initializes the DataTransformation component.

        Parameters
        ----------
        data_ingestion_artifact : DataIngestionArtifact
            Contains file paths for raw train/test CSV files.
        data_validation_artifact : DataValidationArtifact
            Ensures that the input data has passed validation checks.
        data_transformation_config : DataTransformationConfig
            Configuration for saving transformed data and objects.
        """
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_artifact = data_validation_artifact
            self.data_transformation_config = data_transformation_config
            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise CustomException(e, sys) from e

    def get_data_transformer_object(self) -> Pipeline:
        """
        Creates and returns a preprocessing pipeline for numerical scaling.

        Includes:
        - StandardScaler for some numeric features
        - MinMaxScaler for specified columns
        - ColumnTransformer to apply correct mapping

        Returns
        -------
        Pipeline
            Sklearn pipeline containing preprocessing steps.
        """
        try:
            logging.info("creating data transformation pipeline...")
            # initialise transformers
            numeric_transformer = StandardScaler()
            min_max_scaler = MinMaxScaler()
            logging.info("transformers initialized: StandardScaler-MinMaxScaler")

            # load schema configurations
            num_features = self._schema_config["num_features"]
            mm_columns = self._schema_config["mm_columns"]

            # creating preprocessor pipeline
            preprocessor = ColumnTransformer(
                transformers = [
                    ("StandardScaler", numeric_transformer, num_features),
                    ("MinMaxScaler", min_max_scaler, mm_columns)
                ],
                remainder= "passthrough" # leaves other columns as they are
            )

            # wrapping everything in a single pipeline
            pipeline = Pipeline(steps= [("Preprocessor", preprocessor)])
            logging.info("data transformation pipeline is ready.")

            return pipeline
        except Exception as e:
            logging.exception("error occured while creating the pipeline for data transformation")
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
        drop_col = self._schema_config["drop_columns"]
        if drop_col in dataframe:
            return dataframe.drop(drop_col, axis= 1)

    @staticmethod
    def read_data(file_path: str) -> pd.DataFrame:
        """
        Reads a CSV file into a pandas DataFrame.

        Parameters
        ----------
        file_path : str
            Path to the CSV file.

        Returns
        -------
        pd.DataFrame
            Loaded dataset.
        """
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise CustomException(e, sys) from e

    def initiate_data_transformation(self):
        """
        Executes the full data transformation pipeline.

        Steps:
        1. Check validation status.
        2. Load train/test CSVs.
        3. Split into input features and target.
        4. Apply custom feature engineering (mapping, dummy vars, renaming).
        5. Apply preprocessing pipeline (scalers).
        6. Handle imbalance using SMOTEENN.
        7. Concatenate final features + labels.
        8. Save:
            - Preprocessor object (pickle)
            - Transformed training array
            - Transformed test array

        Returns
        -------
        DataTransformationArtifact
            Contains file paths of saved transformed datasets.
        """
        logging.info("Starting data tranformation...")
        try:
            if not self.data_validation_artifact.validation_status:
                raise Exception(self.data_validation_artifact.message)
            
            # load train and test set
            train_df = DataTransformation.read_data(self.data_ingestion_artifact.trained_file_path)
            test_df = DataTransformation.read_data(self.data_ingestion_artifact.test_file_path)
            logging.info("loaded train and test dataframes")

            train_features_df = train_df.drop(columns= [TARGET_COLUMN], axis= 1)
            train_target_df = train_df[TARGET_COLUMN]

            test_features_df = test_df.drop(columns= [TARGET_COLUMN], axis= 1)
            test_target_df = test_df[TARGET_COLUMN]
            logging.info("splitted train-features/target, test-features/target from train and test dataframes")

            # custom transformations
            train_features_df = self._map_gender_columns(train_features_df)
            train_features_df = self._drop_id_column(train_features_df)
            train_features_df = self._create_dummy_columns(train_features_df)
            train_features_df = self._rename_columns(train_features_df)

            test_features_df = self._map_gender_columns(test_features_df)
            test_features_df = self._drop_id_column(test_features_df)
            test_features_df = self._create_dummy_columns(test_features_df)
            test_features_df = self._rename_columns(test_features_df)

            logging.info("starting transformation pipeline...")
            preprocessor = self.get_data_transformer_object()

            logging.info("initialising transformation pipeline for training data")
            train_features_arr = preprocessor.fit_transform(train_features_df)

            logging.info("initialising transformation pipeline for test data")
            test_features_arr = preprocessor.transform(test_features_df)
            logging.info("transformation pipeline completed for train and test features.")

            logging.info("applying SMOTEENN for handling imbalanced dataset...")
            smt = SMOTEENN(sampling_strategy= "minority")
            final_train_features_df, final_train_target_df = smt.fit_resample(train_features_arr, train_target_df)
            final_test_features_df, final_test_target_df = smt.fit_resample(test_features_arr, test_target_df)
            logging.info("SMOTEENN applied to train-test dataframes successfully.")

            train_arr = np.c_[final_train_features_df, np.array(final_train_target_df)] # np.c_ is for concatenation
            test_arr = np.c_[final_test_features_df, np.array(final_test_target_df)]

            logging.info("saving pipeline object and final train and test dataframes...")
            save_object(self.data_transformation_config.transformed_object_file_path, preprocessor)
            save_numpy_array(self.data_transformation_config.transformed_train_file_path, train_arr)
            save_numpy_array(self.data_transformation_config.transformed_test_file_path, test_arr)
            logging.info("pipeline object and final train test dataframes saved.")

            data_transformation_artifact = DataTransformationArtifact(
                self.data_transformation_config.transformed_object_file_path,
                self.data_transformation_config.transformed_train_file_path,
                self.data_transformation_config.transformed_test_file_path,
            )

            logging.info(f"data transformation completed, Data Transformation Artifact: {data_transformation_artifact}")
            return data_transformation_artifact
        except Exception as e:
            raise CustomException(e, sys) from e