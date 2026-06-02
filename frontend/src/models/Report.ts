export interface TrainingReportSummary {
  totalTrainedPeople: number;
  totalInternalTrainedPeople: number;
  totalExternalTrainedPeople: number;
}

export interface TrainingBySolutionCenter {
  nameSolutionCenter: string;
  totalTrainedPeople: number;
}

export interface TrainingReportResponse {
  summary: TrainingReportSummary;
  bySolutionCenter: TrainingBySolutionCenter[];
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