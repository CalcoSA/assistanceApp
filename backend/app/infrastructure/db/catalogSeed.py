from app.domain.entities.AssistanceReason import AssistanceReason
from app.domain.constants.ParameterNames import EVENT_NOTIFICATION_RECIPIENTS_PARAMETER
from app.domain.entities.RoleMenuOption import RoleMenuOption
from app.domain.entities.MenuOption import MenuOption
from app.domain.entities.Parameter import Parameter
from app.domain.entities.Role import Role
from app.infrastructure.db.connection import SessionLocal
from sqlalchemy import func
import unicodedata


REQUIRED_ASSISTANCE_REASONS = ("REINDUCCIÓN", "TRANSVERSALES")
PARAMETERS_MENU_PATH = "/maestros/parametros"
PARAMETERS_MENU_NAME = "Parámetros"
COMPETENCIES_MENU_PATH = "/maestros/competencias"
COMPETENCIES_MENU_NAME = "Competencias"
ADMIN_ROLE_NAMES = {"administrador", "superadministrador", "superadmin"}


def _normalizeCatalogName(value: str) -> str:
    normalizedValue = unicodedata.normalize("NFD", value.strip())
    return "".join(
        character
        for character in normalizedValue
        if unicodedata.category(character) != "Mn"
    ).casefold()


def seedRequiredCatalogs() -> None:
    db = SessionLocal()

    try:
        assistanceReasons = db.query(AssistanceReason).all()
        reasonsByNormalizedName = {
            _normalizeCatalogName(reason.nameAssistanceReason): reason
            for reason in assistanceReasons
        }
        hasChanges = False

        for requiredReasonName in REQUIRED_ASSISTANCE_REASONS:
            normalizedName = _normalizeCatalogName(requiredReasonName)
            existingReason = reasonsByNormalizedName.get(normalizedName)

            if existingReason:
                if existingReason.nameAssistanceReason != requiredReasonName:
                    existingReason.nameAssistanceReason = requiredReasonName
                    hasChanges = True
                continue

            db.add(AssistanceReason(nameAssistanceReason=requiredReasonName))
            hasChanges = True

        eventRecipientsParameter = (
            db.query(Parameter)
            .filter(
                func.lower(Parameter.nameParameter)
                == EVENT_NOTIFICATION_RECIPIENTS_PARAMETER.lower()
            )
            .first()
        )

        if not eventRecipientsParameter:
            db.add(
                Parameter(
                    nameParameter=EVENT_NOTIFICATION_RECIPIENTS_PARAMETER,
                    valueParameter="",
                )
            )
            hasChanges = True
        elif (
            eventRecipientsParameter.nameParameter
            != EVENT_NOTIFICATION_RECIPIENTS_PARAMETER
        ):
            eventRecipientsParameter.nameParameter = (
                EVENT_NOTIFICATION_RECIPIENTS_PARAMETER
            )
            hasChanges = True

        parametersMenuOption = (
            db.query(MenuOption)
            .filter(MenuOption.pathMenuOption == PARAMETERS_MENU_PATH)
            .first()
        )
        usersMenuOption = (
            db.query(MenuOption)
            .filter(MenuOption.pathMenuOption == "/maestros/usuarios")
            .first()
        )
        parametersMenuOrder = (
            usersMenuOption.orderMenuOption + 1 if usersMenuOption else 50
        )

        if not parametersMenuOption:
            parametersMenuOption = MenuOption(
                nameMenuOption=PARAMETERS_MENU_NAME,
                pathMenuOption=PARAMETERS_MENU_PATH,
                iconMenuOption="TuneOutlined",
                orderMenuOption=parametersMenuOrder,
                statusMenuOption=True,
            )
            db.add(parametersMenuOption)
            db.flush()
            hasChanges = True
        else:
            if parametersMenuOption.nameMenuOption != PARAMETERS_MENU_NAME:
                parametersMenuOption.nameMenuOption = PARAMETERS_MENU_NAME
                hasChanges = True
            if not parametersMenuOption.statusMenuOption:
                parametersMenuOption.statusMenuOption = True
                hasChanges = True
            if parametersMenuOption.orderMenuOption != parametersMenuOrder:
                parametersMenuOption.orderMenuOption = parametersMenuOrder
                hasChanges = True

        competenciesMenuOption = (
            db.query(MenuOption)
            .filter(MenuOption.pathMenuOption == COMPETENCIES_MENU_PATH)
            .first()
        )
        competenciesMenuOrder = parametersMenuOrder + 1

        if not competenciesMenuOption:
            competenciesMenuOption = MenuOption(
                nameMenuOption=COMPETENCIES_MENU_NAME,
                pathMenuOption=COMPETENCIES_MENU_PATH,
                iconMenuOption="PsychologyOutlined",
                orderMenuOption=competenciesMenuOrder,
                statusMenuOption=True,
            )
            db.add(competenciesMenuOption)
            db.flush()
            hasChanges = True
        else:
            if competenciesMenuOption.nameMenuOption != COMPETENCIES_MENU_NAME:
                competenciesMenuOption.nameMenuOption = COMPETENCIES_MENU_NAME
                hasChanges = True
            if not competenciesMenuOption.statusMenuOption:
                competenciesMenuOption.statusMenuOption = True
                hasChanges = True
            if competenciesMenuOption.orderMenuOption != competenciesMenuOrder:
                competenciesMenuOption.orderMenuOption = competenciesMenuOrder
                hasChanges = True

        administratorRoles = [
            role
            for role in db.query(Role).all()
            if role.nameRole.strip().casefold() in ADMIN_ROLE_NAMES
        ]

        for administratorRole in administratorRoles:
            for requiredMenuOption in (
                parametersMenuOption,
                competenciesMenuOption,
            ):
                existingAssignment = (
                    db.query(RoleMenuOption)
                    .filter(
                        RoleMenuOption.IdRole == administratorRole.IdRole,
                        RoleMenuOption.IdMenuOption
                        == requiredMenuOption.IdMenuOption,
                    )
                    .first()
                )

                if not existingAssignment:
                    db.add(
                        RoleMenuOption(
                            IdRole=administratorRole.IdRole,
                            IdMenuOption=requiredMenuOption.IdMenuOption,
                        )
                    )
                    hasChanges = True

        if hasChanges:
            db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
