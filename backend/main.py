from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.document_routes import router as document_router


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(document_router)
