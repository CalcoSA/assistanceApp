import type {
  Parameter,
  ParameterCreate,
  ParameterUpdate,
} from "../models/Parameter";
import type { ApiResponse } from "../models/ApiResponse";
import { apiClient } from "./apiClient";

export const parameterService = {
  async getAll(): Promise<ApiResponse<Parameter[]>> {
    const response = await apiClient.get<ApiResponse<Parameter[]>>(
      "/parameter/"
    );
    return response.data;
  },

  async getById(IdParameter: number): Promise<ApiResponse<Parameter>> {
    const response = await apiClient.get<ApiResponse<Parameter>>(
      `/parameter/${IdParameter}`
    );
    return response.data;
  },

  async create(data: ParameterCreate): Promise<ApiResponse<Parameter>> {
    const response = await apiClient.post<ApiResponse<Parameter>>(
      "/parameter/",
      data
    );
    return response.data;
  },

  async update(
    IdParameter: number,
    data: ParameterUpdate
  ): Promise<ApiResponse<Parameter>> {
    const response = await apiClient.put<ApiResponse<Parameter>>(
      `/parameter/${IdParameter}`,
      data
    );
    return response.data;
  },

  async delete(IdParameter: number): Promise<ApiResponse<boolean>> {
    const response = await apiClient.delete<ApiResponse<boolean>>(
      `/parameter/${IdParameter}`
    );
    return response.data;
  },
};
