from app.api.authController import getCurrentPayload
from app.domain.entities.RoleMenuOption import RoleMenuOption
from app.domain.entities.MenuOption import MenuOption
from app.infrastructure.db.connection import getDb
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session


def requireMenuPermission(pathMenuOption: str):
    def dependency(
        payload: dict = Depends(getCurrentPayload),
        db: Session = Depends(getDb),
    ) -> dict:
        roleIds = payload.get("roleIds") or []

        hasPermission = (
            db.query(RoleMenuOption)
            .join(
                MenuOption,
                MenuOption.IdMenuOption == RoleMenuOption.IdMenuOption,
            )
            .filter(
                RoleMenuOption.IdRole.in_(roleIds),
                MenuOption.pathMenuOption == pathMenuOption,
                MenuOption.statusMenuOption.is_(True),
            )
            .first()
            is not None
        )

        if not hasPermission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta operación.",
            )

        return payload

    return dependency
