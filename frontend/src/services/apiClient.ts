import { apiConfig } from "../config/apiConfig";
import axios from "axios";

export const apiClient = axios.create({
  baseURL: apiConfig.baseUrl,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});