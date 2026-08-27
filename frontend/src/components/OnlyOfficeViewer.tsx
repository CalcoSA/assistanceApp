import { Alert, Box, CircularProgress, Stack, Typography } from "@mui/material";
import type { OnlyOfficeConfig } from "../models/OnlyOffice";
import { useEffect, useId, useState } from "react";


interface OnlyOfficeEditorInstance {
  destroyEditor?: () => void;
}

interface OnlyOfficeErrorEvent {
  data?: {
    errorCode?: number;
    errorDescription?: string;
  };
}

interface OnlyOfficeViewerProps {
  documentServerUrl: string;
  config: OnlyOfficeConfig;
}

declare global {
  interface Window {
    DocsAPI?: {
      DocEditor: new (
        elementId: string,
        config: Record<string, unknown>
      ) => OnlyOfficeEditorInstance;
    };
  }
}

const apiLoadPromises = new Map<string, Promise<void>>();

const loadOnlyOfficeApi = (documentServerUrl: string): Promise<void> => {
  if (window.DocsAPI?.DocEditor) {
    return Promise.resolve();
  }

  const normalizedUrl = documentServerUrl.replace(/\/$/, "");
  const scriptUrl = `${normalizedUrl}/web-apps/apps/api/documents/api.js`;
  const currentPromise = apiLoadPromises.get(scriptUrl);

  if (currentPromise) {
    return currentPromise;
  }

  const loadPromise = new Promise<void>((resolve, reject) => {
    const existingScript = document.querySelector<HTMLScriptElement>(
      `script[data-onlyoffice-api="${scriptUrl}"]`
    );
    const script = existingScript ?? document.createElement("script");

    const handleLoad = () => {
      if (window.DocsAPI?.DocEditor) {
        resolve();
      } else {
        script.remove();
        reject(new Error("OnlyOffice no expuso su API de documentos."));
      }
    };
    const handleError = () => {
      script.remove();
      reject(new Error("No fue posible conectar con el servidor de OnlyOffice."));
    };

    script.addEventListener("load", handleLoad, { once: true });
    script.addEventListener("error", handleError, { once: true });

    if (!existingScript) {
      script.src = scriptUrl;
      script.async = true;
      script.dataset.onlyofficeApi = scriptUrl;
      document.head.appendChild(script);
    }
  }).catch((error) => {
    apiLoadPromises.delete(scriptUrl);
    throw error;
  });

  apiLoadPromises.set(scriptUrl, loadPromise);

  return loadPromise;
};


export function OnlyOfficeViewer({
  documentServerUrl,
  config,
}: OnlyOfficeViewerProps) {
  const reactId = useId();
  const editorElementId = `onlyoffice-viewer-${reactId.replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let disposed = false;
    let editor: OnlyOfficeEditorInstance | null = null;

    void loadOnlyOfficeApi(documentServerUrl)
      .then(() => {
        if (disposed || !window.DocsAPI?.DocEditor) {
          return;
        }

        editor = new window.DocsAPI.DocEditor(editorElementId, {
          ...config,
          events: {
            onAppReady: () => {
              if (!disposed) {
                setLoading(false);
              }
            },
            onError: (event: OnlyOfficeErrorEvent) => {
              if (!disposed) {
                const description = event.data?.errorDescription;
                setErrorMessage(
                  description
                    ? `OnlyOffice no pudo abrir el documento: ${description}`
                    : "OnlyOffice no pudo abrir el documento."
                );
                setLoading(false);
              }
            },
          },
        });
      })
      .catch((error: unknown) => {
        if (!disposed) {
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "No fue posible iniciar el visor de OnlyOffice."
          );
          setLoading(false);
        }
      });

    return () => {
      disposed = true;
      editor?.destroyEditor?.();
    };
  }, [config, documentServerUrl, editorElementId]);

  return (
    <Box sx={{ position: "relative", height: "75vh", minHeight: 480 }}>
      {loading && (
        <Stack
          sx={{
            position: "absolute",
            inset: 0,
            zIndex: 1,
            alignItems: "center",
            justifyContent: "center",
            gap: 1.5,
            bgcolor: "#FFFDF8",
          }}
        >
          <CircularProgress sx={{ color: "#4B2E1F" }} />
          <Typography sx={{ color: "#7A6252" }}>
            Preparando vista de solo lectura...
          </Typography>
        </Stack>
      )}

      {errorMessage ? (
        <Alert severity="error" sx={{ mt: 2 }}>
          {errorMessage}
        </Alert>
      ) : (
        <Box id={editorElementId} sx={{ width: "100%", height: "100%" }} />
      )}
    </Box>
  );
}
