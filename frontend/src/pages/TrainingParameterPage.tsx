import {
  Alert, Box, Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent,
  DialogTitle, Divider, FormControlLabel, IconButton, MenuItem, Paper, Stack, Switch,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Tooltip, Typography,
} from "@mui/material";
import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import ArrowDownwardOutlinedIcon from "@mui/icons-material/ArrowDownwardOutlined";
import ArrowUpwardOutlinedIcon from "@mui/icons-material/ArrowUpwardOutlined";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import SchoolOutlinedIcon from "@mui/icons-material/SchoolOutlined";
import UploadFileOutlinedIcon from "@mui/icons-material/UploadFileOutlined";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import { ResponseModal, type ResponseModalSeverity } from "../components/ResponseModal";
import type { ApiResponse } from "../models/ApiResponse";
import type { TrainingParameter, TrainingParameterUpdate } from "../models/TrainingParameter";
import { getErrorMessage } from "../services/errorService";
import { trainingParameterService } from "../services/trainingParameterService";

type Mode = "create" | "view" | "edit";
type Pending = "detail" | "save" | "upload" | "replace" | "reload" | "status" | "access" | null;
type StatusFilter = "all" | "active" | "inactive";
interface Form {
  name: string;
  topics: { key: string; name: string }[];
  isActive: boolean;
}

// Same formats accepted by the existing event uploader and backend.
const pensumExtensions = [
  "pdf", "doc", "docm", "docx", "odt", "rtf", "txt", "csv", "ods", "xls", "xlsb",
  "xlsm", "xlsx", "odp", "ppt", "pptm", "pptx", "png", "jpg", "jpeg",
];
const emptyForm: Form = { name: "", topics: [], isActive: false };
const normalizeName = (value: string) => value.trim().replace(/\s+/g, " ").toUpperCase().normalize("NFC");
const nameKey = (value: string) => normalizeName(value).normalize("NFKD").replace(/\p{M}/gu, "");
const characterCount = (value: string) => Array.from(value).length;
const orderedTopics = (parameter: TrainingParameter) => [...parameter.topics]
  .sort((a, b) => a.sortOrder - b.sortOrder || a.IdParameterTopic - b.IdParameterTopic);
const fileExtension = (name: string) => name.split(".").pop()?.toLowerCase() || "";
const formatSize = (size: number | null) => size === null ? "Tamaño no disponible"
  : size < 1024 ? `${size} bytes`
  : size < 1024 * 1024 ? `${(size / 1024).toFixed(1)} KB`
  : `${(size / (1024 * 1024)).toFixed(1)} MB`;

function resultOf<T>(response: ApiResponse<T>): T {
  if (!response.isSuccess || response.result == null) {
    throw new Error(response.Message || "No fue posible completar la operación.");
  }
  return response.result;
}

function operationError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) return "No se pudo conectar con el servidor. Revisa tu conexión y vuelve a consultar antes de reintentar.";
    if (error.response.status === 401) return "La sesión no es válida o expiró. Vuelve a iniciar sesión.";
  }
  return getErrorMessage(error);
}

function activationIssue(name: string, topics: string[], parameter: TrainingParameter | null): string {
  if (!normalizeName(name) || characterCount(normalizeName(name)) > 200) {
    return "Para activar, ingresa un nombre válido de hasta 200 caracteres.";
  }
  if (!topics.length || topics.some((topic) => !normalizeName(topic))) {
    return "Para activar, agrega al menos un tema válido.";
  }
  if (!parameter?.pensumPathTrainingParameter || !parameter.pensumOriginalNameTrainingParameter
    || !parameter.pensumMimeTypeTrainingParameter || !((parameter.pensumSizeTrainingParameter ?? 0) > 0)) {
    return "Para activar, adjunta primero el PÉNSUM oficial.";
  }
  return "";
}

export function TrainingParameterPage() {
  const [parameters, setParameters] = useState<TrainingParameter[]>([]);
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [selected, setSelected] = useState<TrainingParameter | null>(null);
  const [mode, setMode] = useState<Mode>("create");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<Form>(emptyForm);
  const [pending, setPending] = useState<Pending>(null);
  const [formError, setFormError] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState("");
  const [documentUnconfirmed, setDocumentUnconfirmed] = useState(false);
  const [confirmPensum, setConfirmPensum] = useState(false);
  const [creationUnconfirmed, setCreationUnconfirmed] = useState(false);
  const [response, setResponse] = useState({
    open: false, severity: "info" as ResponseModalSeverity, title: "", message: "",
  });
  const listRequest = useRef(0);
  const topicSequence = useRef(0);
  const saving = useRef(false);
  const replacingPensum = useRef(false);
  const busy = pending !== null;

  const notify = (severity: ResponseModalSeverity, title: string, message: string) =>
    setResponse({ open: true, severity, title, message });

  const loadParameters = useCallback(async () => {
    const request = ++listRequest.current;
    setLoading(true);
    setListError("");
    try {
      const items = resultOf(await trainingParameterService.getAll(
        filter === "all" ? undefined : filter === "active",
      ));
      if (request === listRequest.current) setParameters(items);
    } catch (error) {
      if (request === listRequest.current) {
        setParameters([]);
        setListError(operationError(error));
      }
    } finally {
      if (request === listRequest.current) setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadParameters();
    return () => { listRequest.current += 1; };
  }, [loadParameters]);

  const fillForm = (parameter: TrainingParameter) => {
    setForm({
      name: parameter.nameTrainingParameter,
      topics: orderedTopics(parameter).map((topic) => ({
        key: `saved-${topic.IdParameterTopic}`, name: topic.nameParameterTopic,
      })),
      isActive: parameter.isActive,
    });
  };

  const acceptSaved = (parameter: TrainingParameter, reveal = false, preserveForm = false) => {
    setSelected(parameter);
    if (!preserveForm) fillForm(parameter);
    setParameters((current) => {
      const others = current.filter((item) => item.IdTrainingParameter !== parameter.IdTrainingParameter);
      if (reveal || filter === "all" || parameter.isActive === (filter === "active")) others.push(parameter);
      return others.sort((a, b) => a.nameTrainingParameter.localeCompare(b.nameTrainingParameter, "es"));
    });
  };

  const openCreate = () => {
    setConfirmPensum(false);
    setCreationUnconfirmed(false);
    setMode("create");
    setSelected(null);
    setForm(emptyForm);
    setFile(null);
    setFileError("");
    setDocumentUnconfirmed(false);
    setFormError("");
    setOpen(true);
  };

  const openParameter = async (id: number, nextMode: Mode) => {
    if (busy) return;
    setConfirmPensum(false);
    setMode(nextMode);
    setSelected(null);
    setForm(emptyForm);
    setFile(null);
    setFileError("");
    setDocumentUnconfirmed(false);
    setFormError("");
    setOpen(true);
    setPending("detail");
    try {
      const parameter = resultOf(await trainingParameterService.getById(id));
      acceptSaved(parameter);
    } catch (error) {
      setFormError(operationError(error));
    } finally {
      setPending(null);
    }
  };

  const moveTopic = (index: number, offset: number) => {
    setForm((current) => {
      const topics = [...current.topics];
      [topics[index], topics[index + offset]] = [topics[index + offset], topics[index]];
      return { ...current, topics };
    });
  };

  const save = async () => {
    if (busy || saving.current || (mode === "create" && loading) || (mode !== "create" && !selected)) return;
    const creating = mode === "create";
    const name = normalizeName(form.name);
    const topics = form.topics.map((topic) => normalizeName(topic.name));
    let error = "";
    if (!name || characterCount(name) > 200) error = "El nombre es obligatorio y admite hasta 200 caracteres.";
    else if (creating && !topics.length) error = "Agrega al menos un tema para crear la capacitación.";
    else if (topics.some((topic) => !topic || characterCount(topic) > 300)) {
      error = "Cada tema debe tener entre 1 y 300 caracteres. Completa o quita las filas vacías.";
    } else if (new Set(topics.map(nameKey)).size !== topics.length) error = "Los temas no pueden repetirse.";
    else if (parameters.some((item) => item.IdTrainingParameter !== selected?.IdTrainingParameter
      && nameKey(item.nameTrainingParameter) === nameKey(name))) error = "Ya existe una capacitación con ese nombre.";
    else if (form.isActive) error = activationIssue(name, topics, selected);
    if (error) { setFormError(error); return; }
    if (creating && !file) {
      setFileError(fileError || "Selecciona el PÉNSUM oficial para crear la capacitación.");
      return;
    }

    saving.current = true;
    setPending("save");
    setFormError("");
    setCreationUnconfirmed(false);
    try {
      const update: TrainingParameterUpdate = {};
      if (selected) {
        if (name !== selected.nameTrainingParameter) update.nameTrainingParameter = name;
        if (form.isActive !== selected.isActive) update.isActive = form.isActive;
        const previous = orderedTopics(selected).map((topic) => topic.nameParameterTopic);
        if (JSON.stringify(topics) !== JSON.stringify(previous)) update.topics = topics;
      }
      const saved = resultOf(creating
        ? await trainingParameterService.createComplete({ nameTrainingParameter: name, topics }, file!)
        : await trainingParameterService.update(selected!.IdTrainingParameter, update));
      if (creating && (!saved.isActive || !saved.pensumPathTrainingParameter || !saved.topics.length)) {
        throw new Error("El servidor no confirmó una capacitación completa y activa. Actualiza el listado antes de reintentar.");
      }
      acceptSaved(saved, creating);
      setMode("view");
      if (creating) {
        setOpen(false);
        setFile(null);
        if (filter === "inactive") setFilter("all");
      }
      notify("success", creating ? "Capacitación creada" : "Parámetro actualizado",
        creating ? "La capacitación quedó activa con sus temas y PÉNSUM oficial."
          : "Los cambios se guardaron correctamente.");
    } catch (error) {
      if (creating && (!axios.isAxiosError(error) || !error.response || error.response.status >= 500)) {
        setCreationUnconfirmed(true);
      }
      setFormError(operationError(error));
      notify("error", "No se pudo guardar", operationError(error));
    } finally {
      saving.current = false;
      setPending(null);
    }
  };

  const changeStatus = async () => {
    if (!selected || busy) return;
    if (!selected.isActive) {
      const issue = activationIssue(selected.nameTrainingParameter,
        selected.topics.map((topic) => topic.nameParameterTopic), selected);
      if (issue) { setFormError(issue); return; }
    }
    setPending("status");
    setFormError("");
    try {
      const saved = resultOf(await trainingParameterService.setStatus(
        selected.IdTrainingParameter, !selected.isActive,
      ));
      acceptSaved(saved);
      notify("success", saved.isActive ? "Parámetro activado" : "Parámetro desactivado",
        "El estado fue confirmado por el servidor.");
    } catch (error) {
      setFormError(operationError(error));
      notify("error", "No se pudo cambiar el estado", operationError(error));
    } finally {
      setPending(null);
    }
  };

  const selectFile = (candidate: File | null) => {
    setFile(null);
    setFileError("");
    if (!candidate) return;
    if (!pensumExtensions.includes(fileExtension(candidate.name))) {
      setFileError("Formato no permitido. Selecciona PDF, imagen o un documento de oficina compatible.");
    } else if (!candidate.size) setFileError("El archivo está vacío.");
    else if (candidate.size > 2147483647) setFileError("El tamaño del archivo supera el límite permitido por el servidor.");
    else if (characterCount(candidate.name) > 255) setFileError("El nombre del archivo no puede superar 255 caracteres.");
    else if (candidate.type.length > 150) setFileError("El tipo de archivo indicado no es válido.");
    else setFile(candidate);
  };

  const upload = async () => {
    if (!selected || !file || busy || documentUnconfirmed || selected.pensumPathTrainingParameter) return;
    setPending("upload");
    setFormError("");
    setFileError("");
    try {
      const saved = resultOf(await trainingParameterService.uploadPensum(selected.IdTrainingParameter, file));
      acceptSaved(saved);
      setFile(null);
      notify("success", "PÉNSUM adjuntado", "El primer documento oficial quedó guardado.");
    } catch (error) {
      const message = operationError(error);
      setFileError(message);
      // A failed upload/commit response may still have saved the document.
      // Reconcile before offering another initial upload; never retry automatically.
      try {
        const current = resultOf(await trainingParameterService.getById(selected.IdTrainingParameter));
        acceptSaved(current);
        if (current.pensumPathTrainingParameter) setFile(null);
      } catch {
        setFileError(`${message} No se pudo confirmar el estado del documento. Cierra y vuelve a consultar el parámetro antes de reintentar.`);
        setDocumentUnconfirmed(true);
        setFile(null);
      }
      notify("error", "La carga no pudo confirmarse", message);
    } finally {
      setPending(null);
    }
  };

  const replacePensum = async () => {
    if (!confirmPensum || !selected?.pensumPathTrainingParameter || !file
      || busy || replacingPensum.current || documentUnconfirmed) return;
    replacingPensum.current = true;
    setPending("replace");
    setFileError("");
    try {
      const response = await trainingParameterService.updatePensum(selected.IdTrainingParameter, file);
      const saved = resultOf(response);
      acceptSaved(saved, false, true);
      setFile(null);
      notify("success", "PÉNSUM actualizado", response.Message || "El documento vigente fue actualizado correctamente.");
    } catch (error) {
      let message = operationError(error);
      const status = axios.isAxiosError(error) ? error.response?.status : undefined;
      if (status === 409) {
        message += " Otro administrador pudo actualizar el PÉNSUM. Consulta el documento vigente antes de reintentar.";
      } else if (status === undefined || status >= 500) {
        message += " Consulta primero el documento vigente para comprobar si la actualización se completó.";
      }
      if (status === 409 || status === undefined || status >= 500) {
        setDocumentUnconfirmed(true);
        setFile(null);
      }
      setFileError(message);
      notify("error", "No se pudo confirmar la actualización", message);
    } finally {
      setConfirmPensum(false);
      replacingPensum.current = false;
      setPending(null);
    }
  };

  const reloadDocument = async () => {
    if (!selected || busy) return;
    setPending("reload");
    try {
      const current = resultOf(await trainingParameterService.getById(selected.IdTrainingParameter));
      acceptSaved(current, false, mode === "edit");
      setFile(null);
      setFileError("");
      setDocumentUnconfirmed(false);
    } catch (error) {
      setFileError(operationError(error));
    } finally {
      setPending(null);
    }
  };

  const accessDocument = async (download: boolean) => {
    if (!selected?.pensumPathTrainingParameter || busy) return;
    // Open synchronously so the browser does not block a PDF/image after awaiting HTTP.
    const viewer = download ? null : window.open("", "_blank");
    if (!download && !viewer) {
      notify("warning", "No se pudo abrir el documento", "Permite ventanas emergentes para este sitio o utiliza Descargar.");
      return;
    }
    if (viewer) viewer.opener = null;
    setPending("access");
    try {
      const access = resultOf(await trainingParameterService.getPensumAccess(selected.IdTrainingParameter, download));
      const url = new URL(access);
      if (url.protocol !== "https:") throw new Error("El servidor no devolvió un acceso temporal válido.");
      if (viewer) viewer.location.replace(url.href);
      else {
        const link = document.createElement("a");
        link.href = url.href;
        link.download = selected.pensumOriginalNameTrainingParameter || "Pensum";
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        document.body.appendChild(link);
        link.click();
        link.remove();
      }
    } catch (error) {
      viewer?.close();
      notify("error", "No se pudo consultar el PÉNSUM", operationError(error));
    } finally {
      setPending(null);
    }
  };

  const hasDocument = Boolean(selected?.pensumPathTrainingParameter);
  const canPreview = ["pdf", "png", "jpg", "jpeg"].includes(fileExtension(
    selected?.pensumOriginalNameTrainingParameter || "",
  ));
  const missingActivation = activationIssue(form.name, form.topics.map((topic) => topic.name), selected);
  const showForm = mode !== "view" && (mode === "create" || selected !== null);

  return (
    <Stack spacing={3}>
      <Stack direction={{ xs: "column", sm: "row" }} sx={{ justifyContent: "space-between", gap: 2 }}>
        <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
          <SchoolOutlinedIcon sx={{ color: "primary.main", fontSize: 30 }} />
          <Box>
            <Typography component="h1" sx={{ fontSize: 26, fontWeight: 700 }}>
              Parametrización de capacitaciones
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Administra capacitaciones reutilizables, sus temas y su PÉNSUM oficial.
            </Typography>
          </Box>
        </Stack>
        <Button variant="outlined" startIcon={<AddOutlinedIcon />} onClick={openCreate} disabled={busy || loading}>
          Nueva capacitación
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
        <TextField select label="Estado" size="small" value={filter} sx={{ minWidth: 180 }}
          disabled={busy || open} onChange={(event) => setFilter(event.target.value as StatusFilter)}>
          <MenuItem value="all">Todos</MenuItem>
          <MenuItem value="active">Activos</MenuItem>
          <MenuItem value="inactive">Inactivos</MenuItem>
        </TextField>
        <Button onClick={() => void loadParameters()} disabled={busy || loading || open}>Actualizar listado</Button>
      </Stack>
      {listError && <Alert severity="error">{listError}</Alert>}
      <Paper elevation={0} sx={{ border: "1px solid", borderColor: "primary.light", borderRadius: 2, overflow: "hidden" }}>
        {loading ? <Box sx={{ py: 7, textAlign: "center" }}><CircularProgress aria-label="Cargando parámetros" /></Box> : (
          <TableContainer>
            <Table aria-label="Parámetros de capacitación">
              <TableHead>
                <TableRow sx={{ bgcolor: "primary.light", "& th": { fontWeight: 700 } }}>
                  <TableCell>Capacitación</TableCell><TableCell align="center">Temas</TableCell>
                  <TableCell>PÉNSUM oficial</TableCell><TableCell>Estado</TableCell><TableCell align="center">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {parameters.map((parameter) => (
                  <TableRow hover key={parameter.IdTrainingParameter}>
                    <TableCell sx={{ fontWeight: 600, overflowWrap: "anywhere" }}>{parameter.nameTrainingParameter}</TableCell>
                    <TableCell align="center">{parameter.topics.length}</TableCell>
                    <TableCell sx={{ overflowWrap: "anywhere" }}>
                      {parameter.pensumOriginalNameTrainingParameter || "Sin documento"}
                    </TableCell>
                    <TableCell><Chip size="small" label={parameter.isActive ? "Activo" : "Inactivo"}
                      color={parameter.isActive ? "success" : "default"} /></TableCell>
                    <TableCell align="center" sx={{ whiteSpace: "nowrap" }}>
                      <Tooltip title="Consultar detalle"><span><IconButton aria-label={`Consultar ${parameter.nameTrainingParameter}`}
                        disabled={busy} color="primary" onClick={() => void openParameter(parameter.IdTrainingParameter, "view")}>
                        <VisibilityOutlinedIcon fontSize="small" />
                      </IconButton></span></Tooltip>
                      <Tooltip title="Editar parámetro"><span><IconButton aria-label={`Editar ${parameter.nameTrainingParameter}`}
                        disabled={busy} color="primary" onClick={() => void openParameter(parameter.IdTrainingParameter, "edit")}>
                        <EditOutlinedIcon fontSize="small" />
                      </IconButton></span></Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
                {!parameters.length && <TableRow><TableCell colSpan={5} align="center" sx={{ py: 5 }}>
                  {listError ? "No se pudo cargar el listado." : filter === "all"
                    ? "No hay parámetros registrados. Crea el primero con Nueva capacitación."
                    : "No hay parámetros con el estado seleccionado."}
                </TableCell></TableRow>}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      <Dialog open={open} onClose={busy ? undefined : () => setOpen(false)} fullWidth maxWidth="md"
        aria-labelledby="training-parameter-title">
        <DialogTitle id="training-parameter-title" sx={{ fontWeight: 700 }}>
          {mode === "create" ? "Nueva capacitación" : mode === "edit" ? "Editar parámetro" : "Detalle de capacitación"}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ mt: 1 }}>
            {formError && <Alert severity="error">{formError}</Alert>}
            {mode === "create" && creationUnconfirmed && <Alert severity="warning"
              action={<Button color="inherit" disabled={busy || loading} onClick={() => void loadParameters()}>
                Actualizar listado
              </Button>}>
              La creación no pudo confirmarse. Actualiza el listado antes de reintentar; puedes cerrar el formulario para revisarlo.
              {listError && ` ${listError}`}
              {parameters.some((item) => nameKey(item.nameTrainingParameter) === nameKey(form.name))
                && " Ya aparece una capacitación con este nombre. Consulta su detalle antes de crear otra."}
            </Alert>}
            {pending === "detail" && <Box sx={{ textAlign: "center", py: 4 }}><CircularProgress aria-label="Cargando detalle" /></Box>}
            {showForm && <>
              <TextField label="Nombre de la capacitación" value={form.name} required fullWidth autoFocus disabled={busy}
                slotProps={{ htmlInput: { maxLength: 200 } }}
                helperText={`${characterCount(form.name)}/200 caracteres. Se guardará en mayúsculas.`}
                onChange={(event) => setForm({ ...form, name: event.target.value })} />
              <Box>
                <Typography variant="h6" sx={{ mb: 1 }}>Temas</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Agrega los temas y usa las flechas para ordenar cómo aparecerán en la capacitación.
                </Typography>
                <Stack spacing={1.5}>
                  {form.topics.map((topic, index) => (
                    <Stack key={topic.key} direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ alignItems: { sm: "flex-start" } }}>
                      <TextField label={`Tema ${index + 1}`} value={topic.name} fullWidth required disabled={busy}
                        slotProps={{ htmlInput: { maxLength: 300 } }} helperText={`${characterCount(topic.name)}/300 caracteres`}
                        onChange={(event) => setForm({ ...form, topics: form.topics.map((item) =>
                          item.key === topic.key ? { ...item, name: event.target.value } : item) })} />
                      <Stack direction="row">
                        <IconButton aria-label={`Subir tema ${index + 1}`} disabled={busy || index === 0}
                          onClick={() => moveTopic(index, -1)}><ArrowUpwardOutlinedIcon /></IconButton>
                        <IconButton aria-label={`Bajar tema ${index + 1}`} disabled={busy || index === form.topics.length - 1}
                          onClick={() => moveTopic(index, 1)}><ArrowDownwardOutlinedIcon /></IconButton>
                        <IconButton aria-label={`Quitar tema ${index + 1}`} disabled={busy} color="error"
                          onClick={() => setForm({ ...form, topics: form.topics.filter((item) => item.key !== topic.key) })}>
                          <DeleteOutlineOutlinedIcon />
                        </IconButton>
                      </Stack>
                    </Stack>
                  ))}
                  {!form.topics.length && <Typography color="text.secondary">{mode === "create"
                    ? "Agrega al menos un tema para crear la capacitación."
                    : "Aún no hay temas. Puedes guardar un borrador inactivo."}</Typography>}
                  <Button variant="outlined" startIcon={<AddOutlinedIcon />} disabled={busy} sx={{ alignSelf: "flex-start" }}
                    onClick={() => setForm({ ...form, topics: [...form.topics, { key: `new-${++topicSequence.current}`, name: "" }] })}>
                    Agregar tema
                  </Button>
                </Stack>
              </Box>
              {mode === "create" ? <>
                <Divider />
                <Typography variant="h6">PÉNSUM oficial (obligatorio)</Typography>
                {fileError && <Alert severity="error">{fileError}</Alert>}
                <Button component="label" variant="outlined" startIcon={<UploadFileOutlinedIcon />}
                  disabled={busy} sx={{ alignSelf: "flex-start" }}>
                  {file ? "Cambiar archivo" : "Seleccionar archivo"}
                  <input hidden type="file" aria-label="PÉNSUM oficial" disabled={busy}
                    accept={pensumExtensions.map((extension) => `.${extension}`).join(",")}
                    onChange={(event) => {
                      if (event.target.files?.[0]) selectFile(event.target.files[0]);
                      event.target.value = "";
                    }} />
                </Button>
                <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: "anywhere" }}>
                  {file ? `${file.name} · ${formatSize(file.size)}` : "Sin archivo seleccionado. Admite PDF, imágenes y documentos de oficina."}
                </Typography>
                <Alert severity="info">
                  Al crear, la capacitación quedará activa con sus temas y PÉNSUM oficial. Puedes cambiar el archivo antes de guardar;
                  los cambios posteriores del PÉNSUM se realizan desde la edición de la capacitación.
                </Alert>
              </> : <>
                <FormControlLabel label={form.isActive ? "Activo" : "Inactivo"}
                  control={<Switch checked={form.isActive} disabled={busy}
                    onChange={(_, isActive) => setForm({ ...form, isActive })} />} />
                {missingActivation && <Alert severity="info">{missingActivation}</Alert>}
                <Typography variant="body2" color="text.secondary">
                  Los cambios del catálogo no modifican los temas ni documentos de eventos anteriores.
                </Typography>
              </>}
            </>}

            {selected && mode === "view" && <>
              <Typography variant="h6" sx={{ overflowWrap: "anywhere" }}>{selected.nameTrainingParameter}</Typography>
              <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
                <Chip label={selected.isActive ? "Activo" : "Inactivo"} color={selected.isActive ? "success" : "default"} />
                <Button variant="outlined" onClick={() => void changeStatus()} disabled={busy}>
                  {pending === "status" ? "Actualizando..." : selected.isActive ? "Desactivar" : "Activar"}
                </Button>
              </Stack>
              {!selected.isActive && missingActivation && <Alert severity="info">{missingActivation}</Alert>}
              <Box>
                <Typography variant="h6">Temas ({selected.topics.length})</Typography>
                {selected.topics.length ? <Box component="ol" sx={{ pl: 3, my: 1 }}>
                  {orderedTopics(selected).map((topic) => <Typography component="li" key={topic.IdParameterTopic}
                    sx={{ py: 0.5, overflowWrap: "anywhere" }}>{topic.nameParameterTopic}</Typography>)}
                </Box> : <Typography color="text.secondary">Sin temas registrados.</Typography>}
              </Box>
            </>}

            {selected && <>
              <Divider />
              <Typography variant="h6">PÉNSUM oficial</Typography>
              {fileError && <Alert severity="error">{fileError}</Alert>}
              {documentUnconfirmed && <Alert severity="warning" action={
                <Button color="inherit" disabled={busy} onClick={() => void reloadDocument()}>
                  {pending === "reload" ? "Consultando..." : "Consultar documento vigente"}
                </Button>
              }>
                Vuelve a consultar el parámetro para confirmar el estado del documento antes de realizar otra carga.
              </Alert>}
              {hasDocument ? <>
                <Box sx={{ overflowWrap: "anywhere" }}>
                  <Typography sx={{ fontWeight: 600 }}>{selected.pensumOriginalNameTrainingParameter}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {fileExtension(selected.pensumOriginalNameTrainingParameter || "").toUpperCase()} · {formatSize(selected.pensumSizeTrainingParameter)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">{selected.pensumMimeTypeTrainingParameter}</Typography>
                </Box>
                <Stack direction="row" sx={{ gap: 1, flexWrap: "wrap" }}>
                  {canPreview && <Button startIcon={<VisibilityOutlinedIcon />} variant="outlined" disabled={busy}
                    onClick={() => void accessDocument(false)}>Abrir documento</Button>}
                  <Button startIcon={<DownloadOutlinedIcon />} variant="outlined" disabled={busy}
                    onClick={() => void accessDocument(true)}>Descargar</Button>
                  {pending === "access" && <CircularProgress size={24} aria-label="Obteniendo acceso al documento" />}
                </Stack>
                {!canPreview && <Typography variant="body2" color="text.secondary">
                  Descarga este formato para abrirlo en una aplicación compatible.
                </Typography>}
                {mode === "edit" && <>
                  <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                    <Button component="label" variant="outlined" disabled={busy || documentUnconfirmed}>
                      {file ? "Cambiar archivo seleccionado" : "Seleccionar nuevo PÉNSUM"}
                      <input hidden type="file" aria-label="Nuevo PÉNSUM oficial"
                        accept={pensumExtensions.map((extension) => `.${extension}`).join(",")}
                        disabled={busy || documentUnconfirmed} onChange={(event) => {
                          if (event.target.files?.[0]) selectFile(event.target.files[0]);
                          event.target.value = "";
                        }} />
                    </Button>
                    <Button variant="contained" disabled={busy || documentUnconfirmed || !file}
                      startIcon={pending === "replace" ? <CircularProgress size={18} color="inherit" /> : <UploadFileOutlinedIcon />}
                      onClick={() => setConfirmPensum(true)}>
                      {pending === "replace" ? "Actualizando PÉNSUM..." : "Actualizar PÉNSUM"}
                    </Button>
                  </Stack>
                  {file && <Typography variant="body2" sx={{ overflowWrap: "anywhere" }}>
                    {file.name} · {formatSize(file.size)}
                  </Typography>}
                </>}
                <Alert severity="info">
                  El PÉNSUM se actualiza desde la edición de la capacitación. Los eventos anteriores conservan su documento original.
                  No se permite eliminar documentos.
                </Alert>
              </> : mode === "view" ? <>
                <Alert severity="info">Adjunta el primer PÉNSUM oficial. Las actualizaciones posteriores se realizan desde la edición de la capacitación.</Alert>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                  <Button component="label" variant="outlined" disabled={busy || documentUnconfirmed}>
                    Seleccionar archivo
                    <input hidden type="file" accept={pensumExtensions.map((extension) => `.${extension}`).join(",")}
                      disabled={busy || documentUnconfirmed} onChange={(event) => {
                        selectFile(event.target.files?.[0] || null);
                        event.target.value = "";
                      }} />
                  </Button>
                  <Button variant="contained" startIcon={pending === "upload"
                    ? <CircularProgress size={18} color="inherit" /> : <UploadFileOutlinedIcon />}
                    disabled={busy || documentUnconfirmed || !file} onClick={() => void upload()}>
                    {pending === "upload" ? "Subiendo..." : "Cargar primer PÉNSUM"}
                  </Button>
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: "anywhere" }}>
                  {file ? `${file.name} · ${formatSize(file.size)}` : "Sin archivo seleccionado. Admite PDF, imágenes y documentos de oficina."}
                </Typography>
              </> : <Typography color="text.secondary">Sin documento. Guarda los cambios para adjuntar el primer PÉNSUM desde el detalle.</Typography>}
            </>}
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2, flexWrap: "wrap", gap: 1 }}>
          <Button color="secondary" onClick={() => setOpen(false)} disabled={busy}>
            {mode === "view" ? "Cerrar" : "Cancelar"}
          </Button>
          {mode === "view" && selected && <Button variant="contained" startIcon={<EditOutlinedIcon />}
            disabled={busy} onClick={() => { setMode("edit"); setFormError(""); setFile(null); setFileError(""); }}>
            Editar parámetro
          </Button>}
          {showForm && <Button variant="contained" disabled={busy || (mode === "create" && loading)} onClick={() => void save()}
            startIcon={pending === "save" ? <CircularProgress size={18} color="inherit" /> : undefined}>
            {pending === "save" ? "Guardando..." : mode === "create" ? "Crear capacitación" : "Guardar cambios"}
          </Button>}
        </DialogActions>
      </Dialog>
      <Dialog open={confirmPensum} onClose={busy ? undefined : () => setConfirmPensum(false)}
        fullWidth maxWidth="sm" aria-labelledby="confirm-pensum-title">
        <DialogTitle id="confirm-pensum-title">Confirmar actualización del PÉNSUM</DialogTitle>
        <DialogContent>
          <Stack spacing={2}>
            <Typography>¿Deseas actualizar el PÉNSUM de esta capacitación?</Typography>
            <Typography>Los nuevos eventos utilizarán el documento actualizado. Los eventos creados anteriormente
              conservarán el PÉNSUM que utilizaron originalmente.</Typography>
            <Typography sx={{ overflowWrap: "anywhere", fontWeight: 600 }}>{file?.name}</Typography>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button disabled={busy} onClick={() => setConfirmPensum(false)}>Cancelar</Button>
          <Button variant="contained" disabled={busy || !file || documentUnconfirmed} onClick={() => void replacePensum()}
            startIcon={pending === "replace" ? <CircularProgress size={18} color="inherit" /> : undefined}>
            {pending === "replace" ? "Actualizando..." : "Confirmar actualización"}
          </Button>
        </DialogActions>
      </Dialog>
      <ResponseModal {...response} onClose={() => setResponse((current) => ({ ...current, open: false }))} />
    </Stack>
  );
}
