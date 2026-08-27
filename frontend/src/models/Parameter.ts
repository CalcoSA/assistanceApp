export const EVENT_NOTIFICATION_RECIPIENTS_PARAMETER =
  "DESTINATARIOS_NOTIFICACION_EVENTO";

export interface Parameter {
  IdParameter: number;
  nameParameter: string;
  valueParameter: string;
}

export interface ParameterCreate {
  nameParameter: string;
  valueParameter: string;
}

export interface ParameterUpdate {
  valueParameter: string;
}
