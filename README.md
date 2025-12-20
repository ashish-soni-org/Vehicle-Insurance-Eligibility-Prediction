
# Vehicle Insurance Eligibility Prediction

## Executive Summary

This repository houses a comprehensive, end-to-end machine learning ecosystem designed to predict customer eligibility for vehicle insurance. Utilizing advanced statistical modeling and high-performance data engineering, this project transforms raw customer demographics and historical data into actionable predictive insights. The architecture is built with a focus on scalability, reproducibility, and professional-grade MLOps standards, bridging the gap between exploratory data science and production-ready software engineering.

---

## Business Logic and Objectives

In the insurance industry, identifying the correct target audience is critical for optimizing marketing spend and managing risk. This project addresses the "Propensity to Buy" problem. By analyzing historical patterns, the model identifies features that correlate with a high probability of conversion.

**Core Objectives:**

* **Precision Targeting:** Minimize false positives to ensure marketing resources are not wasted on ineligible leads.
* **Feature Sensitivity:** Identify which variables—such as vehicle age, past damage, or policy premium—are the strongest predictors of eligibility.
* **Operational Efficiency:** Provide a modular codebase that can be integrated into automated CI/CD pipelines for continuous retraining and deployment.

---

## Technical Architecture

### 1. Data Engineering and Preprocessing

The pipeline employs a rigorous data cleaning process to ensure the integrity of the model input.

* **Categorical Encoding:** Implementation of sophisticated encoding techniques (One-Hot and Label Encoding) to convert qualitative data into mathematical vectors without introducing artificial ordinality.
* **Feature Scaling:** Utilization of StandardScaler and MinMaxScaler to normalize numerical distributions, ensuring that high-magnitude features like "Annual Premium" do not disproportionately bias the model weights.
* **Handling Imbalance:** Strategic management of class distribution to prevent the model from developing a bias toward the majority class.

### 2. Model Selection and Training

The project explores a hierarchy of algorithms, moving from baseline statistical models to ensemble methods.

* **Ensemble Learning:** The primary engine utilizes Gradient Boosting and Random Forest architectures to capture non-linear relationships within the data.
* **Hyperparameter Optimization:** Extensive use of cross-validation to tune parameters such as tree depth, learning rates, and estimator counts, ensuring the model generalizes well to unseen data.

### 3. Evaluation Metrics

Success is not measured by accuracy alone. The project evaluates performance through:

* **ROC-AUC Score:** To measure the model’s ability to distinguish between classes.
* **Precision-Recall Curves:** Critical for insurance business cases where the cost of missing a potential customer differs from the cost of misidentifying one.
* **Confusion Matrix Analysis:** Providing a granular view of Type I and Type II errors.

---

## Repository Structure

The directory is organized following professional software development standards to ensure ease of navigation and maintenance:

* `data/`: Contains raw and processed datasets (restricted or versioned).
* `notebooks/`: Exploratory Data Analysis (EDA) and initial prototyping.
* `src/`: Production-grade source code for the end-to-end pipeline.
  * `preprocessing.py`: Logic for data transformation and cleaning.
  * `model_trainer.py`: Script for training, validating, and saving models.
  * `predictor.py`: The inference engine for real-time or batch predictions.
* `models/`: Serialized model files (e.g., .pkl or .h5) ready for deployment.
* `requirements.txt`: A comprehensive list of dependencies to ensure environment parity.

---

## Installation and Deployment

### Prerequisites

* Python 3.8 or higher
* Virtual Environment (venv or Conda)

### Setup

1. Clone the repository:
   ```bash
   git clone [https://github.com/ashish-soni-org/Vehicle-Insurance-Eligibility-Prediction.git](https://github.com/ashish-soni-org/Vehicle-Insurance-Eligibility-Prediction.git)
   ```
