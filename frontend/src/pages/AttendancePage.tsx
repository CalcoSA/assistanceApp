import { Box, Button, CircularProgress, MenuItem, Paper, Stack, TextField, Typography, } from "@mui/material";
import type { AttendanceRegisterRequest, PublicEvent, PersonnelType } from "../models/Attendance";
import { solutionCenterService } from "../services/solutionCenterService";
import type { ResponseModalSeverity } from "../components/ResponseModal";
import { publicAttendanceService } from "../services/attendanceService";
import type { SolutionCenter } from "../models/SolutionCenter";
import { ResponseModal } from "../components/ResponseModal";
import { getErrorMessage } from "../services/errorService";
import { getBackendFileUrl } from "../services/backendFileService";
import SignatureCanvas from "react-signature-canvas";
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

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

interface AttendanceFormState {
  documentNumberAttendancePerson: string;
  fullNameAttendancePerson: string;
  positionAttendancePerson: string;
  IdSolutionCenter: number | "";
  IdPersonnelType: number | "";
  phoneAttendancePerson: string;
  signaturePathAttendancePerson: string;
}

const emptyForm: AttendanceFormState = {
  documentNumberAttendancePerson: "",
  fullNameAttendancePerson: "",
  positionAttendancePerson: "",
  IdSolutionCenter: "",
  IdPersonnelType: "",
  phoneAttendancePerson: "",
  signaturePathAttendancePerson: "",
};

export function AttendancePage() {
  const [signatureCanvasSize, setSignatureCanvasSize] = useState({ width: 700, height: 180, });
  const [responseModal, setResponseModal] = useState<ResponseModalState>(emptyResponseModal);  
  const [solutionCenters, setSolutionCenters] = useState<SolutionCenter[]>([]);
  const [personnelTypes, setPersonnelTypes] = useState<PersonnelType[]>([]);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const signatureContainerRef = useRef<HTMLDivElement | null>(null);
  const [form, setForm] = useState<AttendanceFormState>(emptyForm);
  const [replaceSignature, setReplaceSignature] = useState(false);
  const [searchingPerson, setSearchingPerson] = useState(false);
  const [event, setEvent] = useState<PublicEvent | null>(null);
  const { tokenEvent } = useParams<{ tokenEvent: string }>();
  const signatureRef = useRef<SignatureCanvas | null>(null);
  const [, setPersonFound] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
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

  const loadEvent = async () => {
    if (!tokenEvent) {
      showResponseModal("error", "Error", "No se encontró el token del evento.");
      return;
    }

    try {
      setLoading(true);
      const response = await publicAttendanceService.getEventByToken(tokenEvent);

      if (!response.isSuccess || !response.result) {
        showResponseModal("error", "Error", response.Message || "No se pudo cargar el evento.");
        return;
      }

      setEvent(response.result);
    } catch (err) {
      showResponseModal("error", "Error", getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const loadSolutionCenters = async () => {
    try {
      const response = await solutionCenterService.getAll();

      if (response.isSuccess && response.result) {
        setSolutionCenters(response.result);
      }
    } catch {
      setSolutionCenters([]);
    }
  };

  const loadPersonnelTypes = async () => {
    try {
      const response = await publicAttendanceService.getPersonnelTypes();

      if (response.isSuccess && response.result) {
        setPersonnelTypes(response.result);

        const noAplica = response.result.find((item) => item.namePersonnelType.trim().toLowerCase() === "no aplica");

        if (noAplica) {
          setForm((prev) => ({
            ...prev,
            IdPersonnelType: noAplica.IdPersonnelType,
          }));
        }
      }
    } catch {
      setPersonnelTypes([]);
    }
  };

  useEffect(() => {
    loadEvent();
    loadPersonnelTypes();
    loadSolutionCenters();
  }, [tokenEvent]);

  useEffect(() => {
    const updateCanvasSize = () => {
      if (!signatureContainerRef.current) return;

      const width = signatureContainerRef.current.offsetWidth;
      setSignatureCanvasSize({ width, height: 180, });

      setTimeout(() => {
        signatureRef.current?.clear();
      }, 0);
    };

    updateCanvasSize();

    window.addEventListener("resize", updateCanvasSize);
    window.addEventListener("orientationchange", updateCanvasSize);

    return () => {
      window.removeEventListener("resize", updateCanvasSize);
      window.removeEventListener("orientationchange", updateCanvasSize);
    };
  }, []);

  const handleFormChange = (
    field: keyof AttendanceFormState,
    value: string | number | ""
  ) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const searchPerson = async () => {
    const documentNumber = form.documentNumberAttendancePerson.trim();

    if (!documentNumber) {
      showResponseModal("warning", "Campo obligatorio", "Debes ingresar la cédula.");
      return;
    }

    try {
      setSearchingPerson(true);
      setPersonFound(false);
      setReplaceSignature(false);

      const response = await publicAttendanceService.getPersonByDocument(documentNumber);

      if (!response.isSuccess || !response.result) {
        setPersonFound(false);

        setForm((prev) => ({
          ...prev,
          fullNameAttendancePerson: "",
          positionAttendancePerson: "",
          IdSolutionCenter: "",
          IdPersonnelType: prev.IdPersonnelType,
          phoneAttendancePerson: "",
          signaturePathAttendancePerson: "",
        }));

        signatureRef.current?.clear();
        return;
      }

      const person = response.result;

      setPersonFound(true);

      setForm((prev) => ({
        ...prev,
        documentNumberAttendancePerson: person.documentNumberAttendancePerson ?? documentNumber,
        fullNameAttendancePerson: person.fullNameAttendancePerson ?? "",
        positionAttendancePerson: person.positionAttendancePerson ?? "",
        IdSolutionCenter: person.IdSolutionCenter ?? "",
        IdPersonnelType: prev.IdPersonnelType,
        phoneAttendancePerson: person.phoneAttendancePerson ?? "",
        signaturePathAttendancePerson: person.signaturePathAttendancePerson ?? "",
      }));

      signatureRef.current?.clear();
    } catch (err) {
      showResponseModal("error", "Error", getErrorMessage(err));
    } finally {
      setSearchingPerson(false);
    }
  };

  const clearSignature = () => {
    signatureRef.current?.clear();
  };

  const getSignatureBase64 = () => {
    const hasCurrentSignature = Boolean(form.signaturePathAttendancePerson);

    if (hasCurrentSignature && !replaceSignature) {
      return null;
    }

    if (!signatureRef.current || signatureRef.current.isEmpty()) {
      return null;
    }

    return signatureRef.current.toDataURL("image/png");
  };

  const validateForm = () => {
    if (!form.documentNumberAttendancePerson.trim()) {
      showResponseModal("warning", "Campo obligatorio", "La cédula es obligatoria.");
      return false;
    }

    if (!form.fullNameAttendancePerson.trim()) {
      showResponseModal("warning", "Campo obligatorio", "El nombre completo es obligatorio.");
      return false;
    }

    if (!form.IdPersonnelType) {
      showResponseModal("warning", "Campo obligatorio", "Debe seleccionar el tipo de personal.");
      return false;
    }

    const hasCurrentSignature = Boolean(form.signaturePathAttendancePerson);
    const needsSignature = !hasCurrentSignature || replaceSignature;

    if (needsSignature && (!signatureRef.current || signatureRef.current.isEmpty())) {
      showResponseModal("warning", "Campo obligatorio", "La firma es obligatoria.");
      return false;
    }

    return true;
  };

  const submitAttendance = async () => {
    if (!tokenEvent) {
      showResponseModal("error", "Error", "No se encontró el token del evento.");
      return;
    }

    if (!validateForm()) {
      return;
    }

    try {
      setSaving(true);

      const payload: AttendanceRegisterRequest = {
        documentNumberAttendancePerson: form.documentNumberAttendancePerson.trim(),
        fullNameAttendancePerson: form.fullNameAttendancePerson.trim(),
        positionAttendancePerson: form.positionAttendancePerson.trim() || null,
        IdSolutionCenter: form.IdSolutionCenter === "" ? null : Number(form.IdSolutionCenter),
        IdPersonnelType: Number(form.IdPersonnelType),
        phoneAttendancePerson: form.phoneAttendancePerson.trim() || null,
        signatureBase64: getSignatureBase64(),
      };

      const response = await publicAttendanceService.registerAttendance(tokenEvent, payload);

      if (!response.isSuccess) {
        showResponseModal("error", "Error", response.Message || "No se pudo registrar la asistencia.");
        return;
      }

      setRegistrationSuccess(true);

      setForm(emptyForm);
      setPersonFound(false);
      setReplaceSignature(false);
      signatureRef.current?.clear();
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      showResponseModal("error", "Error", errorMessage);
    } finally {
      setSaving(false);
    }
  };

  if (registrationSuccess) {
    return (
      <Box sx={{ minHeight: "100vh", bgcolor: "#F8F3EC", display: "flex", alignItems: "center", justifyContent: "center", px: 2, }}>
        <Paper elevation={0} sx={{ width: "100%", maxWidth: 520, borderRadius: 4, border: "1px solid #E0CDBB", bgcolor: "#FFFDF8", p: 4, textAlign: "center", }}>
          <Box sx={{ width: 86, height: 86, borderRadius: "50%", bgcolor: "#E8F5E9", color: "#2E7D32", display: "flex", alignItems: "center", justifyContent: "center", mx: "auto", mb: 2, fontSize: 48, fontWeight: 800, }}>
            ✓
          </Box>
          <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800, mb: 1, }}>
            Registro exitoso
          </Typography>
          <Typography sx={{ color: "#7A6252", fontSize: 16, lineHeight: 1.6, mb: 3, }}>
            Tu asistencia fue registrada correctamente.
          </Typography>
          <Typography sx={{ color: "#4B2E1F", fontSize: 15, fontWeight: 600, }}>
            Puedes cerrar esta página.
          </Typography>
        </Paper>
      </Box>
    );
  }

  if (loading) {
    return (
      <Box sx={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#F8F3EC", p: { xs: 2, md: 4 }, }}>
      <Paper elevation={0} sx={{ maxWidth: 760, mx: "auto", p: { xs: 2, md: 4 }, borderRadius: 4, border: "1px solid #E8D8C8", bgcolor: "#FFFDF8", }}>
        <Stack spacing={3}>
          <Box>
            <Typography sx={{ color: "#4B2E1F", fontWeight: 800, fontSize: 26, textAlign: "center", }}>
              Registro de asistencia
            </Typography>
            {event && (
              <Box sx={{ mt: 2, textAlign: "center" }}>
                <Typography sx={{ color: "#4B2E1F", fontWeight: 700 }}>
                  {event.titleEvent}
                </Typography>
                <Typography sx={{ color: "#7A6252" }}>
                  {event.dateEvent} | {event.startTimeEvent} -{" "}
                  {event.endTimeEvent}
                </Typography>
                {event.eventPlace && (
                  <Typography sx={{ color: "#7A6252" }}>
                    Lugar: {event.eventPlace}
                  </Typography>
                )}
              </Box>
            )}
          </Box>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField label="Cédula" value={ form.documentNumberAttendancePerson } onChange={(event) => handleFormChange("documentNumberAttendancePerson", event.target.value) } fullWidth required disabled={ saving }/>
            <Button variant="contained" onClick={ searchPerson } disabled={ saving || searchingPerson } sx={{ minWidth: 150, bgcolor: "#4B2E1F", "&:hover": { bgcolor: "#3A2318" }, }}>
              {searchingPerson ? "Buscando..." : "Buscar"}
            </Button>
          </Stack>
          <TextField label="Nombre completo" value={ form.fullNameAttendancePerson } onChange={ (event) => handleFormChange("fullNameAttendancePerson", event.target.value) } fullWidth required disabled={ saving }/>
          <TextField label="Cargo" value={ form.positionAttendancePerson } onChange={ (event) => handleFormChange("positionAttendancePerson", event.target.value) } fullWidth disabled={ saving }/>
          <TextField
            label="Centro de soluciones"
            select
            value={form.IdSolutionCenter}
            onChange={(event) => {
              const value = event.target.value;
              handleFormChange(
                "IdSolutionCenter",
                value === "" ? "" : Number(value)
              );
            }}
            fullWidth
            disabled={saving}
            slotProps={{
              inputLabel: {
                shrink: true,
              },
              select: {
                native: true,
              },
            }}
          >
            <option value="">Seleccione</option>
            {solutionCenters.map((item) => (
              <option key={ item.IdSolutionCenter } value={ item.IdSolutionCenter }>
                { item.codeSolutionCenter } - { item.nameSolutionCenter }
              </option>
            ))}
          </TextField>
          <TextField
            select
            label="Tipo de personal"
            value={form.IdPersonnelType}
            onChange={(event) =>
              handleFormChange("IdPersonnelType", Number(event.target.value))
            }
            fullWidth
            required
          >
            {personnelTypes.map((item) => (
              <MenuItem key={item.IdPersonnelType} value={item.IdPersonnelType}>
                {item.namePersonnelType}
              </MenuItem>
            ))}
          </TextField>
          <TextField label="Teléfono" value={ form.phoneAttendancePerson } onChange={(event) => handleFormChange("phoneAttendancePerson", event.target.value) } fullWidth disabled={ saving }/>
          <Box>
            <Typography sx={{ color: "#4B2E1F", fontWeight: 700, mb: 1 }}>
              Firma
            </Typography>
            {form.signaturePathAttendancePerson && !replaceSignature ? (
              <Stack spacing={2}>
                <Box
                  component="img"
                  src={getBackendFileUrl(form.signaturePathAttendancePerson)}
                  alt="Firma registrada"
                  sx={{ width: "100%", maxWidth: 420, height: 160, objectFit: "contain", border: "1px solid #E8D8C8", borderRadius: 2, bgcolor: "#fff", }}
                />
                <Button variant="outlined" onClick={ () => setReplaceSignature(true) } disabled={ saving } sx={{ width: "fit-content", borderColor: "#8B6A55", color: "#4B2E1F", }}>
                  Actualizar firma
                </Button>
              </Stack>
            ) : (
              <Stack spacing={1}>
                <Box
                  ref={signatureContainerRef}
                  sx={{
                    border: "1px solid #E8D8C8",
                    borderRadius: 2,
                    bgcolor: "#fff",
                    width: "100%",
                    height: 180,
                    overflow: "hidden",
                    touchAction: "none",
                  }}
                >
                  <SignatureCanvas
                    ref={signatureRef}
                    canvasProps={{
                      width: signatureCanvasSize.width,
                      height: signatureCanvasSize.height,
                      style: {
                        width: `${signatureCanvasSize.width}px`,
                        height: `${signatureCanvasSize.height}px`,
                        display: "block",
                        touchAction: "none",
                      },
                    }}
                  />
                </Box>
                <Stack direction="row" spacing={1}>
                  <Button variant="outlined" onClick={ clearSignature } disabled={ saving } sx={{ borderColor: "#8B6A55", color: "#4B2E1F", }}>
                    Limpiar firma
                  </Button>
                  {form.signaturePathAttendancePerson && (
                    <Button variant="text" onClick={() => { setReplaceSignature(false); signatureRef.current?.clear(); }} disabled={ saving } sx={{ color: "#4B2E1F" }}>
                      Conservar firma actual
                    </Button>
                  )}
                </Stack>
              </Stack>
            )}
          </Box>
          <Button variant="contained" onClick={ submitAttendance } disabled={ saving } sx={{ bgcolor: "#4B2E1F", py: 1.4, fontWeight: 700, "&:hover": { bgcolor: "#3A2318" },}}>
            {saving ? "Registrando..." : "Registrar asistencia"}
          </Button>
        </Stack>
      </Paper>
      <ResponseModal
        open={responseModal.open}
        severity={responseModal.severity}
        title={responseModal.title}
        message={responseModal.message}
        onClose={closeResponseModal}
      />
    </Box>
  );
}
