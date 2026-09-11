from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import routes

app = FastAPI(title="SchemaLens API")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
