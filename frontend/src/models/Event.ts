import type { SolutionCenter } from "./SolutionCenter";
import type { EventStatus } from "./EventCatalog";

export interface EventTopic {
  IdEventTopic: number;
  IdEvent: number;
  nameEventTopic: string;
}

export interface EventCompetency {
  IdEventCompetency: number;
  IdEvent: number;
  IdCompetency: number;
}

export interface Event {
  IdEvent: number;
  titleEvent: string;
  descriptionEvent?: string | null;
  dateEvent: string;
  durationEvent?: string | null;
  startTimeEvent: string;
  endTimeEvent: string;
  IdSolutionCenter?: number | null;
  solutionCenter?: SolutionCenter | null;
  IdAssistanceReason?: number | null;
  IdSpecificTrainingProgram?: number | null;
  IdEventCategory?: number | null;
  IdEventStatus: number;
  eventStatus?: EventStatus | null;
  facilitatorNameEvent?: string | null;
  facilitatorTypeEvent?: "INTERNO" | "EXTERNO" | null;
  facilitatorCompanyEvent?: string | null;
  facilitatorPositionEvent?: string | null;
  secondFacilitatorNameEvent?: string | null;
  secondFacilitatorTypeEvent?: "INTERNO" | "EXTERNO" | null;
  secondFacilitatorCompanyEvent?: string | null;
  secondFacilitatorPositionEvent?: string | null;
  scheduledPeopleNumber?: number | null;
  attendedPeopleNumber?: number | null;
  observationsEvent?: string | null;
  eventPlace?: string | null;
  attendanceStartDateTime: string;
  attendanceEndDateTime: string;
  tokenEvent: string;
  publicUrlEvent?: string | null;
  qrPathEvent?: string | null;
  pensumOriginalNameEvent?: string | null;
  pensumPathEvent?: string | null;
  pensumMimeTypeEvent?: string | null;
  pensumSizeEvent?: number | null;
  isPaidTrainingEvent: boolean;
  isNewStaffInductionEvent?: boolean | null;
  createdByUserLogin: string;
  updatedByUserLogin?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  notificationEmailSent?: boolean | null;
  notificationMessage?: string | null;
  topics: EventTopic[];
  competencies: EventCompetency[];
}

export interface EventCreateRequest {
  titleEvent: string;
  descriptionEvent?: string | null;
  dateEvent: string;
  durationEvent?: string | null;
  startTimeEvent: string;
  endTimeEvent: string;
  IdSolutionCenter?: number | null;
  IdAssistanceReason?: number | null;
  IdSpecificTrainingProgram?: number | null;
  IdEventCategory?: number | null;
  facilitatorNameEvent?: string | null;
  facilitatorTypeEvent?: "INTERNO" | "EXTERNO" | null;
  facilitatorCompanyEvent?: string | null;
  facilitatorPositionEvent?: string | null;
  secondFacilitatorNameEvent?: string | null;
  secondFacilitatorTypeEvent?: "INTERNO" | "EXTERNO" | null;
  secondFacilitatorCompanyEvent?: string | null;
  secondFacilitatorPositionEvent?: string | null;
  scheduledPeopleNumber?: number | null;
  isPaidTrainingEvent: boolean | null;
  isNewStaffInductionEvent?: boolean;
  observationsEvent?: string | null;
  eventPlace?: string | null;
  topics: string[];
  competencies: number[];
}

export interface EventQr {
  IdEvent: number;
  tokenEvent: string;
  publicUrlEvent?: string | null;
  qrPathEvent?: string | null;
}

export interface EventAttendancePerson {
  IdAttendancePerson: number;
  fullNameAttendancePerson: string;
  documentNumberAttendancePerson: string;
  positionAttendancePerson?: string | null;
  IdSolutionCenter?: number | null;
  phoneAttendancePerson?: string | null;
  signaturePathAttendancePerson?: string | null;
}

export interface EventAttendance {
  IdAttendance: number;
  IdEvent: number;
  IdAttendancePerson: number;
  ipAddressAttendance?: string | null;
  userAgentAttendance?: string | null;
  createdAt?: string | null;
  attendancePerson?: EventAttendancePerson | null;
}

export interface EventPaginatedResult {
  items: Event[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface EventFilterRequest {
  page: number;
  pageSize: number;
  statusFilter?: string;
}
