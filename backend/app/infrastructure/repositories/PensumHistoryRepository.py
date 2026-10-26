import hashlib
from sqlalchemy import case, desc, func, literal, or_
from app.domain.entities.Event import Event
from app.domain.entities.TrainingParameter import TrainingParameter as Parameter
from app.domain.entities.TrainingParameterVersion import TrainingParameterVersion as Version
from app.domain.dtos.PensumHistoryDto import TrainingParameterVersionResponseDto
from app.domain.interfaces.IPensumHistoryRepository import IPensumHistoryRepository


def referenceColumn(column):
    # Object names are case-sensitive, regardless of the MySQL database collation.
    return column.collate("utf8mb4_bin")


class PensumHistoryRepository(IPensumHistoryRepository):
    def __init__(self, db):
        self.db = db

    def _events(self, userLogin, allEvents):
        query = self.db.query(Event).filter(Event.pensumPathEvent.isnot(None), Event.pensumPathEvent != "")
        return query if allEvents else query.filter(referenceColumn(Event.createdByUserLogin) == userLogin)

    def getEvent(self, eventId, userLogin, allEvents):
        return self._events(userLogin, allEvents).filter(Event.IdEvent == eventId).first()

    @staticmethod
    def _association(event):
        return dict(IdEvent=event.IdEvent, titleEvent=event.titleEvent,
                    IdTrainingParameter=event.IdTrainingParameter, createdAt=event.createdAt)

    def _documents(self, userLogin, allEvents, search, origin, versionState):
        versions = self.db.query(
            referenceColumn(Version.pensumPathTrainingParameterVersion).label("reference"),
            Version.pensumOriginalNameTrainingParameterVersion.label("name"),
            Parameter.nameTrainingParameter.label("relatedName"), Version.createdAt.label("registeredAt"),
            literal("parameter").label("origin"),
            (referenceColumn(Version.pensumPathTrainingParameterVersion) == referenceColumn(Parameter.pensumPathTrainingParameter)).label("isCurrent"),
        ).join(Parameter, Parameter.IdTrainingParameter == Version.IdTrainingParameter)
        events = self._events(userLogin, allEvents).with_entities(
            referenceColumn(Event.pensumPathEvent).label("reference"), Event.pensumOriginalNameEvent.label("name"),
            func.concat(Event.titleEvent, " ", func.coalesce(Parameter.nameTrainingParameter, "")).label("relatedName"), Event.createdAt.label("registeredAt"),
            case((Event.IdTrainingParameter.is_(None), "freeEvent"), else_="parameterEvent").label("origin"),
            case((Version.IdTrainingParameterVersion.isnot(None),
                  referenceColumn(Event.pensumPathEvent) == referenceColumn(Parameter.pensumPathTrainingParameter)), else_=None).label("isCurrent"),
        ).outerjoin(Version, (Version.IdTrainingParameter == Event.IdTrainingParameter) &
                    (referenceColumn(Version.pensumPathTrainingParameterVersion) == referenceColumn(Event.pensumPathEvent)))
        events = events.outerjoin(Parameter, Parameter.IdTrainingParameter == Event.IdTrainingParameter)
        source = versions.union_all(events).subquery()
        query = self.db.query(source.c.reference, func.max(source.c.registeredAt).label("registeredAt"))
        if search:
            query = query.filter(or_(source.c.name.contains(search, autoescape=True), source.c.relatedName.contains(search, autoescape=True)))
        if origin != "all":
            query = query.filter(source.c.origin == origin)
        if versionState != "all":
            query = query.filter(source.c.isCurrent.is_(versionState == "current"))
        return query.group_by(source.c.reference)

    def getPage(self, userLogin, allEvents, page, pageSize, search, origin, versionState):
        query = self._documents(userLogin, allEvents, search, origin, versionState)
        total = query.count()
        # Stable pagination; grouping prevents event associations from becoming extra versions.
        documents = query.order_by(desc("registeredAt"), "reference").offset((page - 1) * pageSize).limit(pageSize).all()
        items = []
        for document in documents:
            reference = document.reference
            versions = self.db.query(Version, Parameter).join(Parameter, Parameter.IdTrainingParameter == Version.IdTrainingParameter).filter(
                referenceColumn(Version.pensumPathTrainingParameterVersion) == reference,
            ).order_by(Version.versionNumber.desc()).all()
            versionDtos = [TrainingParameterVersionResponseDto.model_validate(v).model_copy(update={
                "parameterName": p.nameTrainingParameter,
                "isCurrent": v.pensumPathTrainingParameterVersion == p.pensumPathTrainingParameter,
            }) for v, p in versions]
            events = self._events(userLogin, allEvents).filter(referenceColumn(Event.pensumPathEvent) == reference)
            eventCount = events.count()
            samples = events.order_by(Event.IdEvent.desc()).limit(5).all()
            origins = ["parameter"] if versions else []
            # Counts are scoped before being exposed, including on documents shared with parameters.
            if events.filter(Event.IdTrainingParameter.is_(None)).first():
                origins.append("freeEvent")
            if events.filter(Event.IdTrainingParameter.isnot(None)).first():
                origins.append("parameterEvent")
            v = versions[0][0] if versions else None
            e = samples[0] if samples else None
            if v is None and e is None:
                continue
            items.append(dict(
                documentKey=hashlib.sha256(reference.encode()).hexdigest(),
                name=v.pensumOriginalNameTrainingParameterVersion if v else (e.pensumOriginalNameEvent or reference.rsplit("/", 1)[-1]),
                mime=v.pensumMimeTypeTrainingParameterVersion if v else e.pensumMimeTypeEvent,
                size=v.pensumSizeTrainingParameterVersion if v else e.pensumSizeEvent,
                registeredAt=v.createdAt if v else e.createdAt, isLocal=not reference.startswith("gs://"),
                versions=versionDtos, events=[self._association(e) for e in samples], eventCount=eventCount,
                eventId=e.IdEvent if e else None, origins=origins,
            ))
        return dict(items=items, total=total, page=page, pageSize=pageSize)

    def getEvents(self, userLogin, allEvents, versionId, eventId, page, pageSize):
        if versionId is not None:
            version = self.db.query(Version).filter(Version.IdTrainingParameterVersion == versionId).first()
            reference = version.pensumPathTrainingParameterVersion if version else None
        else:
            event = self.getEvent(eventId, userLogin, allEvents)
            reference = event.pensumPathEvent if event else None
        if not reference:
            raise LookupError("No se encontró un documento accesible.")
        query = self._events(userLogin, allEvents).filter(referenceColumn(Event.pensumPathEvent) == reference)
        total = query.count()
        events = query.order_by(Event.IdEvent.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
        return dict(items=[self._association(e) for e in events], total=total, page=page, pageSize=pageSize)
