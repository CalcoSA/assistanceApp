import type { ApiResponse } from "../models/ApiResponse";
import { apiClient } from "./apiClient";
import type {
  TrainingReportFilter,
  TrainingReportResponse,
  SstTrainingReportResponse,
  TrainingHoursReportResponse,
  NewStaffInductionReportResponse,
  AdministrativeInductionReportResponse,
  GeneralReportResponse,
  AverageTrainingTimeReportResponse
} from "../models/Report";

export const reportService = {

  getTrainingReport: async (filters: TrainingReportFilter): Promise<ApiResponse<TrainingReportResponse>> => {
    const response = await apiClient.get<ApiResponse<TrainingReportResponse>>("/reports/training", { params: { dateFrom: filters.dateFrom || undefined, dateTo: filters.dateTo || undefined, },});
    return response.data;
  },

  getSstTrainingReport: async (filters: TrainingReportFilter): Promise<ApiResponse<SstTrainingReportResponse>> => {
    const response = await apiClient.get<ApiResponse<SstTrainingReportResponse>>("/reports/sst-training", { params: { dateFrom: filters.dateFrom || undefined, dateTo: filters.dateTo || undefined, },});
    return response.data;
  },

  getTrainingHoursReport: async (filters: TrainingReportFilter): Promise<ApiResponse<TrainingHoursReportResponse>> => {
    const response = await apiClient.get<ApiResponse<TrainingHoursReportResponse>>("/reports/training-hours", { params: { dateFrom: filters.dateFrom || undefined, dateTo: filters.dateTo || undefined, },});
    return response.data;
  },

  getNewStaffInductionReport: async (filters: TrainingReportFilter): Promise<ApiResponse<NewStaffInductionReportResponse>> => {
    const response = await apiClient.get<ApiResponse<NewStaffInductionReportResponse>>("/reports/new-staff-induction", { params: { dateFrom: filters.dateFrom || undefined, dateTo: filters.dateTo || undefined, },});
    return response.data;
  },

  getAdministrativeInductionReport: async (filters: TrainingReportFilter): Promise<ApiResponse<AdministrativeInductionReportResponse>> => {
    const response = await apiClient.get<ApiResponse<AdministrativeInductionReportResponse>>("/reports/administrative-induction", { params: { dateFrom: filters.dateFrom || undefined, dateTo: filters.dateTo || undefined, },});
    return response.data;
  },

  getGeneralReport: async (filters: TrainingReportFilter): Promise<ApiResponse<GeneralReportResponse>> => {
    const response = await apiClient.get<ApiResponse<GeneralReportResponse>>("/reports/general", { params: { dateFrom: filters.dateFrom || undefined, dateTo: filters.dateTo || undefined, },});
    return response.data;
  },

  getAverageTrainingTimeReport: async (filters: TrainingReportFilter, totalWorkers: number): Promise<ApiResponse<AverageTrainingTimeReportResponse>> => {
    const response = await apiClient.get<ApiResponse<AverageTrainingTimeReportResponse>>("/reports/average-training-time", { params: { dateFrom: filters.dateFrom || undefined, dateTo: filters.dateTo || undefined, totalWorkers, },});
    return response.data;
  },
};