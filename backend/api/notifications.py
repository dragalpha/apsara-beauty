from fastapi import APIRouter

router = APIRouter()


@router.get("/notifications/ping")
def ping():
    return {"message": "Daily tip: Always apply sunscreen (SPF 30+) every morning."}


