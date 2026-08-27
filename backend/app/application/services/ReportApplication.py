from app.application.interfaces.IReportApplication import IReportApplication
from app.domain.interfaces.IReportRepository import IReportRepository
from typing import Optional
from datetime import date
from app.domain.dtos.ReportDto import (
    CollaboratorTrainingBySolutionCenterDto,
    CollaboratorTrainingDetailDto,
    CollaboratorTrainingReportResponseDto,
    CollaboratorTrainingSummaryDto,
    TrainingBySolutionCenterDto,
    TrainingByCompetencyDto,
    TrainingParticipantDetailDto,
    TrainingReportResponseDto,
    TrainingReportSummaryDto,
    SstTrainingReportResponseDto,
    SstTrainingReportSummaryDto,
    SstTrainingByCollaboratorDto,
    TrainingHoursReportResponseDto,
    NewStaffInductionReportResponseDto,
    AdministrativeInductionReportResponseDto,
    TransversalTrainingByCollaboratorDto,
    TransversalTrainingReportResponseDto,
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
        solutionCenterDetails = self.reportRepository.getTrainingDetailsBySolutionCenter(dateFrom, dateTo)
        byCompetency = self.reportRepository.getTrainingByCompetency(dateFrom, dateTo)
        detailsBySolutionCenter = {}

        for item in solutionCenterDetails:
            solutionCenterName = item.nameSolutionCenter or "SIN CENTRO DE SOLUCIONES"
            detailsBySolutionCenter.setdefault(solutionCenterName, []).append(
                TrainingParticipantDetailDto(
                    IdEvent=item.IdEvent,
                    titleEvent=item.titleEvent,
                    dateEvent=item.dateEvent,
                    documentNumberAttendancePerson=item.documentNumberAttendancePerson,
                    fullNameAttendancePerson=item.fullNameAttendancePerson,
                    trainingHours=round(float(item.trainingHours or 0), 2),
                )
            )

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
                    details=detailsBySolutionCenter.get(
                        item.nameSolutionCenter or "SIN CENTRO DE SOLUCIONES",
                        [],
                    ),
                )
                for item in bySolutionCenter
            ],
            byCompetency=[
                TrainingByCompetencyDto(
                    nameCompetency=item.nameCompetency,
                    totalEvents=int(item.totalEvents or 0),
                    totalTrainedPeople=int(item.totalTrainedPeople or 0),
                )
                for item in byCompetency
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

    def getTransversalTrainingReport(self, dateFrom: Optional[date], dateTo: Optional[date],):
        if dateFrom and dateTo and dateFrom > dateTo:
            raise ValueError("La fecha inicial no puede ser mayor a la fecha final.")

        summary = self.reportRepository.getTransversalTrainingSummary(dateFrom, dateTo)
        byCollaborator = self.reportRepository.getTransversalTrainingByCollaborator(dateFrom, dateTo)

        return TransversalTrainingReportResponseDto(
            totalTransversalTrainingHours=summary["totalTransversalTrainingHours"],
            totalTransversalTrainingPeople=summary["totalTransversalTrainingPeople"],
            byCollaborator=[
                TransversalTrainingByCollaboratorDto(
                    documentNumberAttendancePerson=item.documentNumberAttendancePerson,
                    fullNameAttendancePerson=item.fullNameAttendancePerson,
                    nameSolutionCenter=item.nameSolutionCenter or "SIN CENTRO DE SOLUCIONES",
                    totalTransversalTrainingHours=round(
                        float(item.totalTransversalTrainingHours or 0),
                        2,
                    ),
                )
                for item in byCollaborator
            ],
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

    def getCollaboratorTrainingReport(self, search: str, dateFrom: Optional[date], dateTo: Optional[date],):
        if dateFrom and dateTo and dateFrom > dateTo:
            raise ValueError("La fecha inicial no puede ser mayor a la fecha final.")

        normalizedSearch = search.strip()

        if not normalizedSearch:
            raise ValueError("Debe ingresar el nombre o la cédula del colaborador.")

        historyRows = self.reportRepository.getCollaboratorTrainingHistory(
            normalizedSearch,
            dateFrom,
            dateTo,
        )
        collaborators = {}

        for item in historyRows:
            documentNumber = item.documentNumberAttendancePerson
            collaborator = collaborators.setdefault(
                documentNumber,
                {
                    "documentNumberAttendancePerson": documentNumber,
                    "fullNameAttendancePerson": item.fullNameAttendancePerson,
                    "nameSolutionCenter": item.personSolutionCenterName or "SIN CENTRO DE SOLUCIONES",
                    "totalTrainings": 0,
                    "totalTrainingHours": 0.0,
                    "byTrainingSolutionCenter": {},
                    "trainings": [],
                },
            )
            trainingHours = float(item.trainingHours or 0)
            trainingSolutionCenterName = item.trainingSolutionCenterName or "SIN CENTRO DE SOLUCIONES"

            collaborator["totalTrainings"] += 1
            collaborator["totalTrainingHours"] += trainingHours
            collaborator["trainings"].append(
                CollaboratorTrainingDetailDto(
                    IdEvent=item.IdEvent,
                    titleEvent=item.titleEvent,
                    dateEvent=item.dateEvent,
                    nameSolutionCenter=trainingSolutionCenterName,
                    trainingHours=round(trainingHours, 2),
                )
            )

            solutionCenterSummary = collaborator["byTrainingSolutionCenter"].setdefault(
                trainingSolutionCenterName,
                {"totalTrainings": 0, "totalTrainingHours": 0.0},
            )
            solutionCenterSummary["totalTrainings"] += 1
            solutionCenterSummary["totalTrainingHours"] += trainingHours

        result = []

        for collaborator in collaborators.values():
            byTrainingSolutionCenter = [
                CollaboratorTrainingBySolutionCenterDto(
                    nameSolutionCenter=nameSolutionCenter,
                    totalTrainings=values["totalTrainings"],
                    totalTrainingHours=round(values["totalTrainingHours"], 2),
                )
                for nameSolutionCenter, values in sorted(
                    collaborator["byTrainingSolutionCenter"].items(),
                    key=lambda item: (-item[1]["totalTrainings"], item[0]),
                )
            ]
            result.append(
                CollaboratorTrainingSummaryDto(
                    documentNumberAttendancePerson=collaborator["documentNumberAttendancePerson"],
                    fullNameAttendancePerson=collaborator["fullNameAttendancePerson"],
                    nameSolutionCenter=collaborator["nameSolutionCenter"],
                    totalTrainings=collaborator["totalTrainings"],
                    totalTrainingHours=round(collaborator["totalTrainingHours"], 2),
                    byTrainingSolutionCenter=byTrainingSolutionCenter,
                    trainings=collaborator["trainings"],
                )
            )

        return CollaboratorTrainingReportResponseDto(collaborators=result)
