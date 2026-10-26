from datetime import date, datetime, time
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.services.EventApplication import EventApplication
from app.domain.dtos.EventDto import EventCreateDto, EventUpdateDto
from app.infrastructure.db.base import Base
from app.infrastructure.repositories.EventRepository import EventRepository


@pytest.fixture
def service():
    # Isolated in-memory database; never connects to the configured application DB.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        application = EventApplication(EventRepository(db))
        application._currentDateTime = lambda: datetime(2026, 10, 6, 8, 0)
        application._generateQr = Mock(return_value="/uploads/qrs/test.png")
        yield application
    engine.dispose()


def create_event(service, **overrides):
    data = EventCreateDto(**{
        "titleEvent": "Evento de prueba",
        "dateEvent": date(2026, 10, 8),
        "startTimeEvent": time(9, 0),
        "endTimeEvent": time(10, 0),
        "facilitatorNameEvent": "Principal",
        "facilitatorTypeEvent": "INTERNO",
        "facilitatorPositionEvent": "Formador",
        "isPaidTrainingEvent": False,
        **overrides,
    })
    return service.create(data, "tester", ["formador"])


def reload_event(service, event_id):
    service.eventRepository.db.expire_all()
    return service.getByIdByUserScope(event_id, "tester", ["formador"])


@pytest.mark.parametrize("fields, expected", [
    ({}, (None, None, None, None)),
    ({"thirdFacilitatorNameEvent": " ", "thirdFacilitatorTypeEvent": "", "thirdFacilitatorCompanyEvent": "", "thirdFacilitatorPositionEvent": " "}, (None, None, None, None)),
    ({"thirdFacilitatorNameEvent": " Ana ", "thirdFacilitatorTypeEvent": "interno"}, ("ANA", "INTERNO", None, None)),
    ({"thirdFacilitatorNameEvent": " Ana ", "thirdFacilitatorTypeEvent": "externo", "thirdFacilitatorCompanyEvent": " Acme ", "thirdFacilitatorPositionEvent": " Consultora "}, ("ANA", "EXTERNO", "ACME", "CONSULTORA")),
])
def test_create_and_read_optional_third_facilitator(service, fields, expected):
    created = create_event(service, **fields)
    loaded = reload_event(service, created.IdEvent)

    for response in (created, loaded):
        assert (
            response.thirdFacilitatorNameEvent,
            response.thirdFacilitatorTypeEvent,
            response.thirdFacilitatorCompanyEvent,
            response.thirdFacilitatorPositionEvent,
        ) == expected
        assert response.secondFacilitatorNameEvent is None
        assert response.facilitatorNameEvent == "PRINCIPAL"
        assert response.facilitatorTypeEvent == "INTERNO"
        assert response.facilitatorPositionEvent == "FORMADOR"


@pytest.mark.parametrize("mode", ["create", "update"])
@pytest.mark.parametrize("fields, error", [
    ({"thirdFacilitatorTypeEvent": "INTERNO"}, "nombre del tercer facilitador"),
    ({"thirdFacilitatorPositionEvent": "Consultora"}, "nombre del tercer facilitador"),
    ({"thirdFacilitatorNameEvent": "Ana"}, "tipo del tercer facilitador"),
    ({"thirdFacilitatorNameEvent": "Ana", "thirdFacilitatorTypeEvent": "OTRO"}, "debe ser INTERNO o EXTERNO"),
    ({"thirdFacilitatorNameEvent": "Ana", "thirdFacilitatorTypeEvent": "EXTERNO", "thirdFacilitatorCompanyEvent": " "}, "empresa del tercer facilitador"),
])
def test_partial_or_invalid_third_facilitator_is_rejected(service, mode, fields, error):
    event = create_event(service) if mode == "update" else None

    with pytest.raises(ValueError, match=error):
        if mode == "create":
            create_event(service, **fields)
        else:
            service.update(event.IdEvent, EventUpdateDto(**fields), "tester", ["formador"])

    if event:
        assert reload_event(service, event.IdEvent).thirdFacilitatorNameEvent is None


def test_edit_add_preserve_change_type_and_remove_third_facilitator(service):
    created = create_event(
        service,
        secondFacilitatorNameEvent="Segundo",
        secondFacilitatorTypeEvent="EXTERNO",
        secondFacilitatorCompanyEvent="Empresa segunda",
        secondFacilitatorPositionEvent="Asesor",
    )
    service.update(created.IdEvent, EventUpdateDto(
        thirdFacilitatorNameEvent="Ana",
        thirdFacilitatorTypeEvent="EXTERNO",
        thirdFacilitatorCompanyEvent="Acme",
        thirdFacilitatorPositionEvent="Consultora",
    ), "tester", ["formador"])

    service.update(created.IdEvent, EventUpdateDto(titleEvent="Otro título"), "tester", ["formador"])
    loaded = reload_event(service, created.IdEvent)
    assert loaded.thirdFacilitatorNameEvent == "ANA"
    assert loaded.thirdFacilitatorTypeEvent == "EXTERNO"
    assert loaded.thirdFacilitatorCompanyEvent == "ACME"
    assert loaded.thirdFacilitatorPositionEvent == "CONSULTORA"

    service.update(created.IdEvent, EventUpdateDto(thirdFacilitatorTypeEvent="INTERNO"), "tester", ["formador"])
    loaded = reload_event(service, created.IdEvent)
    assert loaded.thirdFacilitatorTypeEvent == "INTERNO"
    assert loaded.thirdFacilitatorCompanyEvent is None

    service.update(created.IdEvent, EventUpdateDto(
        thirdFacilitatorNameEvent=None,
        thirdFacilitatorTypeEvent=None,
        thirdFacilitatorCompanyEvent=None,
        thirdFacilitatorPositionEvent=None,
    ), "tester", ["formador"])
    loaded = reload_event(service, created.IdEvent)
    assert loaded.thirdFacilitatorNameEvent is None
    assert loaded.thirdFacilitatorTypeEvent is None
    assert loaded.thirdFacilitatorCompanyEvent is None
    assert loaded.thirdFacilitatorPositionEvent is None
    assert loaded.facilitatorNameEvent == "PRINCIPAL"
    assert loaded.facilitatorTypeEvent == "INTERNO"
    assert loaded.facilitatorPositionEvent == "FORMADOR"
    assert loaded.secondFacilitatorNameEvent == "SEGUNDO"
    assert loaded.secondFacilitatorTypeEvent == "EXTERNO"
    assert loaded.secondFacilitatorCompanyEvent == "EMPRESA SEGUNDA"
    assert loaded.secondFacilitatorPositionEvent == "ASESOR"


@pytest.mark.parametrize("prefix", ["second", "third"])
def test_optional_facilitators_keep_the_same_company_and_position_rules(service, prefix):
    created = create_event(service, **{
        f"{prefix}FacilitatorNameEvent": "Ana",
        f"{prefix}FacilitatorTypeEvent": "INTERNO",
        f"{prefix}FacilitatorCompanyEvent": "Discard this company",
    })
    loaded = reload_event(service, created.IdEvent)
    assert getattr(loaded, f"{prefix}FacilitatorTypeEvent") == "INTERNO"
    assert getattr(loaded, f"{prefix}FacilitatorCompanyEvent") is None
    assert getattr(loaded, f"{prefix}FacilitatorPositionEvent") is None
