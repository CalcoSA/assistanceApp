from datetime import date
from pydantic import BaseModel, Field
from typing import List

class TrainingReportSummaryDto(BaseModel):
    totalTrainedPeople: int
    totalInternalTrainedPeople: int
    totalExternalTrainedPeople: int

class TrainingBySolutionCenterDto(BaseModel):
    nameSolutionCenter: str
    totalTrainedPeople: int
    details: List["TrainingParticipantDetailDto"] = Field(default_factory=list)

class TrainingParticipantDetailDto(BaseModel):
    IdEvent: int
    titleEvent: str
    dateEvent: date
    documentNumberAttendancePerson: str
    fullNameAttendancePerson: str
    trainingHours: float

class TrainingByCompetencyDto(BaseModel):
    nameCompetency: str
    totalEvents: int
    totalTrainedPeople: int

class TrainingReportResponseDto(BaseModel):
    summary: TrainingReportSummaryDto
    bySolutionCenter: List[TrainingBySolutionCenterDto]
    byCompetency: List[TrainingByCompetencyDto]

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

class TransversalTrainingByCollaboratorDto(BaseModel):
    documentNumberAttendancePerson: str
    fullNameAttendancePerson: str
    nameSolutionCenter: str
    totalTransversalTrainingHours: float

class TransversalTrainingReportResponseDto(BaseModel):
    totalTransversalTrainingHours: float
    totalTransversalTrainingPeople: int
    byCollaborator: List[TransversalTrainingByCollaboratorDto]

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

class CollaboratorTrainingBySolutionCenterDto(BaseModel):
    nameSolutionCenter: str
    totalTrainings: int
    totalTrainingHours: float

class CollaboratorTrainingDetailDto(BaseModel):
    IdEvent: int
    titleEvent: str
    dateEvent: date
    nameSolutionCenter: str
    trainingHours: float

class CollaboratorTrainingSummaryDto(BaseModel):
    documentNumberAttendancePerson: str
    fullNameAttendancePerson: str
    nameSolutionCenter: str
    totalTrainings: int
    totalTrainingHours: float
    byTrainingSolutionCenter: List[CollaboratorTrainingBySolutionCenterDto]
    trainings: List[CollaboratorTrainingDetailDto]

class CollaboratorTrainingReportResponseDto(BaseModel):
    collaborators: List[CollaboratorTrainingSummaryDto]
