from app.application.interfaces.IReportApplication import IReportApplication
from app.domain.interfaces.IReportRepository import IReportRepository
from typing import Optional
from datetime import date
from app.domain.dtos.ReportDto import (
    TrainingBySolutionCenterDto,
    TrainingReportResponseDto,
    TrainingReportSummaryDto,
    SstTrainingReportResponseDto,
    SstTrainingReportSummaryDto,
    SstTrainingByCollaboratorDto,
    TrainingHoursReportResponseDto,
    NewStaffInductionReportResponseDto,
    AdministrativeInductionReportResponseDto,
    GeneralReportResponseDto,
    AverageTrainingTimeReportResponseDto
)

class ReportApplication(IReportApplication):

    def __init__(self, reportRepository: IReportRepository):
        self.reportRepository = reportRepository

    def getTrainingReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        if dateFrom and dateTo and dateFrom > dateTo:
            raise ValueError("La fecha inicial no puede ser mayor a la fecha final.")

        summary = self.reportRepository.getTrainingSummary(dateFrom, dateTo)
        bySolutionCenter = self.reportRepository.getTrainingBySolutionCenter(dateFrom, dateTo)

        return TrainingReportResponseDto(
            summary=TrainingReportSummaryDto(
                totalTrainedPeople=summary["totalTrainedPeople"],
                totalInternalTrainedPeople=summary["totalInternalTrainedPeople"],
                totalExternalTrainedPeople=summary["totalExternalTrainedPeople"],
            ),
            bySolutionCenter=[
                TrainingBySolutionCenterDto(
                    nameSolutionCenter=item.nameSolutionCenter or "SIN CENTRO DE SOLUCIONES",
                    totalTrainedPeople=item.totalTrainedPeople or 0,
                )
                for item in bySolutionCenter
            ],
        )
    
    def getSstTrainingReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        if dateFrom and dateTo and dateFrom > dateTo:
            raise ValueError("La fecha inicial no puede ser mayor a la fecha final.")

        summary = self.reportRepository.getSstTrainingSummary(dateFrom, dateTo)
        byCollaborator = self.reportRepository.getSstTrainingByCollaborator(dateFrom, dateTo)

        return SstTrainingReportResponseDto(
            summary=SstTrainingReportSummaryDto(
                totalInternalSstTrainedPeople=summary["totalInternalSstTrainedPeople"],
                totalSstTrainingHours=summary["totalSstTrainingHours"],
            ),
            byCollaborator=[
                SstTrainingByCollaboratorDto(
                    documentNumberAttendancePerson=item.documentNumberAttendancePerson,
                    fullNameAttendancePerson=item.fullNameAttendancePerson,
                    nameSolutionCenter=item.nameSolutionCenter or "SIN CENTRO DE SOLUCIONES",
                    totalSstTrainingHours=round(float(item.totalSstTrainingHours or 0), 2),
                )
                for item in byCollaborator
            ],
        )
    
    def getTrainingHoursReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        if dateFrom and dateTo and dateFrom > dateTo:
            raise ValueError("La fecha inicial no puede ser mayor a la fecha final.")

        summary = self.reportRepository.getTrainingHoursSummary(dateFrom, dateTo)

        return TrainingHoursReportResponseDto(
            totalTrainingHours=summary["totalTrainingHours"],
            totalMultipleFunctionsTrainingHours=summary["totalMultipleFunctionsTrainingHours"],
            totalPositionTrainingHours=summary["totalPositionTrainingHours"],
            totalPersonalTrainingHours=summary["totalPersonalTrainingHours"],
            totalSerTrainingHours=summary["totalSerTrainingHours"],
            totalHacerTrainingHours=summary["totalHacerTrainingHours"],
            totalInternalTrainingHours=summary["totalInternalTrainingHours"],
            totalExternalTrainingHours=summary["totalExternalTrainingHours"],
        )
    
    def getNewStaffInductionReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        if dateFrom and dateTo and dateFrom > dateTo:
            raise ValueError("La fecha inicial no puede ser mayor a la fecha final.")

        summary = self.reportRepository.getNewStaffInductionSummary(dateFrom, dateTo)

        return NewStaffInductionReportResponseDto(
            totalNewStaffInductionHours=summary["totalNewStaffInductionHours"],
            totalNewStaffInductionPeople=summary["totalNewStaffInductionPeople"],
        )
    
    def getAdministrativeInductionReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        if dateFrom and dateTo and dateFrom > dateTo:
            raise ValueError("La fecha inicial no puede ser mayor a la fecha final.")

        summary = self.reportRepository.getAdministrativeInductionSummary(dateFrom, dateTo)

        return AdministrativeInductionReportResponseDto(
            totalAdministrativeInductionHours=summary["totalAdministrativeInductionHours"],
            totalAdministrativeInductionPeople=summary["totalAdministrativeInductionPeople"],
        )
    
    def getGeneralReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        if dateFrom and dateTo and dateFrom > dateTo:
            raise ValueError("La fecha inicial no puede ser mayor a la fecha final.")

        summary = self.reportRepository.getGeneralSummary(dateFrom, dateTo)

        return GeneralReportResponseDto(
            topTrainingSolutionCenterName=summary["topTrainingSolutionCenterName"],
            topTrainingSolutionCenterTotal=summary["topTrainingSolutionCenterTotal"],
            totalInternalQualityTrainedPeople=summary["totalInternalQualityTrainedPeople"],
            totalInternalSerTrainedPeople=summary["totalInternalSerTrainedPeople"],
            totalInternalHacerTrainedPeople=summary["totalInternalHacerTrainedPeople"],
        )
    
    def getAverageTrainingTimeReport(self, dateFrom: Optional[date], dateTo: Optional[date], totalWorkers: int,):
        if dateFrom and dateTo and dateFrom > dateTo:
            raise ValueError("La fecha inicial no puede ser mayor a la fecha final.")

        if totalWorkers <= 0:
            raise ValueError("El total de trabajadores debe ser mayor a cero.")

        summary = self.reportRepository.getAverageTrainingTimeSummary(dateFrom, dateTo, totalWorkers,)

        return AverageTrainingTimeReportResponseDto(
            totalWorkers=summary["totalWorkers"],
            totalInternalTrainingHours=summary["totalInternalTrainingHours"],
            averageTrainingHoursPerWorker=summary["averageTrainingHoursPerWorker"],
        )