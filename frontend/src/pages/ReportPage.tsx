import { Box, Button, Card, CardContent, CircularProgress, Collapse, IconButton, Paper, Table, TableBody, TableCell, TableHead, TableRow, TextField, Tooltip, Typography, } from "@mui/material";
import { ResponseModal, type ResponseModalSeverity, } from "../components/ResponseModal";
import FileDownloadOutlinedIcon from "@mui/icons-material/FileDownloadOutlined";
import EngineeringOutlinedIcon from "@mui/icons-material/EngineeringOutlined";
import AccessTimeOutlinedIcon from "@mui/icons-material/AccessTimeOutlined";
import AssessmentOutlinedIcon from "@mui/icons-material/AssessmentOutlined";
import PersonOffOutlinedIcon from "@mui/icons-material/PersonOffOutlined";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import BadgeOutlinedIcon from "@mui/icons-material/BadgeOutlined";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import SearchOutlinedIcon from "@mui/icons-material/SearchOutlined";
import { getErrorMessage } from "../services/errorService";
import { reportService } from "../services/reportService";
import { Fragment, useEffect, useState } from "react";
import * as XLSX from "xlsx-js-style";
import type {
  TrainingReportResponse,
  SstTrainingReportResponse,
  TrainingHoursReportResponse,
  NewStaffInductionReportResponse,
  AdministrativeInductionReportResponse,
  TransversalTrainingReportResponse,
  CollaboratorTrainingReportResponse,
  GeneralReportResponse,
  AverageTrainingTimeReportResponse
} from "../models/Report";

interface ResponseModalState {
  open: boolean;
  severity: ResponseModalSeverity;
  title: string;
  message: string;
}

interface DonutChartItem {
  name: string;
  value: number;
}

interface DonutChartProps {
  data: DonutChartItem[];
  centerLabel?: string;
}

const emptyResponseModal: ResponseModalState = {
  open: false,
  severity: "info",
  title: "",
  message: "",
};

const donutColors = [
  "#4B2E1F",
  "#8B6A55",
  "#D8A86A",
  "#A56B46",
  "#6D4C41",
  "#BCAAA4",
  "#795548",
  "#C7A27C",
  "#A1887F",
  "#D7CCC8",
];

function DonutChart({ data, centerLabel = "capacitados" }: DonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  const radius = 80;
  const strokeWidth = 34;
  const circumference = 2 * Math.PI * radius;

  if (total === 0) {
    return (
      <Box sx={{ minHeight: 320, display: "flex", alignItems: "center", justifyContent: "center", }}>
        <Typography sx={{ color: "#7A6252" }}>
          No hay datos para graficar.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "320px 1fr", }, gap: 2,   alignItems: "center", }}>
      <Box sx={{ position: "relative", width: 320, height: 320, mx: "auto", }}>
        <svg width="320" height="320" viewBox="0 0 220 220">
          <circle
            cx="110"
            cy="110"
            r={radius}
            fill="none"
            stroke="#F7E8D8"
            strokeWidth={strokeWidth}
          />
          {data.map((item, index) => {
            const percentage = item.value / total;
            const dash = percentage * circumference;
            const gap = circumference - dash;
            const offset = -data
              .slice(0, index)
              .reduce(
                (sum, previousItem) =>
                  sum + (previousItem.value / total) * circumference,
                0
              );

            return (
              <circle
                key={`${item.name}-${index}`}
                cx="110"
                cy="110"
                r={radius}
                fill="none"
                stroke={donutColors[index % donutColors.length]}
                strokeWidth={strokeWidth}
                strokeDasharray={`${dash} ${gap}`}
                strokeDashoffset={offset}
                strokeLinecap="round"
                transform="rotate(-90 110 110)"
              />
            );
          })}
        </svg>

        <Box sx={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", }}>
          <Typography sx={{ color: "#4B2E1F", fontSize: 34, fontWeight: 800, }}>
            {total}
          </Typography>
          <Typography sx={{ color: "#7A6252", fontSize: 13 }}>
            {centerLabel}
          </Typography>
        </Box>
      </Box>

      <Box sx={{ display: "flex", flexDirection: "column", gap: 1, maxHeight: 320, overflowY: "auto", pr: 1, }}>
        {data.map((item, index) => {
          const percentage =
            total > 0 ? Math.round((item.value / total) * 100) : 0;

          return (
            <Box key={`${item.name}-legend-${index}`} sx={{ display: "grid", gridTemplateColumns: "18px 1fr auto", gap: 1, alignItems: "center", }}>
              <Box sx={{ width: 12, height: 12, borderRadius: "50%", bgcolor: donutColors[index % donutColors.length],}}/>
              <Typography
                sx={{ color: "#4B2E1F", fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", }} title={ item.name }>
                {item.name}
              </Typography>
              <Typography sx={{ color: "#7A6252", fontSize: 13, fontWeight: 700, }}>
                {item.value} ({percentage}%)
              </Typography>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}

interface BarChartItem {
  label: string;
  value: number;
  formattedValue?: string;
}

interface SimpleBarChartProps {
  data: BarChartItem[];
}

function SimpleBarChart({ data }: SimpleBarChartProps) {
  if (data.length === 0) {
    return (
      <Box sx={{ py: 5, display: "flex", justifyContent: "center" }}>
        <Typography sx={{ color: "#7A6252" }}>
          No hay datos para graficar.
        </Typography>
      </Box>
    );
  }

  const maxValue = Math.max(...data.map((item) => item.value), 1);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {data.map((item, index) => {
        const widthPercent = Math.max((item.value / maxValue) * 100, 4);

        return (
          <Box key={`${item.label}-${index}`}>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.8, gap: 2, }}>
              <Typography sx={{ color: "#4B2E1F", fontSize: 14, fontWeight: 600, }}>
                { item.label }
              </Typography>
              <Typography sx={{ color: "#7A6252", fontSize: 14, fontWeight: 700, }}>
                {item.formattedValue ?? item.value}
              </Typography>
            </Box>
            <Box sx={{ height: 14, borderRadius: 10, bgcolor: "#F7E8D8", overflow: "hidden", }}>
              <Box sx={{ width: `${widthPercent}%`, height: "100%", borderRadius: 10, bgcolor: donutColors[index % donutColors.length], }}/>
            </Box>
          </Box>
        );
      })}
    </Box>
  );
}

interface AverageGaugeProps { value: number; }

function AverageGauge({ value }: AverageGaugeProps) {
  const maxReference = Math.max(value, 8);
  const percentage = Math.min((value / maxReference) * 100, 100);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
      <Box sx={{ height: 18, borderRadius: 10, bgcolor: "#F7E8D8", overflow: "hidden", }}>
        <Box sx={{ width: `${percentage}%`, height: "100%", borderRadius: 10, bgcolor: "#4B2E1F", transition: "width 0.3s ease", }}/>
      </Box>
      <Typography sx={{ color: "#7A6252", fontSize: 13 }}>
        Promedio calculado sobre el total de colaboradores vinculados ingresado.
      </Typography>
    </Box>
  );
}

const formatDateForInput = (date: Date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
};

const getCurrentMonthRange = () => {
  const now = new Date();

  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);

  return {
    dateFrom: formatDateForInput(firstDay),
    dateTo: formatDateForInput(lastDay),
  };
};

const formatReportDate = (value: string) =>
  new Date(`${value}T00:00:00`).toLocaleDateString("es-CO");

const formatTrainingDuration = (decimalHours?: number | null) => {
  const numericHours = Number(decimalHours ?? 0);

  if (!Number.isFinite(numericHours) || numericHours <= 0) {
    return "0 min";
  }

  const totalMinutes = Math.round(numericHours * 60);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours === 0) {
    return `${minutes} min`;
  }

  if (minutes === 0) {
    return `${hours} h`;
  }

  return `${hours} h ${minutes} min`;
};

export function ReportPage() {
  const [administrativeInductionReport, setAdministrativeInductionReport] = useState<AdministrativeInductionReportResponse | null>(null);
  const [transversalTrainingReport, setTransversalTrainingReport] = useState<TransversalTrainingReportResponse | null>(null);
  const [averageTrainingTimeReport, setAverageTrainingTimeReport] = useState<AverageTrainingTimeReportResponse | null>(null);
  const [newStaffInductionReport, setNewStaffInductionReport] = useState<NewStaffInductionReportResponse | null>(null);
  const [trainingHoursReport, setTrainingHoursReport] = useState<TrainingHoursReportResponse | null>(null);
  const [responseModal, setResponseModal] = useState<ResponseModalState>(emptyResponseModal);
  const [generalReport, setGeneralReport] = useState<GeneralReportResponse | null>(null);
  const [loadingAverageTrainingTime, setLoadingAverageTrainingTime] = useState(false);
  const [sstReport, setSstReport] = useState<SstTrainingReportResponse | null>(null);
  const [report, setReport] = useState<TrainingReportResponse | null>(null);
  const [expandedSolutionCenter, setExpandedSolutionCenter] = useState<string | null>(null);
  const [collaboratorReport, setCollaboratorReport] = useState<CollaboratorTrainingReportResponse | null>(null);
  const [selectedCollaboratorDocument, setSelectedCollaboratorDocument] = useState<string | null>(null);
  const [collaboratorSearch, setCollaboratorSearch] = useState("");
  const [totalWorkers, setTotalWorkers] = useState("");
  const currentMonthRange = getCurrentMonthRange();
  const [dateFrom, setDateFrom] = useState(currentMonthRange.dateFrom);
  const [dateTo, setDateTo] = useState(currentMonthRange.dateTo);
  const [collaboratorDateFrom, setCollaboratorDateFrom] = useState(currentMonthRange.dateFrom);
  const [collaboratorDateTo, setCollaboratorDateTo] = useState(currentMonthRange.dateTo);
  const [loading, setLoading] = useState(false);
  const [loadingCollaborator, setLoadingCollaborator] = useState(false);
  
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

  const loadReport = async () => {
    try {
      if (dateFrom && dateTo && dateFrom > dateTo) {
        showResponseModal("warning", "Fechas inválidas", "La fecha inicial no puede ser mayor a la fecha final.");
        return;
      }

      setLoading(true);

      const [trainingResponse, sstTrainingResponse, trainingHoursResponse, newStaffInductionResponse, administrativeInductionResponse, transversalTrainingResponse, generalResponse] = await Promise.all([
        reportService.getTrainingReport({
          dateFrom,
          dateTo,
        }),
        reportService.getSstTrainingReport({
          dateFrom,
          dateTo,
        }),
        reportService.getTrainingHoursReport({
          dateFrom,
          dateTo,
        }),
        reportService.getNewStaffInductionReport({
          dateFrom,
          dateTo,
        }),
        reportService.getAdministrativeInductionReport({
          dateFrom,
          dateTo,
        }),
        reportService.getTransversalTrainingReport({
          dateFrom,
          dateTo,
        }),
        reportService.getGeneralReport({
          dateFrom,
          dateTo
        }),
      ]);

      if (!trainingResponse.isSuccess || !trainingResponse.result) {
        showResponseModal("error", "Error", trainingResponse.Message || "No se pudo cargar el reporte.");
        return;
      }

      if (!sstTrainingResponse.isSuccess || !sstTrainingResponse.result) {
        showResponseModal("error", "Error", sstTrainingResponse.Message || "No se pudo cargar el reporte SST.");
        return;
      }

      if (!trainingHoursResponse.isSuccess || !trainingHoursResponse.result) {
        showResponseModal("error", "Error", trainingHoursResponse.Message || "No se pudo cargar el reporte de tiempo de capacitación.");
        return;
      }

      if (!newStaffInductionResponse.isSuccess || !newStaffInductionResponse.result) {
        showResponseModal("error", "Error", newStaffInductionResponse.Message || "No se pudo cargar el reporte de inducción a personal nuevo.");
        return;
      }

      if (!administrativeInductionResponse.isSuccess || !administrativeInductionResponse.result) {
        showResponseModal("error", "Error", administrativeInductionResponse.Message || "No se pudo cargar el reporte de inducción a personal administrativo.");
        return;
      }

      if (!transversalTrainingResponse.isSuccess || !transversalTrainingResponse.result) {
        showResponseModal("error", "Error", transversalTrainingResponse.Message || "No se pudo cargar el reporte de capacitaciones transversales.");
        return;
      }

      if (!generalResponse.isSuccess || !generalResponse.result) {
        showResponseModal("error", "Error", generalResponse.Message || "No se pudo cargar el reporte general.");
        return;
      }

      setReport(trainingResponse.result);
      setSstReport(sstTrainingResponse.result);
      setTrainingHoursReport(trainingHoursResponse.result);
      setNewStaffInductionReport(newStaffInductionResponse.result);
      setAdministrativeInductionReport(administrativeInductionResponse.result);
      setTransversalTrainingReport(transversalTrainingResponse.result);
      setGeneralReport(generalResponse.result);
    } catch (err) {
      showResponseModal("error", "Error", getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = async () => {
    const currentMonthRange = getCurrentMonthRange();

    setDateFrom(currentMonthRange.dateFrom);
    setDateTo(currentMonthRange.dateTo);

    try {
      setLoading(true);

      const [trainingResponse, sstTrainingResponse, trainingHoursResponse, newStaffInductionResponse, administrativeInductionResponse, transversalTrainingResponse, generalResponse] = await Promise.all([
        reportService.getTrainingReport({
          dateFrom: currentMonthRange.dateFrom,
          dateTo: currentMonthRange.dateTo,
        }),
        reportService.getSstTrainingReport({
          dateFrom: currentMonthRange.dateFrom,
          dateTo: currentMonthRange.dateTo,
        }),
        reportService.getTrainingHoursReport({
          dateFrom: currentMonthRange.dateFrom,
          dateTo: currentMonthRange.dateTo,
        }),
        reportService.getNewStaffInductionReport({
          dateFrom: currentMonthRange.dateFrom,
          dateTo: currentMonthRange.dateTo,
        }),
        reportService.getAdministrativeInductionReport({
          dateFrom: currentMonthRange.dateFrom,
          dateTo: currentMonthRange.dateTo,
        }),
        reportService.getTransversalTrainingReport({
          dateFrom: currentMonthRange.dateFrom,
          dateTo: currentMonthRange.dateTo,
        }),
        reportService.getGeneralReport({
          dateFrom: currentMonthRange.dateFrom,
          dateTo: currentMonthRange.dateTo,
        }),
      ]);

      setReport(trainingResponse.isSuccess ? trainingResponse.result ?? null : null);
      setSstReport(sstTrainingResponse.isSuccess ? sstTrainingResponse.result ?? null : null);
      setTrainingHoursReport(trainingHoursResponse.isSuccess ? trainingHoursResponse.result ?? null : null);
      setNewStaffInductionReport(newStaffInductionResponse.isSuccess ? newStaffInductionResponse.result ?? null : null);
      setAdministrativeInductionReport(administrativeInductionResponse.isSuccess ? administrativeInductionResponse.result ?? null : null);
      setTransversalTrainingReport(transversalTrainingResponse.isSuccess ? transversalTrainingResponse.result ?? null : null);
      setGeneralReport(generalResponse.isSuccess ? generalResponse.result ?? null : null);
    } catch (err) {
      showResponseModal("error", "Error", getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const loadAverageTrainingTimeReport = async () => {
    try {
      if (dateFrom && dateTo && dateFrom > dateTo) {
        showResponseModal("warning", "Fechas inválidas", "La fecha inicial no puede ser mayor a la fecha final.");
        return;
      }

      const totalWorkersNumber = Number(totalWorkers);

      if (!totalWorkers || Number.isNaN(totalWorkersNumber) || totalWorkersNumber <= 0) {
        showResponseModal("warning", "Campo obligatorio", "Debe ingresar el total de colaboradores vinculados a la compañía.");
        return;
      }

      setLoadingAverageTrainingTime(true);

      const response = await reportService.getAverageTrainingTimeReport( { dateFrom, dateTo, }, totalWorkersNumber);

      if (!response.isSuccess || !response.result) {
        showResponseModal("error", "Error", response.Message || "No se pudo cargar el reporte de promedio de tiempo de capacitación.");
        return;
      }

      setAverageTrainingTimeReport(response.result);
    } catch (err) {
      showResponseModal("error", "Error", getErrorMessage(err));
    } finally {
      setLoadingAverageTrainingTime(false);
    }
  };

  const loadCollaboratorTrainingReport = async () => {
    const normalizedSearch = collaboratorSearch.trim();

    if (!normalizedSearch) {
      showResponseModal(
        "warning",
        "Campo obligatorio",
        "Ingresa el nombre o la cédula del colaborador."
      );
      return;
    }

    if (
      collaboratorDateFrom &&
      collaboratorDateTo &&
      collaboratorDateFrom > collaboratorDateTo
    ) {
      showResponseModal(
        "warning",
        "Fechas inválidas",
        "La fecha inicial no puede ser mayor a la fecha final."
      );
      return;
    }

    try {
      setLoadingCollaborator(true);
      const response = await reportService.getCollaboratorTrainingReport({
        search: normalizedSearch,
        dateFrom: collaboratorDateFrom,
        dateTo: collaboratorDateTo,
      });

      if (!response.isSuccess || !response.result) {
        showResponseModal(
          "error",
          "Error",
          response.Message || "No se pudo consultar el historial del colaborador."
        );
        return;
      }

      setCollaboratorReport(response.result);
      setSelectedCollaboratorDocument(
        response.result.collaborators[0]?.documentNumberAttendancePerson ?? null
      );
    } catch (err) {
      showResponseModal("error", "Error", getErrorMessage(err));
    } finally {
      setLoadingCollaborator(false);
    }
  };

  const exportReportsToExcel = () => {
    const hasData =
      report ||
      sstReport ||
      trainingHoursReport ||
      newStaffInductionReport ||
      administrativeInductionReport ||
      transversalTrainingReport ||
      generalReport ||
      averageTrainingTimeReport ||
      collaboratorReport;

    if (!hasData) {
      showResponseModal(
        "warning",
        "Sin datos",
        "No hay resultados de reportes para exportar."
      );
      return;
    }

    const workbook = XLSX.utils.book_new();

    const rows: unknown[][] = [];
    const sectionRows: number[] = [];
    const sectionEndColumns = new Map<number, number>();
    const headerRows: number[] = [];
    const headerEndColumns = new Map<number, number>();
    const historyTitleRows: number[] = [];
    const historySubsectionRows: number[] = [];
    const collaboratorDataRows: number[] = [];
    const trainingDetailRows: number[] = [];
    const trainingDetailRowHeights = new Map<number, number>();
    const trainingSummaryRows: number[] = [];
    const collaboratorTotalRows: number[] = [];
    const durationCells: Array<{ row: number; col: number }> = [];

    const addRow = (row: unknown[]) => {
      rows.push(row);
      return rows.length - 1;
    };

    const addDurationRow = (row: unknown[], durationColumn: number) => {
      const index = addRow(row);
      durationCells.push({ row: index, col: durationColumn });
      return index;
    };

    const addBlankRow = () => addRow([]);

    const addSection = (title: string, endColumn = 5) => {
      addBlankRow();
      const index = addRow([title]);
      sectionRows.push(index);
      sectionEndColumns.set(index, endColumn);
      return index;
    };

    const addHeader = (row: unknown[], endColumn = 5) => {
      const index = addRow(row);
      headerRows.push(index);
      headerEndColumns.set(index, endColumn);
      return index;
    };

    const addHistorySubsection = (title: string) => {
      const index = addRow([title]);
      historySubsectionRows.push(index);
      return index;
    };

    const formatNumber = (value?: number | null) => {
      return value ?? 0;
    };

    const titleRow = addRow(["REPORTE GENERAL DE CAPACITACIONES"]);
    const filterRow = addRow([
      "Fecha inicial",
      dateFrom || "Sin fecha",
      "Fecha final",
      dateTo || "Sin fecha",
      "Generado",
      new Date().toLocaleString("es-CO"),
    ]);

    addSection("TOTAL DE COLABORADORES CAPACITADOS");
    addHeader(["Indicador", "Valor"]);
    addRow([
      "Total de colaboradores capacitados",
      formatNumber(report?.summary.totalTrainedPeople),
    ]);
    addRow([
      "Total de colaboradores internos capacitados",
      formatNumber(report?.summary.totalInternalTrainedPeople),
    ]);
    addRow([
      "Total de personal externo capacitado",
      formatNumber(report?.summary.totalExternalTrainedPeople),
    ]);

    addBlankRow();
    addHeader(["Centro de soluciones", "Total capacitados"]);
    if ((report?.bySolutionCenter ?? []).length === 0) {
      addRow(["No hay datos", 0]);
    } else {
      report?.bySolutionCenter.forEach((item) => {
        addRow([
          item.nameSolutionCenter,
          formatNumber(item.totalTrainedPeople),
        ]);
      });
    }

    addBlankRow();
    addHeader([
      "Centro de soluciones",
      "Capacitación",
      "Fecha",
      "Cédula",
      "Colaborador",
      "Tiempo",
    ]);
    const solutionCenterDetails = (report?.bySolutionCenter ?? []).flatMap(
      (solutionCenter) =>
        solutionCenter.details.map((detail) => ({
          ...detail,
          nameSolutionCenter: solutionCenter.nameSolutionCenter,
        }))
    );
    if (solutionCenterDetails.length === 0) {
      addRow(["No hay datos", "", "", "", "", 0]);
    } else {
      solutionCenterDetails.forEach((item) => {
        addDurationRow([
          item.nameSolutionCenter,
          item.titleEvent,
          item.dateEvent,
          item.documentNumberAttendancePerson,
          item.fullNameAttendancePerson,
          formatNumber(item.trainingHours),
        ], 5);
      });
    }

    addSection("COMPETENCIAS FORMADAS");
    addHeader(["Competencia", "Eventos", "Asistencias"]);
    if ((report?.byCompetency ?? []).length === 0) {
      addRow(["No hay datos", 0, 0]);
    } else {
      report?.byCompetency.forEach((item) => {
        addRow([
          item.nameCompetency,
          formatNumber(item.totalEvents),
          formatNumber(item.totalTrainedPeople),
        ]);
      });
    }

    addSection("CAPACITACIONES SST");
    addHeader(["Indicador", "Valor"]);
    addRow([
      "Total de colaboradores internos capacitados en SST",
      formatNumber(sstReport?.summary.totalInternalSstTrainedPeople),
    ]);
    addDurationRow([
      "Tiempo total de capacitación en SST",
      formatNumber(sstReport?.summary.totalSstTrainingHours),
    ], 1);
    addDurationRow([
      "Tiempo promedio de capacitación en SST por colaborador interno",
      sstAverageHoursByCollaborator,
    ], 1);

    addBlankRow();
    addHeader([
      "Documento",
      "Colaborador",
      "Centro de soluciones",
      "Tiempo SST",
    ]);
    if ((sstReport?.byCollaborator ?? []).length === 0) {
      addRow(["No hay datos", "", "", 0]);
    } else {
      sstReport?.byCollaborator.forEach((item) => {
        addDurationRow([
          item.documentNumberAttendancePerson,
          item.fullNameAttendancePerson,
          item.nameSolutionCenter,
          formatNumber(item.totalSstTrainingHours),
        ], 3);
      });
    }

    addSection("TIEMPO DE CAPACITACIÓN");
    addHeader(["Indicador", "Valor"]);
    addDurationRow([
      "Tiempo total de capacitación",
      formatNumber(trainingHoursReport?.totalTrainingHours),
    ], 1);
    addDurationRow([
      "Tiempo total de capacitación categoría: Múltiples funciones",
      formatNumber(trainingHoursReport?.totalMultipleFunctionsTrainingHours),
    ], 1);
    addDurationRow([
      "Tiempo total de capacitación categoría: Cargo",
      formatNumber(trainingHoursReport?.totalPositionTrainingHours),
    ], 1);
    addDurationRow([
      "Tiempo total de capacitación categoría: Personal",
      formatNumber(trainingHoursReport?.totalPersonalTrainingHours),
    ], 1);
    addDurationRow([
      "Tiempo total: Ser",
      formatNumber(trainingHoursReport?.totalSerTrainingHours),
    ], 1);
    addDurationRow([
      "Tiempo total: Hacer",
      formatNumber(trainingHoursReport?.totalHacerTrainingHours),
    ], 1);
    addDurationRow([
      "Tiempo total de capacitación a personal interno",
      formatNumber(trainingHoursReport?.totalInternalTrainingHours),
    ], 1);
    addDurationRow([
      "Tiempo total de capacitación a personal externo",
      formatNumber(trainingHoursReport?.totalExternalTrainingHours),
    ], 1);

    addSection("INDUCCIÓN A PERSONAL NUEVO");
    addHeader(["Indicador", "Valor"]);
    addDurationRow([
      "Tiempo total de inducción a personal nuevo",
      formatNumber(newStaffInductionReport?.totalNewStaffInductionHours),
    ], 1);
    addRow([
      "Total de personal capacitado en inducción a personal nuevo",
      formatNumber(newStaffInductionReport?.totalNewStaffInductionPeople),
    ]);

    addSection("INDUCCIÓN A PERSONAL ADMINISTRATIVO");
    addHeader(["Indicador", "Valor"]);
    addDurationRow([
      "Tiempo total de inducción a personal administrativo",
      formatNumber(administrativeInductionReport?.totalAdministrativeInductionHours),
    ], 1);
    addRow([
      "Total de personal capacitado en inducción a personal administrativo",
      formatNumber(administrativeInductionReport?.totalAdministrativeInductionPeople),
    ]);

    addSection("CAPACITACIONES TRANSVERSALES");
    addHeader(["Indicador", "Valor"]);
    addDurationRow([
      "Tiempo total de capacitación transversal",
      formatNumber(transversalTrainingReport?.totalTransversalTrainingHours),
    ], 1);
    addRow([
      "Personal capacitado en transversales",
      formatNumber(transversalTrainingReport?.totalTransversalTrainingPeople),
    ]);
    addBlankRow();
    addHeader(["Cédula", "Colaborador", "Centro de soluciones", "Tiempo"]);
    if ((transversalTrainingReport?.byCollaborator ?? []).length === 0) {
      addRow(["No hay datos", "", "", 0]);
    } else {
      transversalTrainingReport?.byCollaborator.forEach((item) => {
        addDurationRow([
          item.documentNumberAttendancePerson,
          item.fullNameAttendancePerson,
          item.nameSolutionCenter,
          formatNumber(item.totalTransversalTrainingHours),
        ], 3);
      });
    }

    addSection("GENERAL");
    addHeader(["Indicador", "Valor"]);
    addRow([
      "Centro de soluciones que más capacitó",
      generalReport?.topTrainingSolutionCenterName ?? "SIN DATOS",
    ]);
    addRow([
      "Total de colaboradores internos capacitados por el centro que más capacitó",
      formatNumber(generalReport?.topTrainingSolutionCenterTotal),
    ]);
    addRow([
      "Total de colaboradores internos capacitados en Calidad",
      formatNumber(generalReport?.totalInternalQualityTrainedPeople),
    ]);
    addRow([
      "Total de colaboradores internos capacitados: Ser",
      formatNumber(generalReport?.totalInternalSerTrainedPeople),
    ]);
    addRow([
      "Total de colaboradores internos capacitados: Hacer",
      formatNumber(generalReport?.totalInternalHacerTrainedPeople),
    ]);

    if (averageTrainingTimeReport) {
      addSection("PROMEDIO DE TIEMPO DE CAPACITACIÓN POR COLABORADOR");
      addHeader(["Indicador", "Valor"]);
      addRow([
        "Total colaboradores vinculados a la compañía",
        formatNumber(averageTrainingTimeReport.totalWorkers),
      ]);
      addDurationRow([
        "Tiempo total de capacitación personal interno",
        formatNumber(averageTrainingTimeReport.totalInternalTrainingHours),
      ], 1);
      addDurationRow([
        "Promedio tiempo por colaborador",
        formatNumber(averageTrainingTimeReport.averageTrainingHoursPerWorker),
      ], 1);
    }

    if (collaboratorReport) {
      historyTitleRows.push(
        addSection("HISTORIAL DE CAPACITACIÓN POR COLABORADOR", 3)
      );
      if (collaboratorReport.collaborators.length === 0) {
        addRow(["No hay datos"]);
      } else {
        collaboratorReport.collaborators.forEach((collaborator, index) => {
          addHistorySubsection("DATOS DEL COLABORADOR");
          addHeader(["Cédula", "Colaborador"], 1);
          collaboratorDataRows.push(addRow([
            collaborator.documentNumberAttendancePerson,
            collaborator.fullNameAttendancePerson,
          ]));

          addBlankRow();
          addHistorySubsection("DETALLE DE CAPACITACIONES");
          addHeader(
            ["Capacitación", "Centro formador", "Fecha", "Tiempo"],
            3
          );

          if (collaborator.trainings.length === 0) {
            addRow(["No hay datos"]);
          } else {
            collaborator.trainings.forEach((training) => {
              const trainingRow = addDurationRow([
                training.titleEvent,
                training.nameSolutionCenter,
                training.dateEvent,
                training.trainingHours,
              ], 3);
              const estimatedLines = Math.max(
                1,
                Math.ceil(training.titleEvent.length / 45),
                Math.ceil(training.nameSolutionCenter.length / 25)
              );

              trainingDetailRows.push(trainingRow);
              trainingDetailRowHeights.set(
                trainingRow,
                Math.min(60, Math.max(20, estimatedLines * 15))
              );
            });
          }

          addBlankRow();
          addHistorySubsection("RESUMEN POR CENTRO FORMADOR");
          addHeader(
            ["Centro formador", "Total capacitaciones", "Tiempo total"],
            2
          );

          if (collaborator.byTrainingSolutionCenter.length === 0) {
            addRow(["No hay datos"]);
          } else {
            collaborator.byTrainingSolutionCenter.forEach((solutionCenter) => {
              trainingSummaryRows.push(addDurationRow([
                solutionCenter.nameSolutionCenter,
                solutionCenter.totalTrainings,
                solutionCenter.totalTrainingHours,
              ], 2));
            });
          }

          collaboratorTotalRows.push(addDurationRow([
            "TOTAL GENERAL",
            collaborator.totalTrainings,
            collaborator.totalTrainingHours,
          ], 2));

          if (index < collaboratorReport.collaborators.length - 1) {
            addBlankRow();
          }
        });
      }
    }

    const worksheet = XLSX.utils.aoa_to_sheet(rows);

    worksheet["!cols"] = [
      { wch: 48 },
      { wch: 28 },
      { wch: 30 },
      { wch: 22 },
      { wch: 22 },
      { wch: 28 },
    ];

    worksheet["!merges"] = [
      {
        s: { r: titleRow, c: 0 },
        e: { r: titleRow, c: 5 },
      },
      ...historyTitleRows.map((row) => ({
        s: { r: row, c: 0 },
        e: { r: row, c: 3 },
      })),
      ...historySubsectionRows.map((row) => ({
        s: { r: row, c: 0 },
        e: { r: row, c: 3 },
      })),
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

    const sectionStyle = {
      font: { bold: true, sz: 13, color: { rgb: "FFFFFF" } },
      fill: { fgColor: { rgb: "8B6A55" } },
      alignment: { horizontal: "left", vertical: "center" },
      border: borderThin,
    };

    const headerStyle = {
      font: { bold: true, color: { rgb: "FFFFFF" } },
      fill: { fgColor: { rgb: "4B2E1F" } },
      alignment: { horizontal: "center", vertical: "center", wrapText: true },
      border: borderThin,
    };

    const filterLabelStyle = {
      font: { bold: true, color: { rgb: "4B2E1F" } },
      fill: { fgColor: { rgb: "F7E8D8" } },
      alignment: { horizontal: "center", vertical: "center" },
      border: borderThin,
    };

    const filterValueStyle = {
      font: { color: { rgb: "2F241D" } },
      fill: { fgColor: { rgb: "FFFDF8" } },
      alignment: { horizontal: "center", vertical: "center" },
      border: borderThin,
    };

    const cellStyle = {
      font: { color: { rgb: "2F241D" } },
      alignment: { vertical: "center", wrapText: true },
      border: borderThin,
    };

    const mutedStyle = {
      font: { italic: true, color: { rgb: "7A6252" } },
      alignment: { vertical: "center", wrapText: true },
      border: borderThin,
    };

    const historySubsectionStyle = {
      font: { bold: true, color: { rgb: "4B2E1F" } },
      fill: { fgColor: { rgb: "F7E8D8" } },
      alignment: { horizontal: "left", vertical: "center" },
      border: borderThin,
    };

    const collaboratorDataStyle = {
      font: { bold: true, color: { rgb: "2F241D" } },
      fill: { fgColor: { rgb: "FFFDF8" } },
      alignment: { vertical: "center", wrapText: true },
      border: borderThin,
    };

    const dateCellStyle = {
      ...cellStyle,
      alignment: {
        horizontal: "center",
        vertical: "center",
        wrapText: true,
      },
    };

    const integerCellStyle = {
      ...cellStyle,
      alignment: { horizontal: "right", vertical: "center" },
      numFmt: "0",
    };

    const excelDurationNumberFormat =
      '[>=0.0416666667][h]" h "mm" min";[m]" min"';

    const durationCellStyle = {
      ...cellStyle,
      alignment: { horizontal: "right", vertical: "center" },
      numFmt: excelDurationNumberFormat,
    };

    const collaboratorTotalStyle = {
      font: { bold: true, color: { rgb: "4B2E1F" } },
      fill: { fgColor: { rgb: "F7E8D8" } },
      alignment: { vertical: "center", wrapText: true },
      border: borderThin,
    };

    const setStyle = (row: number, col: number, style: object) => {
      const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });

      if (!worksheet[cellAddress]) {
        worksheet[cellAddress] = { t: "s", v: "" };
      }

      const styledCell = worksheet[cellAddress] as XLSX.CellObject & {
        s?: object;
      };
      styledCell.s = style;
    };

    const styleFullRow = (row: number, style: object, fromCol = 0, toCol = 5) => {
      for (let col = fromCol; col <= toCol; col++) {
        setStyle(row, col, style);
      }
    };

    styleFullRow(titleRow, titleStyle);
    styleFullRow(filterRow, cellStyle);

    setStyle(filterRow, 0, filterLabelStyle);
    setStyle(filterRow, 1, filterValueStyle);
    setStyle(filterRow, 2, filterLabelStyle);
    setStyle(filterRow, 3, filterValueStyle);
    setStyle(filterRow, 4, filterLabelStyle);
    setStyle(filterRow, 5, filterValueStyle);

    sectionRows.forEach((row) => {
      styleFullRow(row, sectionStyle, 0, sectionEndColumns.get(row) ?? 5);
    });

    headerRows.forEach((row) => {
      styleFullRow(row, headerStyle, 0, headerEndColumns.get(row) ?? 5);
    });

    historySubsectionRows.forEach((row) => {
      styleFullRow(row, historySubsectionStyle, 0, 3);
    });

    collaboratorDataRows.forEach((row) => {
      styleFullRow(row, collaboratorDataStyle, 0, 1);
    });

    trainingDetailRows.forEach((row) => {
      styleFullRow(row, cellStyle, 0, 3);
      setStyle(row, 2, dateCellStyle);
      setStyle(row, 3, durationCellStyle);
    });

    trainingSummaryRows.forEach((row) => {
      styleFullRow(row, cellStyle, 0, 2);
      setStyle(row, 1, integerCellStyle);
      setStyle(row, 2, durationCellStyle);
    });

    collaboratorTotalRows.forEach((row) => {
      styleFullRow(row, collaboratorTotalStyle, 0, 2);
      setStyle(row, 1, {
        ...collaboratorTotalStyle,
        alignment: { horizontal: "right", vertical: "center" },
        numFmt: "0",
      });
      setStyle(row, 2, {
        ...collaboratorTotalStyle,
        alignment: { horizontal: "right", vertical: "center" },
        numFmt: excelDurationNumberFormat,
      });
    });

    const range = XLSX.utils.decode_range(worksheet["!ref"] ?? "A1:A1");

    for (let row = 0; row <= range.e.r; row++) {
      for (let col = 0; col <= range.e.c; col++) {
        const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });

        if (!worksheet[cellAddress]) continue;
        const styledCell = worksheet[cellAddress] as XLSX.CellObject & {
          s?: object;
        };

        if (styledCell.s) continue;

        const value = worksheet[cellAddress]?.v;
        const text = String(value ?? "").toLowerCase();

        styledCell.s = text.includes("no hay datos")
          ? mutedStyle
          : cellStyle;
      }
    }

    durationCells.forEach(({ row, col }) => {
      const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });
      const durationCell = worksheet[cellAddress] as
        | (XLSX.CellObject & {
            s?: Record<string, unknown> & {
              alignment?: Record<string, unknown>;
            };
          })
        | undefined;

      if (!durationCell) return;

      const decimalHours = Number(durationCell.v ?? 0);
      const totalMinutes = Number.isFinite(decimalHours)
        ? Math.max(0, Math.round(decimalHours * 60))
        : 0;
      const currentStyle = durationCell.s ?? cellStyle;

      durationCell.t = "n";
      durationCell.v = totalMinutes / 1440;
      durationCell.z = excelDurationNumberFormat;
      delete durationCell.w;
      durationCell.s = {
        ...currentStyle,
        alignment: {
          ...(currentStyle.alignment ?? {}),
          horizontal: "right",
          vertical: "center",
        },
        numFmt: excelDurationNumberFormat,
      };
    });

    worksheet["!rows"] = rows.map((_, index) => {
      let height = 20;

      if (index === titleRow) {
        height = 32;
      } else if (sectionRows.includes(index)) {
        height = 24;
      } else if (
        historySubsectionRows.includes(index) ||
        headerRows.includes(index)
      ) {
        height = 22;
      } else if (trainingDetailRowHeights.has(index)) {
        height = trainingDetailRowHeights.get(index) ?? 20;
      }

      return { hpt: height };
    });

    worksheet["!autofilter"] = {
      ref: XLSX.utils.encode_range({
        s: { r: 0, c: 0 },
        e: { r: range.e.r, c: range.e.c },
      }),
    };

    XLSX.utils.book_append_sheet(workbook, worksheet, "Reportes");

    XLSX.writeFile(
      workbook,
      `reportes_capacitacion_${dateFrom || "sin_fecha"}_${dateTo || "sin_fecha"}.xlsx`
    );
  };

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadReport();
    }, 0);

    return () => window.clearTimeout(timeoutId);
    // La carga inicial debe ejecutarse una sola vez; los cambios de filtros se
    // aplican explícitamente con el botón Consultar.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const donutData =
    report?.bySolutionCenter
      ?.filter((item) => item.totalTrainedPeople > 0)
      .map((item) => ({
        name: item.nameSolutionCenter,
        value: item.totalTrainedPeople,
      })) ?? [];

  const competencyChartData =
    report?.byCompetency
      ?.filter((item) => item.totalTrainedPeople > 0)
      .map((item) => ({
        name: item.nameCompetency,
        value: item.totalTrainedPeople,
      })) ?? [];

  const selectedCollaborator =
    collaboratorReport?.collaborators.find(
      (item) =>
        item.documentNumberAttendancePerson === selectedCollaboratorDocument
    ) ?? null;

  const collaboratorDonutData =
    selectedCollaborator?.byTrainingSolutionCenter.map((item) => ({
      name: item.nameSolutionCenter,
      value: item.totalTrainings,
    })) ?? [];

  const sstAverageHoursByCollaborator =
    sstReport?.summary.totalInternalSstTrainedPeople
      ? Number(
          (
            sstReport.summary.totalSstTrainingHours /
            sstReport.summary.totalInternalSstTrainedPeople
          ).toFixed(2)
        )
      : 0;

  const sstSummaryChartData = [
    {
      label: "Colaboradores internos SST",
      value: sstReport?.summary.totalInternalSstTrainedPeople ?? 0,
    },
    {
      label: "Tiempo total SST",
      value: sstReport?.summary.totalSstTrainingHours ?? 0,
      formattedValue: formatTrainingDuration(
        sstReport?.summary.totalSstTrainingHours
      ),
    },
    {
      label: "Tiempo por colaborador",
      value: sstAverageHoursByCollaborator,
      formattedValue: formatTrainingDuration(sstAverageHoursByCollaborator),
    },
  ];

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Box sx={{ display: "flex", flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 2, }}>
        <Box sx={{ display: "flex", flexDirection: "row", gap: 1.5, alignItems: "center", }}>
          <AssessmentOutlinedIcon sx={{ color: "#4B2E1F", fontSize: 30 }} />
          <Typography sx={{ color: "#4B2E1F", fontSize: 26, fontWeight: 700 }}>
            Reportes
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<FileDownloadOutlinedIcon />}
          onClick={exportReportsToExcel}
          disabled={loading}
          sx={{ borderColor: "#8B6A55", color: "#4B2E1F", textTransform: "none", fontWeight: 600, "&:hover": { borderColor: "#4B2E1F", bgcolor: "rgba(75, 46, 31, 0.05)", },}}>
          Exportar Excel
        </Button>
      </Box>
      <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 2, p: 2, bgcolor: "#FFFDF8", }}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, }}>
          <Typography sx={{ color: "#4B2E1F", fontSize: 16, fontWeight: 700, }}>
            Filtros
          </Typography>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr auto auto", }, gap: 2, alignItems: "center", }}>
            <TextField
              label="Fecha inicial"
              type="date"
              value={dateFrom}
              onChange={(event) => setDateFrom(event.target.value)}
              size="small"
              fullWidth
              slotProps={{
                inputLabel: {
                  shrink: true,
                },
              }}
            />
            <TextField
              label="Fecha final"
              type="date"
              value={dateTo}
              onChange={(event) => setDateTo(event.target.value)}
              size="small"
              fullWidth
              slotProps={{
                inputLabel: {
                  shrink: true,
                },
              }}
            />
            <Button
              variant="contained"
              onClick={loadReport}
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
              Consultar
            </Button>
            <Button
              variant="outlined"
              onClick={clearFilters}
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
          </Box>
        </Box>
      </Paper>

      <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, }}>
        <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 800, }}>
          Total de colaboradores capacitados
        </Typography>
      </Box>

      {loading ? (
        <Box sx={{ py: 6, display: "flex", justifyContent: "center" }}>
          <CircularProgress sx={{ color: "#4B2E1F" }} />
        </Box>
      ) : (
        <>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr 1fr", }, gap: 2, }}>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", minWidth: 0, }}>
              <CardContent sx={{ minWidth: 0 }}>
                <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center", }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#F7E8D8", color: "#4B2E1F", display: "flex", alignItems: "center", justifyContent: "center", }}>
                    <GroupsOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Total de colaboradores capacitados
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800, }}>
                      { report?.summary.totalTrainedPeople ?? 0 }
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
              <CardContent>
                <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center", }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#E8F5E9", color: "#2E7D32", display: "flex", alignItems: "center", justifyContent: "center", }}>
                    <BadgeOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Colaboradores internos capacitados
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800, }}>
                      { report?.summary.totalInternalTrainedPeople ?? 0 }
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
              <CardContent>
                <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center", }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#FFEBEE", color: "#C62828", display: "flex", alignItems: "center", justifyContent: "center", }}>
                    <PersonOffOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Personal externo capacitado
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800, }}>
                      { report?.summary.totalExternalTrainedPeople ?? 0 }
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "1.1fr 0.9fr", }, gap: 2, }}>
            <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, p: 2, bgcolor: "#FFFDF8", minHeight: 420, }}>
              <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700, mb: 2, }}>
                Colaboradores capacitados por centro de soluciones
              </Typography>
              <DonutChart data={donutData} />
            </Paper>
            <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, overflow: "hidden", bgcolor: "#FFFDF8", minHeight: 420, maxHeight: { xs: 620, lg: 520 }, display: "flex", flexDirection: "column", alignSelf: "start", width: "100%", }}>
              <Box sx={{ p: 2, flexShrink: 0 }}>
                <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700, }}>
                  Detalle por centro de soluciones
                </Typography>
              </Box>
              <Box
                sx={{
                  flex: 1,
                  minHeight: 0,
                  overflow: "auto",
                  scrollbarColor: "#8B6A55 #F7E8D8",
                  scrollbarWidth: "thin",
                  "&::-webkit-scrollbar": { width: 10, height: 10 },
                  "&::-webkit-scrollbar-track": { bgcolor: "#F7E8D8" },
                  "&::-webkit-scrollbar-thumb": { bgcolor: "#8B6A55", borderRadius: 10 },
                }}
              >
              <Table size="small" stickyHeader sx={{ minWidth: 620 }}>
                <TableHead>
                  <TableRow sx={{ bgcolor: "#F7E8D8" }}>
                    <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>
                      Centro de soluciones
                    </TableCell>
                    <TableCell align="right" sx={{ color: "#4B2E1F", fontWeight: 700 }}>
                      Capacitados
                    </TableCell>
                    <TableCell align="center" sx={{ color: "#4B2E1F", fontWeight: 700, width: 64 }}>
                      Detalle
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(report?.bySolutionCenter ?? []).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3} align="center" sx={{ color: "#7A6252", py: 3 }}>
                        No hay registros para mostrar.
                      </TableCell>
                    </TableRow>
                  ) : (
                    report?.bySolutionCenter.map((item) => {
                      const isExpanded =
                        expandedSolutionCenter === item.nameSolutionCenter;

                      return (
                        <Fragment key={item.nameSolutionCenter}>
                          <TableRow hover>
                            <TableCell>{item.nameSolutionCenter}</TableCell>
                            <TableCell align="right">
                              {item.totalTrainedPeople}
                            </TableCell>
                            <TableCell align="center">
                              <Tooltip title={isExpanded ? "Ocultar detalle" : "Ver detalle"}>
                                <IconButton
                                  size="small"
                                  onClick={() =>
                                    setExpandedSolutionCenter(
                                      isExpanded ? null : item.nameSolutionCenter
                                    )
                                  }
                                  aria-label={`${isExpanded ? "Ocultar" : "Ver"} detalle de ${item.nameSolutionCenter}`}
                                >
                                  {isExpanded ? (
                                    <KeyboardArrowUpIcon />
                                  ) : (
                                    <KeyboardArrowDownIcon />
                                  )}
                                </IconButton>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell colSpan={3} sx={{ p: 0, borderBottom: isExpanded ? undefined : 0 }}>
                              <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                                <Box sx={{ p: 2, bgcolor: "#FFFAF4", overflowX: "auto" }}>
                                  <Typography sx={{ color: "#4B2E1F", fontWeight: 700, mb: 1.5 }}>
                                    Asistencias registradas ({item.details.length})
                                  </Typography>
                                  <Table size="small" sx={{ minWidth: 720 }}>
                                    <TableHead>
                                      <TableRow>
                                        <TableCell sx={{ fontWeight: 700 }}>Capacitación</TableCell>
                                        <TableCell sx={{ fontWeight: 700 }}>Fecha</TableCell>
                                        <TableCell sx={{ fontWeight: 700 }}>Cédula</TableCell>
                                        <TableCell sx={{ fontWeight: 700 }}>Colaborador</TableCell>
                                        <TableCell align="right" sx={{ fontWeight: 700 }}>Tiempo</TableCell>
                                      </TableRow>
                                    </TableHead>
                                    <TableBody>
                                      {item.details.length === 0 ? (
                                        <TableRow>
                                          <TableCell colSpan={5} align="center" sx={{ color: "#7A6252" }}>
                                            No hay asistencias para mostrar.
                                          </TableCell>
                                        </TableRow>
                                      ) : (
                                        item.details.map((detail) => (
                                          <TableRow key={`${detail.IdEvent}-${detail.documentNumberAttendancePerson}`}>
                                            <TableCell>{detail.titleEvent}</TableCell>
                                            <TableCell>{formatReportDate(detail.dateEvent)}</TableCell>
                                            <TableCell>{detail.documentNumberAttendancePerson}</TableCell>
                                            <TableCell>{detail.fullNameAttendancePerson}</TableCell>
                                            <TableCell align="right">
                                              {formatTrainingDuration(detail.trainingHours)}
                                            </TableCell>
                                          </TableRow>
                                        ))
                                      )}
                                    </TableBody>
                                  </Table>
                                </Box>
                              </Collapse>
                            </TableCell>
                          </TableRow>
                        </Fragment>
                      );
                    })
                  )}
                </TableBody>
              </Table>
              </Box>
            </Paper>
          </Box>
          <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, p: 2, bgcolor: "#FFFDF8" }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700, mb: 2 }}>
              Competencias formadas
            </Typography>
            <Typography sx={{ color: "#7A6252", fontSize: 13, mb: 2 }}>
              Distribución porcentual de las asistencias registradas por competencia.
            </Typography>
            <DonutChart data={competencyChartData} centerLabel="Asistencias" />
          </Paper>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, mt: 2 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 800 }}>
              Capacitaciones SST
            </Typography>
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr 1fr", }, gap: 2, }}>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center" }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#F7E8D8", color: "#4B2E1F", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <EngineeringOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Colaboradores internos capacitados en SST
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {sstReport?.summary.totalInternalSstTrainedPeople ?? 0}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center" }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#E8F5E9", color: "#2E7D32", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <AccessTimeOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Tiempo total de capacitación SST
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {formatTrainingDuration(
                        sstReport?.summary.totalSstTrainingHours
                      )}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center" }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#FFEBEE", color: "#C62828", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <BadgeOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Tiempo SST por colaborador interno
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {formatTrainingDuration(sstAverageHoursByCollaborator)}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr", }, gap: 2, }}>
            <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, p: 2, bgcolor: "#FFFDF8" }}>
              <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700, mb: 2 }}>
                Indicadores SST
              </Typography>
              <SimpleBarChart data={sstSummaryChartData} />
            </Paper>
            <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, overflow: "hidden", bgcolor: "#FFFDF8" }}>
              <Box sx={{ p: 2 }}>
                <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700 }}>
                  Tiempo SST por colaborador interno
                </Typography>
              </Box>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: "#F7E8D8" }}>
                    <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>
                      Documento
                    </TableCell>
                    <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>
                      Colaborador
                    </TableCell>
                    <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>
                      Centro
                    </TableCell>
                    <TableCell align="right" sx={{ color: "#4B2E1F", fontWeight: 700 }}>
                      Tiempo
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(sstReport?.byCollaborator ?? []).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} align="center" sx={{ color: "#7A6252", py: 3 }}>
                        No hay registros para mostrar.
                      </TableCell>
                    </TableRow>
                  ) : (
                    sstReport?.byCollaborator.map((item) => (
                      <TableRow key={item.documentNumberAttendancePerson} hover>
                        <TableCell>{item.documentNumberAttendancePerson}</TableCell>
                        <TableCell>{item.fullNameAttendancePerson}</TableCell>
                        <TableCell>{item.nameSolutionCenter}</TableCell>
                        <TableCell align="right">
                          {formatTrainingDuration(item.totalSstTrainingHours)}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </Paper>
          </Box>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, mt: 2 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 800 }}>
              Tiempo de capacitación
            </Typography>
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr 1fr", }, gap: 2, }}>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Tiempo total de capacitación
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {formatTrainingDuration(
                    trainingHoursReport?.totalTrainingHours
                  )}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Tiempo categoría: Múltiples funciones
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {formatTrainingDuration(
                    trainingHoursReport?.totalMultipleFunctionsTrainingHours
                  )}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Tiempo categoría: Cargo
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {formatTrainingDuration(
                    trainingHoursReport?.totalPositionTrainingHours
                  )}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Tiempo categoría: Personal
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {formatTrainingDuration(
                    trainingHoursReport?.totalPersonalTrainingHours
                  )}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Tiempo programa: Ser
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {formatTrainingDuration(
                    trainingHoursReport?.totalSerTrainingHours
                  )}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Tiempo programa: Hacer
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {formatTrainingDuration(
                    trainingHoursReport?.totalHacerTrainingHours
                  )}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Tiempo total de capacitación a personal interno
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {formatTrainingDuration(
                    trainingHoursReport?.totalInternalTrainingHours
                  )}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Tiempo total de capacitación a personal externo
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {formatTrainingDuration(
                    trainingHoursReport?.totalExternalTrainingHours
                  )}
                </Typography>
              </CardContent>
            </Card>
          </Box>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, mt: 2 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 800 }}>
              Inducción a personal nuevo
            </Typography>
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr", }, gap: 2, }}>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
              <CardContent>
                <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center", }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#F7E8D8", color: "#4B2E1F", display: "flex", alignItems: "center", justifyContent: "center", }}>
                    <AccessTimeOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Tiempo total de inducción a personal nuevo
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {formatTrainingDuration(
                        newStaffInductionReport?.totalNewStaffInductionHours
                      )}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
              <CardContent>
                <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center", }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#E8F5E9", color: "#2E7D32", display: "flex", alignItems: "center", justifyContent: "center", }}>
                    <GroupsOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Personal capacitado en inducción a personal nuevo
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {newStaffInductionReport?.totalNewStaffInductionPeople ?? 0}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, mt: 2 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 800 }}>
              Inducción a personal administrativo
            </Typography>
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr", }, gap: 2, }}>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
              <CardContent>
                <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center", }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#F7E8D8", color: "#4B2E1F", display: "flex", alignItems: "center", justifyContent: "center", }}>
                    <AccessTimeOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Tiempo total de inducción a personal administrativo
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {formatTrainingDuration(
                        administrativeInductionReport?.totalAdministrativeInductionHours
                      )}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
              <CardContent>
                <Box sx={{ display: "flex", flexDirection: "row", gap: 2, alignItems: "center", }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#E8F5E9", color: "#2E7D32", display: "flex", alignItems: "center", justifyContent: "center", }}>
                    <GroupsOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Personal capacitado en inducción a personal administrativo
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {administrativeInductionReport?.totalAdministrativeInductionPeople ?? 0}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, mt: 2 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 800 }}>
              Transversales
            </Typography>
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr", }, gap: 2, }}>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#F7E8D8", color: "#4B2E1F", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <AccessTimeOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Tiempo total de capacitación transversal
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {formatTrainingDuration(
                        transversalTrainingReport?.totalTransversalTrainingHours
                      )}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
                  <Box sx={{ width: 50, height: 50, borderRadius: "50%", bgcolor: "#E8F5E9", color: "#2E7D32", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <GroupsOutlinedIcon />
                  </Box>
                  <Box>
                    <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                      Personal capacitado en transversales
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {transversalTrainingReport?.totalTransversalTrainingPeople ?? 0}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
          <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, overflow: "hidden", bgcolor: "#FFFDF8" }}>
            <Box sx={{ p: 2 }}>
              <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700 }}>
                Personal capacitado en transversales
              </Typography>
            </Box>
            <Box sx={{ overflowX: "auto" }}>
              <Table size="small" sx={{ minWidth: 700 }}>
                <TableHead>
                  <TableRow sx={{ bgcolor: "#F7E8D8" }}>
                    <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>Cédula</TableCell>
                    <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>Colaborador</TableCell>
                    <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>Centro de soluciones</TableCell>
                    <TableCell align="right" sx={{ color: "#4B2E1F", fontWeight: 700 }}>Tiempo</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(transversalTrainingReport?.byCollaborator ?? []).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} align="center" sx={{ color: "#7A6252", py: 3 }}>
                        No hay registros para mostrar.
                      </TableCell>
                    </TableRow>
                  ) : (
                    transversalTrainingReport?.byCollaborator.map((item) => (
                      <TableRow key={item.documentNumberAttendancePerson} hover>
                        <TableCell>{item.documentNumberAttendancePerson}</TableCell>
                        <TableCell>{item.fullNameAttendancePerson}</TableCell>
                        <TableCell>{item.nameSolutionCenter}</TableCell>
                        <TableCell align="right">
                          {formatTrainingDuration(
                            item.totalTransversalTrainingHours
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </Box>
          </Paper>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, mt: 2 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 800 }}>
              General
            </Typography>
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr", lg: "1fr 1fr 1fr 1fr", }, gap: 2, }}>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", minWidth: 0, }}>
              <CardContent sx={{ minWidth: 0 }}>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Centro de soluciones que más capacitó
                </Typography>
                <Typography
                  title={generalReport?.topTrainingSolutionCenterName ?? "SIN DATOS"}
                  sx={{
                    color: "#4B2E1F",
                    fontSize: { xs: 22, lg: 20 },
                    fontWeight: 800,
                    lineHeight: 1.2,
                    overflowWrap: "anywhere",
                    mt: 0.5,
                  }}
                >
                  {generalReport?.topTrainingSolutionCenterName ?? "SIN DATOS"}
                </Typography>
                <Typography sx={{ color: "#7A6252", fontSize: 13, mt: 0.5 }}>
                  {generalReport?.topTrainingSolutionCenterTotal ?? 0} colaboradores internos capacitados
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Internos capacitados en Calidad
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {generalReport?.totalInternalQualityTrainedPeople ?? 0}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Internos capacitados: Ser
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {generalReport?.totalInternalSerTrainedPeople ?? 0}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Internos capacitados: Hacer
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {generalReport?.totalInternalHacerTrainedPeople ?? 0}
                </Typography>
              </CardContent>
            </Card>
          </Box>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, mt: 2 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 800 }}>
              Promedio de tiempo de capacitación por colaborador
            </Typography>
          </Box>
          <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, p: 2, bgcolor: "#FFFDF8", }}>
            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr auto", }, gap: 2, alignItems: "center", mb: 2, }}>
              <TextField
                label="Total colaboradores vinculados a la compañía"
                type="number"
                value={totalWorkers}
                onChange={(event) => setTotalWorkers(event.target.value)}
                fullWidth
                size="small"
                slotProps={{
                  htmlInput: {
                    min: 1,
                  },
                }}
              />
              <Button
                variant="contained"
                onClick={loadAverageTrainingTimeReport}
                disabled={loadingAverageTrainingTime}
                sx={{ bgcolor: "#4B2E1F", textTransform: "none", fontWeight: 600, height: 40, minWidth: 170, "&:hover": { bgcolor: "#3A2318", }, }}>
                {loadingAverageTrainingTime ? "Consultando..." : "Consultar promedio"}
              </Button>
            </Box>
            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr 1fr", }, gap: 2, mb: 2, }}>
              <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
                <CardContent>
                  <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                    Total colaboradores vinculados
                  </Typography>
                  <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                    {averageTrainingTimeReport?.totalWorkers ?? 0}
                  </Typography>
                </CardContent>
              </Card>
              <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
                <CardContent>
                  <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                    Tiempo total de capacitación personal interno
                  </Typography>
                  <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                    {formatTrainingDuration(
                      averageTrainingTimeReport?.totalInternalTrainingHours
                    )}
                  </Typography>
                </CardContent>
              </Card>
              <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
                <CardContent>
                  <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                    Promedio tiempo por colaborador
                  </Typography>
                  <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                    {formatTrainingDuration(
                      averageTrainingTimeReport?.averageTrainingHoursPerWorker
                    )}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
            <AverageGauge
              value={averageTrainingTimeReport?.averageTrainingHoursPerWorker ?? 0}
            />
          </Paper>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, mt: 2 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 800 }}>
              Historial de capacitación por colaborador
            </Typography>
            <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
              Consulta por nombre o cédula y revisa sus tiempos y capacitaciones por centro de soluciones.
            </Typography>
          </Box>
          <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, p: 2, bgcolor: "#FFFDF8" }}>
            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "2fr 1fr 1fr auto" }, gap: 2, alignItems: "center" }}>
              <TextField
                label="Nombre o cédula del colaborador"
                value={collaboratorSearch}
                onChange={(event) => setCollaboratorSearch(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    loadCollaboratorTrainingReport();
                  }
                }}
                size="small"
                fullWidth
              />
              <TextField
                label="Fecha inicial"
                type="date"
                value={collaboratorDateFrom}
                onChange={(event) => setCollaboratorDateFrom(event.target.value)}
                size="small"
                fullWidth
                slotProps={{ inputLabel: { shrink: true } }}
              />
              <TextField
                label="Fecha final"
                type="date"
                value={collaboratorDateTo}
                onChange={(event) => setCollaboratorDateTo(event.target.value)}
                size="small"
                fullWidth
                slotProps={{ inputLabel: { shrink: true } }}
              />
              <Button
                variant="contained"
                startIcon={<SearchOutlinedIcon />}
                onClick={loadCollaboratorTrainingReport}
                disabled={loadingCollaborator}
                sx={{ bgcolor: "#4B2E1F", textTransform: "none", fontWeight: 600, height: 40, whiteSpace: "nowrap", "&:hover": { bgcolor: "#3A2318" } }}
              >
                {loadingCollaborator ? "Consultando..." : "Consultar"}
              </Button>
            </Box>
          </Paper>

          {loadingCollaborator ? (
            <Box sx={{ py: 4, display: "flex", justifyContent: "center" }}>
              <CircularProgress sx={{ color: "#4B2E1F" }} />
            </Box>
          ) : collaboratorReport === null ? (
            <Paper elevation={0} sx={{ border: "1px dashed #D8C2AE", borderRadius: 3, p: 3, bgcolor: "#FFFDF8", textAlign: "center" }}>
              <Typography sx={{ color: "#7A6252" }}>
                Usa los filtros para consultar el historial de un colaborador.
              </Typography>
            </Paper>
          ) : collaboratorReport.collaborators.length === 0 ? (
            <Paper elevation={0} sx={{ border: "1px dashed #D8C2AE", borderRadius: 3, p: 3, bgcolor: "#FFFDF8", textAlign: "center" }}>
              <Typography sx={{ color: "#7A6252" }}>
                No se encontraron capacitaciones para el colaborador y rango indicados.
              </Typography>
            </Paper>
          ) : (
            <>
              <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, overflow: "hidden", bgcolor: "#FFFDF8" }}>
                <Box sx={{ p: 2 }}>
                  <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700 }}>
                    Colaboradores encontrados
                  </Typography>
                  <Typography sx={{ color: "#7A6252", fontSize: 13 }}>
                    Selecciona una fila para visualizar su detalle.
                  </Typography>
                </Box>
                <Box sx={{ overflowX: "auto" }}>
                  <Table size="small" sx={{ minWidth: 760 }}>
                    <TableHead>
                      <TableRow sx={{ bgcolor: "#F7E8D8" }}>
                        <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>Cédula</TableCell>
                        <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>Colaborador</TableCell>
                        <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>Centro del colaborador</TableCell>
                        <TableCell align="right" sx={{ color: "#4B2E1F", fontWeight: 700 }}>Capacitaciones</TableCell>
                        <TableCell align="right" sx={{ color: "#4B2E1F", fontWeight: 700 }}>Tiempo</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {collaboratorReport.collaborators.map((item) => {
                        const isSelected =
                          item.documentNumberAttendancePerson ===
                          selectedCollaboratorDocument;

                        return (
                          <TableRow
                            key={item.documentNumberAttendancePerson}
                            hover
                            selected={isSelected}
                            onClick={() =>
                              setSelectedCollaboratorDocument(
                                item.documentNumberAttendancePerson
                              )
                            }
                            sx={{ cursor: "pointer", "&.Mui-selected": { bgcolor: "#F7E8D8" } }}
                          >
                            <TableCell>{item.documentNumberAttendancePerson}</TableCell>
                            <TableCell>{item.fullNameAttendancePerson}</TableCell>
                            <TableCell>{item.nameSolutionCenter}</TableCell>
                            <TableCell align="right">{item.totalTrainings}</TableCell>
                            <TableCell align="right">
                              {formatTrainingDuration(item.totalTrainingHours)}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </Box>
              </Paper>

              {selectedCollaborator && (
                <>
                  <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" }, gap: 2 }}>
                    <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
                      <CardContent>
                        <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                          Total de capacitaciones recibidas
                        </Typography>
                        <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                          {selectedCollaborator.totalTrainings}
                        </Typography>
                      </CardContent>
                    </Card>
                    <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
                      <CardContent>
                        <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                          Tiempo total acumulado
                        </Typography>
                        <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                          {formatTrainingDuration(
                            selectedCollaborator.totalTrainingHours
                          )}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Box>
                  <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "0.9fr 1.1fr" }, gap: 2 }}>
                    <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, p: 2, bgcolor: "#FFFDF8" }}>
                      <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700, mb: 2 }}>
                        Capacitaciones por centro de soluciones
                      </Typography>
                      <DonutChart data={collaboratorDonutData} centerLabel="capacitaciones" />
                    </Paper>
                    <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, overflow: "hidden", bgcolor: "#FFFDF8" }}>
                      <Box sx={{ p: 2 }}>
                        <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700 }}>
                          Capacitaciones recibidas
                        </Typography>
                      </Box>
                      <Box sx={{ overflowX: "auto" }}>
                        <Table size="small" sx={{ minWidth: 650 }}>
                          <TableHead>
                            <TableRow sx={{ bgcolor: "#F7E8D8" }}>
                              <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>Capacitación</TableCell>
                              <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>Fecha</TableCell>
                              <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>Centro formador</TableCell>
                              <TableCell align="right" sx={{ color: "#4B2E1F", fontWeight: 700 }}>Tiempo</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {selectedCollaborator.trainings.map((training) => (
                              <TableRow key={`${training.IdEvent}-${training.dateEvent}`} hover>
                                <TableCell>{training.titleEvent}</TableCell>
                                <TableCell>{formatReportDate(training.dateEvent)}</TableCell>
                                <TableCell>{training.nameSolutionCenter}</TableCell>
                                <TableCell align="right">
                                  {formatTrainingDuration(training.trainingHours)}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </Box>
                    </Paper>
                  </Box>
                </>
              )}
            </>
          )}
        </>
      )}

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
