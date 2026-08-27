import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import CloseOutlinedIcon from "@mui/icons-material/CloseOutlined";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import EmailOutlinedIcon from "@mui/icons-material/EmailOutlined";
import SaveOutlinedIcon from "@mui/icons-material/SaveOutlined";
import TuneOutlinedIcon from "@mui/icons-material/TuneOutlined";
import {
  ResponseModal,
  type ResponseModalSeverity,
} from "../components/ResponseModal";
import {
  EVENT_NOTIFICATION_RECIPIENTS_PARAMETER,
  type Parameter,
  type ParameterCreate,
} from "../models/Parameter";
import { getErrorMessage } from "../services/errorService";
import { parameterService } from "../services/parameterService";
import { useCallback, useEffect, useState } from "react";

type ModalMode = "create" | "update";

interface ResponseModalState {
  open: boolean;
  severity: ResponseModalSeverity;
  title: string;
  message: string;
}

const emptyForm: ParameterCreate = {
  nameParameter: "",
  valueParameter: "",
};

const emptyResponseModal: ResponseModalState = {
  open: false,
  severity: "info",
  title: "",
  message: "",
};

const emailPattern = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;

const isRecipientParameter = (nameParameter: string) =>
  nameParameter.trim().toUpperCase() ===
  EVENT_NOTIFICATION_RECIPIENTS_PARAMETER;

const splitRecipients = (valueParameter: string) =>
  Array.from(
    new Set(
      valueParameter
        .split(/[,;\n\r]+/)
        .map((value) => value.trim().toLowerCase())
        .filter(Boolean)
    )
  );

export function ParameterPage() {
  const theme = useTheme();
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [selectedParameter, setSelectedParameter] =
    useState<Parameter | null>(null);
  const [parameterToDelete, setParameterToDelete] =
    useState<Parameter | null>(null);
  const [responseModal, setResponseModal] =
    useState<ResponseModalState>(emptyResponseModal);
  const [form, setForm] = useState<ParameterCreate>(emptyForm);
  const [modalMode, setModalMode] = useState<ModalMode>("create");
  const [validationError, setValidationError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const isCreate = modalMode === "create";
  const currentName = form.nameParameter.trim().toUpperCase();
  const currentValueIsRecipients = isRecipientParameter(currentName);

  const showResponseModal = useCallback(
    (
      severity: ResponseModalSeverity,
      title: string,
      message: string
    ) => {
      setResponseModal({ open: true, severity, title, message });
    },
    []
  );

  const loadParameters = useCallback(
    async (showError = true) => {
      try {
        setLoading(true);
        const response = await parameterService.getAll();
        setParameters(response.result ?? []);
      } catch (error) {
        setParameters([]);
        if (showError) {
          showResponseModal(
            "error",
            "Error al cargar parámetros",
            getErrorMessage(error)
          );
        }
      } finally {
        setLoading(false);
      }
    },
    [showResponseModal]
  );

  const openCreateModal = () => {
    setModalMode("create");
    setSelectedParameter(null);
    setForm(emptyForm);
    setValidationError("");
    setModalOpen(true);
  };

  const openUpdateModal = (parameter: Parameter) => {
    setModalMode("update");
    setSelectedParameter(parameter);
    setForm({
      nameParameter: parameter.nameParameter,
      valueParameter: parameter.valueParameter,
    });
    setValidationError("");
    setModalOpen(true);
  };

  const closeModal = () => {
    if (saving) return;
    setModalOpen(false);
    setSelectedParameter(null);
    setForm(emptyForm);
    setValidationError("");
  };

  const validateForm = () => {
    const nameParameter = form.nameParameter.trim().toUpperCase();
    const valueParameter = form.valueParameter.trim();

    if (!nameParameter) {
      return "El nombre del parámetro es obligatorio.";
    }

    if (!/^[A-Z0-9_]+$/.test(nameParameter)) {
      return "El nombre solo puede contener letras, números y guion bajo.";
    }

    if (!valueParameter) {
      return "El valor del parámetro es obligatorio.";
    }

    if (isRecipientParameter(nameParameter)) {
      const recipients = splitRecipients(valueParameter);

      if (recipients.length === 0) {
        return "Debes configurar al menos un correo destinatario.";
      }

      const invalidRecipient = recipients.find(
        (recipient) => !emailPattern.test(recipient)
      );

      if (invalidRecipient) {
        return `El correo "${invalidRecipient}" no tiene un formato válido.`;
      }
    }

    return "";
  };

  const handleSave = async () => {
    const errorMessage = validateForm();

    if (errorMessage) {
      setValidationError(errorMessage);
      return;
    }

    try {
      setSaving(true);
      setValidationError("");

      const nameParameter = form.nameParameter.trim().toUpperCase();
      const valueParameter = isRecipientParameter(nameParameter)
        ? splitRecipients(form.valueParameter).join(", ")
        : form.valueParameter.trim();

      const response = isCreate
        ? await parameterService.create({ nameParameter, valueParameter })
        : await parameterService.update(selectedParameter!.IdParameter, {
            valueParameter,
          });

      if (!response.isSuccess) {
        throw new Error(
          response.Message ||
            `No se pudo ${isCreate ? "crear" : "actualizar"} el parámetro.`
        );
      }

      setModalOpen(false);
      setSelectedParameter(null);
      setForm(emptyForm);
      await loadParameters(false);
      showResponseModal(
        "success",
        isCreate ? "Parámetro creado" : "Parámetro actualizado",
        response.Message ||
          `Parámetro ${isCreate ? "creado" : "actualizado"} correctamente.`
      );
    } catch (error) {
      showResponseModal(
        "error",
        "Error en la operación",
        getErrorMessage(error)
      );
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!parameterToDelete) return;

    try {
      setDeleting(true);
      const response = await parameterService.delete(
        parameterToDelete.IdParameter
      );

      if (!response.isSuccess) {
        throw new Error(response.Message || "No se pudo eliminar el parámetro.");
      }

      setParameterToDelete(null);
      await loadParameters(false);
      showResponseModal(
        "success",
        "Parámetro eliminado",
        response.Message || "Parámetro eliminado correctamente."
      );
    } catch (error) {
      showResponseModal(
        "error",
        "No se pudo eliminar",
        getErrorMessage(error)
      );
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadParameters();
  }, [loadParameters]);

  return (
    <Stack spacing={3}>
      <Stack
        sx={{
          flexDirection: { xs: "column", sm: "row" },
          justifyContent: "space-between",
          alignItems: { xs: "stretch", sm: "center" },
          gap: 2,
        }}
      >
        <Stack
          sx={{ flexDirection: "row", gap: 1.5, alignItems: "center" }}
        >
          <TuneOutlinedIcon
            sx={{ color: theme.palette.primary.main, fontSize: 30 }}
          />
          <Box>
            <Typography
              sx={{
                color: theme.palette.text.primary,
                fontSize: 26,
                fontWeight: 700,
              }}
            >
              Parámetros
            </Typography>
            <Typography color="text.secondary" variant="body2">
              Configura valores generales utilizados por la aplicación.
            </Typography>
          </Box>
        </Stack>

        <Button
          variant="outlined"
          startIcon={<AddOutlinedIcon />}
          onClick={openCreateModal}
          disabled={loading || saving}
          sx={{
            borderColor: theme.palette.secondary.main,
            color: theme.palette.primary.main,
            "&:hover": {
              borderColor: theme.palette.primary.main,
              bgcolor: "rgba(75, 46, 31, 0.05)",
            },
          }}
        >
          Crear parámetro
        </Button>
      </Stack>

      <Paper
        elevation={0}
        sx={{
          border: `1px solid ${theme.palette.primary.light}`,
          borderRadius: 2,
          overflow: "hidden",
        }}
      >
        {loading ? (
          <Box sx={{ py: 7, display: "flex", justifyContent: "center" }}>
            <CircularProgress color="primary" />
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: theme.palette.primary.light }}>
                  <TableCell sx={{ fontWeight: 700, color: "text.primary" }}>
                    ID
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, color: "text.primary" }}>
                    Nombre del parámetro
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, color: "text.primary" }}>
                    Valor del parámetro
                  </TableCell>
                  <TableCell
                    align="center"
                    sx={{ fontWeight: 700, color: "text.primary" }}
                  >
                    Acciones
                  </TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {parameters.map((parameter) => {
                  const recipientParameter = isRecipientParameter(
                    parameter.nameParameter
                  );
                  const recipients = recipientParameter
                    ? splitRecipients(parameter.valueParameter)
                    : [];

                  return (
                    <TableRow key={parameter.IdParameter} hover>
                      <TableCell>{parameter.IdParameter}</TableCell>
                      <TableCell>
                        <Typography
                          sx={{
                            color: "text.primary",
                            fontWeight: 600,
                            overflowWrap: "anywhere",
                          }}
                        >
                          {parameter.nameParameter}
                        </Typography>
                      </TableCell>
                      <TableCell sx={{ minWidth: 320 }}>
                        {recipientParameter && recipients.length > 0 ? (
                          <Stack
                            sx={{
                              flexDirection: "row",
                              gap: 1,
                              flexWrap: "wrap",
                            }}
                          >
                            {recipients.map((recipient) => (
                              <Chip
                                key={recipient}
                                size="small"
                                icon={<EmailOutlinedIcon />}
                                label={recipient}
                                color={
                                  emailPattern.test(recipient)
                                    ? "default"
                                    : "error"
                                }
                                variant="outlined"
                                sx={{
                                  bgcolor: theme.palette.background.default,
                                  borderColor: emailPattern.test(recipient)
                                    ? theme.palette.primary.light
                                    : undefined,
                                }}
                              />
                            ))}
                          </Stack>
                        ) : (
                          <Typography
                            sx={{
                              color: parameter.valueParameter
                                ? "text.secondary"
                                : "error.main",
                              whiteSpace: "pre-wrap",
                              overflowWrap: "anywhere",
                            }}
                          >
                            {parameter.valueParameter || "Sin valor configurado"}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        <Stack
                          sx={{
                            flexDirection: "row",
                            gap: 0.5,
                            justifyContent: "center",
                          }}
                        >
                          <Tooltip title="Actualizar parámetro">
                            <IconButton
                              size="small"
                              onClick={() => openUpdateModal(parameter)}
                              sx={{ color: theme.palette.primary.main }}
                            >
                              <EditOutlinedIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>

                          <Tooltip
                            title={
                              recipientParameter
                                ? "Este parámetro es requerido por el sistema"
                                : "Eliminar parámetro"
                            }
                          >
                            <span>
                              <IconButton
                                size="small"
                                disabled={recipientParameter}
                                onClick={() => setParameterToDelete(parameter)}
                                sx={{ color: "error.main" }}
                              >
                                <DeleteOutlineOutlinedIcon fontSize="small" />
                              </IconButton>
                            </span>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  );
                })}

                {parameters.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} align="center" sx={{ py: 5 }}>
                      No hay parámetros para mostrar.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      <Dialog
        open={modalOpen}
        onClose={saving ? undefined : closeModal}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            color: theme.palette.text.primary,
            fontWeight: 700,
          }}
        >
          {isCreate ? <AddOutlinedIcon /> : <EditOutlinedIcon />}
          {isCreate ? "Crear parámetro" : "Actualizar parámetro"}
        </DialogTitle>

        <DialogContent>
          <Stack spacing={2.5} sx={{ mt: 1 }}>
            <Typography color="text.secondary" variant="body2">
              {isCreate
                ? "Crea una clave estable y define el valor que utilizará la aplicación."
                : "El nombre es una clave técnica y no se puede modificar; actualiza únicamente su valor."}
            </Typography>

            {validationError && (
              <Alert severity="warning">{validationError}</Alert>
            )}

            <TextField
              label="Nombre del parámetro"
              value={form.nameParameter}
              disabled={!isCreate || saving}
              required
              fullWidth
              onChange={(event) =>
                setForm((previous) => ({
                  ...previous,
                  nameParameter: event.target.value.toUpperCase(),
                }))
              }
              helperText={
                isCreate
                  ? "Usa letras, números y guion bajo. Se guardará en mayúsculas."
                  : "La clave permanece fija para no afectar los procesos que la consumen."
              }
            />

            <TextField
              label={
                currentValueIsRecipients
                  ? "Correos destinatarios adicionales"
                  : "Valor del parámetro"
              }
              value={form.valueParameter}
              disabled={saving}
              required
              fullWidth
              multiline
              minRows={currentValueIsRecipients ? 3 : 2}
              onChange={(event) =>
                setForm((previous) => ({
                  ...previous,
                  valueParameter: event.target.value,
                }))
              }
              helperText={
                currentValueIsRecipients
                  ? "Se enviará también al creador del evento. Separa los correos adicionales por coma, punto y coma o salto de línea."
                  : "Ingresa el valor que utilizará la aplicación."
              }
            />
          </Stack>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            variant="outlined"
            startIcon={<CloseOutlinedIcon />}
            onClick={closeModal}
            disabled={saving}
            color="secondary"
          >
            Cancelar
          </Button>
          <Button
            variant="contained"
            startIcon={
              saving ? (
                <CircularProgress size={17} color="inherit" />
              ) : (
                <SaveOutlinedIcon />
              )
            }
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? "Guardando..." : isCreate ? "Crear" : "Actualizar"}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={Boolean(parameterToDelete)}
        onClose={deleting ? undefined : () => setParameterToDelete(null)}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle sx={{ color: "text.primary", fontWeight: 700 }}>
          Eliminar parámetro
        </DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            ¿Confirmas que deseas eliminar el parámetro{" "}
            <strong>{parameterToDelete?.nameParameter}</strong>? Esta acción no
            se puede deshacer.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            variant="outlined"
            onClick={() => setParameterToDelete(null)}
            disabled={deleting}
            color="secondary"
          >
            Cancelar
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDelete}
            disabled={deleting}
            startIcon={
              deleting ? (
                <CircularProgress size={17} color="inherit" />
              ) : (
                <DeleteOutlineOutlinedIcon />
              )
            }
          >
            {deleting ? "Eliminando..." : "Eliminar"}
          </Button>
        </DialogActions>
      </Dialog>

      <ResponseModal
        open={responseModal.open}
        severity={responseModal.severity}
        title={responseModal.title}
        message={responseModal.message}
        onClose={() =>
          setResponseModal((previous) => ({ ...previous, open: false }))
        }
      />
    </Stack>
  );
}
