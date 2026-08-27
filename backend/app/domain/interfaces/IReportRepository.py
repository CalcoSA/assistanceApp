from abc import ABC, abstractmethod
from typing import Optional
from datetime import date

class IReportRepository(ABC):

    @abstractmethod
    def getTrainingSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getTrainingBySolutionCenter(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getTrainingDetailsBySolutionCenter(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getTrainingByCompetency(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getSstTrainingSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getSstTrainingByCollaborator(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getTrainingHoursSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getNewStaffInductionSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getAdministrativeInductionSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getTransversalTrainingSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getTransversalTrainingByCollaborator(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getGeneralSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getAverageTrainingTimeSummary( self, dateFrom: Optional[date], dateTo: Optional[date], totalWorkers: int,):
        pass

    @abstractmethod
    def getCollaboratorTrainingHistory(self, search: str, dateFrom: Optional[date], dateTo: Optional[date],):
        pass
