from abc import ABC, abstractmethod
from typing import Optional
from datetime import date

class IReportApplication(ABC):

    @abstractmethod
    def getTrainingReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getSstTrainingReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getTrainingHoursReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getNewStaffInductionReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getAdministrativeInductionReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getTransversalTrainingReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getGeneralReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getAverageTrainingTimeReport(self, dateFrom: Optional[date], dateTo: Optional[date], totalWorkers: int,):
        pass

    @abstractmethod
    def getCollaboratorTrainingReport(self, search: str, dateFrom: Optional[date], dateTo: Optional[date],):
        pass
