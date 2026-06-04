from app.api.specificTrainingProgramController import router as specificTrainingProgramRouter
from app.api.assistanceReasonController import router as assistanceReasonRouter
from app.api.applicationUserController import router as applicationUserRouter
from app.infrastructure.logging.loggerConfig import setupLogging, getLogger
from app.api.solutionCenterController import router as solutionCenterRouter
from app.api.eventCategoryController import router as eventCategoryRouter
from app.api.eventStatusController import router as eventStatusRouter
from app.api.menuOptionController import router as menuOptionRouter
from app.api.competencyController import router as competencyRouter
from app.api.attendanceController import router as attendanceRouter
from app.api.exceptionHandler import registerExceptionHandlers
from app.api.reportController import router as reportRouter
from app.api.eventController import router as eventRouter
from app.infrastructure.db.connection import Base, engine
from app.api.authController import router as authRouter
from app.api.roleController import router as roleRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.infrastructure.db.base import Base
from fastapi import FastAPI, Request
from pathlib import Path
from time import time

setupLogging()
logger = getLogger(__name__)

#app = FastAPI(title="Assistance API", version="1.0.0", root_path="/api")
app = FastAPI(title="Assistance API", version="1.0.0")

BACKEND_DIR = Path(__file__).resolve().parents[1]
UPLOADS_DIR = BACKEND_DIR / "uploads"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

registerExceptionHandlers(app)

@app.middleware("http")
async def logRequests(request: Request, call_next):
    startTime = time()
    try:
        response = await call_next(request)
        durationMs = round((time() - startTime) * 1000, 2)
        logger.info(
            "Request finalizado | method=%s | path=%s | status=%s | duration_ms=%s | client=%s",
            request.method,
            request.url.path,
            response.status_code,
            durationMs,
            request.client.host if request.client else "unknown"
        )
        return response
    except Exception:
        durationMs = round((time() - startTime) * 1000, 2)
        logger.exception(
            "Error no controlado en request | method=%s | path=%s | duration_ms=%s | client=%s",
            request.method,
            request.url.path,
            durationMs,
            request.client.host if request.client else "unknown"
        )
        raise

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://qa-assistanceapp.calcoweb.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(specificTrainingProgramRouter)
app.include_router(assistanceReasonRouter)
app.include_router(applicationUserRouter)
app.include_router(solutionCenterRouter)
app.include_router(eventCategoryRouter)
app.include_router(eventStatusRouter)
app.include_router(competencyRouter)
app.include_router(attendanceRouter)
app.include_router(menuOptionRouter)
app.include_router(reportRouter)
app.include_router(eventRouter)
app.include_router(authRouter)
app.include_router(roleRouter)

@app.get("/")
def root():
    logger.info("Health check ejecutado")
    return { "message": "API assistance funcionando correctamente" }