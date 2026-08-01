from fastapi import APIRouter

from app.api import categories, dashboard, export, statements, transactions

api_router = APIRouter()
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(statements.router, prefix="/statements", tags=["statements"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
