from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.db import models  # noqa: F401 - ensures models are registered on Base.metadata
from app.db.database import Base, engine


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="Plataforma SaaS B2B de Business Intelligence y Auditoria Operativa para restaurantes.",
        version="1.0.0",
    )

    Base.metadata.create_all(bind=engine)

    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return application


app = create_app()
