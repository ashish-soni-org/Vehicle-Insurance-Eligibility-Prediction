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

# Mount static files and configure Jinja2 template engine
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory='templates')

# Allow all origins for CORS
origins = ["*"]

# Configure middleware to handle CORS
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
    """

    def __init__(self, request: Request):
        """
        Initialize the DataForm with an incoming FastAPI Request.
        
        Parameters
        ----------
        request : Request
            The HTTP request that contains the submitted form data.
        """
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
        """
        Parse vehicle insurance details submitted via HTML form.

        Extracts values from the FastAPI request body and assigns them 
        to the corresponding instance attributes.
        """
        form = await self.request.form()
        self.Gender = form.get("Gender")
        self.Age = form.get("Age")
        self.Driving_License = form.get("Driving_License")
        self.Region_Code = form.get("Region_Code")
        self.Previously_Insured = form.get("Previously_Insured")
        self.Annual_Premium = form.get("Annual_Premium")
        self.Policy_Sales_Channel = form.get("Policy_Sales_Channel")
        self.Vintage = form.get("Vintage")
        self.Vehicle_Age_lt_1_Year = form.get("Vehicle_Age_lt_1_Year")
        self.Vehicle_Age_gt_2_Years = form.get("Vehicle_Age_gt_2_Years")
        self.Vehicle_Damage_Yes = form.get("Vehicle_Damage_Yes")


@app.get("/", tags=["prediction"])
async def index(request: Request):
    """
    Render the main HTML form page.

    Parameters
    ----------
    request : Request
        FastAPI request object used for template rendering.

    Returns
    -------
    TemplateResponse
        Renders index.html with a default context message.
    """
    return templates.TemplateResponse("index.html", {"request": request, "context": "Ready for Prediction"})

    
@app.post("/")
async def predictRouteClient(request: Request):
    """
    Handle form submission and generate prediction using trained model.

    Workflow:
    1. Extract form data using DataForm.
    2. Convert values to DataFrame via VehicleData.
    3. Run prediction using VehicleDataClassifier.
    4. Interpret and render result back into the template.

    Parameters
    ----------
    request : Request
        FastAPI request containing user form data.

    Returns
    -------
    TemplateResponse or dict
        Renders page with prediction, or returns an error dict.
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
    

# Entry point for the application
if __name__ == "__main__":
    app_run(app, host=APP_HOST, port=APP_PORT)