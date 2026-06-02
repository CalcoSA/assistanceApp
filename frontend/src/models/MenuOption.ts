export interface MenuOption {
  IdMenuOption: number;
  nameMenuOption: string;
  pathMenuOption: string | null;
  iconMenuOption: string | null;
  parentMenuOption: number | null;
  orderMenuOption: number;
  statusMenuOption: boolean;
}