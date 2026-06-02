from app.infrastructure.logging.loggerConfig import getLogger
from fastapi import FastAPI, Request, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.domain.dtos.ApiResponseDto import apiResponseDto
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = getLogger(__name__)

def buildErrorResult(request: Request, statusCode: int, errorType: str, detail) -> dict:
    return {
        "statusCode": statusCode,
        "errorType": errorType,
        "path": request.url.path,
        "method": request.method,
        "detail": detail
    }

def registerExceptionHandlers(app: FastAPI) -> None:

    @app.exception_handler(HTTPException)
    async def httpExceptionHandler(request: Request, exc: HTTPException):
        logger.warning(
            "HTTPException | path=%s | method=%s | status=%s | detail=%s",
            request.url.path,
            request.method,
            exc.status_code,
            exc.detail
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=apiResponseDto[dict](
                isSuccess=False,
                Message=str(exc.detail),
                result=buildErrorResult(
                    request=request,
                    statusCode=exc.status_code,
                    errorType="HTTPException",
                    detail=exc.detail
                )
            ).model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def validationExceptionHandler(request: Request, exc: RequestValidationError):
        logger.warning(
            "RequestValidationError | path=%s | method=%s | errors=%s",
            request.url.path,
            request.method,
            exc.errors()
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=apiResponseDto[dict](
                isSuccess=False,
                Message="Error de validación en los datos enviados.",
                result=buildErrorResult(
                    request=request,
                    statusCode=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    errorType="RequestValidationError",
                    detail=exc.errors()
                )
            ).model_dump()
        )

    @app.exception_handler(IntegrityError)
    async def integrityExceptionHandler(request: Request, exc: IntegrityError):
        logger.exception(
            "IntegrityError | path=%s | method=%s | error=%s",
            request.url.path,
            request.method,
            str(exc)
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=apiResponseDto[dict](
                isSuccess=False,
                Message="No se pudo procesar la solicitud porque existe una restricción de datos.",
                result=buildErrorResult(
                    request=request,
                    statusCode=status.HTTP_400_BAD_REQUEST,
                    errorType="IntegrityError",
                    detail=str(exc)
                )
            ).model_dump()
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemyExceptionHandler(request: Request, exc: SQLAlchemyError):
        logger.exception(
            "SQLAlchemyError | path=%s | method=%s | error=%s",
            request.url.path,
            request.method,
            str(exc)
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=apiResponseDto[dict](
                isSuccess=False,
                Message="Error interno de base de datos.",
                result=buildErrorResult(
                    request=request,
                    statusCode=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    errorType="SQLAlchemyError",
                    detail=str(exc)
                )
            ).model_dump()
        )

    @app.exception_handler(Exception)
    async def generalExceptionHandler(request: Request, exc: Exception):
        logger.exception(
            "UnhandledException | path=%s | method=%s | error=%s",
            request.url.path,
            request.method,
            str(exc)
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=apiResponseDto[dict](
                isSuccess=False,
                Message="Error interno del servidor.",
                result=buildErrorResult(
                    request=request,
                    statusCode=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    errorType=type(exc).__name__,
                    detail=str(exc)
                )
            ).model_dump()
        )