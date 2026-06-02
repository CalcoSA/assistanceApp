import { Alert, Box, Button, Checkbox, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, FormControl, FormControlLabel, InputLabel, ListItemText, MenuItem, OutlinedInput, Paper, Select, Stack, Switch, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography, } from "@mui/material";
import AdminPanelSettingsOutlinedIcon from "@mui/icons-material/AdminPanelSettingsOutlined";
import { ResponseModal, type ResponseModalSeverity, } from "../components/ResponseModal";
import PersonAddAlt1OutlinedIcon from "@mui/icons-material/PersonAddAlt1Outlined";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import type { Role, RoleCreate, RoleUpdate } from "../models/Role";
import CloseOutlinedIcon from "@mui/icons-material/CloseOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import SaveOutlinedIcon from "@mui/icons-material/SaveOutlined";
import { getErrorMessage } from "../services/errorService";
import type { MenuOption } from "../models/MenuOption";
import { roleService } from "../services/roleService";
import { useEffect, useState } from "react";

type ModalMode = "create" | "update";

interface RoleForm {
  nameRole: string;
  statusRole: boolean;
  menuOptionIds: number[];
}

interface ResponseModalState {
  open: boolean;
  severity: ResponseModalSeverity;
  title: string;
  message: string;
}

const emptyForm: RoleForm = {
  nameRole: "",
  statusRole: true,
  menuOptionIds: [],
};

const emptyResponseModal: ResponseModalState = {
  open: false,
  severity: "info",
  title: "",
  message: "",
};

export function RolePage() {
  const [responseModal, setResponseModal] = useState<ResponseModalState>(emptyResponseModal);
  const [menuOptionsModalOpen, setMenuOptionsModalOpen] = useState(false);
  const [loadingRoleId, setLoadingRoleId] = useState<number | null>(null);
  const [allMenuOptions, setAllMenuOptions] = useState<MenuOption[]>([]);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [loadingMenuOptions, setLoadingMenuOptions] = useState(false);
  const [menuOptions, setMenuOptions] = useState<MenuOption[]>([]);
  const [roleFormModalOpen, setRoleFormModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<ModalMode>("create");
  const [validationError, setValidationError] = useState("");
  const [form, setForm] = useState<RoleForm>(emptyForm);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const isCreate = modalMode === "create";
  const protectedRoleNames = ["administrador", "formador"];

  const normalizeRoleName = (value?: string | null) => {
    return value?.trim().toLowerCase() ?? "";
  };

  const isProtectedRoleName = (value?: string | null) => {
    return protectedRoleNames.includes(normalizeRoleName(value));
  };

  const isProtectedRole = !isCreate && isProtectedRoleName(selectedRole?.nameRole);

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

  const loadRoles = async () => {
    try {
      setLoading(true);
      const response = await roleService.getAll();
      setRoles(response.result ?? []);
    } catch (err) {
      setRoles([]);
      showResponseModal("error", "Error al cargar", getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const loadAllMenuOptions = async () => {
    try {
      const response = await roleService.getMenuOptions();
      setAllMenuOptions(response.result ?? []);
    } catch (err) {
      setAllMenuOptions([]);
      showResponseModal(
        "error",
        "Error al cargar opciones de menú",
        getErrorMessage(err)
      );
    }
  };

  const getMenuOptionLabel = (idMenuOption: number) => {
    const option = allMenuOptions.find(
      (item) => item.IdMenuOption === idMenuOption
    );

    return option?.nameMenuOption ?? String(idMenuOption);
  };

  const openMenuOptionsModal = async (role: Role) => {
    try {
      setSelectedRole(role);
      setMenuOptions([]);
      setMenuOptionsModalOpen(true);
      setLoadingRoleId(role.IdRole);
      setLoadingMenuOptions(true);
      const response = await roleService.getMenuOptionsByRole(role.IdRole);
      setMenuOptions(response.result ?? []);
    } catch (err) {
      setMenuOptions([]);
      showResponseModal(
        "error",
        "Error al consultar permisos",
        getErrorMessage(err)
      );
    } finally {
      setLoadingRoleId(null);
      setLoadingMenuOptions(false);
    }
  };

  const closeMenuOptionsModal = () => {
    if (loadingMenuOptions) return;
    setMenuOptionsModalOpen(false);
    setSelectedRole(null);
    setMenuOptions([]);
  };

  const openCreateModal = () => {
    setValidationError("");
    setSelectedRole(null);
    setForm(emptyForm);
    setModalMode("create");
    setRoleFormModalOpen(true);
  };

  const openUpdateModal = async (role: Role) => {
    try {
      setValidationError("");
      setSelectedRole(role);
      setLoadingRoleId(role.IdRole);
      const response = await roleService.getMenuOptionsByRole(role.IdRole);
      const roleMenuOptionIds = (response.result ?? []).map((item) => item.IdMenuOption);
      setForm({
        nameRole: role.nameRole,
        statusRole: role.statusRole,
        menuOptionIds: roleMenuOptionIds,
      });
      setModalMode("update");
      setRoleFormModalOpen(true);
    } catch (err) {
      showResponseModal(
        "error",
        "Error al consultar rol",
        getErrorMessage(err)
      );
    } finally {
      setLoadingRoleId(null);
    }
  };

  const closeRoleFormModal = () => {
    if (saving) return;
    setRoleFormModalOpen(false);
    setSelectedRole(null);
    setForm(emptyForm);
    setValidationError("");
  };

  const handleSubmitRole = async () => {
    try {
      const nameRole = form.nameRole.trim();
      if (!nameRole) {
        setValidationError("El nombre del rol es obligatorio.");
        return;
      }
      if (form.menuOptionIds.length === 0) {
        setValidationError("Debes seleccionar al menos una opción de menú.");
        return;
      }
      setSaving(true);
      setValidationError("");
      const response = isCreate
      ? await roleService.create({
          nameRole,
          statusRole: form.statusRole,
          menuOptionIds: form.menuOptionIds,
        } as RoleCreate)
      : await roleService.update(
          selectedRole!.IdRole,
          {
            ...(isProtectedRole ? {} : { nameRole }),
            statusRole: form.statusRole,
            menuOptionIds: form.menuOptionIds,
          } as RoleUpdate
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
            } el rol.`
        );
        return;
      }

      setRoleFormModalOpen(false);
      setSelectedRole(null);
      setForm(emptyForm);

      await loadRoles();

      showResponseModal(
        "success",
        modalMode === "create" ? "Rol creado" : "Rol actualizado",
        response.Message ||
          `Rol ${
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
    loadRoles();
    loadAllMenuOptions();
  }, []);

  return (
    <Stack spacing={3}>
      <Stack
        sx={{
          display: "flex",
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Stack
          sx={{
            display: "flex",
            flexDirection: "row",
            gap: 1.5,
            alignItems: "center",
          }}
        >
          <AdminPanelSettingsOutlinedIcon
            sx={{ color: "#4B2E1F", fontSize: 30 }}
          />

          <Typography
            sx={{
              color: "#4B2E1F",
              fontSize: 26,
              fontWeight: 700,
            }}
          >
            Roles
          </Typography>
        </Stack>

        <Button
          variant="outlined"
          startIcon={<PersonAddAlt1OutlinedIcon />}
          onClick={openCreateModal}
          disabled={loading || saving}
          sx={{
            borderColor: "#8B6A55",
            color: "#4B2E1F",
            textTransform: "none",
            fontWeight: 600,
            "&:hover": {
              borderColor: "#4B2E1F",
              bgcolor: "rgba(75, 46, 31, 0.05)",
            },
          }}
        >
          Crear rol
        </Button>
      </Stack>

      <Paper
        elevation={0}
        sx={{
          border: "1px solid #E0CDBB",
          borderRadius: 2,
          overflow: "hidden",
        }}
      >
        {loading ? (
          <Box
            sx={{
              py: 6,
              display: "flex",
              justifyContent: "center",
            }}
          >
            <CircularProgress sx={{ color: "#4B2E1F" }} />
          </Box>
        ) : (
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: "#F7E8D8" }}>
                <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                  ID
                </TableCell>

                <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                  Nombre
                </TableCell>

                <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                  Estado
                </TableCell>

                <TableCell
                  align="center"
                  sx={{ fontWeight: 700, color: "#4B2E1F" }}
                />
              </TableRow>
            </TableHead>

            <TableBody>
              {roles.map((item) => {
                const isLoadingThisRow = loadingRoleId === item.IdRole;

                return (
                  <TableRow key={item.IdRole} hover>
                    <TableCell>{item.IdRole}</TableCell>

                    <TableCell>{item.nameRole}</TableCell>

                    <TableCell>
                      <Chip
                        label={item.statusRole ? "Activo" : "Inactivo"}
                        size="small"
                        sx={{
                          bgcolor: item.statusRole ? "#E8F5E9" : "#FFEBEE",
                          color: item.statusRole ? "#2E7D32" : "#C62828",
                          fontWeight: 600,
                        }}
                      />
                    </TableCell>

                    <TableCell align="center">
                      <Stack
                        sx={{
                          display: "flex",
                          flexDirection: "row",
                          justifyContent: "center",
                          gap: 1,
                        }}
                      >
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={
                            isLoadingThisRow ? (
                              <CircularProgress size={16} />
                            ) : (
                              <VisibilityOutlinedIcon />
                            )
                          }
                          onClick={() => openMenuOptionsModal(item)}
                          disabled={loadingRoleId !== null || saving}
                          sx={{
                            borderColor: "#8B6A55",
                            color: "#4B2E1F",
                            textTransform: "none",
                            fontWeight: 600,
                            "&:hover": {
                              borderColor: "#4B2E1F",
                              bgcolor: "rgba(75, 46, 31, 0.05)",
                            },
                          }}
                        >
                          {isLoadingThisRow ? "Cargando..." : "Visualizar"}
                        </Button>

                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<EditOutlinedIcon />}
                          onClick={() => openUpdateModal(item)}
                          disabled={loadingRoleId !== null || saving}
                          sx={{
                            borderColor: "#8B6A55",
                            color: "#4B2E1F",
                            textTransform: "none",
                            fontWeight: 600,
                            "&:hover": {
                              borderColor: "#4B2E1F",
                              bgcolor: "rgba(75, 46, 31, 0.05)",
                            },
                          }}
                        >
                          Actualizar
                        </Button>
                      </Stack>
                    </TableCell>
                  </TableRow>
                );
              })}

              {roles.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ py: 4 }}>
                    No hay roles para mostrar.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </Paper>

      <Dialog
        open={roleFormModalOpen}
        onClose={saving ? undefined : closeRoleFormModal}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            color: "#4B2E1F",
            fontWeight: 700,
          }}
        >
          {isCreate ? <PersonAddAlt1OutlinedIcon /> : <EditOutlinedIcon />}
          {isCreate ? "Crear rol" : "Actualizar rol"}
        </DialogTitle>

        <DialogContent>
          <Stack spacing={2.5} sx={{ mt: 1 }}>
            <Typography sx={{ color: "#6B4A3A", fontSize: 14 }}>
              {isCreate
                ? "Completa la información para crear un nuevo rol."
                : "Modifica la información del rol seleccionado."}
            </Typography>

            {validationError && (
              <Alert severity="warning">{validationError}</Alert>
            )}

            <TextField
              label="Nombre del rol"
              value={form.nameRole}
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  nameRole: event.target.value,
                }))
              }
              fullWidth
              disabled={saving || isProtectedRole}
              helperText={
                isProtectedRole
                  ? "El nombre de este rol no se puede modificar."
                  : ""
              }
            />

            <FormControl fullWidth disabled={saving}>
              <InputLabel id="menu-options-label">
                Opciones del menú
              </InputLabel>

              <Select
                labelId="menu-options-label"
                multiple
                value={form.menuOptionIds}
                input={<OutlinedInput label="Opciones del menú" />}
                renderValue={(selected) =>
                  selected.map((id) => getMenuOptionLabel(Number(id))).join(", ")
                }
                onChange={(event) => {
                  const value = event.target.value;

                  setForm((prev) => ({
                    ...prev,
                    menuOptionIds:
                      typeof value === "string"
                        ? value.split(",").map(Number)
                        : value.map(Number),
                  }));
                }}
              >
                {allMenuOptions.map((item) => (
                  <MenuItem
                    key={item.IdMenuOption}
                    value={item.IdMenuOption}
                  >
                    <Checkbox
                      checked={form.menuOptionIds.includes(item.IdMenuOption)}
                    />

                    <ListItemText
                      primary={item.nameMenuOption}
                      secondary={item.pathMenuOption ?? "Menú principal"}
                    />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Switch
                  checked={form.statusRole}
                  disabled={saving}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      statusRole: event.target.checked,
                    }))
                  }
                />
              }
              label={form.statusRole ? "Activo" : "Inactivo"}
            />
          </Stack>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            variant="outlined"
            startIcon={<CloseOutlinedIcon />}
            onClick={closeRoleFormModal}
            disabled={saving}
            sx={{
              borderColor: "#8B6A55",
              color: "#4B2E1F",
              textTransform: "none",
              fontWeight: 600,
              "&:hover": {
                borderColor: "#4B2E1F",
                bgcolor: "rgba(75, 46, 31, 0.05)",
              },
            }}
          >
            Cancelar
          </Button>

          <Button
            variant="contained"
            startIcon={<SaveOutlinedIcon />}
            onClick={handleSubmitRole}
            disabled={saving}
            sx={{
              bgcolor: "#4B2E1F",
              color: "#FFFFFF",
              textTransform: "none",
              fontWeight: 600,
              "&:hover": {
                bgcolor: "#3A2318",
              },
            }}
          >
            {saving ? "Guardando..." : isCreate ? "Crear" : "Actualizar"}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={menuOptionsModalOpen}
        onClose={loadingMenuOptions ? undefined : closeMenuOptionsModal}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            color: "#4B2E1F",
            fontWeight: 700,
          }}
        >
          <VisibilityOutlinedIcon />
          Permisos del rol: {selectedRole?.nameRole ?? ""}
        </DialogTitle>

        <DialogContent>
          {loadingMenuOptions ? (
            <Box
              sx={{
                py: 6,
                display: "flex",
                justifyContent: "center",
              }}
            >
              <CircularProgress sx={{ color: "#4B2E1F" }} />
            </Box>
          ) : (
            <Paper
              elevation={0}
              sx={{
                border: "1px solid #E0CDBB",
                borderRadius: 2,
                overflow: "hidden",
                mt: 1,
              }}
            >
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: "#F7E8D8" }}>
                    <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                      Opción
                    </TableCell>

                    <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                      Ruta
                    </TableCell>

                    <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                      Estado
                    </TableCell>
                  </TableRow>
                </TableHead>

                <TableBody>
                  {menuOptions.map((item) => (
                    <TableRow key={item.IdMenuOption} hover>
                      <TableCell>{item.nameMenuOption}</TableCell>

                      <TableCell>
                        {item.pathMenuOption ?? "Menú principal"}
                      </TableCell>

                      <TableCell>
                        <Chip
                          label={item.statusMenuOption ? "Activo" : "Inactivo"}
                          size="small"
                          sx={{
                            bgcolor: item.statusMenuOption
                              ? "#E8F5E9"
                              : "#FFEBEE",
                            color: item.statusMenuOption
                              ? "#2E7D32"
                              : "#C62828",
                            fontWeight: 600,
                          }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}

                  {menuOptions.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} align="center" sx={{ py: 4 }}>
                        Este rol no tiene opciones de menú asignadas.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Paper>
          )}
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            variant="outlined"
            startIcon={<CloseOutlinedIcon />}
            onClick={closeMenuOptionsModal}
            disabled={loadingMenuOptions}
            sx={{
              borderColor: "#8B6A55",
              color: "#4B2E1F",
              textTransform: "none",
              fontWeight: 600,
              "&:hover": {
                borderColor: "#4B2E1F",
                bgcolor: "rgba(75, 46, 31, 0.05)",
              },
            }}
          >
            Cerrar
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