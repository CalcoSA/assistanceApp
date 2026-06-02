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
    def getGeneralSummary(self, dateFrom: Optional[date], dateTo: Optional[date],):
        pass

    @abstractmethod
    def getAverageTrainingTimeSummary( self, dateFrom: Optional[date], dateTo: Optional[date], totalWorkers: int,):
        pass