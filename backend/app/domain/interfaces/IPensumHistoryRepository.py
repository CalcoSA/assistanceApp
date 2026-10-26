from abc import ABC, abstractmethod


class IPensumHistoryRepository(ABC):
    @abstractmethod
    def getPage(self, userLogin, allEvents, page, pageSize, search, origin, versionState):
        pass

    @abstractmethod
    def getEvents(self, userLogin, allEvents, versionId, eventId, page, pageSize):
        pass

    @abstractmethod
    def getEvent(self, eventId, userLogin, allEvents):
        pass
