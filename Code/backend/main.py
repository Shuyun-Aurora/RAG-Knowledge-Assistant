from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from config.settings import settings
import controller.CourseController as CourseController
import controller.ExerciseController as ExerciseController
import controller.LoginController as LoginController
import controller.PostController as PostController
import controller.UserController as UserController
import controller.rag_controller as rag_controller
from controller.rag_controller import router as rag_router
from dao.document_dao import DocumentDAO
from repository.document_repository import DocumentRepository
from util.exception import http_exception_handler, validation_exception_handler


app = FastAPI()

default_origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:3000",
]
origins = [
    origin.strip()
    for origin in settings.CORS_ALLOWED_ORIGINS.split(",")
    if origin.strip()
] or default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(LoginController.router, prefix="/api")
app.include_router(UserController.router, prefix="/api/user")
app.include_router(CourseController.router, prefix="/api/course")
app.include_router(PostController.router, prefix="/api/course")
app.include_router(ExerciseController.router)
app.include_router(rag_router)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

document_repository = DocumentRepository()
rag_controller.document_dao = DocumentDAO(document_repository=document_repository)


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


@app.on_event("shutdown")
async def shutdown_event():
    document_repository.close()
