"""GIS API routers."""

from fastapi import APIRouter

from app.api.gis import router as gis_router

api_router = APIRouter()
api_router.include_router(gis_router, prefix="/gis", tags=["GIS"])
