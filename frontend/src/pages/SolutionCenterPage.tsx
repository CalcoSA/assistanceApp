import { Alert, Box, Button, Chip, CircularProgress, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Switch, TextField } from "@mui/material";
import { ResponseModal, type ResponseModalSeverity, } from "../components/ResponseModal";
import type { SolutionCenter, SolutionCenterCreate  } from "../models/SolutionCenter";
import AddBusinessOutlinedIcon from "@mui/icons-material/AddBusinessOutlined";
import { solutionCenterService } from "../services/solutionCenterService";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import CloseOutlinedIcon from "@mui/icons-material/CloseOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import SaveOutlinedIcon from "@mui/icons-material/SaveOutlined";
import { getErrorMessage } from "../services/errorService";
import { useEffect, useState } from "react";

type ModalMode = "create" | "update";

const emptyForm: SolutionCenterCreate = {
  codeSolutionCenter: "",
  nameSolutionCenter: "",
  statusSolutionCenter: true,
};

interface ResponseModalState {
  open: boolean;
  severity: ResponseModalSeverity;
  title: string;
  message: string;
}

const emptyResponseModal: ResponseModalState = {
  open: false,
  severity: "info",
  title: "",
  message: "",
};

export function SolutionCenterPage() {
  const [responseModal, setResponseModal] = useState<ResponseModalState>(emptyResponseModal);
  const [selectedSolutionCenter, setSelectedSolutionCenter] = useState<SolutionCenter | null>(null);
  const [loadingSolutionCenterId, setLoadingSolutionCenterId] = useState<number | null>(null);
  const [modalMode, setModalMode] = useState<ModalMode>("create");
  const [solutionCenters, setSolutionCenters] = useState<SolutionCenter[]>([]);
  const [form, setForm] = useState<SolutionCenterCreate>(emptyForm);
  const [validationError, setValidationError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const isCreate = modalMode === "create";

  const showResponseModal = (severity: ResponseModalSeverity, title: string, message: string) => {
    setResponseModal({
      open: true,
      severity,
      title,
      message,
    });
  };

  const closeResponseModal = () => {
    setResponseModal((prev) => ({
      ...prev,
      open: false,
    }));
  };

  const loadSolutionCenters = async (showError = true) => {
    try {
      setLoading(true);
      const response = await solutionCenterService.getAll();
      setSolutionCenters(response.result ?? []);
    } catch (err) {
      setSolutionCenters([]);
      if (showError) {
        showResponseModal(
          "error",
          "Error al cargar",
          getErrorMessage(err)
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = () => {
    setValidationError("");
    setSelectedSolutionCenter(null);
    setForm(emptyForm);
    setModalMode("create");
    setModalOpen(true);
  };

  const openUpdateModal = async (idSolutionCenter: number) => {
    try {
      setValidationError("");
      setLoadingSolutionCenterId(idSolutionCenter);
      const response = await solutionCenterService.getById(idSolutionCenter);
      if (!response.isSuccess || !response.result) {
        showResponseModal(
          "error",
          "No se pudo obtener",
          response.Message || "No se pudo obtener el centro de soluciones o punto de venta."
        );
        return;
      }
      setSelectedSolutionCenter(response.result);
      setForm({
        codeSolutionCenter: response.result.codeSolutionCenter,
        nameSolutionCenter: response.result.nameSolutionCenter,
        statusSolutionCenter: response.result.statusSolutionCenter,
      });
      setModalMode("update");
      setModalOpen(true);
    } catch (err) {
      showResponseModal(
        "error",
        "Error al consultar",
        getErrorMessage(err)
      );
    } finally {
      setLoadingSolutionCenterId(null);
    }
  };

  const closeModal = () => {
    if (saving) return;
    setModalOpen(false);
    setSelectedSolutionCenter(null);
    setForm(emptyForm);
    setValidationError("");
  };

  const handleSubmitSolutionCenter = async () => {
    try {
      const codeSolutionCenter = form.codeSolutionCenter.trim();
      const nameSolutionCenter = form.nameSolutionCenter.trim();
      if (!codeSolutionCenter) {
        setValidationError("El código del centro de soluciones o punto de venta es obligatorio.");
        return;
      }
      if (!nameSolutionCenter) {
        setValidationError("El nombre del centro de soluciones o punto de venta es obligatorio.");
        return;
      }
      setSaving(true);
      setValidationError("");
      const data: SolutionCenterCreate = {
        codeSolutionCenter,
        nameSolutionCenter,
        statusSolutionCenter: form.statusSolutionCenter,
      };
      const response =
        modalMode === "create"
          ? await solutionCenterService.create(data)
          : await solutionCenterService.update(
              selectedSolutionCenter!.IdSolutionCenter,
              data
            );
      if (!response.isSuccess) {
        showResponseModal(
          "error",
          modalMode === "create"
            ? "No se pudo crear"
            : "No se pudo actualizar",
          response.Message ||
            `No se pudo ${
              modalMode === "create" ? "crear" : "actualizar"
            } el centro de soluciones o punto de venta.`
        );
        return;
      }
      setModalOpen(false);
      setSelectedSolutionCenter(null);
      setForm(emptyForm);
      await loadSolutionCenters(false);
      showResponseModal(
        "success",
        modalMode === "create"
          ? "Centro de Soluciones o Punto de venta creado"
          : "Centro de Soluciones o Punto de venta actualizado",
        response.Message ||
          `Centro de Soluciones o Punto de venta ${
            modalMode === "create" ? "creado" : "actualizado"
          } correctamente.`
      );
    } catch (err) {
      showResponseModal(
        "error",
        "Error en la operación",
        getErrorMessage(err)
      );
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    loadSolutionCenters();
  }, []);

  return (
    <Stack spacing={3}>
      <Stack sx={{ display: "flex", flexDirection: "row", justifyContent: "space-between", alignItems: "center", }}>
        <Box>
          <Stack sx={{ display: "flex", flexDirection: "row", gap: 1.5, alignItems: "center", }}>
            <BusinessOutlinedIcon sx={{ color: "#4B2E1F", fontSize: 30 }} />
            <Typography sx={{ color: "#4B2E1F", fontSize: 26, fontWeight: 700, }}>
              Centro de Soluciones
            </Typography>
          </Stack>
        </Box>

        <Button
          variant="outlined"
          startIcon={<AddBusinessOutlinedIcon />}
          onClick={openCreateModal}
          disabled={loading || saving}
          sx={{ borderColor: "#8B6A55", color: "#4B2E1F", "&:hover": { borderColor: "#4B2E1F", bgcolor: "rgba(75, 46, 31, 0.05)", },}}>
          Crear centro de soluciones
        </Button>
      </Stack>

      <Paper
        elevation={0}
        sx={{ border: "1px solid #E0CDBB", borderRadius: 2, overflow: "hidden", }}>
        {loading ? (
          <Box sx={{ py: 6, display: "flex", justifyContent: "center", }}>
            <CircularProgress sx={{ color: "#4B2E1F" }} />
          </Box>
        ) : (
          <Table>

            <TableHead>
              <TableRow sx={{ bgcolor: "#F7E8D8", }}>
                <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                  ID
                </TableCell>
                <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                  Código
                </TableCell>
                <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                  Centro de Soluciones
                </TableCell>
                <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                  Estado
                </TableCell>
                <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }} align="center">
                </TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {solutionCenters.map((item) => {
                const isLoadingThisRow = loadingSolutionCenterId === item.IdSolutionCenter;
                return (
                  <TableRow key={item.IdSolutionCenter} hover>
                    <TableCell>{item.IdSolutionCenter}</TableCell>
                    <TableCell>{item.codeSolutionCenter}</TableCell>
                    <TableCell>{item.nameSolutionCenter}</TableCell>
                    <TableCell>
                      <Chip
                        label={item.statusSolutionCenter ? "Activo" : "Inactivo"}
                        size="small"
                        sx={{ bgcolor: item.statusSolutionCenter ? "#E8F5E9" : "#FFEBEE", color: item.statusSolutionCenter ? "#2E7D32" : "#C62828", fontWeight: 600, }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={ isLoadingThisRow ? ( <CircularProgress size={16} /> ) : ( <EditOutlinedIcon /> ) }
                        onClick={() => openUpdateModal(item.IdSolutionCenter)}
                        disabled={saving || loadingSolutionCenterId !== null}
                        sx={{ borderColor: "#8B6A55", color: "#4B2E1F", textTransform: "none", fontWeight: 600, "&:hover": { borderColor: "#4B2E1F", bgcolor: "rgba(75, 46, 31, 0.05)", },}}>
                        { isLoadingThisRow ? "Cargando..." : "Actualizar" }
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}

              {solutionCenters.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ py: 4 }}>
                    No hay centro de soluciones para mostrar.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </Paper>

      <Dialog open={modalOpen} onClose={saving ? undefined : closeModal} fullWidth maxWidth="sm">
        <DialogTitle sx={{ display: "flex", alignItems: "center", gap: 1, color: "#4B2E1F", fontWeight: 700, }}>
          {isCreate ? <AddBusinessOutlinedIcon /> : <EditOutlinedIcon />}
          {isCreate ? "Crear centro de soluciones" : "Actualizar centro de soluciones"}
        </DialogTitle>

        <DialogContent>
          
          <Stack spacing={2.5} sx={{ mt: 1 }}>
            <Typography sx={{ color: "#6B4A3A", fontSize: 14 }}>
              {isCreate
                ? "Completa la información para registrar un centro de soluciones."
                : "Modifica la información del centro de soluciones seleccionado."}
            </Typography>

            {validationError && (
              <Alert severity="warning">{validationError}</Alert>
            )}

            <TextField
              label="Código"
              value={form.codeSolutionCenter}
              disabled={saving}
              fullWidth
              required
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  codeSolutionCenter: event.target.value,
                }))
              }
            />

            <TextField
              label="Nombre centro de soluciones"
              value={form.nameSolutionCenter}
              disabled={saving}
              fullWidth
              required
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  nameSolutionCenter: event.target.value,
                }))
              }
            />

            <FormControlLabel
              control={
                <Switch
                  checked={form.statusSolutionCenter}
                  disabled={saving}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      statusSolutionCenter: event.target.checked,
                    }))
                  }
                />
              }
              label={form.statusSolutionCenter ? "Activo" : "Inactivo"}
            />
          </Stack>

        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            variant="outlined"
            startIcon={<CloseOutlinedIcon />}
            onClick={closeModal}
            disabled={saving}
            sx={{ borderColor: "#8B6A55", color: "#4B2E1F", textTransform: "none", fontWeight: 600, "&:hover": { borderColor: "#4B2E1F", bgcolor: "rgba(75, 46, 31, 0.05)", },}}>
            Cancelar
          </Button>

          <Button
            variant="contained"
            startIcon={<SaveOutlinedIcon />}
            onClick={handleSubmitSolutionCenter}
            disabled={saving}
            sx={{ bgcolor: "#4B2E1F", color: "#FFFFFF", textTransform: "none", fontWeight: 600, "&:hover": { bgcolor: "#3A2318", },}}>
            {saving ? "Guardando..." : isCreate ? "Crear" : "Actualizar"}
          </Button>
        </DialogActions>
      </Dialog>
      <ResponseModal
        open={responseModal.open}
        severity={responseModal.severity}
        title={responseModal.title}
        message={responseModal.message}
        onClose={closeResponseModal}
      />
    </Stack>
  );
}