import { Alert, Box, Button, Chip, CircularProgress, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControl, FormControlLabel, FormHelperText, IconButton, InputLabel, ListItemText, ListSubheader, MenuItem, OutlinedInput, Paper, Radio, RadioGroup, Select, Stack, Table, TableBody, TableCell, TableHead, TablePagination, TableRow, TextField, Tooltip, Typography, } from "@mui/material";
import type { AssistanceReason, Competency, EventCategory, SpecificTrainingProgram, } from "../models/EventCatalog";
import { ResponseModal, type ResponseModalSeverity, } from "../components/ResponseModal";
import { OnlyOfficeViewer } from "../components/OnlyOfficeViewer";
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
import type { OnlyOfficePreview } from "../models/OnlyOffice";
import { getErrorMessage } from "../services/errorService";
import { getBackendFileUrl } from "../services/backendFileService";
import { eventService } from "../services/eventService";
import { useEffect, useState } from "react";
import JSZip from "jszip";
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
type FacilitatorType = "" | "INTERNO" | "EXTERNO";

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
  facilitatorTypeEvent: FacilitatorType;
  facilitatorCompanyEvent: string;
  facilitatorPositionEvent: string;
  secondFacilitatorNameEvent: string;
  secondFacilitatorTypeEvent: FacilitatorType;
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
  facilitatorTypeEvent: "",
  facilitatorCompanyEvent: "",
  facilitatorPositionEvent: "",
  secondFacilitatorNameEvent: "",
  secondFacilitatorTypeEvent: "",
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

const createUppercaseFields = new Set<keyof EventFormState>([
  "titleEvent",
  "descriptionEvent",
  "facilitatorNameEvent",
  "facilitatorCompanyEvent",
  "facilitatorPositionEvent",
  "secondFacilitatorNameEvent",
  "secondFacilitatorCompanyEvent",
  "secondFacilitatorPositionEvent",
  "observationsEvent",
  "eventPlace",
]);

const onlyOfficePensumExtensions = new Set([
  "doc",
  "docm",
  "docx",
  "odt",
  "rtf",
  "txt",
  "csv",
  "ods",
  "xls",
  "xlsb",
  "xlsm",
  "xlsx",
  "odp",
  "ppt",
  "pptm",
  "pptx",
]);

const getBogotaDateTime = () => {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Bogota",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date());
  const getPart = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((part) => part.type === type)?.value ?? "";

  return {
    date: `${getPart("year")}-${getPart("month")}-${getPart("day")}`,
    time: `${getPart("hour")}:${getPart("minute")}`,
  };
};

const formatDropdownOption = (value: string) =>
  value.toLocaleUpperCase("es-CO");

const calculateDuration = (startTime: string, endTime: string) => {
  const [startHour, startMinute] = startTime
    .substring(0, 5)
    .split(":")
    .map(Number);
  const [endHour, endMinute] = endTime
    .substring(0, 5)
    .split(":")
    .map(Number);

  if (
    [startHour, startMinute, endHour, endMinute].some(Number.isNaN) ||
    startTime.length < 5 ||
    endTime.length < 5
  ) {
    return "";
  }

  const totalMinutes = endHour * 60 + endMinute - (startHour * 60 + startMinute);

  if (totalMinutes <= 0) {
    return "";
  }

  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  const parts: string[] = [];

  if (hours > 0) {
    parts.push(`${hours} ${hours === 1 ? "HORA" : "HORAS"}`);
  }

  if (minutes > 0) {
    parts.push(`${minutes} ${minutes === 1 ? "MINUTO" : "MINUTOS"}`);
  }

  return parts.join(" ");
};

const compressSignatureForExcel = async (signaturePath: string) => {
  const signatureUrl = getBackendFileUrl(signaturePath);
  const accessToken = localStorage.getItem("accessToken");
  const response = await fetch(signatureUrl, {
    headers: accessToken
      ? { Authorization: `Bearer ${accessToken}` }
      : undefined,
  });

  if (!response.ok) {
    throw new Error("No fue posible descargar la firma.");
  }

  const signatureBlob = await response.blob();
  const objectUrl = URL.createObjectURL(signatureBlob);

  try {
    const image = new Image();
    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve();
      image.onerror = () => reject(new Error("La firma no es una imagen válida."));
      image.src = objectUrl;
    });

    const maxWidth = 180;
    const maxHeight = 54;
    const scale = Math.min(
      maxWidth / Math.max(image.naturalWidth, 1),
      maxHeight / Math.max(image.naturalHeight, 1),
      1
    );
    const width = Math.max(Math.round(image.naturalWidth * scale), 1);
    const height = Math.max(Math.round(image.naturalHeight * scale), 1);
    const canvas = document.createElement("canvas");
    canvas.width = maxWidth;
    canvas.height = maxHeight;
    const context = canvas.getContext("2d");

    if (!context) {
      throw new Error("No fue posible procesar la firma.");
    }

    context.fillStyle = "#FFFFFF";
    context.fillRect(0, 0, maxWidth, maxHeight);
    context.drawImage(
      image,
      Math.round((maxWidth - width) / 2),
      Math.round((maxHeight - height) / 2),
      width,
      height
    );

    return canvas.toDataURL("image/jpeg", 0.6);
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
};

interface ExcelSignaturePlacement {
  excelRowNumber: number;
  imageData: string;
}

const embedSignaturesWithoutChangingWorkbook = async (
  workbookData: ArrayBuffer,
  signatures: ExcelSignaturePlacement[]
) => {
  if (signatures.length === 0) {
    return new Uint8Array(workbookData);
  }

  const zip = await JSZip.loadAsync(workbookData);
  const worksheetPath = "xl/worksheets/sheet1.xml";
  const worksheetRelationshipsPath =
    "xl/worksheets/_rels/sheet1.xml.rels";
  const worksheetFile = zip.file(worksheetPath);

  if (!worksheetFile) {
    throw new Error("No fue posible encontrar la hoja de asistencia.");
  }

  let worksheetXml = await worksheetFile.async("string");

  if (/<drawing\b/i.test(worksheetXml)) {
    throw new Error("La hoja ya contiene un dibujo que no se puede reemplazar.");
  }

  const drawingIndexes = Object.keys(zip.files)
    .map((path) => path.match(/^xl\/drawings\/drawing(\d+)\.xml$/)?.[1])
    .filter((value): value is string => Boolean(value))
    .map(Number);
  const drawingIndex = Math.max(0, ...drawingIndexes) + 1;
  const drawingPath = `xl/drawings/drawing${drawingIndex}.xml`;
  const drawingRelationshipsPath =
    `xl/drawings/_rels/drawing${drawingIndex}.xml.rels`;
  const existingWorksheetRelationships = zip.file(
    worksheetRelationshipsPath
  );
  let worksheetRelationshipsXml = existingWorksheetRelationships
    ? await existingWorksheetRelationships.async("string")
    : '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>';
  const relationshipIndexes = Array.from(
    worksheetRelationshipsXml.matchAll(/Id="rId(\d+)"/g),
    (match) => Number(match[1])
  );
  const drawingRelationshipId =
    `rId${Math.max(0, ...relationshipIndexes) + 1}`;
  const drawingRelationship =
    `<Relationship Id="${drawingRelationshipId}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing${drawingIndex}.xml"/>`;

  worksheetRelationshipsXml = worksheetRelationshipsXml.replace(
    "</Relationships>",
    `${drawingRelationship}</Relationships>`
  );
  worksheetXml = worksheetXml.replace(
    "</worksheet>",
    `<drawing r:id="${drawingRelationshipId}"/></worksheet>`
  );

  const mediaIndexes = Object.keys(zip.files)
    .map((path) => path.match(/^xl\/media\/image(\d+)\.[^.]+$/)?.[1])
    .filter((value): value is string => Boolean(value))
    .map(Number);
  let nextMediaIndex = Math.max(0, ...mediaIndexes) + 1;
  const drawingAnchors: string[] = [];
  const imageRelationships: string[] = [];

  signatures.forEach((signature, index) => {
    const mediaIndex = nextMediaIndex++;
    const imageName = `image${mediaIndex}.jpeg`;
    const imageRelationshipId = `rId${index + 1}`;
    const base64Content = signature.imageData.replace(
      /^data:image\/[a-zA-Z0-9.+-]+;base64,/,
      ""
    );
    const drawingRow = signature.excelRowNumber - 1;

    zip.file(`xl/media/${imageName}`, base64Content, { base64: true });
    imageRelationships.push(
      `<Relationship Id="${imageRelationshipId}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/${imageName}"/>`
    );
    drawingAnchors.push(
      `<xdr:oneCellAnchor>` +
        `<xdr:from><xdr:col>7</xdr:col><xdr:colOff>95250</xdr:colOff><xdr:row>${drawingRow}</xdr:row><xdr:rowOff>19050</xdr:rowOff></xdr:from>` +
        `<xdr:ext cx="1619250" cy="476250"/>` +
        `<xdr:pic>` +
          `<xdr:nvPicPr><xdr:cNvPr id="${index + 1}" name="Firma ${index + 1}"/><xdr:cNvPicPr><a:picLocks noChangeAspect="1"/></xdr:cNvPicPr></xdr:nvPicPr>` +
          `<xdr:blipFill><a:blip r:embed="${imageRelationshipId}"/><a:stretch><a:fillRect/></a:stretch></xdr:blipFill>` +
          `<xdr:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="1619250" cy="476250"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></xdr:spPr>` +
        `</xdr:pic><xdr:clientData/>` +
      `</xdr:oneCellAnchor>`
    );
  });

  const drawingXml =
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">' +
    drawingAnchors.join("") +
    "</xdr:wsDr>";
  const drawingRelationshipsXml =
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
    imageRelationships.join("") +
    "</Relationships>";
  const contentTypesFile = zip.file("[Content_Types].xml");

  if (!contentTypesFile) {
    throw new Error("No fue posible validar el formato del archivo Excel.");
  }

  let contentTypesXml = await contentTypesFile.async("string");
  contentTypesXml = contentTypesXml.replace(
    "</Types>",
    `<Override PartName="/${drawingPath}" ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/></Types>`
  );

  zip.file(worksheetPath, worksheetXml);
  zip.file(worksheetRelationshipsPath, worksheetRelationshipsXml);
  zip.file(drawingPath, drawingXml);
  zip.file(drawingRelationshipsPath, drawingRelationshipsXml);
  zip.file("[Content_Types].xml", contentTypesXml);

  return zip.generateAsync({
    type: "uint8array",
    compression: "DEFLATE",
    compressionOptions: { level: 6 },
  });
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
  const [competenciesMenuOpen, setCompetenciesMenuOpen] = useState(false);
  const [confirmCancelOpen, setConfirmCancelOpen] = useState(false);
  const [pensumFile, setPensumFile] = useState<File | null>(null);
  const [pensumPreviewUrl, setPensumPreviewUrl] = useState("");
  const [pensumPreviewOpen, setPensumPreviewOpen] = useState(false);
  const [onlyOfficePreview, setOnlyOfficePreview] = useState<OnlyOfficePreview | null>(null);
  const [pensumPreviewLoading, setPensumPreviewLoading] = useState(false);
  const [pensumPreviewError, setPensumPreviewError] = useState("");
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
  const [exportingExcel, setExportingExcel] = useState(false);
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

  const resetPensumPreview = () => {
    setPensumPreviewOpen(false);
    setPensumPreviewUrl("");
    setOnlyOfficePreview(null);
    setPensumPreviewLoading(false);
    setPensumPreviewError("");
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

  const eventToForm = (event: Event): EventFormState => {
    const startTimeEvent = normalizeTimeForInput(event.startTimeEvent);
    const endTimeEvent = normalizeTimeForInput(event.endTimeEvent);
    const facilitatorTypeEvent: FacilitatorType =
      event.facilitatorTypeEvent ??
      (event.facilitatorCompanyEvent
        ? "EXTERNO"
        : event.facilitatorNameEvent
          ? "INTERNO"
          : "");
    const secondFacilitatorTypeEvent: FacilitatorType =
      event.secondFacilitatorTypeEvent ??
      (event.secondFacilitatorCompanyEvent
        ? "EXTERNO"
        : event.secondFacilitatorNameEvent
          ? "INTERNO"
          : "");

    return {
      titleEvent: event.titleEvent ?? "",
      descriptionEvent: event.descriptionEvent ?? "",
      dateEvent: event.dateEvent ?? "",
      durationEvent:
        calculateDuration(startTimeEvent, endTimeEvent) || event.durationEvent || "",
      startTimeEvent,
      endTimeEvent,
      IdSolutionCenter: event.IdSolutionCenter?.toString() ?? "",
      IdAssistanceReason: event.IdAssistanceReason?.toString() ?? "",
      IdSpecificTrainingProgram: event.IdSpecificTrainingProgram?.toString() ?? "",
      IdEventCategory: event.IdEventCategory?.toString() ?? "",
      facilitatorNameEvent: event.facilitatorNameEvent ?? "",
      facilitatorTypeEvent,
      facilitatorCompanyEvent:
        facilitatorTypeEvent === "EXTERNO"
          ? event.facilitatorCompanyEvent ?? ""
          : "",
      facilitatorPositionEvent: event.facilitatorPositionEvent ?? "",
      secondFacilitatorNameEvent: event.secondFacilitatorNameEvent ?? "",
      secondFacilitatorTypeEvent,
      secondFacilitatorCompanyEvent:
        secondFacilitatorTypeEvent === "EXTERNO"
          ? event.secondFacilitatorCompanyEvent ?? ""
          : "",
      secondFacilitatorPositionEvent:
        event.secondFacilitatorPositionEvent ?? "",
      scheduledPeopleNumber: event.scheduledPeopleNumber?.toString() ?? "",
      isPaidTrainingEvent: event.isPaidTrainingEvent ?? false,
      isNewStaffInductionEvent: event.isNewStaffInductionEvent ?? false,
      observationsEvent: event.observationsEvent ?? "",
      eventPlace: event.eventPlace ?? "",
      topics: event.topics?.map((topic) => topic.nameEventTopic) ?? [],
      competencies:
        event.competencies?.map((item) => item.IdCompetency) ?? [],
    };
  };

  const openCreateModal = () => {
    resetPensumPreview();
    setCompetenciesMenuOpen(false);
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
      resetPensumPreview();
      setCompetenciesMenuOpen(false);
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
    resetPensumPreview();
    setCompetenciesMenuOpen(false);
    setSelectedEvent(event);
    setEventForm(eventToForm(event));
    setTopicInput("");
    setPensumFile(null);
    setEventModalMode("update");
    setEventModalOpen(true);
  };

  const closeEventModal = () => {
    if (saving) return;
    resetPensumPreview();
    setCompetenciesMenuOpen(false);
    setEventModalOpen(false);
    setSelectedEvent(null);
    setPensumFile(null);
    setEventForm(emptyEventForm);
  };

  const handleEventFormChange = (field: keyof EventFormState, value: string) => {
    const normalizedValue =
      eventModalMode === "create" && createUppercaseFields.has(field)
        ? value.toLocaleUpperCase("es-CO")
        : value;

    setEventForm((prev) => {
      const nextForm = {
        ...prev,
        [field]: normalizedValue,
      } as EventFormState;

      if (field === "startTimeEvent" || field === "endTimeEvent") {
        nextForm.durationEvent = calculateDuration(
          nextForm.startTimeEvent,
          nextForm.endTimeEvent
        );
      }

      if (field === "facilitatorTypeEvent" && normalizedValue === "INTERNO") {
        nextForm.facilitatorCompanyEvent = "";
      }

      if (
        field === "secondFacilitatorTypeEvent" &&
        normalizedValue === "INTERNO"
      ) {
        nextForm.secondFacilitatorCompanyEvent = "";
      }

      return nextForm;
    });
  };

  const addTopic = () => {
    const cleanTopic =
      eventModalMode === "create"
        ? topicInput.trim().toLocaleUpperCase("es-CO")
        : topicInput.trim();

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

  const buildEventPayload = () => {
    const hasSecondFacilitator = Boolean(
      eventForm.secondFacilitatorNameEvent.trim() ||
        eventForm.secondFacilitatorTypeEvent ||
        eventForm.secondFacilitatorCompanyEvent.trim() ||
        eventForm.secondFacilitatorPositionEvent.trim()
    );

    return {
      titleEvent: eventForm.titleEvent,
      descriptionEvent: eventForm.descriptionEvent || null,
      dateEvent: eventForm.dateEvent,
      durationEvent:
        calculateDuration(eventForm.startTimeEvent, eventForm.endTimeEvent) ||
        null,
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
      facilitatorTypeEvent: eventForm.facilitatorTypeEvent || null,
      facilitatorCompanyEvent:
        eventForm.facilitatorTypeEvent === "EXTERNO"
          ? eventForm.facilitatorCompanyEvent || null
          : null,
      facilitatorPositionEvent: eventForm.facilitatorPositionEvent || null,
      secondFacilitatorNameEvent: hasSecondFacilitator
        ? eventForm.secondFacilitatorNameEvent || null
        : null,
      secondFacilitatorTypeEvent: hasSecondFacilitator
        ? eventForm.secondFacilitatorTypeEvent || null
        : null,
      secondFacilitatorCompanyEvent:
        hasSecondFacilitator &&
        eventForm.secondFacilitatorTypeEvent === "EXTERNO"
          ? eventForm.secondFacilitatorCompanyEvent || null
          : null,
      secondFacilitatorPositionEvent: hasSecondFacilitator
        ? eventForm.secondFacilitatorPositionEvent || null
        : null,
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
      { value: eventForm.startTimeEvent, label: "Hora inicio" },
      { value: eventForm.endTimeEvent, label: "Hora fin" },
      { value: eventForm.IdSolutionCenter, label: "Centro de soluciones" },
      { value: eventForm.IdAssistanceReason, label: "Motivo de asistencia" },
      { value: eventForm.IdSpecificTrainingProgram, label: "Programa de formación" },
      { value: eventForm.IdEventCategory, label: "Categoría" },
      { value: eventForm.facilitatorNameEvent, label: "Nombre facilitador" },
      { value: eventForm.facilitatorTypeEvent, label: "Tipo de facilitador" },
      { value: eventForm.facilitatorPositionEvent, label: "Cargo facilitador" },
      { value: eventForm.scheduledPeopleNumber, label: "Personas programadas" },
      { value: eventForm.eventPlace, label: "Lugar" },
    ];
    const missingField = requiredFields.find((field) => !field.value || field.value.toString().trim() === "");
    if (missingField) {
      showResponseModal("warning", "Campo obligatorio", `El campo "${missingField.label}" es obligatorio.`);
      return false;
    }

    if (eventForm.startTimeEvent >= eventForm.endTimeEvent) {
      showResponseModal(
        "warning",
        "Horario no válido",
        "La hora de inicio debe ser menor que la hora de fin."
      );
      return false;
    }

    if (
      eventForm.facilitatorTypeEvent === "EXTERNO" &&
      !eventForm.facilitatorCompanyEvent.trim()
    ) {
      showResponseModal(
        "warning",
        "Campo obligatorio",
        'El campo "Empresa del facilitador" es obligatorio para un facilitador externo.'
      );
      return false;
    }

    const hasSecondFacilitatorData = Boolean(
      eventForm.secondFacilitatorNameEvent.trim() ||
        eventForm.secondFacilitatorTypeEvent ||
        eventForm.secondFacilitatorCompanyEvent.trim() ||
        eventForm.secondFacilitatorPositionEvent.trim()
    );

    if (hasSecondFacilitatorData && !eventForm.secondFacilitatorNameEvent.trim()) {
      showResponseModal(
        "warning",
        "Segundo facilitador incompleto",
        "Debes ingresar el nombre del segundo facilitador."
      );
      return false;
    }

    if (hasSecondFacilitatorData && !eventForm.secondFacilitatorTypeEvent) {
      showResponseModal(
        "warning",
        "Segundo facilitador incompleto",
        "Debes indicar si el segundo facilitador es interno o externo."
      );
      return false;
    }

    if (
      hasSecondFacilitatorData &&
      eventForm.secondFacilitatorTypeEvent === "EXTERNO" &&
      !eventForm.secondFacilitatorCompanyEvent.trim()
    ) {
      showResponseModal(
        "warning",
        "Campo obligatorio",
        "Debes ingresar la empresa del segundo facilitador externo."
      );
      return false;
    }

    if (eventModalMode === "create") {
      const bogotaNow = getBogotaDateTime();
      const selectedStartDateTime = `${eventForm.dateEvent}T${eventForm.startTimeEvent}`;
      const currentDateTime = `${bogotaNow.date}T${bogotaNow.time}`;

      if (selectedStartDateTime <= currentDateTime) {
        showResponseModal(
          "warning",
          "Fecha y hora no válidas",
          "La fecha y hora de inicio deben ser posteriores a la fecha y hora actual."
        );
        return false;
      }
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

        const notificationWasSent =
          response.result.notificationEmailSent !== false;

        showResponseModal(
          notificationWasSent ? "success" : "warning",
          notificationWasSent
            ? "Evento creado"
            : "Evento creado con una advertencia",
          response.result.notificationMessage ||
            response.Message ||
            "Evento creado correctamente."
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
    if (isPaidTrainingEvent === true) {
      return "PAGA";
    }

    if (isPaidTrainingEvent === false) {
      return "DENTRO DE LA JORNADA";
    }

    return "NO ESPECIFICADO";
  };

  const formatDateTimeForExcel = (value?: string | null) => {
    if (!value) return "";

    return new Date(value).toLocaleString("es-CO");
  };

  const exportEventToExcel = async () => {
    if (!selectedEvent) {
      showResponseModal(
        "warning",
        "Sin evento",
        "No se encontró información del evento para exportar."
      );
      return;
    }

    try {
      setExportingExcel(true);

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
      "Tipo de capacitación",
      getTrainingTypeName(selectedEvent.isPaidTrainingEvent),
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
      getTrainingTypeName(selectedEvent.isPaidTrainingEvent),
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
      "Firma",
    ]);
    const signatureExcelRows: Array<{
      excelRowNumber: number;
      signaturePath: string;
    }> = [];

    if (eventAttendances.length === 0) {
      addRow(["", "No hay asistentes registrados para este evento."]);
    } else {
      eventAttendances.forEach((attendance) => {
        const signaturePath =
          attendance.attendancePerson?.signaturePathAttendancePerson ?? "";
        const attendanceRow = addRow([
          attendance.attendancePerson?.documentNumberAttendancePerson ?? "",
          attendance.attendancePerson?.fullNameAttendancePerson ?? "",
          attendance.attendancePerson?.positionAttendancePerson ?? "",
          attendance.attendancePerson?.phoneAttendancePerson ?? "",
          getSolutionCenterName(attendance.attendancePerson?.IdSolutionCenter),
          attendance.ipAddressAttendance ?? "",
          formatDateTimeForExcel(attendance.createdAt),
          signaturePath ? "" : "Sin firma",
        ]);

        if (signaturePath) {
          signatureExcelRows.push({
            excelRowNumber: attendanceRow + 1,
            signaturePath,
          });
        }
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
      { wch: 28 },
    ];

    const signatureWorksheetRowIndexes = new Set(
      signatureExcelRows.map((item) => item.excelRowNumber - 1)
    );

    worksheet["!rows"] = rows.map((_, index) => ({
      hpt:
        signatureWorksheetRowIndexes.has(index)
          ? 45
          : index === titleRow
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
      { s: { r: titleRow, c: 0 }, e: { r: titleRow, c: 7 } },
      { s: { r: subtitleRow, c: 0 }, e: { r: subtitleRow, c: 7 } },
      { s: { r: eventSectionRow, c: 0 }, e: { r: eventSectionRow, c: 7 } },
      { s: { r: facilitatorSectionRow, c: 0 }, e: { r: facilitatorSectionRow, c: 7 } },
      { s: { r: descriptionSectionRow, c: 0 }, e: { r: descriptionSectionRow, c: 7 } },
      { s: { r: topicSectionRow, c: 0 }, e: { r: topicSectionRow, c: 7 } },
      { s: { r: competencySectionRow, c: 0 }, e: { r: competencySectionRow, c: 7 } },
      { s: { r: attendanceSectionRow, c: 0 }, e: { r: attendanceSectionRow, c: 7 } },
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

    const styleFullRow = (row: number, style: object, fromCol = 0, toCol = 7) => {
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
    setStyle(summaryRow2, 6, summaryLabelStyle);
    setStyle(summaryRow2, 7, summaryValueStyle);

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
        e: { r: range.e.r, c: 7 },
      }),
    };

    XLSX.utils.book_append_sheet(workbook, worksheet, "Registro asistencia");

    const cleanTitle = selectedEvent.titleEvent
      .replace(/[\\/:*?"<>|]/g, "")
      .replace(/\s+/g, "_");
    const fileName = `registro_asistencia_evento_${selectedEvent.IdEvent}_${cleanTitle || "evento"}.xlsx`;
    const baseWorkbookData = XLSX.write(workbook, {
      type: "array",
      bookType: "xlsx",
    }) as ArrayBuffer;
    const processedSignatures = await Promise.allSettled(
      signatureExcelRows.map(async (signatureRow) => ({
        ...signatureRow,
        imageData: await compressSignatureForExcel(
          signatureRow.signaturePath
        ),
      }))
    );
    let failedSignatures = 0;
    const successfulSignatures = processedSignatures.flatMap((result) => {
      if (result.status === "rejected") {
        failedSignatures += 1;
        return [];
      }

      return [{
        excelRowNumber: result.value.excelRowNumber,
        imageData: result.value.imageData,
      }];
    });
    const outputBytes = await embedSignaturesWithoutChangingWorkbook(
      baseWorkbookData,
      successfulSignatures
    );
    const outputArrayBuffer = new ArrayBuffer(outputBytes.byteLength);
    new Uint8Array(outputArrayBuffer).set(outputBytes);
    const outputBlob = new Blob([outputArrayBuffer], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    const downloadUrl = URL.createObjectURL(outputBlob);
    const downloadLink = document.createElement("a");
    downloadLink.href = downloadUrl;
    downloadLink.download = fileName;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    downloadLink.remove();
    URL.revokeObjectURL(downloadUrl);

    if (failedSignatures > 0) {
      showResponseModal(
        "warning",
        "Excel generado con advertencia",
        `No fue posible incorporar ${failedSignatures} firma${failedSignatures === 1 ? "" : "s"}. Las demás firmas fueron incluidas correctamente.`
      );
    }
    } catch (err) {
      showResponseModal(
        "error",
        "Error al exportar",
        getErrorMessage(err)
      );
    } finally {
      setExportingExcel(false);
    }
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

  const savedPensumPreviewUrl = selectedEvent?.pensumPathEvent
    ? getBackendFileUrl(selectedEvent.pensumPathEvent)
    : "";
  const activePensumPreviewUrl = pensumPreviewUrl || savedPensumPreviewUrl;
  const activePensumPreviewName =
    pensumFile?.name || selectedEvent?.pensumOriginalNameEvent || "Pensum adjunto";
  const activePensumPreviewMimeType =
    pensumFile?.type || selectedEvent?.pensumMimeTypeEvent || "";
  const activePensumPreviewExtension = activePensumPreviewName
    .split(".")
    .pop()
    ?.toLowerCase();
  const pensumPreviewIsImage =
    activePensumPreviewMimeType.startsWith("image/") ||
    ["png", "jpg", "jpeg"].includes(activePensumPreviewExtension ?? "");
  const pensumPreviewIsPdf =
    activePensumPreviewMimeType === "application/pdf" ||
    activePensumPreviewExtension === "pdf";
  const pensumPreviewUsesOnlyOffice = onlyOfficePensumExtensions.has(
    activePensumPreviewExtension ?? ""
  );

  const openPensumPreview = async () => {
    if (!activePensumPreviewUrl && !pensumFile) {
      showResponseModal(
        "warning",
        "PENSUM no disponible",
        "No hay un archivo PENSUM para previsualizar."
      );
      return;
    }

    setPensumPreviewOpen(true);
    setPensumPreviewError("");

    if (!pensumPreviewUsesOnlyOffice || onlyOfficePreview) {
      return;
    }

    try {
      setPensumPreviewLoading(true);
      const response = pensumFile
        ? await eventService.createPensumPreview(pensumFile)
        : selectedEvent
        ? await eventService.getPensumPreview(selectedEvent.IdEvent)
        : null;

      if (!response?.isSuccess || !response.result) {
        throw new Error(
          response?.Message || "No fue posible preparar la vista previa."
        );
      }

      setOnlyOfficePreview(response.result);
    } catch (error) {
      setPensumPreviewError(getErrorMessage(error));
    } finally {
      setPensumPreviewLoading(false);
    }
  };

  const closePensumPreview = () => {
    setPensumPreviewOpen(false);
    setOnlyOfficePreview(null);
    setPensumPreviewError("");
    setPensumPreviewLoading(false);
  };

  useEffect(() => {
    return () => {
      if (pensumPreviewUrl) {
        window.URL.revokeObjectURL(pensumPreviewUrl);
      }
    };
  }, [pensumPreviewUrl]);

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
            <Box sx={{ overflowX: "auto" }}>
            <Table sx={{ minWidth: 1350 }}>
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
                  <TableCell sx={{ fontWeight: 700, color: "#4B2E1F", minWidth: 180 }}>
                    Tipo de capacitación
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
                    <TableCell colSpan={9} align="center" sx={{ color: "#7A6252", py: 3 }}>
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
                      <TableCell>{getTrainingTypeName(item.isPaidTrainingEvent)}</TableCell>
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
            </Box>
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
                disabled={exportingExcel}
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
                {exportingExcel ? "Generando..." : "Exportar Excel"}
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
                slotProps={{
                  inputLabel: { shrink: true, },
                  htmlInput: eventModalMode === "create"
                    ? { min: getBogotaDateTime().date }
                    : {},
                }}
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
                disabled={saving}
                fullWidth
                helperText="Se calcula automáticamente con la hora de inicio y la hora de fin."
                slotProps={{ htmlInput: { readOnly: true } }}
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
                        {formatDropdownOption(item.codeSolutionCenter)} - {formatDropdownOption(item.nameSolutionCenter)}
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
                      {formatDropdownOption(item.nameAssistanceReason)}
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
                      {formatDropdownOption(item.nameSpecificTrainingProgram)}
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
                      {formatDropdownOption(item.nameEventCategory)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Box
                sx={{
                  gridColumn: "1 / -1",
                  border: "1px solid",
                  borderColor: "divider",
                  borderRadius: 2,
                  p: 2,
                }}
              >
                <Typography
                  sx={{ color: "primary.main", fontWeight: 700, mb: 2 }}
                >
                  Facilitador principal
                </Typography>
                <Box
                  sx={{
                    display: "grid",
                    gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
                    gap: 2,
                  }}
                >
                  <TextField
                    required
                    label="Nombre facilitador"
                    value={eventForm.facilitatorNameEvent}
                    disabled={eventModalMode === "view" || saving}
                    fullWidth
                    onChange={(event) =>
                      handleEventFormChange(
                        "facilitatorNameEvent",
                        event.target.value
                      )
                    }
                  />
                  <FormControl
                    required
                    fullWidth
                    disabled={eventModalMode === "view" || saving}
                  >
                    <InputLabel>Tipo de facilitador</InputLabel>
                    <Select
                      label="Tipo de facilitador"
                      value={eventForm.facilitatorTypeEvent}
                      onChange={(event) =>
                        handleEventFormChange(
                          "facilitatorTypeEvent",
                          event.target.value
                        )
                      }
                    >
                      <MenuItem value="">
                        <em>Seleccione</em>
                      </MenuItem>
                      <MenuItem value="INTERNO">INTERNO</MenuItem>
                      <MenuItem value="EXTERNO">EXTERNO</MenuItem>
                    </Select>
                  </FormControl>
                  {eventForm.facilitatorTypeEvent === "EXTERNO" && (
                    <TextField
                      required
                      label="Empresa del facilitador"
                      value={eventForm.facilitatorCompanyEvent}
                      disabled={eventModalMode === "view" || saving}
                      fullWidth
                      onChange={(event) =>
                        handleEventFormChange(
                          "facilitatorCompanyEvent",
                          event.target.value
                        )
                      }
                    />
                  )}
                  <TextField
                    required
                    label="Cargo facilitador"
                    value={eventForm.facilitatorPositionEvent}
                    disabled={eventModalMode === "view" || saving}
                    fullWidth
                    onChange={(event) =>
                      handleEventFormChange(
                        "facilitatorPositionEvent",
                        event.target.value
                      )
                    }
                  />
                </Box>
              </Box>
              {(eventModalMode !== "view" ||
                eventForm.secondFacilitatorNameEvent ||
                eventForm.secondFacilitatorCompanyEvent ||
                eventForm.secondFacilitatorPositionEvent) && (
                <Box
                  sx={{
                    gridColumn: "1 / -1",
                    border: "1px solid",
                    borderColor: "divider",
                    borderRadius: 2,
                    p: 2,
                  }}
                >
                  <Typography
                    sx={{ color: "primary.main", fontWeight: 700, mb: 2 }}
                  >
                    Segundo facilitador (opcional)
                  </Typography>
                  <Box
                    sx={{
                      display: "grid",
                      gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
                      gap: 2,
                    }}
                  >
                    <TextField
                      label="Nombre segundo facilitador"
                      value={eventForm.secondFacilitatorNameEvent}
                      disabled={eventModalMode === "view" || saving}
                      fullWidth
                      onChange={(event) =>
                        handleEventFormChange(
                          "secondFacilitatorNameEvent",
                          event.target.value
                        )
                      }
                    />
                    <FormControl
                      fullWidth
                      required={Boolean(eventForm.secondFacilitatorNameEvent)}
                      disabled={eventModalMode === "view" || saving}
                    >
                      <InputLabel>Tipo de segundo facilitador</InputLabel>
                      <Select
                        label="Tipo de segundo facilitador"
                        value={eventForm.secondFacilitatorTypeEvent}
                        onChange={(event) =>
                          handleEventFormChange(
                            "secondFacilitatorTypeEvent",
                            event.target.value
                          )
                        }
                      >
                        <MenuItem value="">
                          <em>Seleccione</em>
                        </MenuItem>
                        <MenuItem value="INTERNO">INTERNO</MenuItem>
                        <MenuItem value="EXTERNO">EXTERNO</MenuItem>
                      </Select>
                    </FormControl>
                    {eventForm.secondFacilitatorTypeEvent === "EXTERNO" && (
                      <TextField
                        required
                        label="Empresa del segundo facilitador"
                        value={eventForm.secondFacilitatorCompanyEvent}
                        disabled={eventModalMode === "view" || saving}
                        fullWidth
                        onChange={(event) =>
                          handleEventFormChange(
                            "secondFacilitatorCompanyEvent",
                            event.target.value
                          )
                        }
                      />
                    )}
                    <TextField
                      label="Cargo segundo facilitador"
                      value={eventForm.secondFacilitatorPositionEvent}
                      disabled={eventModalMode === "view" || saving}
                      fullWidth
                      onChange={(event) =>
                        handleEventFormChange(
                          "secondFacilitatorPositionEvent",
                          event.target.value
                        )
                      }
                    />
                  </Box>
                </Box>
              )}
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
                    onChange={(event) =>
                      setTopicInput(
                        eventModalMode === "create"
                          ? event.target.value.toLocaleUpperCase("es-CO")
                          : event.target.value
                      )
                    }
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
                open={
                  competenciesMenuOpen &&
                  eventModalMode !== "view" &&
                  !saving
                }
                onOpen={() => setCompetenciesMenuOpen(true)}
                onClose={() => setCompetenciesMenuOpen(false)}
                value={eventForm.competencies}
                input={<OutlinedInput label="Competencias" />}
                MenuProps={{
                  slotProps: {
                    paper: {
                      sx: { maxHeight: 420 },
                    },
                  },
                }}
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

                      return competency
                        ? formatDropdownOption(competency.nameCompetency)
                        : String(IdCompetency);
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
                    <ListItemText primary={formatDropdownOption(item.nameCompetency)} />
                  </MenuItem>
                ))}
                <ListSubheader
                  component="div"
                  sx={{
                    position: "sticky",
                    top: "auto",
                    bottom: 0,
                    zIndex: 1,
                    py: 1,
                    bgcolor: "background.paper",
                    borderTop: "1px solid",
                    borderColor: "divider",
                  }}
                  onMouseDown={(event) => event.stopPropagation()}
                  onClick={(event) => event.stopPropagation()}
                >
                  <Button
                    fullWidth
                    variant="contained"
                    disabled={eventForm.competencies.length === 0}
                    onClick={(event) => {
                      event.stopPropagation();
                      setCompetenciesMenuOpen(false);
                    }}
                  >
                    Agregar selección ({eventForm.competencies.length})
                  </Button>
                </ListSubheader>
              </Select>
              {eventModalMode !== "view" && (
                <FormHelperText>
                  Marca las competencias y pulsa “Agregar selección”. También se
                  conservarán si cierras el desplegable.
                </FormHelperText>
              )}
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
                      onClick={() => void openPensumPreview()}
                      sx={{
                        borderColor: "#8B6A55",
                        color: "#4B2E1F",
                        "&:hover": {
                          borderColor: "#4B2E1F",
                          bgcolor: "rgba(75, 46, 31, 0.05)",
                        },
                      }}
                    >
                      Previsualizar
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
                      accept=".pdf,.doc,.docm,.docx,.odt,.rtf,.txt,.csv,.ods,.xls,.xlsb,.xlsm,.xlsx,.odp,.ppt,.pptm,.pptx,.png,.jpg,.jpeg"
                      onChange={(event) => {
                        const file = event.target.files?.[0] ?? null;
                        setPensumFile(file);
                        setPensumPreviewOpen(false);
                        setOnlyOfficePreview(null);
                        setPensumPreviewError("");
                        setPensumPreviewUrl(
                          file ? window.URL.createObjectURL(file) : ""
                        );
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

                  {pensumFile && pensumPreviewUrl && (
                    <Button
                      variant="text"
                      onClick={() => void openPensumPreview()}
                      sx={{
                        mt: 1,
                        color: "#4B2E1F",
                        textTransform: "none",
                      }}
                    >
                      Previsualizar archivo seleccionado
                    </Button>
                  )}

                  {eventModalMode === "update" &&
                    !pensumFile &&
                    selectedEvent?.pensumPathEvent && (
                    <Button
                      variant="text"
                      onClick={() => void openPensumPreview()}
                      sx={{
                        mt: 1,
                        color: "#4B2E1F",
                        textTransform: "none",
                      }}
                    >
                      Previsualizar archivo actual
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
      <Dialog
        open={pensumPreviewOpen}
        onClose={closePensumPreview}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle sx={{ color: "#4B2E1F", fontWeight: 700 }}>
          <Stack sx={{ flexDirection: "row", gap: 1.5, alignItems: "center" }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 20, fontWeight: 700 }}>
              Previsualización del PENSUM
            </Typography>
            {pensumPreviewUsesOnlyOffice && (
              <Chip
                label="SOLO LECTURA"
                size="small"
                sx={{ bgcolor: "#F7E8D8", color: "#4B2E1F", fontWeight: 700 }}
              />
            )}
          </Stack>
        </DialogTitle>
        <DialogContent dividers>
          <Typography sx={{ color: "#7A6252", mb: 2, wordBreak: "break-word" }}>
            {activePensumPreviewName}
          </Typography>

          {pensumPreviewIsImage ? (
            <Box
              component="img"
              src={activePensumPreviewUrl}
              alt={`Previsualización de ${activePensumPreviewName}`}
              sx={{
                display: "block",
                width: "100%",
                maxHeight: "75vh",
                objectFit: "contain",
                bgcolor: "#FFFFFF",
              }}
            />
          ) : pensumPreviewIsPdf ? (
            <Box
              component="iframe"
              src={activePensumPreviewUrl}
              title={`Previsualización de ${activePensumPreviewName}`}
              sx={{
                width: "100%",
                height: "75vh",
                border: "none",
                bgcolor: "#FFFFFF",
              }}
            />
          ) : pensumPreviewUsesOnlyOffice ? (
            pensumPreviewLoading ? (
              <Stack
                sx={{
                  height: "65vh",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 1.5,
                }}
              >
                <CircularProgress sx={{ color: "#4B2E1F" }} />
                <Typography sx={{ color: "#7A6252" }}>
                  Cargando el visor de OnlyOffice...
                </Typography>
              </Stack>
            ) : pensumPreviewError ? (
              <Alert severity="error">
                {pensumPreviewError}
              </Alert>
            ) : onlyOfficePreview ? (
              <OnlyOfficeViewer
                key={onlyOfficePreview.config.token}
                documentServerUrl={onlyOfficePreview.documentServerUrl}
                config={onlyOfficePreview.config}
              />
            ) : (
              <Alert severity="warning">
                No fue posible preparar la vista previa del documento.
              </Alert>
            )
          ) : (
            <Box sx={{ py: 5, textAlign: "center" }}>
              <Typography sx={{ color: "#4B2E1F", fontWeight: 700, mb: 1 }}>
                Formato sin vista previa
              </Typography>
              <Typography sx={{ color: "#7A6252", mb: 3 }}>
                Este formato no es compatible con el visor integrado. Puedes
                abrirlo con una aplicación disponible en tu equipo.
              </Typography>
              <Button
                variant="contained"
                onClick={() =>
                  window.open(activePensumPreviewUrl, "_blank", "noopener,noreferrer")
                }
                disabled={!activePensumPreviewUrl}
                sx={{
                  bgcolor: "#4B2E1F",
                  "&:hover": { bgcolor: "#3A2318" },
                }}
              >
                Abrir archivo
              </Button>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button
            onClick={closePensumPreview}
            sx={{ color: "#4B2E1F" }}
          >
            Cerrar
          </Button>
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
          <Alert
            severity="warning"
            variant="outlined"
            sx={{ mb: 2, textAlign: "left" }}
          >
            Recuerda validar que el número de personas asistentes sea igual al
            número registrado.
          </Alert>
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
