import {
  Alert,
  Box,
  Button,
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
import PsychologyOutlinedIcon from "@mui/icons-material/PsychologyOutlined";
import SaveOutlinedIcon from "@mui/icons-material/SaveOutlined";
import {
  ResponseModal,
  type ResponseModalSeverity,
} from "../components/ResponseModal";
import type {
  Competency,
  CompetencyCreate,
} from "../models/EventCatalog";
import { competencyService } from "../services/competencyService";
import { getErrorMessage } from "../services/errorService";
import { useCallback, useEffect, useState } from "react";

type ModalMode = "create" | "update";

interface ResponseModalState {
  open: boolean;
  severity: ResponseModalSeverity;
  title: string;
  message: string;
}

const emptyForm: CompetencyCreate = {
  nameCompetency: "",
};

const emptyResponseModal: ResponseModalState = {
  open: false,
  severity: "info",
  title: "",
  message: "",
};

const normalizeCompetencyName = (value: string) =>
  value
    .trim()
    .replace(/\s+/g, " ")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleUpperCase("es-CO");

export function CompetencyPage() {
  const theme = useTheme();
  const [competencies, setCompetencies] = useState<Competency[]>([]);
  const [selectedCompetency, setSelectedCompetency] =
    useState<Competency | null>(null);
  const [competencyToDelete, setCompetencyToDelete] =
    useState<Competency | null>(null);
  const [responseModal, setResponseModal] =
    useState<ResponseModalState>(emptyResponseModal);
  const [form, setForm] = useState<CompetencyCreate>(emptyForm);
  const [modalMode, setModalMode] = useState<ModalMode>("create");
  const [validationError, setValidationError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const isCreate = modalMode === "create";

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

  const loadCompetencies = useCallback(
    async (showError = true) => {
      try {
        setLoading(true);
        const response = await competencyService.getAll();
        setCompetencies(response.result ?? []);
      } catch (error) {
        setCompetencies([]);
        if (showError) {
          showResponseModal(
            "error",
            "Error al cargar competencias",
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
    setSelectedCompetency(null);
    setForm(emptyForm);
    setValidationError("");
    setModalOpen(true);
  };

  const openUpdateModal = (competency: Competency) => {
    setModalMode("update");
    setSelectedCompetency(competency);
    setForm({ nameCompetency: competency.nameCompetency });
    setValidationError("");
    setModalOpen(true);
  };

  const closeModal = () => {
    if (saving) return;
    setModalOpen(false);
    setSelectedCompetency(null);
    setForm(emptyForm);
    setValidationError("");
  };

  const validateForm = () => {
    const nameCompetency = form.nameCompetency.trim().replace(/\s+/g, " ");

    if (!nameCompetency) {
      return "El nombre de la competencia es obligatorio.";
    }

    if (nameCompetency.length > 200) {
      return "El nombre de la competencia no puede superar 200 caracteres.";
    }

    const normalizedName = normalizeCompetencyName(nameCompetency);
    const duplicatedCompetency = competencies.some(
      (competency) =>
        competency.IdCompetency !== selectedCompetency?.IdCompetency &&
        normalizeCompetencyName(competency.nameCompetency) === normalizedName
    );

    if (duplicatedCompetency) {
      return "Ya existe una competencia con este nombre.";
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

      const data: CompetencyCreate = {
        nameCompetency: form.nameCompetency
          .trim()
          .replace(/\s+/g, " ")
          .toLocaleUpperCase("es-CO"),
      };
      const response = isCreate
        ? await competencyService.create(data)
        : await competencyService.update(
            selectedCompetency!.IdCompetency,
            data
          );

      if (!response.isSuccess) {
        throw new Error(
          response.Message ||
            `No se pudo ${isCreate ? "crear" : "actualizar"} la competencia.`
        );
      }

      setModalOpen(false);
      setSelectedCompetency(null);
      setForm(emptyForm);
      await loadCompetencies(false);
      showResponseModal(
        "success",
        isCreate ? "Competencia creada" : "Competencia actualizada",
        response.Message ||
          `Competencia ${
            isCreate ? "creada" : "actualizada"
          } correctamente.`
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
    if (!competencyToDelete) return;

    try {
      setDeleting(true);
      const response = await competencyService.delete(
        competencyToDelete.IdCompetency
      );

      if (!response.isSuccess) {
        throw new Error(
          response.Message || "No se pudo eliminar la competencia."
        );
      }

      setCompetencyToDelete(null);
      await loadCompetencies(false);
      showResponseModal(
        "success",
        "Competencia eliminada",
        response.Message || "Competencia eliminada correctamente."
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
    loadCompetencies();
  }, [loadCompetencies]);

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
        <Stack sx={{ flexDirection: "row", gap: 1.5, alignItems: "center" }}>
          <PsychologyOutlinedIcon
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
              Competencias
            </Typography>
            <Typography color="text.secondary" variant="body2">
              Administra las competencias disponibles para los eventos.
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
          Crear competencia
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
                    Nombre de la competencia
                  </TableCell>
                  <TableCell
                    align="center"
                    sx={{ fontWeight: 700, color: "text.primary", width: 140 }}
                  >
                    Acciones
                  </TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {competencies.map((competency) => (
                  <TableRow key={competency.IdCompetency} hover>
                    <TableCell>{competency.IdCompetency}</TableCell>
                    <TableCell>
                      <Typography
                        sx={{
                          color: "text.primary",
                          fontWeight: 600,
                          overflowWrap: "anywhere",
                        }}
                      >
                        {competency.nameCompetency}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Stack
                        sx={{
                          flexDirection: "row",
                          gap: 0.5,
                          justifyContent: "center",
                        }}
                      >
                        <Tooltip title="Actualizar competencia">
                          <IconButton
                            size="small"
                            onClick={() => openUpdateModal(competency)}
                            sx={{ color: theme.palette.primary.main }}
                          >
                            <EditOutlinedIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>

                        <Tooltip title="Eliminar competencia">
                          <IconButton
                            size="small"
                            onClick={() => setCompetencyToDelete(competency)}
                            sx={{ color: "error.main" }}
                          >
                            <DeleteOutlineOutlinedIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}

                {competencies.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={3} align="center" sx={{ py: 5 }}>
                      No hay competencias para mostrar.
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
          {isCreate ? "Crear competencia" : "Actualizar competencia"}
        </DialogTitle>

        <DialogContent>
          <Stack spacing={2.5} sx={{ mt: 1 }}>
            <Typography color="text.secondary" variant="body2">
              {isCreate
                ? "Ingresa el nombre de la competencia que estará disponible al crear o actualizar eventos."
                : "Modifica el nombre de la competencia seleccionada. El cambio también se verá en los reportes y eventos relacionados."}
            </Typography>

            {validationError && (
              <Alert severity="warning">{validationError}</Alert>
            )}

            <TextField
              label="Nombre de la competencia"
              value={form.nameCompetency}
              disabled={saving}
              required
              fullWidth
              autoFocus
              slotProps={{ htmlInput: { maxLength: 200 } }}
              onChange={(event) =>
                setForm({
                  nameCompetency: event.target.value.toLocaleUpperCase("es-CO"),
                })
              }
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  void handleSave();
                }
              }}
              helperText={`${form.nameCompetency.length}/200 caracteres. Se guardará en mayúsculas.`}
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
        open={Boolean(competencyToDelete)}
        onClose={deleting ? undefined : () => setCompetencyToDelete(null)}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle sx={{ color: "text.primary", fontWeight: 700 }}>
          Eliminar competencia
        </DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            ¿Confirmas que deseas eliminar la competencia{` `}
            <strong>{competencyToDelete?.nameCompetency}</strong>? Esta acción
            no se puede deshacer.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            variant="outlined"
            onClick={() => setCompetencyToDelete(null)}
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
