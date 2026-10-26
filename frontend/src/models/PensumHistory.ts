export interface PensumVersion {
  IdTrainingParameterVersion: number;
  IdTrainingParameter: number;
  versionNumber: number;
  pensumPathTrainingParameterVersion: string;
  pensumOriginalNameTrainingParameterVersion: string;
  pensumMimeTypeTrainingParameterVersion: string;
  pensumSizeTrainingParameterVersion: number;
  createdAt: string;
  createdByUserLogin: string | null;
  isBaseline: boolean;
  isCurrent: boolean;
  parameterName: string;
}
export interface PensumEventAssociation {
  IdEvent: number;
  titleEvent: string;
  IdTrainingParameter: number | null;
  createdAt: string | null;
}
export interface PensumHistoryItem {
  documentKey: string;
  name: string;
  mime: string | null;
  size: number | null;
  registeredAt: string | null;
  isLocal: boolean;
  versions: PensumVersion[];
  events: PensumEventAssociation[];
  eventCount: number;
  eventId: number | null;
  origins: string[];
}
export interface PensumPage<T> { items: T[]; total: number; page: number; pageSize: number }
