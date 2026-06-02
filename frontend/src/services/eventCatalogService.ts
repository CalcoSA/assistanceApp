import type { SpecificTrainingProgram, EventStatus, EventCategory, Competency, AssistanceReason } from "../models/EventCatalog";
import type { ApiResponse } from "../models/ApiResponse";
import { apiClient } from "./apiClient";

export const eventCatalogService = {

  async getAllSpecificTraining(): Promise<ApiResponse<SpecificTrainingProgram[]>> {
    const response = await apiClient.get<ApiResponse<SpecificTrainingProgram[]>>("/specific-training-program/");
    return response.data;
  },

    async getAllEventStatus(): Promise<ApiResponse<EventStatus[]>> {
    const response = await apiClient.get<ApiResponse<EventStatus[]>>("/event-status/");
    return response.data;
  },

    async getAllEventCategory(): Promise<ApiResponse<EventCategory[]>> {
    const response = await apiClient.get<ApiResponse<EventCategory[]>>("/event-category/");
    return response.data;
  },

    async getAllCompetency(): Promise<ApiResponse<Competency[]>> {
    const response = await apiClient.get<ApiResponse<Competency[]>>("/competency/");
    return response.data;
  },

    async getAllAssistanceReason(): Promise<ApiResponse<AssistanceReason[]>> {
    const response = await apiClient.get<ApiResponse<AssistanceReason[]>>("/assistance-reason/");
    return response.data;
  },
}