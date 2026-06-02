import type { Role } from "./Role";

export interface WordpressUser {
  wordpressUserId: number;
  wordpressUserLogin: string;
  wordpressUserEmail: string;
  wordpressDisplayName: string;
}

export interface ApplicationUser {
  IdApplicationUser: number;
  wordpressUserId: number;
  wordpressUserLogin: string;
  statusApplicationUser: boolean;
  roles: Role[];
}

export interface ApplicationUserCreate {
  wordpressUserId: number;
  wordpressUserLogin: string;
  statusApplicationUser: boolean;
  roleIds: number[];
}

export interface ApplicationUserUpdate {
  statusApplicationUser: boolean;
  roleIds: number[];
}