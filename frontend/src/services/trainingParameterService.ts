import type { ApiResponse } from "../models/ApiResponse";
import type {
  TrainingParameter, TrainingParameterCreate, TrainingParameterUpdate,
} from "../models/TrainingParameter";
import { apiClient } from "./apiClient";

const path = "/training-parameters";

export const trainingParameterService = {
  async getAll(isActive?: boolean): Promise<ApiResponse<TrainingParameter[]>> {
    const response = await apiClient.get<ApiResponse<TrainingParameter[]>>(
      `${path}/`, { params: { isActive } },
    );
    return response.data;
  },

  async getById(id: number): Promise<ApiResponse<TrainingParameter>> {
    const response = await apiClient.get<ApiResponse<TrainingParameter>>(`${path}/${id}`);
    return response.data;
  },

  async create(data: TrainingParameterCreate): Promise<ApiResponse<TrainingParameter>> {
    const response = await apiClient.post<ApiResponse<TrainingParameter>>(`${path}/`, data);
    return response.data;
  },

  async createComplete(
    data: Pick<TrainingParameterCreate, "nameTrainingParameter" | "topics">, file: File,
  ): Promise<ApiResponse<TrainingParameter>> {
    const form = new FormData();
    form.append("nameTrainingParameter", data.nameTrainingParameter);
    form.append("topics", JSON.stringify(data.topics));
    form.append("file", file);
    const response = await apiClient.post<ApiResponse<TrainingParameter>>(`${path}/complete`, form);
    return response.data;
  },

  async update(id: number, data: TrainingParameterUpdate): Promise<ApiResponse<TrainingParameter>> {
    const response = await apiClient.put<ApiResponse<TrainingParameter>>(`${path}/${id}`, data);
    return response.data;
  },

  async setStatus(id: number, isActive: boolean): Promise<ApiResponse<TrainingParameter>> {
    const response = await apiClient.patch<ApiResponse<TrainingParameter>>(
      `${path}/${id}/status`, { isActive },
    );
    return response.data;
  },

  async uploadPensum(id: number, file: File): Promise<ApiResponse<TrainingParameter>> {
    const form = new FormData();
    form.append("file", file);
    // Let the browser supply the multipart boundary.
    const response = await apiClient.post<ApiResponse<TrainingParameter>>(`${path}/${id}/pensum`, form);
    return response.data;
  },

  async updatePensum(id: number, file: File): Promise<ApiResponse<TrainingParameter>> {
    const form = new FormData();
    form.append("file", file);
    const response = await apiClient.put<ApiResponse<TrainingParameter>>(`${path}/${id}/pensum`, form);
    return response.data;
  },

  async getPensumAccess(id: number, download = false): Promise<ApiResponse<string>> {
    const response = await apiClient.get<ApiResponse<string>>(
      `${path}/${id}/pensum/access`, { params: { download } },
    );
    return response.data;
  },
};
