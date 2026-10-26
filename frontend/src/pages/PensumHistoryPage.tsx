import { useEffect, useRef, useState } from "react";
import { Alert, Box, Button, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle,
  MenuItem, Paper, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TablePagination, TableRow, TextField, Typography } from "@mui/material";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import { OnlyOfficeViewer } from "../components/OnlyOfficeViewer";
import type { OnlyOfficePreview } from "../models/OnlyOffice";
import type { ApiResponse } from "../models/ApiResponse";
import type { PensumEventAssociation, PensumHistoryItem, PensumPage, PensumVersion } from "../models/PensumHistory";
import { pensumHistoryService as service } from "../services/pensumHistoryService";
import { eventService } from "../services/eventService";
import { getErrorMessage } from "../services/errorService";

const origins: Record<string, string> = { parameter: "Capacitación parametrizada", freeEvent: "Evento libre", parameterEvent: "Evento parametrizado" };
const dateLabel = (date: string | null) => date ? new Date(date).toLocaleString("es-CO") : "Sin fecha registrada";
const extension = (name: string) => name.split(".").pop()?.toLowerCase() || "";
const inline = (name: string) => ["pdf", "png", "jpg", "jpeg"].includes(extension(name));
const office = (name: string) => ["doc", "docm", "docx", "odt", "rtf", "txt", "csv", "ods", "xls", "xlsb", "xlsm", "xlsx", "odp", "ppt", "pptm", "pptx"].includes(extension(name));
function resultOf<T>(response: ApiResponse<T>): T {
  if (!response.isSuccess || response.result == null) throw new Error(response.Message || "No se pudo completar la consulta.");
  return response.result;
}
function versionItem(v: PensumVersion): PensumHistoryItem {
  return { documentKey: `version-${v.IdTrainingParameterVersion}`, name: v.pensumOriginalNameTrainingParameterVersion,
    mime: v.pensumMimeTypeTrainingParameterVersion, size: v.pensumSizeTrainingParameterVersion,
    registeredAt: v.createdAt, isLocal: false, versions: [v], events: [], eventCount: 0, eventId: null, origins: ["parameter"] };
}

export function PensumHistoryPage() {
  const [data, setData] = useState<PensumPage<PensumHistoryItem>>({ items: [], total: 0, page: 1, pageSize: 20 });
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({ page: 1, pageSize: 20, search: "", origin: "all", versionState: "all" });
  const [refresh, setRefresh] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [versions, setVersions] = useState<PensumVersion[]>([]);
  const [parameter, setParameter] = useState<number | null>(null);
  const [associations, setAssociations] = useState<PensumPage<PensumEventAssociation>>({ items: [], total: 0, page: 1, pageSize: 20 });
  const [associationItem, setAssociationItem] = useState<PensumHistoryItem | null>(null);
  const [associationPage, setAssociationPage] = useState(1);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [preview, setPreview] = useState<{ name: string; url?: string; office?: OnlyOfficePreview } | null>(null);
  const [accessing, setAccessing] = useState(false);
  const accessRequest = useRef(0);
  const localUrl = useRef("");
  useEffect(() => {
    let active = true;
    setLoading(true); setError("");
    service.getPage(filters).then(resultOf).then(value => { if (active) setData(value); })
      .catch(e => { if (active) { setError(getErrorMessage(e)); setData({ items: [], total: 0, page: filters.page, pageSize: filters.pageSize }); } })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [filters, refresh]);
  useEffect(() => {
    if (parameter === null && !associationItem) return;
    let active = true;
    setDetailLoading(true); setDetailError(""); setVersions([]);
    const request = parameter !== null ? service.getVersions(parameter).then(resultOf).then(value => { if (active) setVersions(value); })
      : service.getEvents(associationItem!, associationPage).then(resultOf).then(value => { if (active) setAssociations(value); });
    request.catch(e => { if (active) setDetailError(getErrorMessage(e)); }).finally(() => { if (active) setDetailLoading(false); });
    return () => { active = false; };
  }, [parameter, associationItem, associationPage]);
  useEffect(() => () => { accessRequest.current++; if (localUrl.current) URL.revokeObjectURL(localUrl.current); }, []);
  const closePreview = () => {
    accessRequest.current++; setAccessing(false); setPreview(null);
    if (localUrl.current) URL.revokeObjectURL(localUrl.current);
    localUrl.current = "";
  };
  const access = async (item: PensumHistoryItem, download: boolean) => {
    if (accessing) return;
    const request = ++accessRequest.current;
    setAccessing(true); setError("");
    if (!download) setPreview({ name: item.name });
    try {
      // Existing event viewer validates event scope and preserves its document snapshot.
      if (!download && !inline(item.name) && item.eventId && office(item.name)) {
        const config = resultOf(await eventService.getPensumPreview(item.eventId));
        if (request === accessRequest.current) setPreview({ name: item.name, office: config });
        return;
      }
      let url: string;
      if (item.isLocal && item.eventId) {
        const blob = await service.getLocalDocument(item.eventId);
        if (request !== accessRequest.current) return;
        url = URL.createObjectURL(blob);
        if (localUrl.current) URL.revokeObjectURL(localUrl.current);
        localUrl.current = url;
      } else {
        url = resultOf(item.versions.length ? await service.getVersionAccess(item.versions[0], download)
          : await eventService.getPensumAccess(item.eventId!, download));
        if (new URL(url).protocol !== "https:") throw new Error("No se recibió un acceso temporal seguro.");
      }
      if (request !== accessRequest.current) return;
      if (download) {
        const link = document.createElement("a"); link.href = url; link.download = item.name;
        link.target = "_blank"; link.rel = "noopener noreferrer"; document.body.appendChild(link); link.click(); link.remove();
      } else setPreview({ name: item.name, url });
    } catch (e) {
      if (request === accessRequest.current) { setError(getErrorMessage(e)); setPreview(null); }
    } finally { if (request === accessRequest.current) setAccessing(false); }
  };
  const actions = (item: PensumHistoryItem) => <Stack direction="row" spacing={1}>
    {(inline(item.name) || (item.eventId && office(item.name))) && <Button disabled={accessing} onClick={() => void access(item, false)}>Visualizar</Button>}
    <Button disabled={accessing} onClick={() => void access(item, true)}>Descargar</Button>
  </Stack>;
  const versionLabel = (v: PensumVersion) => <Stack spacing={0.5}>
    <Typography>Versión {v.versionNumber} · {v.isCurrent ? "Vigente" : "Anterior"}</Typography>
    {v.isBaseline && <Chip size="small" label="Versión inicial registrada" />}
    <Typography variant="caption">{v.isBaseline ? "Fecha de registro" : "Publicación"}: {dateLabel(v.createdAt)}</Typography>
    <Typography variant="caption">{v.createdByUserLogin || "Autor no registrado"}</Typography>
  </Stack>;
  return <Stack spacing={3}>
    <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}><HistoryOutlinedIcon color="primary" /><Typography component="h1" variant="h5">Histórico de PÉNSUM</Typography></Stack>
    <Alert severity="info">Consulta de documentos referenciados y versiones registradas. Las versiones iniciales registradas no representan necesariamente la primera publicación histórica. No incluye archivos libres reemplazados que ya no estén referenciados.</Alert>
    <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
      <TextField label="Documento, capacitación o evento" value={search} onChange={e => setSearch(e.target.value)}
        slotProps={{ htmlInput: { maxLength: 200 } }} onKeyDown={e => { if (e.key === "Enter") setFilters({ ...filters, search, page: 1 }); }} />
      <Button onClick={() => setFilters({ ...filters, search, page: 1 })}>Buscar</Button>
      <TextField select label="Origen" value={filters.origin} sx={{ minWidth: 200 }} onChange={e => setFilters({ ...filters, origin: e.target.value, page: 1 })}>
        <MenuItem value="all">Todos</MenuItem>{Object.entries(origins).map(([key, label]) => <MenuItem key={key} value={key}>{label}</MenuItem>)}
      </TextField>
      <TextField select label="Estado de versión" value={filters.versionState} sx={{ minWidth: 180 }} onChange={e => setFilters({ ...filters, versionState: e.target.value, page: 1 })}>
        <MenuItem value="all">Todos</MenuItem><MenuItem value="current">Vigentes</MenuItem><MenuItem value="previous">Anteriores</MenuItem>
      </TextField>
      <Button disabled={loading} onClick={() => setRefresh(v => v + 1)}>Actualizar</Button>
    </Stack>
    {error && <Alert severity="error">{error}</Alert>}
    {loading ? <CircularProgress aria-label="Cargando histórico" /> : <Paper variant="outlined">
      <TableContainer><Table aria-label="Histórico de PÉNSUM"><TableHead><TableRow>
        {['Documento', 'Origen y asociaciones', 'Versión y fecha', 'Acciones'].map(label => <TableCell key={label}>{label}</TableCell>)}
      </TableRow></TableHead><TableBody>{data.items.map(item => <TableRow key={item.documentKey}>
        <TableCell sx={{ overflowWrap: "anywhere" }}>{item.name}<Typography variant="caption" sx={{ display: "block" }}>{item.isLocal ? "Archivo local histórico" : "GCS"} · {item.size === null ? "Tamaño no registrado" : `${(item.size / 1024).toFixed(1)} KB`}</Typography></TableCell>
        <TableCell>{item.origins.map(origin => <Typography key={origin} variant="body2">{origins[origin]}</Typography>)}
          {item.versions.map(v => <Button key={v.IdTrainingParameterVersion} onClick={() => { setAssociationItem(null); setParameter(v.IdTrainingParameter); }}>{v.parameterName} · Ver versiones</Button>)}
          {item.events.map(e => <Typography variant="body2" key={e.IdEvent}>#{e.IdEvent} · {e.titleEvent}</Typography>)}
          {item.eventCount > 0 && <Button onClick={() => { setParameter(null); setAssociationPage(1); setAssociationItem(item); }}>Ver eventos ({item.eventCount})</Button>}
        </TableCell>
        <TableCell>{item.versions.length ? item.versions.map(v => <Box key={v.IdTrainingParameterVersion}>{versionLabel(v)}</Box>)
          : <><Typography>Sin versión registrada</Typography><Typography variant="caption">Registro del evento: {dateLabel(item.registeredAt)}</Typography></>}</TableCell>
        <TableCell>{actions(item)}</TableCell>
      </TableRow>)}{!data.items.length && <TableRow><TableCell colSpan={4}>No hay documentos para estos filtros.</TableCell></TableRow>}</TableBody></Table></TableContainer>
      <TablePagination component="div" count={data.total} page={filters.page - 1} rowsPerPage={filters.pageSize} rowsPerPageOptions={[10, 20, 50]}
        labelRowsPerPage="Documentos por página" onPageChange={(_, page) => setFilters({ ...filters, page: page + 1 })}
        onRowsPerPageChange={e => setFilters({ ...filters, pageSize: Number(e.target.value), page: 1 })} />
    </Paper>}
    <Dialog open={parameter !== null || associationItem !== null} fullWidth maxWidth="md" onClose={() => { setParameter(null); setAssociationItem(null); }}>
      <DialogTitle>{parameter !== null ? "Versiones de la capacitación" : "Eventos asociados al mismo documento"}</DialogTitle>
      <DialogContent><Stack spacing={2}>
        {error && <Alert severity="error">{error}</Alert>}
        {detailLoading ? <CircularProgress /> : detailError ? <Alert severity="error">{detailError}</Alert> : parameter !== null ? <>
          {!versions.length && <Typography>No hay versiones registradas.</Typography>}
          {versions.map(v => <Paper variant="outlined" sx={{ p: 2 }} key={v.IdTrainingParameterVersion}>
            <Typography>{v.pensumOriginalNameTrainingParameterVersion}</Typography>{versionLabel(v)}{actions(versionItem(v))}
          </Paper>)}
        </> : <>
          {associations.items.map(e => <Typography key={e.IdEvent}>#{e.IdEvent} · {e.titleEvent} · {dateLabel(e.createdAt)}</Typography>)}
          {!associations.total && <Typography>No hay eventos accesibles asociados.</Typography>}
          <TablePagination component="div" count={associations.total} page={associationPage - 1} rowsPerPage={20} rowsPerPageOptions={[]}
            onPageChange={(_, page) => setAssociationPage(page + 1)} />
        </>}
      </Stack></DialogContent><DialogActions><Button onClick={() => { setParameter(null); setAssociationItem(null); }}>Cerrar</Button></DialogActions>
    </Dialog>
    <Dialog open={preview !== null} fullWidth maxWidth="lg" onClose={closePreview}>
      <DialogTitle>{preview?.name}</DialogTitle><DialogContent>
        {accessing ? <CircularProgress /> : preview?.office ? <OnlyOfficeViewer documentServerUrl={preview.office.documentServerUrl} config={preview.office.config} />
          : preview?.url && (extension(preview.name) === "pdf" ? <Box component="iframe" src={preview.url} title={preview.name} sx={{ width: "100%", height: "70vh", border: 0 }} />
            : <Box component="img" src={preview.url} alt={preview.name} sx={{ maxWidth: "100%", maxHeight: "70vh" }} />)}
      </DialogContent><DialogActions><Button onClick={closePreview}>Cerrar</Button></DialogActions>
    </Dialog>
  </Stack>;
}
