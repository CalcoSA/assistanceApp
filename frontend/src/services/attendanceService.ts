import type { AttendancePerson, AttendanceRegisterRequest, AttendanceRegisterResponse, PublicEvent, PersonnelType } from "../models/Attendance";
import type { ApiResponse } from "../models/ApiResponse";
import { apiClient } from "./apiClient";

export const publicAttendanceService = {
  getEventByToken: async (tokenEvent: string): Promise<ApiResponse<PublicEvent>> => {
    const response = await apiClient.get<ApiResponse<PublicEvent>>(`/public-attendance/${tokenEvent}/event`);
    return response.data;
  },

  getPersonByDocument: async (documentNumber: string): Promise<ApiResponse<AttendancePerson | null>> => {
    const response = await apiClient.get<ApiResponse<AttendancePerson | null>>(`/public-attendance/person/${documentNumber}`);
    return response.data;
  },

  registerAttendance: async (tokenEvent: string, data: AttendanceRegisterRequest): Promise<ApiResponse<AttendanceRegisterResponse>> => {
    const response = await apiClient.post<ApiResponse<AttendanceRegisterResponse>>(`/public-attendance/${tokenEvent}/register`, data);
    return response.data;
  },

  getPersonnelTypes: async (): Promise<ApiResponse<PersonnelType[]>> => {
    const response = await apiClient.get<ApiResponse<PersonnelType[]>>("/public-attendance/personnel-types");
    return response.data;
  },
};