export interface ParameterTopic {
  IdParameterTopic: number;
  IdTrainingParameter: number;
  nameParameterTopic: string;
  sortOrder: number;
}

export interface TrainingParameter {
  IdTrainingParameter: number;
  nameTrainingParameter: string;
  topics: ParameterTopic[];
  isActive: boolean;
  pensumPathTrainingParameter: string | null;
  pensumOriginalNameTrainingParameter: string | null;
  pensumMimeTypeTrainingParameter: string | null;
  pensumSizeTrainingParameter: number | null;
  createdAt: string;
  updatedAt: string | null;
}

export interface TrainingParameterCreate {
  nameTrainingParameter: string;
  topics: string[];
  isActive: false;
}

export interface TrainingParameterUpdate {
  nameTrainingParameter?: string;
  topics?: string[];
  isActive?: boolean;
}
