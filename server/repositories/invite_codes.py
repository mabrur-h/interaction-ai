"""Invite codes repository for Wally Junior."""

import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import InviteCode
from server.repositories.base import BaseRepository


class InviteCodeRepository(BaseRepository[InviteCode]):
    """Repository for InviteCode operations.

    Note: Uses parent_id instead of user_id, so extends BaseRepository
    and handles user scoping manually.
    """

    model = InviteCode

    def __init__(self, session: AsyncSession, user_id: uuid.UUID):
        """Initialize with a database session and parent user ID.

        Args:
            session: SQLAlchemy async session
            user_id: The parent user's UUID (stored as parent_id)
        """
        super().__init__(session)
        self.user_id = user_id

    async def get_by_id(self, id: int) -> Optional[InviteCode]:
        """Get an invite code by ID, scoped to the current parent.

        Args:
            id: The invite code ID

        Returns:
            The InviteCode or None if not found or not owned by this parent
        """
        result = await self.session.execute(
            select(InviteCode).where(
                InviteCode.id == id,
                InviteCode.parent_id == self.user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_invite(
        self,
        child_name: str,
        initial_balance: int = 0,
        expires_in_hours: int = 72,
    ) -> InviteCode:
        """Create a new invite code for a child account.

        Args:
            child_name: The name to assign to the child
            initial_balance: Starting balance in cents
            expires_in_hours: Hours until the code expires

        Returns:
            The created InviteCode
        """
        # Generate a short, easy-to-type code
        code = secrets.token_urlsafe(6)[:8].upper()

        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        return await self.create(
            code=code,
            parent_id=self.user_id,
            child_name=child_name,
            initial_balance=initial_balance,
            expires_at=expires_at,
        )

    async def get_by_code(self, code: str) -> Optional[InviteCode]:
        """Get an invite code by its code string.

        Note: This does NOT filter by user_id since anyone can use a code.

        Args:
            code: The invite code string

        Returns:
            The InviteCode or None if not found
        """
        result = await self.session.execute(
            select(InviteCode).where(
                InviteCode.code == code.upper(),
                InviteCode.used == False,
                InviteCode.expires_at > datetime.utcnow(),
            )
        )
        return result.scalar_one_or_none()

    async def mark_used(
        self, code_id: int, used_by_user_id: uuid.UUID
    ) -> Optional[InviteCode]:
        """Mark an invite code as used.

        Args:
            code_id: The invite code ID
            used_by_user_id: The user ID who used the code

        Returns:
            The updated InviteCode or None if not found
        """
        return await self.update(
            code_id,
            used=True,
            used_by=used_by_user_id,
        )

    async def get_pending_invites(self) -> Sequence[InviteCode]:
        """Get all pending (unused, not expired) invite codes for this parent.

        Returns:
            List of pending InviteCodes
        """
        result = await self.session.execute(
            select(InviteCode)
            .where(
                InviteCode.parent_id == self.user_id,
                InviteCode.used == False,
                InviteCode.expires_at > datetime.utcnow(),
            )
            .order_by(InviteCode.created_at.desc())
        )
        return result.scalars().all()

    async def get_used_invites(self) -> Sequence[InviteCode]:
        """Get all used invite codes for this parent.

        Returns:
            List of used InviteCodes
        """
        result = await self.session.execute(
            select(InviteCode)
            .where(
                InviteCode.parent_id == self.user_id,
                InviteCode.used == True,
            )
            .order_by(InviteCode.created_at.desc())
        )
        return result.scalars().all()

    async def cancel_invite(self, code_id: int) -> bool:
        """Cancel (delete) an unused invite code.

        Args:
            code_id: The invite code ID

        Returns:
            True if deleted, False if not found or already used
        """
        invite = await self.get_by_id(code_id)
        if not invite or invite.used:
            return False
        return await self.delete(code_id)

    async def is_valid_code(self, code: str) -> bool:
        """Check if a code is valid (exists, unused, not expired).

        Args:
            code: The invite code string

        Returns:
            True if code is valid
        """
        invite = await self.get_by_code(code)
        return invite is not None
