import type { ApplicationUser, ApplicationUserCreate, ApplicationUserUpdate, WordpressUser, } from "../models/ApplicationUser";
import type { ApiResponse } from "../models/ApiResponse";
import { apiClient } from "./apiClient";

export const applicationUserService = {

  async searchWordpressUsers(search: string): Promise<ApiResponse<WordpressUser[]>> {
    const response = await apiClient.get<ApiResponse<WordpressUser[]>>("/application-user/wordpress-users", { params: { search }, });
    return response.data;
  },

  async getAll(): Promise<ApiResponse<ApplicationUser[]>> {
    const response = await apiClient.get<ApiResponse<ApplicationUser[]>>("/application-user/");
    return response.data;
  },

  async create(data: ApplicationUserCreate): Promise<ApiResponse<ApplicationUser>> {
    const response = await apiClient.post<ApiResponse<ApplicationUser>>("/application-user/", data);
    return response.data;
  },

  async update(idApplicationUser: number, data: ApplicationUserUpdate): Promise<ApiResponse<ApplicationUser>> {
    const response = await apiClient.put<ApiResponse<ApplicationUser>>(`/application-user/${idApplicationUser}`, data);
    return response.data;
  },
};