export interface Role {
  IdRole: number;
  nameRole: string;
  statusRole: boolean;
}

export interface RoleCreate {
  nameRole: string;
  statusRole: boolean;
  menuOptionIds: number[];
}

export type RoleUpdate = Partial<RoleCreate>;