import type { ApiResponse } from "../models/ApiResponse";
import type {
  Competency,
  CompetencyCreate,
  CompetencyUpdate,
} from "../models/EventCatalog";
import { apiClient } from "./apiClient";

export const competencyService = {
  async getAll(): Promise<ApiResponse<Competency[]>> {
    const response = await apiClient.get<ApiResponse<Competency[]>>(
      "/competency/"
    );
    return response.data;
  },

  async getById(IdCompetency: number): Promise<ApiResponse<Competency>> {
    const response = await apiClient.get<ApiResponse<Competency>>(
      `/competency/${IdCompetency}`
    );
    return response.data;
  },

  async create(data: CompetencyCreate): Promise<ApiResponse<Competency>> {
    const response = await apiClient.post<ApiResponse<Competency>>(
      "/competency/",
      data
    );
    return response.data;
  },

  async update(
    IdCompetency: number,
    data: CompetencyUpdate
  ): Promise<ApiResponse<Competency>> {
    const response = await apiClient.put<ApiResponse<Competency>>(
      `/competency/${IdCompetency}`,
      data
    );
    return response.data;
  },

  async delete(IdCompetency: number): Promise<ApiResponse<boolean>> {
    const response = await apiClient.delete<ApiResponse<boolean>>(
      `/competency/${IdCompetency}`
    );
    return response.data;
  },
};
