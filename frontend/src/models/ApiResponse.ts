export interface ApiResponse<T> {
  isSuccess: boolean;
  Message: string;
  result: T;
}