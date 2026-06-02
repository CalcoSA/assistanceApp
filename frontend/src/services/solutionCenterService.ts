import type { SolutionCenter, SolutionCenterCreate, SolutionCenterUpdate } from "../models/SolutionCenter";
import type { ApiResponse } from "../models/ApiResponse";
import { apiClient } from "./apiClient";

export const solutionCenterService = {

  async getAll(): Promise<ApiResponse<SolutionCenter[]>> {
    const response = await apiClient.get<ApiResponse<SolutionCenter[]>>("/solution-center/");
    return response.data;
  },

  async getById(idSolutionCenter: number): Promise<ApiResponse<SolutionCenter>> {
    const response = await apiClient.get<ApiResponse<SolutionCenter>>(`/solution-center/${idSolutionCenter}`);
    return response.data;
  },

  async create(data: SolutionCenterCreate): Promise<ApiResponse<SolutionCenter>> {
    const response = await apiClient.post<ApiResponse<SolutionCenter>>("/solution-center/", data);
    return response.data;
  },

  async update(idSolutionCenter: number, data: SolutionCenterUpdate): Promise<ApiResponse<SolutionCenter>> {
    const response = await apiClient.put<ApiResponse<SolutionCenter>>(`/solution-center/${idSolutionCenter}`, data);
    return response.data;
  },
}