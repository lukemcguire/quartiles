"""Utility routes for testing."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_superuser
from app.utils import generate_test_email, send_email

router = APIRouter()


class TestEmailRequest(BaseModel):
    """Test email request body."""

    email_to: str


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(body: TestEmailRequest) -> dict[str, str]:
    """Test emails (superuser only)."""
    email_data = generate_test_email(email_to=body.email_to)
    send_email(
        email_to=body.email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return {"message": "Test email sent"}


@router.get("/health-check/")
def health_check() -> dict[str, bool]:
    """Health check endpoint."""
    return {"healthy": True}
