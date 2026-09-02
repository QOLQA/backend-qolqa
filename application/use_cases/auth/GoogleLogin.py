"""
Google Login use case.

Orchestrates: verify → resolve → create/link → return entity.
Lives in application/ — imports infrastructure via constructor injection.
"""
import re
import logging

from domain.entities.auth.UserEntity import UserEntity
from domain.errors import (
    Duplicate,
    GoogleLoginNotConfigured,
    InvalidGoogleToken,
)
from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
from infrastructure.services.google_auth import verify_google_token

logger = logging.getLogger(__name__)


def _sanitize_username(prefix: str) -> str:
    """Sanitize email prefix to valid username characters."""
    base = re.sub(r'[^a-zA-Z0-9_]', '', prefix.lower())
    return base if base else "user"


async def google_login(
    repository: UserRepositoryImpl,
    credential: str,
    client_id: str | None,
) -> UserEntity:
    """
    Authenticate or create a user via Google OAuth.

    Args:
        repository: UserRepositoryImpl for DB operations
        credential: Google ID token
        client_id: Google OAuth client ID (from settings)

    Returns:
        UserEntity (existing or newly created)

    Raises:
        GoogleLoginNotConfigured: If client_id is None
        InvalidGoogleToken: If token verification fails
        Duplicate: If username generation exhausted (should never happen in practice)
    """
    if client_id is None:
        raise GoogleLoginNotConfigured()

    # Step 1: Verify Google token
    info = await verify_google_token(credential, client_id)
    sub = info['sub']
    email = info['email']
    email_verified = info.get('email_verified', False)
    name = info.get('name')
    picture = info.get('picture')

    # Step 2: Resolve by google_id
    existing = await repository.get_by_google_id(sub)
    if existing:
        return existing

    # Step 3: Link by verified email (hybrid account)
    if email_verified:
        existing_by_email = await repository.get_by_email(email)
        if existing_by_email:
            try:
                return await repository.link_google_account(existing_by_email.id, sub)
            except Duplicate:
                # Race condition: someone linked between our checks
                race_linked = await repository.get_by_google_id(sub)
                if race_linked:
                    return race_linked
                raise

    # Step 4: Create new user with generated username
    prefix = email.split('@')[0] if email else "user"
    base = _sanitize_username(prefix)

    # Try base, then base+1, base+2, ... up to base+100
    for attempt in range(0, 101):
        username = base if attempt == 0 else f"{base}{attempt}"

        try:
            return await repository.add_google_user(
                username=username,
                email=email,
                full_name=name,
                google_id=sub,
                profile_picture_url=picture,
            )
        except Duplicate as exc:
            # Race condition: someone else created with this username
            race_existing = await repository.get_by_google_id(sub)
            if race_existing:
                return race_existing

            # Try to link by email if not yet linked
            if email_verified:
                existing_by_email = await repository.get_by_email(email)
                if existing_by_email:
                    try:
                        return await repository.link_google_account(existing_by_email.id, sub)
                    except Duplicate:
                        # Already linked by someone else
                        race_linked = await repository.get_by_google_id(sub)
                        if race_linked:
                            return race_linked
                        raise

            # If we've exhausted all attempts, re-raise
            if attempt == 100:
                raise

            logger.debug(f"Username {username} collision, trying next suffix")
            continue

    # Should never reach here, but just in case
    raise Duplicate(msg="Username generation exhausted")
