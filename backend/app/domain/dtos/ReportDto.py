from pydantic import BaseModel
from typing import List

class TrainingReportSummaryDto(BaseModel):
    totalTrainedPeople: int
    totalInternalTrainedPeople: int
    totalExternalTrainedPeople: int

class TrainingBySolutionCenterDto(BaseModel):
    nameSolutionCenter: str
    totalTrainedPeople: int

class TrainingReportResponseDto(BaseModel):
    summary: TrainingReportSummaryDto
    bySolutionCenter: List[TrainingBySolutionCenterDto]

class SstTrainingByCollaboratorDto(BaseModel):
    documentNumberAttendancePerson: str
    fullNameAttendancePerson: str
    nameSolutionCenter: str
    totalSstTrainingHours: float

class SstTrainingReportSummaryDto(BaseModel):
    totalInternalSstTrainedPeople: int
    totalSstTrainingHours: float

class SstTrainingReportResponseDto(BaseModel):
    summary: SstTrainingReportSummaryDto
    byCollaborator: List[SstTrainingByCollaboratorDto]

class TrainingHoursReportResponseDto(BaseModel):
    totalTrainingHours: float
    totalMultipleFunctionsTrainingHours: float
    totalPositionTrainingHours: float
    totalPersonalTrainingHours: float
    totalSerTrainingHours: float
    totalHacerTrainingHours: float
    totalInternalTrainingHours: float
    totalExternalTrainingHours: float

class NewStaffInductionReportResponseDto(BaseModel):
    totalNewStaffInductionHours: float
    totalNewStaffInductionPeople: int

class AdministrativeInductionReportResponseDto(BaseModel):
    totalAdministrativeInductionHours: float
    totalAdministrativeInductionPeople: int

class GeneralReportResponseDto(BaseModel):
    topTrainingSolutionCenterName: str
    topTrainingSolutionCenterTotal: int
    totalInternalQualityTrainedPeople: int
    totalInternalSerTrainedPeople: int
    totalInternalHacerTrainedPeople: int

class AverageTrainingTimeReportResponseDto(BaseModel):
    totalWorkers: int
    totalInternalTrainingHours: float
    averageTrainingHoursPerWorker: float