export interface TrainingReportSummary {
  totalTrainedPeople: number;
  totalInternalTrainedPeople: number;
  totalExternalTrainedPeople: number;
}

export interface TrainingBySolutionCenter {
  nameSolutionCenter: string;
  totalTrainedPeople: number;
  details: TrainingParticipantDetail[];
}

export interface TrainingParticipantDetail {
  IdEvent: number;
  titleEvent: string;
  dateEvent: string;
  documentNumberAttendancePerson: string;
  fullNameAttendancePerson: string;
  trainingHours: number;
}

export interface TrainingByCompetency {
  nameCompetency: string;
  totalEvents: number;
  totalTrainedPeople: number;
}

export interface TrainingReportResponse {
  summary: TrainingReportSummary;
  bySolutionCenter: TrainingBySolutionCenter[];
  byCompetency: TrainingByCompetency[];
}

export interface TrainingReportFilter {
  dateFrom?: string;
  dateTo?: string;
}

export interface SstTrainingReportSummary {
  totalInternalSstTrainedPeople: number;
  totalSstTrainingHours: number;
}

export interface SstTrainingByCollaborator {
  documentNumberAttendancePerson: string;
  fullNameAttendancePerson: string;
  nameSolutionCenter: string;
  totalSstTrainingHours: number;
}

export interface SstTrainingReportResponse {
  summary: SstTrainingReportSummary;
  byCollaborator: SstTrainingByCollaborator[];
}

export interface TrainingHoursReportResponse {
  totalTrainingHours: number;
  totalMultipleFunctionsTrainingHours: number;
  totalPositionTrainingHours: number;
  totalPersonalTrainingHours: number;
  totalSerTrainingHours: number;
  totalHacerTrainingHours: number;
  totalInternalTrainingHours: number;
  totalExternalTrainingHours: number;
}

export interface NewStaffInductionReportResponse {
  totalNewStaffInductionHours: number;
  totalNewStaffInductionPeople: number;
}

export interface AdministrativeInductionReportResponse {
  totalAdministrativeInductionHours: number;
  totalAdministrativeInductionPeople: number;
}

export interface TransversalTrainingByCollaborator {
  documentNumberAttendancePerson: string;
  fullNameAttendancePerson: string;
  nameSolutionCenter: string;
  totalTransversalTrainingHours: number;
}

export interface TransversalTrainingReportResponse {
  totalTransversalTrainingHours: number;
  totalTransversalTrainingPeople: number;
  byCollaborator: TransversalTrainingByCollaborator[];
}

export interface GeneralReportResponse {
  topTrainingSolutionCenterName: string;
  topTrainingSolutionCenterTotal: number;
  totalInternalQualityTrainedPeople: number;
  totalInternalSerTrainedPeople: number;
  totalInternalHacerTrainedPeople: number;
}

export interface AverageTrainingTimeReportResponse {
  totalWorkers: number;
  totalInternalTrainingHours: number;
  averageTrainingHoursPerWorker: number;
}

export interface CollaboratorTrainingBySolutionCenter {
  nameSolutionCenter: string;
  totalTrainings: number;
  totalTrainingHours: number;
}

export interface CollaboratorTrainingDetail {
  IdEvent: number;
  titleEvent: string;
  dateEvent: string;
  nameSolutionCenter: string;
  trainingHours: number;
}

export interface CollaboratorTrainingSummary {
  documentNumberAttendancePerson: string;
  fullNameAttendancePerson: string;
  nameSolutionCenter: string;
  totalTrainings: number;
  totalTrainingHours: number;
  byTrainingSolutionCenter: CollaboratorTrainingBySolutionCenter[];
  trainings: CollaboratorTrainingDetail[];
}

export interface CollaboratorTrainingReportResponse {
  collaborators: CollaboratorTrainingSummary[];
}

export interface CollaboratorTrainingReportFilter extends TrainingReportFilter {
  search: string;
}
