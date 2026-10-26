import { apiClient } from "./apiClient";
import type { ApiResponse } from "../models/ApiResponse";
import type { PensumEventAssociation, PensumHistoryItem, PensumPage, PensumVersion } from "../models/PensumHistory";

export const pensumHistoryService = {
  async getPage(params: { page: number; pageSize: number; search: string; origin: string; versionState: string }) {
    return (await apiClient.get<ApiResponse<PensumPage<PensumHistoryItem>>>("/pensum-history", { params })).data;
  },
  async getVersions(id: number) {
    return (await apiClient.get<ApiResponse<PensumVersion[]>>(`/training-parameters/${id}/versions`)).data;
  },
  async getVersionAccess(version: PensumVersion, download: boolean) {
    return (await apiClient.get<ApiResponse<string>>(
      `/training-parameters/${version.IdTrainingParameter}/versions/${version.IdTrainingParameterVersion}/pensum/access`,
      { params: { download } },
    )).data;
  },
  async getEvents(item: PensumHistoryItem, page: number) {
    return (await apiClient.get<ApiResponse<PensumPage<PensumEventAssociation>>>("/pensum-history/events", {
      params: { versionId: item.versions[0]?.IdTrainingParameterVersion,
        eventId: item.versions.length ? undefined : item.eventId, page, pageSize: 20 },
    })).data;
  },
  async getLocalDocument(eventId: number) {
    return (await apiClient.get<Blob>(`/pensum-history/events/${eventId}/local`, { responseType: "blob" })).data;
  },
};
