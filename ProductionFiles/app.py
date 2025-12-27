from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn import run as app_run

from src.exception import CustomException
import sys

from src.constants import APP_HOST, APP_PORT
from src.pipeline.prediction_pipeline import VehicleData, VehicleDataClassifier

# Initialize FastAPI
app = FastAPI()

# -----------------------------------------------------------------------------
# STATIC FILES CONFIGURATION
# -----------------------------------------------------------------------------
# 1. Standard Mount: Handles requests where Nginx strips the prefix
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Fallback Mount: Handles requests where Nginx sends the full path
# This ensures static assets load regardless of how the reverse proxy forwards the path
app.mount("/Vehicle-Insurance-Eligibility-Prediction/static", StaticFiles(directory="static"), name="static_long")
# -----------------------------------------------------------------------------

templates = Jinja2Templates(directory='templates')

# Allow all origins for CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DataForm:
    """
    Wrapper class to extract and store user-submitted vehicle form data 
    from a FastAPI Request object.
    
    CRITICAL UPDATE:
    Performs type conversion from HTML Form Strings to Python Native Types (int/float)
    to ensure the ML Model receives valid input.
    """

    def __init__(self, request: Request):
        self.request: Request = request
        self.Gender: int = None
        self.Age: int = None
        self.Driving_License: int = None
        self.Region_Code: float = None
        self.Previously_Insured: int = None
        self.Annual_Premium: float = None
        self.Policy_Sales_Channel: float = None
        self.Vintage: int = None
        self.Vehicle_Age_lt_1_Year: int = None
        self.Vehicle_Age_gt_2_Years: int = None
        self.Vehicle_Damage_Yes: int = None

    async def get_vehicle_data(self) -> None:
        form = await self.request.form()
        
        # We must cast the string inputs from the HTML form to the correct numeric types
        self.Gender = int(form.get("Gender"))
        self.Age = int(form.get("Age"))
        self.Driving_License = int(form.get("Driving_License"))
        self.Region_Code = float(form.get("Region_Code"))
        self.Previously_Insured = int(form.get("Previously_Insured"))
        self.Annual_Premium = float(form.get("Annual_Premium"))
        self.Policy_Sales_Channel = float(form.get("Policy_Sales_Channel"))
        self.Vintage = int(form.get("Vintage"))
        self.Vehicle_Age_lt_1_Year = int(form.get("Vehicle_Age_lt_1_Year"))
        self.Vehicle_Age_gt_2_Years = int(form.get("Vehicle_Age_gt_2_Years"))
        self.Vehicle_Damage_Yes = int(form.get("Vehicle_Damage_Yes"))


# -----------------------------------------------------------------------------
# ROUTE CONFIGURATION
# -----------------------------------------------------------------------------

@app.get("/Vehicle-Insurance-Eligibility-Prediction/", tags=["prediction"])
@app.get("/", tags=["root_fallback"])
async def index(request: Request):
    """
    Render the main HTML form page.
    """
    return templates.TemplateResponse("index.html", {"request": request, "context": "Ready for Prediction"})

    
@app.post("/Vehicle-Insurance-Eligibility-Prediction/")
@app.post("/")
async def predictRouteClient(request: Request):
    """
    Handle form submission and generate prediction.
    """
    try:
        form = DataForm(request)
        await form.get_vehicle_data()
        
        vehicle_data = VehicleData(
            Gender=form.Gender,
            Age=form.Age,
            Driving_License=form.Driving_License,
            Region_Code=form.Region_Code,
            Previously_Insured=form.Previously_Insured,
            Annual_Premium=form.Annual_Premium,
            Policy_Sales_Channel=form.Policy_Sales_Channel,
            Vintage=form.Vintage,
            Vehicle_Age_lt_1_Year=form.Vehicle_Age_lt_1_Year,
            Vehicle_Age_gt_2_Years=form.Vehicle_Age_gt_2_Years,
            Vehicle_Damage_Yes=form.Vehicle_Damage_Yes
        )
        vehicle_df = vehicle_data.get_vehicle_input_dataframe()

        model_predictor = VehicleDataClassifier()
        value = model_predictor.predict(dataframe=vehicle_df)[0]

        status = "Eligible" if value == 1 else "Not Eligible"

        return templates.TemplateResponse(
            "index.html",
            {"request": request, "context": status},
        )
    
    except Exception as e:
        return {"status": False, "error": f"{CustomException(e, sys)}"}
    

if __name__ == "__main__":
    app_run(app, host=APP_HOST, port=APP_PORT)