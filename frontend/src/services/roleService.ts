import type { Role, RoleCreate, RoleUpdate } from "../models/Role";
import type { ApiResponse } from "../models/ApiResponse";
import type { MenuOption } from "../models/MenuOption";
import { apiClient } from "./apiClient";

export const roleService = {
  async getAll(): Promise<ApiResponse<Role[]>> {
    const response = await apiClient.get<ApiResponse<Role[]>>("/role/");
    return response.data;
  },

  async getMenuOptions(): Promise<ApiResponse<MenuOption[]>> {
    const response = await apiClient.get<ApiResponse<MenuOption[]>>("/menu-option/");
    return response.data;
  },

  async getMenuOptionsByRole(roleId: number): Promise<ApiResponse<MenuOption[]>> {
    const response = await apiClient.get<ApiResponse<MenuOption[]>>(`/role/${roleId}/menu-options`);
    return response.data;
  },

  async create(data: RoleCreate): Promise<ApiResponse<Role>> {
    const response = await apiClient.post<ApiResponse<Role>>("/role/", data);
    return response.data;
  },

  async update(roleId: number, data: RoleUpdate): Promise<ApiResponse<Role>> {
    const response = await apiClient.put<ApiResponse<Role>>(`/role/${roleId}`, data);
    return response.data;
  },
};