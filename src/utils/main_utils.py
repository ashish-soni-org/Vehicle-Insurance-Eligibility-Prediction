import os
import sys
import dill
import yaml
import numpy as np

from src.exception import CustomException

def read_yaml_file(file_path: str) -> dict:
    """
    Read and parse a YAML file.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to the YAML file.

    Returns
    -------
    dict
        Parsed YAML content as a dictionary.
    """
    try:
        with open(file_path, 'rb') as f:
            return yaml.safe_load(f)
        
    except Exception as e:
        raise CustomException(e, sys) from e
    
def save_object(file_path: str, object: object) -> None:
    """
    Serialize a Python object using dill and save it to a file.

    Parameters
    ----------
    file_path : str
        Destination file path where the object will be stored.
    object : object
        Any Python object that supports dill serialization.

    Returns
    -------
    None
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok= True)
        with open(file_path, 'wb') as f:
            dill.dump(object, f)
    except Exception as e:
        raise CustomException(e, sys) from e
    
def load_object(file_path: str) -> object:
    """
    Load and deserialize a Python object stored using dill.

    Parameters
    ----------
    file_path : str
        Path to the serialized object file.

    Returns
    -------
    object
        Deserialized Python object.
    """
    try:
        with open(file_path, 'rb') as f:
            return dill.load(f)
    except Exception as e:
        raise CustomException(e, sys) from e
    
def save_numpy_array(file_path: str, array: np.array) -> None:
    """
    Save a NumPy array to disk in `.npy` format.

    Parameters
    ----------
    file_path : str
        Location where the array should be saved.
    array : np.array
        NumPy array to be saved.

    Returns
    -------
    None
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok= True)
        with open(file_path, 'wb') as f:
            np.save(f, array)
    except Exception as e:
        raise CustomException(e, sys) from e
    
def load_numpy_array(file_path: str) -> np.array:
    """
    Load a NumPy array saved in `.npy` format.

    Parameters
    ----------
    file_path : str
        Path to the `.npy` file.

    Returns
    -------
    np.array
        Loaded NumPy array.
    """
    try:
        with open(file_path, 'rb') as f:
            return np.load(f)
    except Exception as e:
        raise CustomException(e, sys) from e