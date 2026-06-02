export interface PublicEvent {
  IdEvent: number;
  titleEvent: string;
  descriptionEvent?: string | null;
  dateEvent: string;
  startTimeEvent: string;
  endTimeEvent: string;
  eventPlace?: string | null;
  facilitatorNameEvent?: string | null;
  attendanceStartDateTime: string;
  attendanceEndDateTime: string;
}

export interface AttendancePerson {
  IdAttendancePerson: number;
  fullNameAttendancePerson: string;
  documentNumberAttendancePerson: string;
  positionAttendancePerson?: string | null;
  IdSolutionCenter?: number | null;
  phoneAttendancePerson?: string | null;
  signaturePathAttendancePerson?: string | null;
}

export interface AttendanceRegisterRequest {
  documentNumberAttendancePerson: string;
  fullNameAttendancePerson: string;
  positionAttendancePerson?: string | null;
  IdSolutionCenter?: number | null;
  IdPersonnelType: number;
  phoneAttendancePerson?: string | null;
  signatureBase64?: string | null;
}

export interface AttendanceRegisterResponse {
  IdAttendance: number;
  IdEvent: number;
  IdAttendancePerson: number;
  attendedPeopleNumber: number;
}

export interface PersonnelType {
  IdPersonnelType: number;
  namePersonnelType: string;
}