import ee
from dotenv import load_dotenv
import os

load_dotenv()

project = os.getenv("GEE_PROJECT_ID")

ee.Initialize(project=project)

print("GEE working!")