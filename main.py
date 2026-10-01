from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

# Controllers
from controllers.users import router as UsersRouter


app = FastAPI()

app.include_router(UsersRouter, prefix='/api')

@app.get('/health')
def health_check():
  return {'message': 'Api is running'}


