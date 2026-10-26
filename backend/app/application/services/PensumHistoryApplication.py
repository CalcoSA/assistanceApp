import mimetypes
from app.application.services.EventApplication import EventApplication
from app.application.services.OnlyOfficeApplication import OnlyOfficeApplication
from app.domain.interfaces.IPensumHistoryRepository import IPensumHistoryRepository


class PensumHistoryApplication:
    def __init__(self, repository: IPensumHistoryRepository):
        self.repository = repository

    @staticmethod
    def _allEvents(roles):
        return EventApplication(None)._userCanViewAllEvents(roles)

    def getPage(self, userLogin, roles, **filters):
        return self.repository.getPage(userLogin=userLogin, allEvents=self._allEvents(roles), **filters)

    def getEvents(self, userLogin, roles, **filters):
        return self.repository.getEvents(userLogin=userLogin, allEvents=self._allEvents(roles), **filters)

    def getLocalDocument(self, eventId, userLogin, roles):
        event = self.repository.getEvent(eventId, userLogin, self._allEvents(roles))
        if not event or not event.pensumPathEvent or event.pensumPathEvent.startswith("gs://"):
            raise LookupError("No se encontró un documento local accesible.")
        # Reuse the containment check used by the existing authorized office viewer.
        path = OnlyOfficeApplication(None)._resolveStoredPath(event.pensumPathEvent)
        if not path.is_file():
            raise LookupError("No se encontró el documento local.")
        return path, event.pensumOriginalNameEvent or path.name, mimetypes.guess_type(path.name)[0] or "application/octet-stream"
