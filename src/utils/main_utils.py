import os
import sys
import dill
import yaml
import numpy as np

from src.exception import CustomException

def read_yaml_file(file_path: str) -> dict:
    """
    """
    try:
        with open(file_path, 'rb') as f:
            return yaml.safe_load(f)
        
    except Exception as e:
        raise CustomException(e, sys) from e
    
def save_object(file_path: str, object: object) -> None:
    """
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok= True)
        with open(file_path, 'wb') as f:
            dill.dump(object, f)
    except Exception as e:
        raise CustomException(e, sys) from e
    
def load_object(file_path: str) -> object:
    """
    """
    try:
        with open(file_path, 'rb') as f:
            return dill.load(f)
    except Exception as e:
        raise CustomException(e, sys) from e
    
def save_numpy_array(file_path: str, array: np.array) -> None:
    """
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok= True)
        with open(file_path, 'wb') as f:
            np.save(f, array)
    except Exception as e:
        raise CustomException(e, sys) from e
    
def load_numpy_array(file_path: str) -> np.array:
    """
    """
    try:
        with open(file_path, 'rb') as f:
            return np.load(f)
    except Exception as e:
        raise CustomException(e, sys) from e