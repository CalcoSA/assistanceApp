import type { Event, EventCreateRequest, EventQr, EventAttendance, EventFilterRequest, EventPaginatedResult } from "../models/Event";
import type { ApiResponse } from "../models/ApiResponse";
import type { OnlyOfficePreview } from "../models/OnlyOffice";
import { apiClient } from "./apiClient";

export const eventService = {
  getById: async (IdEvent: number): Promise<ApiResponse<Event>> => {
    const response = await apiClient.get<ApiResponse<Event>>(`/events/${IdEvent}`);
    return response.data;
  },

  getAttendances: async (IdEvent: number): Promise<ApiResponse<EventAttendance[]>> => {
    const response = await apiClient.get<ApiResponse<EventAttendance[]>>(`/events/${IdEvent}/attendances`);
    return response.data;
  },

  getAll: async (filters: EventFilterRequest): Promise<ApiResponse<EventPaginatedResult>> => {
    const response = await apiClient.get<ApiResponse<EventPaginatedResult>>("/events/", { params: { page: filters.page, pageSize: filters.pageSize, statusFilter: filters.statusFilter || undefined, },});
    return response.data;
  },

  create: async (data: EventCreateRequest): Promise<ApiResponse<Event>> => {
    const response = await apiClient.post<ApiResponse<Event>>("/events/", data);
    return response.data;
  },

  update: async (IdEvent: number, data: Partial<EventCreateRequest>): Promise<ApiResponse<Event>> => {
    const response = await apiClient.put<ApiResponse<Event>>(`/events/${IdEvent}`, data);
    return response.data;
  },

  cancel: async (IdEvent: number): Promise<ApiResponse<Event>> => {
    const response = await apiClient.patch<ApiResponse<Event>>(`/events/${IdEvent}/cancel`);
    return response.data;
  },

  delete: async (IdEvent: number): Promise<ApiResponse<boolean>> => {
    const response = await apiClient.delete<ApiResponse<boolean>>(`/events/${IdEvent}`);
    return response.data;
  },

  getQr: async (IdEvent: number): Promise<ApiResponse<EventQr>> => {
    const response = await apiClient.get<ApiResponse<EventQr>>(`/events/${IdEvent}/qr`);
    return response.data;
  },

  downloadQr: async (IdEvent: number): Promise<Blob> => {
    const response = await apiClient.get(`/events/${IdEvent}/qr/download`, { responseType: "blob", });
    return response.data;
  },

  uploadPensum: async (IdEvent: number, file: File): Promise<ApiResponse<Event>> => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiClient.post<ApiResponse<Event>>(`/events/${IdEvent}/pensum`, formData, { headers: { "Content-Type": "multipart/form-data", },});
    return response.data;
  },

  createPensumPreview: async (file: File): Promise<ApiResponse<OnlyOfficePreview>> => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiClient.post<ApiResponse<OnlyOfficePreview>>(
      "/onlyoffice/pensum/preview",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return response.data;
  },

  getPensumPreview: async (IdEvent: number): Promise<ApiResponse<OnlyOfficePreview>> => {
    const response = await apiClient.get<ApiResponse<OnlyOfficePreview>>(
      `/onlyoffice/pensum/events/${IdEvent}`
    );
    return response.data;
  },
};
