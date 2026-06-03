import { Box, Button, Chip, CircularProgress, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControl, FormControlLabel, IconButton, InputLabel, ListItemText, MenuItem, OutlinedInput, Paper, Radio, RadioGroup, Select, Stack, Table, TableBody, TableCell, TableHead, TablePagination, TableRow, TextField, Tooltip, Typography, } from "@mui/material";
import type { AssistanceReason, Competency, EventCategory, SpecificTrainingProgram, } from "../models/EventCatalog";
import { ResponseModal, type ResponseModalSeverity, } from "../components/ResponseModal";
import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined";
import DeleteOutlineOutlinedIcon from "@mui/icons-material/DeleteOutlineOutlined";
import FileDownloadOutlinedIcon from "@mui/icons-material/FileDownloadOutlined";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import { solutionCenterService } from "../services/solutionCenterService";
import type { Event, EventQr, EventAttendance } from "../models/Event";
import QrCode2OutlinedIcon from "@mui/icons-material/QrCode2Outlined";
import { eventCatalogService } from "../services/eventCatalogService";
import CancelOutlinedIcon from "@mui/icons-material/CancelOutlined";
import EventOutlinedIcon from "@mui/icons-material/EventOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DrawOutlinedIcon from "@mui/icons-material/DrawOutlined";
import type { SolutionCenter } from "../models/SolutionCenter";
import { getErrorMessage } from "../services/errorService";
import { eventService } from "../services/eventService";
import { useEffect, useState } from "react";
import * as XLSX from "xlsx-js-style";

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

type EventModalMode = "view" | "create" | "update";

interface EventFormState {
  titleEvent: string;
  descriptionEvent: string;
  dateEvent: string;
  durationEvent: string;
  startTimeEvent: string;
  endTimeEvent: string;
  IdSolutionCenter: string;
  IdAssistanceReason: string;
  IdSpecificTrainingProgram: string;
  IdEventCategory: string;
  facilitatorNameEvent: string;
  facilitatorCompanyEvent: string;
  facilitatorPositionEvent: string;
  secondFacilitatorNameEvent: string;
  secondFacilitatorCompanyEvent: string;
  secondFacilitatorPositionEvent: string;
  scheduledPeopleNumber: string;
  isPaidTrainingEvent: boolean | null;
  isNewStaffInductionEvent: boolean | null;
  observationsEvent: string;
  eventPlace: string;
  topics: string[];
  competencies: number[];
}

const emptyEventForm: EventFormState = {
  titleEvent: "",
  descriptionEvent: "",
  dateEvent: "",
  durationEvent: "",
  startTimeEvent: "",
  endTimeEvent: "",
  IdSolutionCenter: "",
  IdAssistanceReason: "",
  IdSpecificTrainingProgram: "",
  IdEventCategory: "",
  facilitatorNameEvent: "",
  facilitatorCompanyEvent: "",
  facilitatorPositionEvent: "",
  secondFacilitatorNameEvent: "",
  secondFacilitatorCompanyEvent: "",
  secondFacilitatorPositionEvent: "",
  scheduledPeopleNumber: "",
  isPaidTrainingEvent: null,
  isNewStaffInductionEvent: false,
  observationsEvent: "",
  eventPlace: "",
  topics: [],
  competencies: [],
};

export function EventPage() {  
  const [specificTrainingPrograms, setSpecificTrainingPrograms] = useState<SpecificTrainingProgram[]>([]);
  const [responseModal, setResponseModal] = useState<ResponseModalState>(emptyResponseModal);
  const [assistanceReasons, setAssistanceReasons] = useState<AssistanceReason[]>([]);
  const [eventAttendances, setEventAttendances] = useState<EventAttendance[]>([]);
  const [solutionCenters, setSolutionCenters] = useState<SolutionCenter[]>([]);
  const [eventModalMode, setEventModalMode] = useState<EventModalMode>("view");
  const [eventIdToCancel, setEventIdToCancel] = useState<number | null>(null);  
  const [eventCategories, setEventCategories] = useState<EventCategory[]>([]);  
  const [eventForm, setEventForm] = useState<EventFormState>(emptyEventForm);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [signatureModalOpen, setSignatureModalOpen] = useState(false);
  const [signaturePersonName, setSignaturePersonName] = useState("");
  const [competencies, setCompetencies] = useState<Competency[]>([]);
  const [confirmCancelOpen, setConfirmCancelOpen] = useState(false);
  const [pensumFile, setPensumFile] = useState<File | null>(null);
  const [signatureImageUrl, setSignatureImageUrl] = useState("");
  const [eventStatusFilter, setEventStatusFilter] = useState("");
  const [eventModalOpen, setEventModalOpen] = useState(false);
  const [qrInfo, setQrInfo] = useState<EventQr | null>(null);
  const [qrModalOpen, setQrModalOpen] = useState(false);
  const [eventsTotal, setEventsTotal] = useState(0);
  const [events, setEvents] = useState<Event[]>([]);
  const [topicInput, setTopicInput] = useState("");
  const [eventPage, setEventPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [eventRowsPerPage] = useState(10);
  const [, setError] = useState("");

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
  
  const loadEvents = async (showError = true, pageToLoad = eventPage, statusToFilter = eventStatusFilter) => {
    try {
      setLoading(true);

      const response = await eventService.getAll({
        page: pageToLoad + 1,
        pageSize: eventRowsPerPage,
        statusFilter: statusToFilter,
      });

      setEvents(response.result?.items ?? []);
      setEventsTotal(response.result?.total ?? 0);
    } catch (err) {
      setEvents([]);
      setEventsTotal(0);

      if (showError) {
        showResponseModal("error", "Error al cargar", getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  };

  const loadCatalogs = async () => {
    try {
      const [ solutionCenterResponse, assistanceReasonResponse, specificTrainingResponse, eventCategoryResponse, competencyResponse, ] = await Promise.all([
        solutionCenterService.getAll(),
        eventCatalogService.getAllAssistanceReason(),
        eventCatalogService.getAllSpecificTraining(),
        eventCatalogService.getAllEventCategory(),
        eventCatalogService.getAllCompetency(),
      ]);
      setSolutionCenters(solutionCenterResponse.result ?? []);
      setAssistanceReasons(assistanceReasonResponse.result ?? []);
      setSpecificTrainingPrograms(specificTrainingResponse.result ?? []);
      setEventCategories(eventCategoryResponse.result ?? []);
      setCompetencies(competencyResponse.result ?? []);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const cancelEvent = (IdEvent: number) => {
    setEventIdToCancel(IdEvent);
    setConfirmCancelOpen(true);
  };

  const confirmCancelEvent = async () => {
    if (!eventIdToCancel) return;

    try {
      setLoading(true);
      const response = await eventService.cancel(eventIdToCancel);
      setConfirmCancelOpen(false);
      setEventIdToCancel(null);
      showResponseModal("success", "Evento cancelado", response.Message || "Evento cancelado correctamente.");
      await loadEvents(false, eventPage, eventStatusFilter);
    } catch (err) {
      setConfirmCancelOpen(false);
      setEventIdToCancel(null);
      showResponseModal(
        "error",
        "Error",
        getErrorMessage(err)
      );
    } finally {
      setLoading(false);
    }
  };

  const closeConfirmCancelModal = () => {
    if (loading) return;

    setConfirmCancelOpen(false);
    setEventIdToCancel(null);
  };

  const showQr = async (IdEvent: number) => {
    try {
      setLoading(true);
      const response = await eventService.getQr(IdEvent);

      if (!response.isSuccess || !response.result) {
        showResponseModal("error", "Error", response.Message || "No se pudo obtener el QR del evento.");
        return;
      }

      setQrInfo(response.result);
      setQrModalOpen(true);
    } catch (err) {
      showResponseModal("error", "Error", getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const closeQrModal = () => {
    setQrModalOpen(false);
    setQrInfo(null);
  };

  const downloadQrImage = async () => {
    if (!qrInfo?.IdEvent) {
      showResponseModal("error", "Error", "No se encontró información del evento.");
      return;
    }

    try {
      const blob = await eventService.downloadQr(qrInfo.IdEvent);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `qr_evento_${qrInfo.IdEvent}.png`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      showResponseModal(
        "error",
        "Error",
        getErrorMessage(err)
      );
    }
  };

  const normalizeTimeForInput = (value?: string | null) => {
    if (!value) return "";
    return value.substring(0, 5);
  };

  const normalizeTimeForApi = (value: string) => {
    if (!value) return "";
    return value.length === 5 ? `${value}:00` : value;
  };

  const eventToForm = (event: Event): EventFormState => ({
    titleEvent: event.titleEvent ?? "",
    descriptionEvent: event.descriptionEvent ?? "",
    dateEvent: event.dateEvent ?? "",
    durationEvent: event.durationEvent ?? "",
    startTimeEvent: normalizeTimeForInput(event.startTimeEvent),
    endTimeEvent: normalizeTimeForInput(event.endTimeEvent),
    IdSolutionCenter: event.IdSolutionCenter?.toString() ?? "",
    IdAssistanceReason: event.IdAssistanceReason?.toString() ?? "",
    IdSpecificTrainingProgram: event.IdSpecificTrainingProgram?.toString() ?? "",
    IdEventCategory: event.IdEventCategory?.toString() ?? "",
    facilitatorNameEvent: event.facilitatorNameEvent ?? "",
    facilitatorCompanyEvent: event.facilitatorCompanyEvent ?? "",
    facilitatorPositionEvent: event.facilitatorPositionEvent ?? "",
    secondFacilitatorNameEvent: event.secondFacilitatorNameEvent ?? "",
    secondFacilitatorCompanyEvent: event.secondFacilitatorCompanyEvent ?? "",
    secondFacilitatorPositionEvent: event.secondFacilitatorPositionEvent ?? "",
    scheduledPeopleNumber: event.scheduledPeopleNumber?.toString() ?? "",
    isPaidTrainingEvent: event.isPaidTrainingEvent ?? false,
    isNewStaffInductionEvent: event.isNewStaffInductionEvent ?? false,
    observationsEvent: event.observationsEvent ?? "",
    eventPlace: event.eventPlace ?? "",
    topics: event.topics?.map((topic) => topic.nameEventTopic) ?? [],
    competencies: event.competencies?.map((item) => item.IdCompetency) ?? [],
  });

  const openCreateModal = () => {
    setSelectedEvent(null);
    setEventForm(emptyEventForm);
    setTopicInput("");
    setPensumFile(null);
    setEventModalMode("create");
    setEventModalOpen(true);
  };

  const openViewModal = async (event: Event) => {
    try {
      setLoading(true);
      setSelectedEvent(event);
      setEventForm(eventToForm(event));
      setTopicInput("");
      setPensumFile(null);
      setEventAttendances([]);
      setEventModalMode("view");

      const response = await eventService.getAttendances(event.IdEvent);

      if (response.isSuccess && response.result) {
        setEventAttendances(response.result);
      }

      setEventModalOpen(true);
    } catch (err) {
      showResponseModal("error", "Error", getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const openUpdateModal = (event: Event) => {
    setSelectedEvent(event);
    setEventForm(eventToForm(event));
    setTopicInput("");
    setPensumFile(null);
    setEventModalMode("update");
    setEventModalOpen(true);
  };

  const closeEventModal = () => {
    if (saving) return;
    setEventModalOpen(false);
    setSelectedEvent(null);
    setPensumFile(null);
    setEventForm(emptyEventForm);
  };

  const handleEventFormChange = (field: keyof EventFormState, value: string) => {
    setEventForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const addTopic = () => {
    const cleanTopic = topicInput.trim();

    if (!cleanTopic) {
      return;
    }

    const alreadyExists = eventForm.topics.some((topic) => topic.trim().toLowerCase() === cleanTopic.toLowerCase());

    if (alreadyExists) {
      return;
    }

    setEventForm((prev) => ({
      ...prev,
      topics: [...prev.topics, cleanTopic],
    }));

    setTopicInput("");
  };

  const removeTopic = (index: number) => {
    setEventForm((prev) => ({
      ...prev,
      topics: prev.topics.filter((_, topicIndex) => topicIndex !== index),
    }));
  };

  const getBackendFileUrl = (path?: string | null) => {

    if (!path) return "";

    if (path.startsWith("http")) {
      return path;
    }

    if (path.startsWith("/api/")) {
      const backendBaseUrl =
        (import.meta.env.VITE_API_URL)
          .replace(/\/api\/?$/, "");

      return `${backendBaseUrl}${path}`;
    }

    const apiBaseUrl = import.meta.env.VITE_API_URL;
    const normalizedApiBaseUrl = apiBaseUrl.endsWith("/api")
      ? apiBaseUrl
      : `${apiBaseUrl.replace(/\/$/, "")}/api`;
    return `${normalizedApiBaseUrl}${path}`;
  };

  const buildEventPayload = () => {
    return {
      titleEvent: eventForm.titleEvent,
      descriptionEvent: eventForm.descriptionEvent || null,
      dateEvent: eventForm.dateEvent,
      durationEvent: eventForm.durationEvent || null,
      startTimeEvent: normalizeTimeForApi(eventForm.startTimeEvent),
      endTimeEvent: normalizeTimeForApi(eventForm.endTimeEvent),
      IdSolutionCenter: eventForm.IdSolutionCenter
        ? Number(eventForm.IdSolutionCenter)
        : null,
      IdAssistanceReason: eventForm.IdAssistanceReason
        ? Number(eventForm.IdAssistanceReason)
        : null,
      IdSpecificTrainingProgram: eventForm.IdSpecificTrainingProgram
        ? Number(eventForm.IdSpecificTrainingProgram)
        : null,
      IdEventCategory: eventForm.IdEventCategory
        ? Number(eventForm.IdEventCategory)
        : null,
      facilitatorNameEvent: eventForm.facilitatorNameEvent || null,
      facilitatorCompanyEvent: eventForm.facilitatorCompanyEvent || null,
      facilitatorPositionEvent: eventForm.facilitatorPositionEvent || null,
      secondFacilitatorNameEvent: eventForm.secondFacilitatorNameEvent || null,
      secondFacilitatorCompanyEvent: eventForm.secondFacilitatorCompanyEvent || null,
      secondFacilitatorPositionEvent: eventForm.secondFacilitatorPositionEvent || null,
      scheduledPeopleNumber: eventForm.scheduledPeopleNumber
        ? Number(eventForm.scheduledPeopleNumber)
        : null,
      isPaidTrainingEvent: eventForm.isPaidTrainingEvent,
      isNewStaffInductionEvent: Boolean(eventForm.isNewStaffInductionEvent),
      observationsEvent: eventForm.observationsEvent || null,
      eventPlace: eventForm.eventPlace || null,
      topics: eventForm.topics,
      competencies: eventForm.competencies,
    };
  };

  const validateEventForm = () => {
    const requiredFields = [
      { value: eventForm.titleEvent, label: "Título" },
      { value: eventForm.descriptionEvent, label: "Descripción" },
      { value: eventForm.dateEvent, label: "Fecha" },
      { value: eventForm.durationEvent, label: "Duración" },
      { value: eventForm.startTimeEvent, label: "Hora inicio" },
      { value: eventForm.endTimeEvent, label: "Hora fin" },
      { value: eventForm.IdSolutionCenter, label: "Centro de soluciones" },
      { value: eventForm.IdAssistanceReason, label: "Motivo de asistencia" },
      { value: eventForm.IdSpecificTrainingProgram, label: "Programa de formación" },
      { value: eventForm.IdEventCategory, label: "Categoría" },
      { value: eventForm.facilitatorNameEvent, label: "Nombre facilitador" },
      { value: eventForm.facilitatorCompanyEvent, label: "Empresa facilitador" },
      { value: eventForm.facilitatorPositionEvent, label: "Cargo facilitador" },
      { value: eventForm.scheduledPeopleNumber, label: "Personas programadas" },
      { value: eventForm.eventPlace, label: "Lugar" },
    ];
    const missingField = requiredFields.find((field) => !field.value || field.value.toString().trim() === "");
    if (missingField) {
      showResponseModal("warning", "Campo obligatorio", `El campo "${missingField.label}" es obligatorio.`);
      return false;
    }
    if (eventForm.topics.length === 0) {
      showResponseModal("warning", "Campo obligatorio", "Debes agregar al menos un tema tratado.");
      return false;
    }
    if (eventForm.competencies.length === 0) {
      showResponseModal("warning", "Campo obligatorio", "Debes seleccionar al menos una competencia.");
      return false;
    }
    if (eventModalMode === "create" && !pensumFile) {
      showResponseModal("warning", "Campo obligatorio", "Debes adjuntar el pensum del evento.");
      return false;
    }
    if (eventForm.isPaidTrainingEvent === null) {
      showResponseModal("warning", "Campo obligatorio", "Debes seleccionar si la capacitación es dentro del horario laboral o paga."
      );
      return false;
    }
    return true;
  };

  const saveEvent = async () => {
    try {

      if (!validateEventForm()) {
        return;
      }

      setSaving(true);
      const payload = buildEventPayload();

      if (eventModalMode === "create") {
        const response = await eventService.create(payload);

        if (!response.isSuccess || !response.result) {
          throw new Error(response.Message || "No se pudo crear el evento.");
        }

        if (pensumFile) {
          await eventService.uploadPensum(response.result.IdEvent, pensumFile);
        }

        showResponseModal(
          "success",
          "Evento creado",
          response.Message || "Evento creado correctamente."
        );
      }

      if (eventModalMode === "update") {

        if (!selectedEvent) return;

        const response = await eventService.update(selectedEvent.IdEvent, payload);

        if (!response.isSuccess || !response.result) {
          throw new Error(response.Message || "No se pudo actualizar el evento.");
        }

        if (pensumFile) {
          await eventService.uploadPensum(selectedEvent.IdEvent, pensumFile);
        }

        showResponseModal(
          "success",
          "Evento actualizado",
          response.Message || "Evento actualizado correctamente."
        );
      }

      closeEventModal();
      await loadEvents(false, eventPage, eventStatusFilter);
    } catch (err) {
      showResponseModal(
        "error",
        "Error",
        getErrorMessage(err)
      );
    } finally {
      setSaving(false);
    }
  };

  const openSignatureModal = (signaturePath?: string | null, personName?: string | null) => {
    if (!signaturePath) {
      showResponseModal("warning", "Sin firma", "Esta persona no tiene firma registrada.");
      return;
    }

    setSignatureImageUrl(getBackendFileUrl(signaturePath));
    setSignaturePersonName(personName || "Firma registrada");
    setSignatureModalOpen(true);
  };

  const closeSignatureModal = () => {
    setSignatureModalOpen(false);
    setSignatureImageUrl("");
    setSignaturePersonName("");
  };

  const getSolutionCenterName = (id?: string | number | null) => {
    const found = solutionCenters.find((item) => item.IdSolutionCenter === Number(id));
    return found ? `${found.codeSolutionCenter} - ${found.nameSolutionCenter}` : "";
  };

  const getAssistanceReasonName = (id?: string | number | null) => {
    return (
      assistanceReasons.find((item) => item.IdAssistanceReason === Number(id))?.nameAssistanceReason ?? ""
    );
  };

  const getSpecificTrainingProgramName = (id?: string | number | null) => {
    return (
      specificTrainingPrograms.find((item) => item.IdSpecificTrainingProgram === Number(id))?.nameSpecificTrainingProgram ?? ""
    );
  };

  const getEventCategoryName = (id?: string | number | null) => {
    return (
      eventCategories.find((item) => item.IdEventCategory === Number(id))?.nameEventCategory ?? ""
    );
  };

  const getCompetencyName = (id: number) => {
    return (
      competencies.find((item) => item.IdCompetency === id)?.nameCompetency ?? ""
    );
  };

  const getTrainingTypeName = (isPaidTrainingEvent?: boolean | null) => {
    return isPaidTrainingEvent ? "Capacitación paga" : "Dentro del horario laboral";
  };

  const formatDateTimeForExcel = (value?: string | null) => {
    if (!value) return "";

    return new Date(value).toLocaleString("es-CO");
  };

  const exportEventToExcel = () => {
    if (!selectedEvent) {
      showResponseModal(
        "warning",
        "Sin evento",
        "No se encontró información del evento para exportar."
      );
      return;
    }

    const workbook = XLSX.utils.book_new();

    const rows: unknown[][] = [];

    const addRow = (row: unknown[]) => {
      rows.push(row);
      return rows.length - 1;
    };

    const addBlankRow = () => addRow([]);

    const titleRow = addRow(["REGISTRO DE ASISTENCIA"]);
    const subtitleRow = addRow([eventForm.titleEvent || "Evento"]);
    addBlankRow();

    const summaryRow = addRow([
      "Fecha",
      eventForm.dateEvent,
      "Horario",
      `${eventForm.startTimeEvent} - ${eventForm.endTimeEvent}`,
      "Estado",
      selectedEvent.eventStatus?.nameEventStatus ?? "Sin estado",
    ]);

    const summaryRow2 = addRow([
      "Lugar",
      eventForm.eventPlace,
      "Personas programadas",
      eventForm.scheduledPeopleNumber,
      "Personas asistentes",
      selectedEvent.attendedPeopleNumber ?? eventAttendances.length,
    ]);

    addBlankRow();

    const eventSectionRow = addRow(["INFORMACIÓN DEL EVENTO"]);
    addRow(["Campo", "Detalle", "Campo", "Detalle"]);

    addRow([
      "Centro de soluciones",
      getSolutionCenterName(eventForm.IdSolutionCenter),
      "Motivo de asistencia",
      getAssistanceReasonName(eventForm.IdAssistanceReason),
    ]);

    addRow([
      "Programa de formación",
      getSpecificTrainingProgramName(eventForm.IdSpecificTrainingProgram),
      "Categoría",
      getEventCategoryName(eventForm.IdEventCategory),
    ]);

    addRow([
      "Tipo de capacitación",
      getTrainingTypeName(eventForm.isPaidTrainingEvent),
      "Duración",
      eventForm.durationEvent,
    ]);

    addRow([
      "Creado por",
      selectedEvent.createdByUserLogin,
      "Fecha creación",
      formatDateTimeForExcel(selectedEvent.createdAt),
    ]);

    addRow([
      "Última actualización",
      formatDateTimeForExcel(selectedEvent.updatedAt),
      "URL pública",
      selectedEvent.publicUrlEvent ?? "",
    ]);

    addBlankRow();

    const facilitatorSectionRow = addRow(["FACILITADORES"]);
    addRow(["Facilitador", "Empresa", "Cargo", "Tipo"]);

    addRow([
      eventForm.facilitatorNameEvent,
      eventForm.facilitatorCompanyEvent,
      eventForm.facilitatorPositionEvent,
      "Principal",
    ]);

    if (
      eventForm.secondFacilitatorNameEvent ||
      eventForm.secondFacilitatorCompanyEvent ||
      eventForm.secondFacilitatorPositionEvent
    ) {
      addRow([
        eventForm.secondFacilitatorNameEvent,
        eventForm.secondFacilitatorCompanyEvent,
        eventForm.secondFacilitatorPositionEvent,
        "Segundo facilitador",
      ]);
    }

    addBlankRow();

    const descriptionSectionRow = addRow(["DESCRIPCIÓN Y OBSERVACIONES"]);
    addRow(["Descripción", eventForm.descriptionEvent || ""]);
    addRow(["Observaciones", eventForm.observationsEvent || ""]);
    addBlankRow();

    const topicSectionRow = addRow(["TEMAS TRATADOS"]);
    addRow(["#", "Tema tratado"]);

    if (eventForm.topics.length === 0) {
      addRow(["", "No hay temas registrados."]);
    } else {
      eventForm.topics.forEach((topic, index) => {
        addRow([index + 1, topic]);
      });
    }

    addBlankRow();

    const competencySectionRow = addRow(["COMPETENCIAS"]);
    addRow(["#", "Competencia"]);

    if (eventForm.competencies.length === 0) {
      addRow(["", "No hay competencias registradas."]);
    } else {
      eventForm.competencies.forEach((IdCompetency, index) => {
        addRow([index + 1, getCompetencyName(IdCompetency)]);
      });
    }

    addBlankRow();

    const attendanceSectionRow = addRow(["ASISTENTES"]);
    const attendanceHeaderRow = addRow([
      "Cédula",
      "Nombre",
      "Cargo",
      "Teléfono",
      "Centro de soluciones",
      "IP",
      "Fecha registro",
    ]);

    if (eventAttendances.length === 0) {
      addRow(["", "No hay asistentes registrados para este evento."]);
    } else {
      eventAttendances.forEach((attendance) => {
        addRow([
          attendance.attendancePerson?.documentNumberAttendancePerson ?? "",
          attendance.attendancePerson?.fullNameAttendancePerson ?? "",
          attendance.attendancePerson?.positionAttendancePerson ?? "",
          attendance.attendancePerson?.phoneAttendancePerson ?? "",
          getSolutionCenterName(attendance.attendancePerson?.IdSolutionCenter),
          attendance.ipAddressAttendance ?? "",
          formatDateTimeForExcel(attendance.createdAt),
        ]);
      });
    }

    const worksheet = XLSX.utils.aoa_to_sheet(rows);

    worksheet["!cols"] = [
      { wch: 22 },
      { wch: 38 },
      { wch: 24 },
      { wch: 32 },
      { wch: 35 },
      { wch: 20 },
      { wch: 25 },
    ];

    worksheet["!rows"] = rows.map((_, index) => ({
      hpt:
        index === titleRow
          ? 30
          : index === subtitleRow
          ? 24
          : [
              eventSectionRow,
              facilitatorSectionRow,
              descriptionSectionRow,
              topicSectionRow,
              competencySectionRow,
              attendanceSectionRow,
            ].includes(index)
          ? 23
          : 20,
    }));

    worksheet["!merges"] = [
      { s: { r: titleRow, c: 0 }, e: { r: titleRow, c: 6 } },
      { s: { r: subtitleRow, c: 0 }, e: { r: subtitleRow, c: 6 } },
      { s: { r: eventSectionRow, c: 0 }, e: { r: eventSectionRow, c: 6 } },
      { s: { r: facilitatorSectionRow, c: 0 }, e: { r: facilitatorSectionRow, c: 6 } },
      { s: { r: descriptionSectionRow, c: 0 }, e: { r: descriptionSectionRow, c: 6 } },
      { s: { r: topicSectionRow, c: 0 }, e: { r: topicSectionRow, c: 6 } },
      { s: { r: competencySectionRow, c: 0 }, e: { r: competencySectionRow, c: 6 } },
      { s: { r: attendanceSectionRow, c: 0 }, e: { r: attendanceSectionRow, c: 6 } },
    ];

    const borderThin = {
      top: { style: "thin", color: { rgb: "D8C2AE" } },
      bottom: { style: "thin", color: { rgb: "D8C2AE" } },
      left: { style: "thin", color: { rgb: "D8C2AE" } },
      right: { style: "thin", color: { rgb: "D8C2AE" } },
    };

    const titleStyle = {
      font: { bold: true, sz: 18, color: { rgb: "FFFFFF" } },
      fill: { fgColor: { rgb: "4B2E1F" } },
      alignment: { horizontal: "center", vertical: "center" },
    };

    const subtitleStyle = {
      font: { bold: true, sz: 14, color: { rgb: "4B2E1F" } },
      fill: { fgColor: { rgb: "F7E8D8" } },
      alignment: { horizontal: "center", vertical: "center" },
    };

    const sectionStyle = {
      font: { bold: true, sz: 12, color: { rgb: "FFFFFF" } },
      fill: { fgColor: { rgb: "8B6A55" } },
      alignment: { horizontal: "left", vertical: "center" },
      border: borderThin,
    };

    const summaryLabelStyle = {
      font: { bold: true, color: { rgb: "4B2E1F" } },
      fill: { fgColor: { rgb: "FFF4E5" } },
      alignment: { horizontal: "center", vertical: "center" },
      border: borderThin,
    };

    const summaryValueStyle = {
      font: { bold: true, color: { rgb: "2F241D" } },
      fill: { fgColor: { rgb: "FFFDF8" } },
      alignment: { horizontal: "center", vertical: "center", wrapText: true },
      border: borderThin,
    };

    const headerStyle = {
      font: { bold: true, color: { rgb: "FFFFFF" } },
      fill: { fgColor: { rgb: "4B2E1F" } },
      alignment: { horizontal: "center", vertical: "center", wrapText: true },
      border: borderThin,
    };

    const labelStyle = {
      font: { bold: true, color: { rgb: "4B2E1F" } },
      fill: { fgColor: { rgb: "F7E8D8" } },
      alignment: { vertical: "center", wrapText: true },
      border: borderThin,
    };

    const valueStyle = {
      font: { color: { rgb: "2F241D" } },
      fill: { fgColor: { rgb: "FFFDF8" } },
      alignment: { vertical: "center", wrapText: true },
      border: borderThin,
    };

    const tableCellStyle = {
      font: { color: { rgb: "2F241D" } },
      alignment: { vertical: "center", wrapText: true },
      border: borderThin,
    };

    const mutedStyle = {
      font: { italic: true, color: { rgb: "7A6252" } },
      alignment: { vertical: "center", wrapText: true },
      border: borderThin,
    };

    const setStyle = (row: number, col: number, style: object) => {
      const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });

      if (!worksheet[cellAddress]) {
        worksheet[cellAddress] = { t: "s", v: "" };
      }

      (worksheet[cellAddress] as any).s = style;
    };

    const styleFullRow = (row: number, style: object, fromCol = 0, toCol = 6) => {
      for (let col = fromCol; col <= toCol; col++) {
        setStyle(row, col, style);
      }
    };

    styleFullRow(titleRow, titleStyle);
    styleFullRow(subtitleRow, subtitleStyle);

    [
      eventSectionRow,
      facilitatorSectionRow,
      descriptionSectionRow,
      topicSectionRow,
      competencySectionRow,
      attendanceSectionRow,
    ].forEach((row) => styleFullRow(row, sectionStyle));

    [summaryRow, summaryRow2].forEach((row) => {
      setStyle(row, 0, summaryLabelStyle);
      setStyle(row, 1, summaryValueStyle);
      setStyle(row, 2, summaryLabelStyle);
      setStyle(row, 3, summaryValueStyle);
      setStyle(row, 4, summaryLabelStyle);
      setStyle(row, 5, summaryValueStyle);
    });

    const range = XLSX.utils.decode_range(worksheet["!ref"] ?? "A1:A1");

    for (let row = 0; row <= range.e.r; row++) {
      for (let col = 0; col <= range.e.c; col++) {
        const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });

        if (!worksheet[cellAddress]) continue;
        if ((worksheet[cellAddress] as any).s) continue;

        const cellValue = worksheet[cellAddress]?.v;

        if (row === eventSectionRow + 1 || row === facilitatorSectionRow + 1 || row === attendanceHeaderRow) {
          (worksheet[cellAddress] as any).s = headerStyle;
        } else if (col === 0 || col === 2) {
          (worksheet[cellAddress] as any).s = labelStyle;
        } else if (!cellValue) {
          (worksheet[cellAddress] as any).s = valueStyle;
        } else {
          (worksheet[cellAddress] as any).s = tableCellStyle;
        }
      }
    }

    const noDataRows = rows
      .map((row, index) => ({
        index,
        hasNoDataText: row.some((value) =>
          String(value ?? "").toLowerCase().includes("no hay")
        ),
      }))
      .filter((item) => item.hasNoDataText)
      .map((item) => item.index);

    noDataRows.forEach((row) => {
      styleFullRow(row, mutedStyle);
    });

    worksheet["!autofilter"] = {
      ref: XLSX.utils.encode_range({
        s: { r: attendanceHeaderRow, c: 0 },
        e: { r: range.e.r, c: 6 },
      }),
    };

    XLSX.utils.book_append_sheet(workbook, worksheet, "Registro asistencia");

    const cleanTitle = selectedEvent.titleEvent
      .replace(/[\\/:*?"<>|]/g, "")
      .replace(/\s+/g, "_");

    XLSX.writeFile(
      workbook,
      `registro_asistencia_evento_${selectedEvent.IdEvent}_${cleanTitle || "evento"}.xlsx`
    );
  };

  const applyStatusFilter = async () => {
    setEventPage(0);
    await loadEvents(true, 0, eventStatusFilter);
  };

  const clearStatusFilter = async () => {
    setEventStatusFilter("");
    setEventPage(0);
    await loadEvents(true, 0, "");
  };

  const changeEventPage = async (_: unknown, newPage: number) => {
    setEventPage(newPage);
    await loadEvents(true, newPage, eventStatusFilter);
  };

  useEffect(() => {
    loadEvents(true, 0, "");
    loadCatalogs();
  }, []);

  return (
    <Stack spacing={3}>
      <Stack sx={{ display: "flex", flexDirection: "row", justifyContent: "space-between", alignItems: "center", }}>
        <Box>
          <Stack sx={{ display: "flex", flexDirection: "row", gap: 1.5, alignItems: "center", }}>
            <EventOutlinedIcon sx={{ color: "#4B2E1F", fontSize: 30 }} />
            <Typography sx={{ color: "#4B2E1F", fontSize: 26, fontWeight: 700, }}>
              Eventos
            </Typography>
          </Stack>
        </Box>
        <Button
          variant="outlined"
          startIcon={<AddCircleOutlineOutlinedIcon />}
          onClick={openCreateModal}
          disabled={loading || saving}
          sx={{ borderColor: "#8B6A55", color: "#4B2E1F", "&:hover": { borderColor: "#4B2E1F", bgcolor: "rgba(75, 46, 31, 0.05)", },}}>
          Crear evento
        </Button>
      </Stack>
      <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 2, p: 2, bgcolor: "#FFFDF8", }}>
        <Stack sx={{ display: "flex", flexDirection: { xs: "column", md: "row" }, gap: 2, alignItems: { xs: "stretch", md: "center" }, justifyContent: "space-between", }}>
          <Stack sx={{ display: "flex", flexDirection: { xs: "column", md: "row" }, gap: 2, alignItems: { xs: "stretch", md: "center" }, }}>
            <FormControl size="small" sx={{ minWidth: 220 }}>
              <InputLabel>Estado</InputLabel>
              <Select label="Estado" value={ eventStatusFilter } onChange={ (event) => setEventStatusFilter(event.target.value) }>
                <MenuItem value="">
                  <em>Todos</em>
                </MenuItem>
                <MenuItem value="Activo">Activo</MenuItem>
                <MenuItem value="Inactivo">Inactivo</MenuItem>
                <MenuItem value="Cancelado">Cancelado</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="contained"
              onClick={applyStatusFilter}
              disabled={loading}
              sx={{
                bgcolor: "#4B2E1F",
                textTransform: "none",
                fontWeight: 600,
                height: 40,
                "&:hover": {
                  bgcolor: "#3A2318",
                },
              }}
            >
              Filtrar
            </Button>
            <Button
              variant="outlined"
              onClick={clearStatusFilter}
              disabled={loading}
              sx={{
                borderColor: "#8B6A55",
                color: "#4B2E1F",
                textTransform: "none",
                fontWeight: 600,
                height: 40,
                "&:hover": {
                  borderColor: "#4B2E1F",
                  bgcolor: "rgba(75, 46, 31, 0.05)",
                },
              }}
            >
              Limpiar
            </Button>
          </Stack>
          <Typography sx={{ color: "#7A6252", fontSize: 13 }}>
            Total registros: {eventsTotal}
          </Typography>
        </Stack>
      </Paper>
      <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 2, overflow: "hidden", }}>
        {loading ? (
          <Box sx={{ py: 6, display: "flex", justifyContent: "center" }}>
            <CircularProgress sx={{ color: "#4B2E1F" }} />
          </Box>
        ) : (
          <>
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: "#F7E8D8" }}>
                  <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                    Título
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                    Fecha
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                    Horario
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                    Lugar
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                    Creado por
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                    Asistentes
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                    Estado
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }} align="center">
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {events.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} align="center" sx={{ color: "#7A6252", py: 3 }}>
                      No hay eventos para mostrar.
                    </TableCell>
                  </TableRow>
                )}
                {events.map((item) => {
                  return (
                    <TableRow key={item.IdEvent} hover>
                      <TableCell>{item.titleEvent}</TableCell>
                      <TableCell>{item.dateEvent}</TableCell>
                      <TableCell>{item.startTimeEvent} - {item.endTimeEvent}</TableCell>
                      <TableCell>{item.eventPlace}</TableCell>
                      <TableCell>{item.createdByUserLogin}</TableCell>
                      <TableCell>
                        {item.attendedPeopleNumber ?? 0}
                        {item.scheduledPeopleNumber ? ` / ${item.scheduledPeopleNumber}` : ""}
                      </TableCell>
                      <TableCell>
                        {(() => {
                          const statusName = item.eventStatus?.nameEventStatus ?? "Sin estado";
                          const normalizedStatus = statusName.trim().toLowerCase();
                          const isActive = normalizedStatus === "activo";
                          const isCancelled = normalizedStatus === "cancelado";
                          const isInactive = normalizedStatus === "inactivo";
                          return (
                            <Chip
                              label={statusName}
                              size="small"
                              sx={{
                                bgcolor: isActive
                                  ? "#E8F5E9"
                                  : isCancelled
                                  ? "#FFEBEE"
                                  : isInactive
                                  ? "#FFF8E1"
                                  : "#ECEFF1",
                                color: isActive
                                  ? "#2E7D32"
                                  : isCancelled
                                  ? "#C62828"
                                  : isInactive
                                  ? "#F57F17"
                                  : "#455A64",
                                fontWeight: 600,
                              }}
                            />
                          );
                        })()}
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={0.5} sx={{ justifyContent: "flex-end" }}>
                          <Tooltip title="Ver Evento">
                            <span>
                              <IconButton
                                size="small"
                                onClick={() => openViewModal(item)}
                                sx={{ color: "#4B2E1F" }}
                              >
                                <VisibilityOutlinedIcon fontSize="small" />
                              </IconButton>
                            </span>
                          </Tooltip>
                          {(() => {
                            const statusName = item.eventStatus?.nameEventStatus ?? "";
                            const isActive = statusName.trim().toLowerCase() === "activo";
                            return (
                              <Tooltip title={isActive ? "Actualizar Evento" : "Solo se pueden actualizar eventos activos"}>
                                <span>
                                  <IconButton
                                    size="small"
                                    onClick={() => openUpdateModal(item)}
                                    disabled={!isActive}
                                    sx={{ color: isActive ? "#8B6A55" : "#BDBDBD" }}
                                  >
                                    <EditOutlinedIcon fontSize="small" />
                                  </IconButton>
                                </span>
                              </Tooltip>
                            );
                          })()}
                          {(() => {
                            const statusName = item.eventStatus?.nameEventStatus ?? "";
                            const isActive = statusName.trim().toLowerCase() === "activo";
                            return (
                              <Tooltip title={isActive ? "Ver QR" : "Solo se puede ver el QR de eventos activos"}>
                                <span>
                                  <IconButton
                                    size="small"
                                    onClick={() => showQr(item.IdEvent)}
                                    disabled={!isActive}
                                    sx={{ color: isActive ? "#4B2E1F" : "#BDBDBD" }}
                                  >
                                    <QrCode2OutlinedIcon fontSize="small" />
                                  </IconButton>
                                </span>
                              </Tooltip>
                            );
                          })()}
                          {(() => {
                            const statusName = item.eventStatus?.nameEventStatus ?? "";
                            const normalizedStatus = statusName.trim().toLowerCase();
                            const isActive = normalizedStatus === "activo";
                            return (
                              <Tooltip title={isActive ? "Cancelar Evento" : "Solo se pueden cancelar eventos activos"}>
                                <span>
                                  <IconButton
                                    size="small"
                                    onClick={() => cancelEvent(item.IdEvent)}
                                    disabled={!isActive}
                                    sx={{ color: isActive ? "#C62828" : "#BDBDBD" }}
                                  >
                                    <CancelOutlinedIcon fontSize="small" />
                                  </IconButton>
                                </span>
                              </Tooltip>
                            );
                          })()}
                        </Stack>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            <TablePagination
              component="div"
              count={eventsTotal}
              page={eventPage}
              onPageChange={changeEventPage}
              rowsPerPage={eventRowsPerPage}
              rowsPerPageOptions={[10]}
              labelRowsPerPage="Registros por página"
              labelDisplayedRows={({ from, to, count }) =>
                `${from}-${to} de ${count !== -1 ? count : `más de ${to}`}`
              }
              sx={{
                borderTop: "1px solid #E0CDBB",
                color: "#4B2E1F",
                ".MuiTablePagination-selectLabel, .MuiTablePagination-displayedRows": {
                  color: "#4B2E1F",
                },
              }}
            />
          </>
        )}
      </Paper>
      <Dialog open={ eventModalOpen } onClose={ closeEventModal } maxWidth="md" fullWidth>
        <DialogTitle sx={{ color: "#4B2E1F", fontWeight: 700, }}>
          <Stack sx={{ display: "flex", flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 2, }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 700, }}>
              {eventModalMode === "create"
                ? "Crear Evento"
                : eventModalMode === "update"
                ? "Actualizar Evento"
                : "Ver Evento"}
            </Typography>
            {eventModalMode === "view" && (
              <Button
                variant="outlined"
                startIcon={<FileDownloadOutlinedIcon />}
                onClick={exportEventToExcel}
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
                Exportar Excel
              </Button>
            )}
          </Stack>
        </DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2}>
            {  
              eventModalMode === "view" && selectedEvent &&
              (
                <Box sx={{ p: 2, borderRadius: 2, bgcolor: "#FFF8F1", border: "1px solid #E0CDBB", }}>
                  <Typography sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                    Estado: {selectedEvent.eventStatus?.nameEventStatus ?? "Sin estado"}
                  </Typography>
                  <Typography sx={{ color: "#7A6252", mt: 0.5 }}>
                    Creado por: {selectedEvent.createdByUserLogin}
                  </Typography>
                  <Typography sx={{ color: "#7A6252", mt: 0.5 }}>
                    URL pública: {selectedEvent.publicUrlEvent ?? "-"}
                  </Typography>
                </Box>
              )
            }
            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr", }, gap: 2,}}>
              <TextField
                required
                label="Título"
                value={eventForm.titleEvent}
                disabled={ eventModalMode === "view" || saving }
                fullWidth
                onChange={(event) =>
                    handleEventFormChange("titleEvent", event.target.value)
                }
              />
              <TextField
                required
                label="Fecha"
                type="date"
                value={eventForm.dateEvent}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                slotProps={{ inputLabel: { shrink: true, }, }}
                onChange={(event) =>
                    handleEventFormChange("dateEvent", event.target.value)
                }
              />
              <TextField
                required
                label="Hora inicio"
                type="time"
                value={eventForm.startTimeEvent}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                slotProps={{ inputLabel: { shrink: true, }, }}
                onChange={(event) =>
                    handleEventFormChange("startTimeEvent", event.target.value)
                }
              />
              <TextField
                required
                label="Hora fin"
                type="time"
                value={eventForm.endTimeEvent}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                slotProps={{ inputLabel: { shrink: true, }, }}
                onChange={(event) =>
                    handleEventFormChange("endTimeEvent", event.target.value)
                }
              />
              <TextField
                required
                label="Duración"
                value={eventForm.durationEvent}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                onChange={(event) =>
                    handleEventFormChange("durationEvent", event.target.value)
                }
              />
              <TextField
                required
                label="Lugar"
                value={eventForm.eventPlace}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                onChange={(event) =>
                    handleEventFormChange("eventPlace", event.target.value)
                }
              />
              <FormControl required fullWidth disabled={ eventModalMode === "view" || saving }>
                <InputLabel>Centro de soluciones</InputLabel>
                <Select label="Centro de soluciones" value={ eventForm.IdSolutionCenter } onChange={(event) => handleEventFormChange("IdSolutionCenter", event.target.value) }>
                  <MenuItem value="">
                    <em>Seleccione</em>
                  </MenuItem>
                  {solutionCenters
                    .filter((item) => item.statusSolutionCenter)
                    .map((item) => (
                      <MenuItem key={ item.IdSolutionCenter } value={ item.IdSolutionCenter.toString() }>
                        { item.codeSolutionCenter } - { item.nameSolutionCenter }
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
              <FormControl required fullWidth disabled={ eventModalMode === "view" || saving }>
                <InputLabel>Motivo de asistencia</InputLabel>
                <Select label="Motivo de asistencia" value={ eventForm.IdAssistanceReason } onChange={(event) => handleEventFormChange("IdAssistanceReason", event.target.value) }>
                  <MenuItem value="">
                    <em>Seleccione</em>
                  </MenuItem>
                  {assistanceReasons.map((item) => (
                    <MenuItem key={ item.IdAssistanceReason } value={ item.IdAssistanceReason.toString() }>
                      { item.nameAssistanceReason }
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl required fullWidth disabled={ eventModalMode === "view" || saving }>
                <InputLabel>Programa de formación</InputLabel>
                <Select label="Programa de formación" value={ eventForm.IdSpecificTrainingProgram } onChange={(event) => handleEventFormChange("IdSpecificTrainingProgram", event.target.value) }>
                  <MenuItem value="">
                    <em>Seleccione</em>
                  </MenuItem>
                  {specificTrainingPrograms.map((item) => (
                    <MenuItem key={ item.IdSpecificTrainingProgram } value={ item.IdSpecificTrainingProgram.toString() }>
                      { item.nameSpecificTrainingProgram }
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl required fullWidth disabled={ eventModalMode === "view" || saving }>
                <InputLabel>Categoría</InputLabel>
                <Select label="Categoría" value={ eventForm.IdEventCategory } onChange={(event) => handleEventFormChange("IdEventCategory", event.target.value) }>
                  <MenuItem value="">
                    <em>Seleccione</em>
                  </MenuItem>
                  { eventCategories.map((item) => (
                    <MenuItem key={ item.IdEventCategory } value={ item.IdEventCategory.toString() }>
                      { item.nameEventCategory }
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                required
                label="Nombre facilitador"
                value={eventForm.facilitatorNameEvent}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                onChange={(event) =>
                    handleEventFormChange("facilitatorNameEvent", event.target.value)
                }
              />
              <TextField
                required
                label="Empresa facilitador"
                value={eventForm.facilitatorCompanyEvent}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                onChange={(event) =>
                    handleEventFormChange("facilitatorCompanyEvent", event.target.value)
                }
              />
              <TextField
                required
                label="Cargo facilitador"
                value={eventForm.facilitatorPositionEvent}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                onChange={(event) =>
                    handleEventFormChange("facilitatorPositionEvent", event.target.value)
                }
              />
              <TextField
                label="Nombre segundo facilitador"
                value={eventForm.secondFacilitatorNameEvent}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                onChange={(event) =>
                  handleEventFormChange("secondFacilitatorNameEvent", event.target.value)
                }
              />
              <TextField
                label="Empresa segundo facilitador"
                value={eventForm.secondFacilitatorCompanyEvent}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                onChange={(event) =>
                  handleEventFormChange("secondFacilitatorCompanyEvent", event.target.value)
                }
              />
              <TextField
                label="Cargo segundo facilitador"
                value={eventForm.secondFacilitatorPositionEvent}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                onChange={(event) =>
                  handleEventFormChange("secondFacilitatorPositionEvent", event.target.value)
                }
              />
              <TextField
                required
                label="Personas programadas"
                type="number"
                value={eventForm.scheduledPeopleNumber}
                disabled={eventModalMode === "view" || saving}
                fullWidth
                onChange={(event) =>
                    handleEventFormChange("scheduledPeopleNumber", event.target.value)
                }
              />
              <FormControl required disabled={eventModalMode === "view" || saving}>
                <RadioGroup
                  row
                  value={
                    eventForm.isPaidTrainingEvent === null
                      ? ""
                      : eventForm.isPaidTrainingEvent
                      ? "paid"
                      : "workday"
                  }
                  onChange={(event) => {
                    const value = event.target.value;
                    setEventForm((prev) => ({
                      ...prev,
                      isPaidTrainingEvent: value === "paid",
                    }));
                  }}
                >
                  <FormControlLabel
                    value="workday"
                    control={
                      <Radio
                        sx={{
                          color: "#8B6A55",
                          "&.Mui-checked": {
                            color: "#4B2E1F",
                          },
                        }}
                      />
                    }
                    label="Dentro del horario laboral"
                  />
                  <FormControlLabel
                    value="paid"
                    control={
                      <Radio
                        sx={{
                          color: "#8B6A55",
                          "&.Mui-checked": {
                            color: "#4B2E1F",
                          },
                        }}
                      />
                    }
                    label="Evento pago"
                  />
                </RadioGroup>
              </FormControl>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={Boolean(eventForm.isNewStaffInductionEvent)}
                    onChange={(event) =>
                      setEventForm((prev) => ({
                        ...prev,
                        isNewStaffInductionEvent: event.target.checked,
                      }))
                    }
                    disabled={eventModalMode === "view"}
                    sx={{ color: "#8B6A55", "&.Mui-checked": { color: "#4B2E1F", },}}/>
                }
                label="Inducción a personal nuevo"
              />
            </Box>
            <TextField
              required
              label="Descripción"
              value={eventForm.descriptionEvent}
              disabled={eventModalMode === "view" || saving}
              fullWidth
              multiline
              minRows={2}
              onChange={(event) =>
                handleEventFormChange("descriptionEvent", event.target.value)
              }
            />
            <TextField
              label="Observaciones"
              value={eventForm.observationsEvent}
              disabled={eventModalMode === "view" || saving}
              fullWidth
              multiline
              minRows={2}
              onChange={(event) =>
                handleEventFormChange("observationsEvent", event.target.value)
              }
            />
            <Box>
              <Typography sx={{ color: "#4B2E1F", fontWeight: 700, mb: 1 }}>
                Temas tratados
              </Typography>
              { eventModalMode !== "view" && (
                <Stack sx={{ display: "flex", flexDirection: "row", gap: 1, mb: 2, }}>
                  <TextField
                    label="Escribe un tema"
                    value={topicInput}
                    disabled={saving}
                    fullWidth
                    onChange={(event) => setTopicInput(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        event.preventDefault();
                        addTopic();
                      }
                    }}
                  />
                  <Button
                    variant="outlined"
                    onClick={addTopic}
                    disabled={saving}
                    sx={{ minWidth: 120, borderColor: "#8B6A55", color: "#4B2E1F", "&:hover": { borderColor: "#4B2E1F", bgcolor: "rgba(75, 46, 31, 0.05)", },}}
                  >
                    Agregar
                  </Button>
                </Stack>
              )}
              <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 2, overflow: "hidden", }}>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: "#F7E8D8" }}>
                      <TableCell sx={{ fontWeight: 700, color: "#4B2E1F", width: 80 }}>
                        #
                      </TableCell>
                      <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>
                        Tema
                      </TableCell>
                      {eventModalMode !== "view" && (
                        <TableCell align="center" sx={{ fontWeight: 700, color: "#4B2E1F", width: 100 }}>
                          Acción
                        </TableCell>
                      )}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {eventForm.topics.length === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={eventModalMode !== "view" ? 3 : 2}
                          align="center"
                          sx={{ color: "#7A6252", py: 2 }}
                        >
                          No hay temas agregados.
                        </TableCell>
                      </TableRow>
                    ) : (
                      eventForm.topics.map((topic, index) => (
                        <TableRow key={`${topic}-${index}`} hover>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell>{topic}</TableCell>
                          {eventModalMode !== "view" && (
                            <TableCell align="center">
                              <Tooltip title="Eliminar tema">
                                <span>
                                  <IconButton
                                    size="small"
                                    onClick={() => removeTopic(index)}
                                    disabled={saving}
                                    sx={{ color: "#C62828" }}
                                  >
                                    <DeleteOutlineOutlinedIcon fontSize="small" />
                                  </IconButton>
                                </span>
                              </Tooltip>
                            </TableCell>
                          )}
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </Paper>
            </Box>
            <FormControl required fullWidth disabled={eventModalMode === "view" || saving}>
              <InputLabel id="competencies-label" shrink>
                Competencias
              </InputLabel>
              <Select
                labelId="competencies-label"
                multiple
                displayEmpty
                value={eventForm.competencies}
                input={<OutlinedInput label="Competencias" />}
                renderValue={(selected) => {
                  const selectedIds = selected as number[];

                  if (selectedIds.length === 0) {
                    return (
                      <Typography component="span" sx={{ color: "#7A6252" }}>
                        Seleccione
                      </Typography>
                    );
                  }
                  return selectedIds
                    .map((IdCompetency) => {
                      const competency = competencies.find(
                        (item) => item.IdCompetency === IdCompetency
                      );

                      return competency?.nameCompetency ?? String(IdCompetency);
                    })
                    .join(", ");
                }}
                onChange={(event) => {
                  const value = event.target.value;
                  setEventForm((prev) => ({
                    ...prev,
                    competencies:
                      typeof value === "string"
                        ? value.split(",").map(Number)
                        : value.map(Number),
                  }));
                }}
              >
                {competencies.map((item) => (
                  <MenuItem key={item.IdCompetency} value={item.IdCompetency}>
                    <Checkbox
                      checked={eventForm.competencies.includes(item.IdCompetency)}
                      sx={{
                        color: "#8B6A55",
                        "&.Mui-checked": {
                          color: "#4B2E1F",
                        },
                      }}
                    />
                    <ListItemText primary={item.nameCompetency} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Box>
              <Typography sx={{ color: "#4B2E1F", fontWeight: 700, mb: 1 }}>
                Pensum{" "}
                {eventModalMode === "create" && (
                  <Box component="span" sx={{ color: "#C62828" }}>
                    *
                  </Box>
                )}
              </Typography>

              {eventModalMode === "view" ? (
                selectedEvent?.pensumPathEvent ? (
                  <Stack
                    sx={{
                      display: "flex",
                      flexDirection: "row",
                      gap: 1,
                      alignItems: "center",
                    }}
                  >
                    <Typography sx={{ color: "#7A6252" }}>
                      {selectedEvent.pensumOriginalNameEvent || "Pensum adjunto"}
                    </Typography>

                    <Button
                      variant="outlined"
                      onClick={() =>
                        window.open(getBackendFileUrl(selectedEvent.pensumPathEvent), "_blank")
                      }
                      sx={{
                        borderColor: "#8B6A55",
                        color: "#4B2E1F",
                        "&:hover": {
                          borderColor: "#4B2E1F",
                          bgcolor: "rgba(75, 46, 31, 0.05)",
                        },
                      }}
                    >
                      Ver archivo
                    </Button>
                  </Stack>
                ) : (
                  <Typography sx={{ color: "#7A6252" }}>
                    No hay pensum adjunto.
                  </Typography>
                )
              ) : (
                <>
                  <Button
                    variant="outlined"
                    component="label"
                    disabled={saving}
                    sx={{
                      borderColor: "#8B6A55",
                      color: "#4B2E1F",
                      "&:hover": {
                        borderColor: "#4B2E1F",
                        bgcolor: "rgba(75, 46, 31, 0.05)",
                      },
                    }}
                  >
                    Seleccionar archivo
                    <input
                      hidden
                      type="file"
                      accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
                      onChange={(event) => {
                        const file = event.target.files?.[0] ?? null;
                        setPensumFile(file);
                      }}
                    />
                  </Button>

                  <Typography sx={{ mt: 1, color: "#7A6252" }}>
                    {pensumFile
                      ? `Archivo seleccionado: ${pensumFile.name}`
                      : selectedEvent?.pensumOriginalNameEvent
                      ? `Archivo actual: ${selectedEvent.pensumOriginalNameEvent}`
                      : "No se ha seleccionado archivo."}
                  </Typography>

                  {eventModalMode === "update" && selectedEvent?.pensumPathEvent && (
                    <Button
                      variant="text"
                      onClick={() =>
                        window.open(getBackendFileUrl(selectedEvent.pensumPathEvent), "_blank")
                      }
                      sx={{
                        mt: 1,
                        color: "#4B2E1F",
                        textTransform: "none",
                      }}
                    >
                      Ver archivo actual
                    </Button>
                  )}
                </>
              )}
            </Box>
          </Stack>
          {eventModalMode === "view" && (
            <Box sx={{ mt: 4 }}>
              <Typography sx={{ color: "#4B2E1F", fontWeight: 700, fontSize: 18, mb: 2, }}>
                Asistencia
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: "#F7E8D8" }}>
                    <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>Cédula</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>Nombre</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>Cargo</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>Teléfono</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>Centro de soluciones</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>IP</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }}>Fecha registro</TableCell>
                    <TableCell sx={{ fontWeight: 700, color: "#4B2E1F" }} align="center">Firma</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {eventAttendances.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} align="center" sx={{ color: "#7A6252" }}>
                        No hay asistentes registrados para este evento.
                      </TableCell>
                    </TableRow>
                  ) : (
                    eventAttendances.map((attendance) => (
                      <TableRow key={attendance.IdAttendance}>
                        <TableCell>
                          {attendance.attendancePerson?.documentNumberAttendancePerson ?? ""}
                        </TableCell>
                        <TableCell>
                          {attendance.attendancePerson?.fullNameAttendancePerson ?? ""}
                        </TableCell>
                        <TableCell>
                          {attendance.attendancePerson?.positionAttendancePerson ?? ""}
                        </TableCell>
                        <TableCell>
                          {attendance.attendancePerson?.phoneAttendancePerson ?? ""}
                        </TableCell>
                        <TableCell>
                          {getSolutionCenterName(attendance.attendancePerson?.IdSolutionCenter)}
                        </TableCell>
                        <TableCell>
                          {attendance.ipAddressAttendance ?? ""}
                        </TableCell>
                        <TableCell>
                          {attendance.createdAt
                            ? new Date(attendance.createdAt).toLocaleString("es-CO")
                            : ""}
                        </TableCell>
                        <TableCell align="center">
                          <Tooltip title="Ver firma">
                            <span>
                              <IconButton
                                size="small"
                                disabled={!attendance.attendancePerson?.signaturePathAttendancePerson}
                                onClick={() =>
                                  openSignatureModal(
                                    attendance.attendancePerson?.signaturePathAttendancePerson,
                                    attendance.attendancePerson?.fullNameAttendancePerson
                                  )
                                }
                                sx={{ color: attendance.attendancePerson?.signaturePathAttendancePerson ? "#4B2E1F" : "#BDBDBD", }}
                              >
                                <DrawOutlinedIcon fontSize="small" />
                              </IconButton>
                            </span>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>  
              </Table>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={closeEventModal} disabled={saving} sx={{ color: "#4B2E1F" }}>
            { eventModalMode === "view" ? "Cerrar" : "Cancelar" }
          </Button>
          {
            eventModalMode !== "view" &&
            (
                <Button
                variant="contained"
                onClick={saveEvent}
                disabled={saving}
                sx={{ bgcolor: "#4B2E1F", "&:hover": { bgcolor: "#3A2318", },}}>
                { saving
                    ? "Guardando..."
                    : eventModalMode === "create"
                    ? "Crear evento"
                    : "Actualizar evento"}
                </Button>
            )
          }
        </DialogActions>
      </Dialog>
      <Dialog open={ confirmCancelOpen } onClose={ closeConfirmCancelModal } maxWidth="xs" fullWidth>
        <DialogTitle sx={{ color: "#4B2E1F", fontWeight: 700, textAlign: "center", }}>
          Cancelar evento
        </DialogTitle>
        <DialogContent dividers sx={{ textAlign: "center" }}>
          <Typography sx={{ color: "#4B2E1F" }}>
            ¿Estás seguro de cancelar este evento?
          </Typography>
          <Typography sx={{ color: "#7A6252", mt: 1 }}>
            Esta acción dejará el evento en estado cancelado y el enlace de asistencia ya no estará disponible.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={ closeConfirmCancelModal } disabled={ loading } sx={{ color: "#4B2E1F" }}>
            No, volver
          </Button>
          <Button variant="contained" color="error" onClick={ confirmCancelEvent } disabled={ loading } sx={{ bgcolor: "#4B2E1F", "&:hover": { bgcolor: "#3A2318", },}}>
            {loading ? "Cancelando..." : "Sí, cancelar"}
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog open={ qrModalOpen } onClose={ closeQrModal } maxWidth="xs" fullWidth>
        <DialogTitle sx={{ color: "#4B2E1F", fontWeight: 700, textAlign: "center", }}>
          QR del evento
        </DialogTitle>
        <DialogContent dividers sx={{ textAlign: "center" }}>
          {qrInfo?.qrPathEvent ? (
            <Box>
              <Box component="img" src={ getBackendFileUrl(qrInfo.qrPathEvent) } alt="QR del evento" sx={{ width: 220, height: 220, objectFit: "contain", mb: 2, }}/>
              <Typography sx={{ color: "#4B2E1F", fontWeight: 700, mb: 1 }}>
                Link del formulario
              </Typography>
              <Typography sx={{ color: "#7A6252", wordBreak: "break-all", fontSize: 14, }}>
                {qrInfo.publicUrlEvent}
              </Typography>
            </Box>
          ) : (
            <Typography sx={{ color: "#7A6252" }}>
              No se encontró imagen QR para este evento.
            </Typography>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={ closeQrModal } sx={{ color: "#4B2E1F" }}>
            Cerrar
          </Button>
          <Button
            variant="outlined"
            onClick={() => {
              if (qrInfo?.publicUrlEvent) {
                navigator.clipboard.writeText(qrInfo.publicUrlEvent);
                showResponseModal(
                  "success",
                  "Link copiado",
                  "El link del formulario fue copiado correctamente."
                );
              }
            }}
            sx={{
              borderColor: "#8B6A55",
              color: "#4B2E1F",
              "&:hover": {
                borderColor: "#4B2E1F",
                bgcolor: "rgba(75, 46, 31, 0.05)",
              },
            }}
          >
            Copiar link
          </Button>
          <Button
            variant="contained"
            onClick={downloadQrImage}
            disabled={!qrInfo?.qrPathEvent}
            sx={{
              bgcolor: "#4B2E1F",
              "&:hover": {
                bgcolor: "#3A2318",
              },
            }}
          >
            Descargar QR
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog open={ signatureModalOpen } onClose={ closeSignatureModal } maxWidth="sm" fullWidth>
        <DialogTitle sx={{ color: "#4B2E1F", fontWeight: 700, textAlign: "center", }}>
          Ver firma
        </DialogTitle>
        <DialogContent dividers sx={{ textAlign: "center" }}>
          <Typography sx={{ color: "#4B2E1F", fontWeight: 700, mb: 2 }}>
            {signaturePersonName}
          </Typography>
          {signatureImageUrl ? (
            <Box
              component="img"
              src={`${signatureImageUrl}?v=${Date.now()}`}
              alt="Firma del asistente"
              sx={{
                width: "100%",
                maxWidth: 520,
                height: 220,
                objectFit: "contain",
                border: "1px solid #E8D8C8",
                borderRadius: 2,
                bgcolor: "#FFFFFF",
                p: 1,
              }}
            />
          ) : (
            <Typography sx={{ color: "#7A6252" }}>
              No se encontró firma registrada.
            </Typography>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={ closeSignatureModal } sx={{ color: "#4B2E1F" }}>
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