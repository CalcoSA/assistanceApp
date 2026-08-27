export interface OnlyOfficeConfig {
  documentType: "word" | "cell" | "slide";
  type: string;
  height: string;
  width: string;
  document: Record<string, unknown>;
  editorConfig: Record<string, unknown>;
  token: string;
}

export interface OnlyOfficePreview {
  documentServerUrl: string;
  config: OnlyOfficeConfig;
}

