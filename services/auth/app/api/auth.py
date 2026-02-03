"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    TOTPSetupResponse,
    TOTPStatusResponse,
    TOTPVerifyRequest,
    TwoFactorRequiredResponse,
)
from app.services.audit_service import AuditAction, AuditService, ResourceType
from app.services.auth_service import AuthService
from app.services.login_tracker import LoginTracker
from app.services.password_service import PasswordService
from app.services.totp_service import TOTPService

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request_data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Register a new user account."""
    import logging
    logger = logging.getLogger(__name__)

    service = AuthService(db)
    audit = AuditService(db)

    try:
        result = await service.register(request_data)

        try:
            await audit.log(
                action=AuditAction.REGISTER,
                resource_type=ResourceType.USER,
                resource_id=result.user_id,
                details={"email": request_data.email},
                ip_address=get_client_ip(request),
                user_agent=request.headers.get("User-Agent"),
            )
        except Exception as audit_error:
            # Log audit error but don't fail registration
            logger.warning(f"Audit logging failed: {audit_error}")

        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {type(e).__name__}"
        )


@router.post("/login", response_model=LoginResponse | TwoFactorRequiredResponse)
async def login(
    request_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse | TwoFactorRequiredResponse:
    """Authenticate user and return tokens."""
    service = AuthService(db)
    tracker = LoginTracker(db)
    audit = AuditService(db)

    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    # Check for lockout
    if await tracker.is_locked_out(request_data.email, ip_address):
        await tracker.record_attempt(
            email=request_data.email,
            ip_address=ip_address,
            success=False,
            user_agent=user_agent,
            failure_reason="account_locked",
        )
        await db.commit()  # Commit lockout attempt before raising exception
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )

    result = await service.login(
        request_data.email, request_data.password, request_data.totp_code
    )

    if result is None:
        await tracker.record_attempt(
            email=request_data.email,
            ip_address=ip_address,
            success=False,
            user_agent=user_agent,
            failure_reason="invalid_credentials",
        )
        await audit.log(
            action=AuditAction.LOGIN_FAILED,
            resource_type=ResourceType.USER,
            details={"email": request_data.email, "reason": "invalid_credentials"},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await db.commit()  # Commit failed attempt before raising exception
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if isinstance(result, dict) and result.get("requires_2fa"):
        return TwoFactorRequiredResponse()

    # Successful login
    await tracker.record_attempt(
        email=request_data.email,
        ip_address=ip_address,
        success=True,
        user_agent=user_agent,
    )
    await audit.log(
        action=AuditAction.LOGIN_SUCCESS,
        resource_type=ResourceType.USER,
        resource_id=result.user_id,
        user_id=result.user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request_data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh access token using refresh token."""
    service = AuthService(db)
    result = await service.refresh_tokens(request_data.refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return result


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request_data: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Logout and revoke refresh token."""
    service = AuthService(db)
    audit = AuditService(db)

    await service.logout(request_data.refresh_token)
    await audit.log(
        action=AuditAction.LOGOUT,
        resource_type=ResourceType.SESSION,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


# Two-Factor Authentication endpoints
@router.post("/2fa/setup", response_model=TOTPSetupResponse)
async def setup_2fa(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TOTPSetupResponse:
    """Set up two-factor authentication."""
    service = TOTPService(db)
    try:
        result = await service.setup_totp(current_user.id)
        return TOTPSetupResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/2fa/enable", response_model=TOTPStatusResponse)
async def enable_2fa(
    request_data: TOTPVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TOTPStatusResponse:
    """Enable 2FA by verifying the TOTP code."""
    service = TOTPService(db)
    audit = AuditService(db)

    if await service.verify_and_enable_totp(current_user.id, request_data.code):
        await audit.log(
            action=AuditAction.TOTP_ENABLED,
            resource_type=ResourceType.USER,
            resource_id=str(current_user.id),
            user_id=current_user.id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return TOTPStatusResponse(enabled=True)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid TOTP code",
    )


@router.post("/2fa/disable", response_model=TOTPStatusResponse)
async def disable_2fa(
    request_data: TOTPVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TOTPStatusResponse:
    """Disable 2FA by verifying current TOTP code."""
    service = TOTPService(db)
    audit = AuditService(db)

    try:
        if await service.disable_totp(current_user.id, request_data.code):
            await audit.log(
                action=AuditAction.TOTP_DISABLED,
                resource_type=ResourceType.USER,
                resource_id=str(current_user.id),
                user_id=current_user.id,
                ip_address=get_client_ip(request),
                user_agent=request.headers.get("User-Agent"),
            )
            return TOTPStatusResponse(enabled=False)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid TOTP code",
    )


@router.get("/2fa/status", response_model=TOTPStatusResponse)
async def get_2fa_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TOTPStatusResponse:
    """Get current 2FA status."""
    service = TOTPService(db)
    enabled = await service.is_totp_enabled(current_user.id)
    return TOTPStatusResponse(enabled=enabled)


# Password reset endpoints
@router.post("/password/reset-request", response_model=MessageResponse)
async def request_password_reset(
    request_data: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Request a password reset email."""
    service = PasswordService(db)
    audit = AuditService(db)

    token = await service.create_reset_token(request_data.email)

    # Always return success to prevent email enumeration
    if token:
        await audit.log(
            action=AuditAction.PASSWORD_RESET_REQUEST,
            resource_type=ResourceType.USER,
            details={"email": request_data.email},
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        # In production, send email with token
        # For now, we'll just log it (token would be sent via email)

    return MessageResponse(
        message="If an account exists with this email, a password reset link will be sent."
    )


@router.post("/password/reset-confirm", response_model=MessageResponse)
async def confirm_password_reset(
    request_data: PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Reset password using token."""
    service = PasswordService(db)
    audit = AuditService(db)

    # Validate token first to get user for audit
    user = await service.validate_reset_token(request_data.token)

    if await service.reset_password(request_data.token, request_data.new_password):
        await audit.log(
            action=AuditAction.PASSWORD_RESET_COMPLETE,
            resource_type=ResourceType.USER,
            resource_id=str(user.id) if user else None,
            user_id=user.id if user else None,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return MessageResponse(message="Password has been reset successfully.")

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired reset token",
    )


@router.post("/password/change", response_model=MessageResponse)
async def change_password(
    request_data: PasswordChangeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Change password for authenticated user."""
    service = PasswordService(db)
    audit = AuditService(db)

    if await service.change_password(
        current_user.id, request_data.current_password, request_data.new_password
    ):
        await audit.log(
            action=AuditAction.PASSWORD_CHANGE,
            resource_type=ResourceType.USER,
            resource_id=str(current_user.id),
            user_id=current_user.id,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        return MessageResponse(message="Password changed successfully.")

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Current password is incorrect",
    )
