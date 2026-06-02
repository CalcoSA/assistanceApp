export interface SolutionCenter {
  IdSolutionCenter: number;
  codeSolutionCenter: string;
  nameSolutionCenter: string;
  statusSolutionCenter: boolean;
}

export interface SolutionCenterCreate {
  codeSolutionCenter: string;
  nameSolutionCenter: string;
  statusSolutionCenter?: boolean;
}

export type SolutionCenterUpdate = Partial<SolutionCenterCreate>;