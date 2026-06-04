import { Box, Button, Card, CardContent, CircularProgress, Paper, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography, } from "@mui/material";
import { ResponseModal, type ResponseModalSeverity, } from "../components/ResponseModal";
import FileDownloadOutlinedIcon from "@mui/icons-material/FileDownloadOutlined";
import EngineeringOutlinedIcon from "@mui/icons-material/EngineeringOutlined";
import AccessTimeOutlinedIcon from "@mui/icons-material/AccessTimeOutlined";
import AssessmentOutlinedIcon from "@mui/icons-material/AssessmentOutlined";
import PersonOffOutlinedIcon from "@mui/icons-material/PersonOffOutlined";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import BadgeOutlinedIcon from "@mui/icons-material/BadgeOutlined";
import { getErrorMessage } from "../services/errorService";
import { reportService } from "../services/reportService";
import { useEffect, useState } from "react";
import * as XLSX from "xlsx-js-style";
import type {
  TrainingReportResponse,
  SstTrainingReportResponse,
  TrainingHoursReportResponse,
  NewStaffInductionReportResponse,
  AdministrativeInductionReportResponse,
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

function DonutChart({ data }: DonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  const radius = 80;
  const strokeWidth = 34;
  const circumference = 2 * Math.PI * radius;

  let accumulated = 0;

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
            const offset = -accumulated;

            accumulated += dash;

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
            capacitados
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
}

interface SimpleBarChartProps {
  data: BarChartItem[];
}

function SimpleBarChart({ data }: SimpleBarChartProps) {
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
                { item.value }
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

export function ReportPage() {
  const [administrativeInductionReport, setAdministrativeInductionReport] = useState<AdministrativeInductionReportResponse | null>(null);
  const [averageTrainingTimeReport, setAverageTrainingTimeReport] = useState<AverageTrainingTimeReportResponse | null>(null);
  const [newStaffInductionReport, setNewStaffInductionReport] = useState<NewStaffInductionReportResponse | null>(null);
  const [trainingHoursReport, setTrainingHoursReport] = useState<TrainingHoursReportResponse | null>(null);
  const [responseModal, setResponseModal] = useState<ResponseModalState>(emptyResponseModal);
  const [generalReport, setGeneralReport] = useState<GeneralReportResponse | null>(null);
  const [loadingAverageTrainingTime, setLoadingAverageTrainingTime] = useState(false);
  const [sstReport, setSstReport] = useState<SstTrainingReportResponse | null>(null);
  const [report, setReport] = useState<TrainingReportResponse | null>(null);
  const [totalWorkers, setTotalWorkers] = useState("");
  const currentMonthRange = getCurrentMonthRange();
  const [dateFrom, setDateFrom] = useState(currentMonthRange.dateFrom);
  const [dateTo, setDateTo] = useState(currentMonthRange.dateTo);
  const [loading, setLoading] = useState(false);
  
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

      const [trainingResponse, sstTrainingResponse, trainingHoursResponse, newStaffInductionResponse, administrativeInductionResponse, generalResponse] = await Promise.all([
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
        showResponseModal("error", "Error", trainingHoursResponse.Message || "No se pudo cargar el reporte de horas.");
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

      if (!generalResponse.isSuccess || !generalResponse.result) {
        showResponseModal("error", "Error", generalResponse.Message || "No se pudo cargar el reporte general.");
        return;
      }

      setReport(trainingResponse.result);
      setSstReport(sstTrainingResponse.result);
      setTrainingHoursReport(trainingHoursResponse.result);
      setNewStaffInductionReport(newStaffInductionResponse.result);
      setAdministrativeInductionReport(administrativeInductionResponse.result);
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

      const [trainingResponse, sstTrainingResponse, trainingHoursResponse, newStaffInductionResponse, administrativeInductionResponse, generalResponse] = await Promise.all([
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
        reportService.getGeneralReport({
          dateFrom,
          dateTo
        }),
      ]);

      setReport(trainingResponse.isSuccess ? trainingResponse.result ?? null : null);
      setSstReport(sstTrainingResponse.isSuccess ? sstTrainingResponse.result ?? null : null);
      setTrainingHoursReport(trainingHoursResponse.isSuccess ? trainingHoursResponse.result ?? null : null);
      setNewStaffInductionReport(newStaffInductionResponse.isSuccess ? newStaffInductionResponse.result ?? null : null);
      setAdministrativeInductionReport(administrativeInductionResponse.isSuccess ? administrativeInductionResponse.result ?? null : null);
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

  const exportReportsToExcel = () => {
    const hasData =
      report ||
      sstReport ||
      trainingHoursReport ||
      newStaffInductionReport ||
      administrativeInductionReport ||
      generalReport ||
      averageTrainingTimeReport;

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
    const headerRows: number[] = [];

    const addRow = (row: unknown[]) => {
      rows.push(row);
      return rows.length - 1;
    };

    const addBlankRow = () => addRow([]);

    const addSection = (title: string) => {
      addBlankRow();
      const index = addRow([title]);
      sectionRows.push(index);
      return index;
    };

    const addHeader = (row: unknown[]) => {
      const index = addRow(row);
      headerRows.push(index);
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

    addSection("CAPACITACIONES SST");
    addHeader(["Indicador", "Valor"]);
    addRow([
      "Total de colaboradores internos capacitados en SST",
      formatNumber(sstReport?.summary.totalInternalSstTrainedPeople),
    ]);
    addRow([
      "Total de horas de capacitación en SST",
      formatNumber(sstReport?.summary.totalSstTrainingHours),
    ]);
    addRow([
      "Número de horas de capacitación en SST por colaborador interno",
      sstAverageHoursByCollaborator,
    ]);

    addBlankRow();
    addHeader([
      "Documento",
      "Colaborador",
      "Centro de soluciones",
      "Horas SST",
    ]);
    if ((sstReport?.byCollaborator ?? []).length === 0) {
      addRow(["No hay datos", "", "", 0]);
    } else {
      sstReport?.byCollaborator.forEach((item) => {
        addRow([
          item.documentNumberAttendancePerson,
          item.fullNameAttendancePerson,
          item.nameSolutionCenter,
          formatNumber(item.totalSstTrainingHours),
        ]);
      });
    }

    addSection("HORAS DE CAPACITACIÓN");
    addHeader(["Indicador", "Valor"]);
    addRow([
      "Horas totales de capacitación",
      formatNumber(trainingHoursReport?.totalTrainingHours),
    ]);
    addRow([
      "Horas totales de capacitación categoría: Múltiples funciones",
      formatNumber(trainingHoursReport?.totalMultipleFunctionsTrainingHours),
    ]);
    addRow([
      "Horas totales de capacitación categoría: Cargo",
      formatNumber(trainingHoursReport?.totalPositionTrainingHours),
    ]);
    addRow([
      "Horas totales de capacitación categoría: Personal",
      formatNumber(trainingHoursReport?.totalPersonalTrainingHours),
    ]);
    addRow([
      "Horas totales: Ser",
      formatNumber(trainingHoursReport?.totalSerTrainingHours),
    ]);
    addRow([
      "Horas totales: Hacer",
      formatNumber(trainingHoursReport?.totalHacerTrainingHours),
    ]);
    addRow([
      "Horas totales de capacitación a personal interno",
      formatNumber(trainingHoursReport?.totalInternalTrainingHours),
    ]);
    addRow([
      "Horas totales de capacitación a personal externo",
      formatNumber(trainingHoursReport?.totalExternalTrainingHours),
    ]);

    addSection("INDUCCIÓN A PERSONAL NUEVO");
    addHeader(["Indicador", "Valor"]);
    addRow([
      "Horas totales inducción personal nuevo",
      formatNumber(newStaffInductionReport?.totalNewStaffInductionHours),
    ]);
    addRow([
      "Total de personal capacitado en inducción a personal nuevo",
      formatNumber(newStaffInductionReport?.totalNewStaffInductionPeople),
    ]);

    addSection("INDUCCIÓN A PERSONAL ADMINISTRATIVO");
    addHeader(["Indicador", "Valor"]);
    addRow([
      "Horas totales en inducción a personal administrativo",
      formatNumber(administrativeInductionReport?.totalAdministrativeInductionHours),
    ]);
    addRow([
      "Total de personal capacitado en inducción a personal administrativo",
      formatNumber(administrativeInductionReport?.totalAdministrativeInductionPeople),
    ]);

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
      addRow([
        "Horas totales capacitación personal interno",
        formatNumber(averageTrainingTimeReport.totalInternalTrainingHours),
      ]);
      addRow([
        "Promedio de horas por colaborador",
        formatNumber(averageTrainingTimeReport.averageTrainingHoursPerWorker),
      ]);
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

    const setStyle = (row: number, col: number, style: object) => {
      const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });

      if (!worksheet[cellAddress]) {
        worksheet[cellAddress] = { t: "s", v: "" };
      }

      (worksheet[cellAddress] as any).s = style;
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
      styleFullRow(row, sectionStyle);
    });

    headerRows.forEach((row) => {
      styleFullRow(row, headerStyle);
    });

    const range = XLSX.utils.decode_range(worksheet["!ref"] ?? "A1:A1");

    for (let row = 0; row <= range.e.r; row++) {
      for (let col = 0; col <= range.e.c; col++) {
        const cellAddress = XLSX.utils.encode_cell({ r: row, c: col });

        if (!worksheet[cellAddress]) continue;
        if ((worksheet[cellAddress] as any).s) continue;

        const value = worksheet[cellAddress]?.v;
        const text = String(value ?? "").toLowerCase();

        (worksheet[cellAddress] as any).s = text.includes("no hay datos")
          ? mutedStyle
          : cellStyle;
      }
    }

    worksheet["!rows"] = rows.map((_, index) => ({
      hpt:
        index === titleRow
          ? 32
          : sectionRows.includes(index)
          ? 24
          : headerRows.includes(index)
          ? 22
          : 20,
    }));

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
    loadReport();
  }, []);

  const donutData =
    report?.bySolutionCenter
      ?.filter((item) => item.totalTrainedPeople > 0)
      .map((item) => ({
        name: item.nameSolutionCenter,
        value: item.totalTrainedPeople,
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
      label: "Horas totales SST",
      value: sstReport?.summary.totalSstTrainingHours ?? 0,
    },
    {
      label: "Horas por colaborador",
      value: sstAverageHoursByCollaborator,
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
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
              <CardContent>
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
            <Paper elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, overflow: "hidden", bgcolor: "#FFFDF8", }}>
              <Box sx={{ p: 2 }}>
                <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700, }}>
                  Detalle por centro de soluciones
                </Typography>
              </Box>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: "#F7E8D8" }}>
                    <TableCell sx={{ color: "#4B2E1F", fontWeight: 700 }}>
                      Centro de soluciones
                    </TableCell>
                    <TableCell align="right" sx={{ color: "#4B2E1F", fontWeight: 700 }}>
                      Capacitados
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(report?.bySolutionCenter ?? []).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={2} align="center" sx={{ color: "#7A6252", py: 3 }}>
                        No hay registros para mostrar.
                      </TableCell>
                    </TableRow>
                  ) : (
                    report?.bySolutionCenter.map((item) => (
                      <TableRow key={item.nameSolutionCenter} hover>
                        <TableCell>{item.nameSolutionCenter}</TableCell>
                        <TableCell align="right">
                          {item.totalTrainedPeople}
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
                      Total de horas de capacitación SST
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {sstReport?.summary.totalSstTrainingHours ?? 0}
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
                      Horas SST por colaborador interno
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {sstAverageHoursByCollaborator}
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
                  Horas SST por colaborador interno
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
                      Horas
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
                        <TableCell align="right">{item.totalSstTrainingHours}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </Paper>
          </Box>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, mt: 2 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 800 }}>
              Horas de capacitación
            </Typography>
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr 1fr", }, gap: 2, }}>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Horas totales de capacitación
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {trainingHoursReport?.totalTrainingHours ?? 0}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Horas categoría: Múltiples funciones
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {trainingHoursReport?.totalMultipleFunctionsTrainingHours ?? 0}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Horas categoría: Cargo
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {trainingHoursReport?.totalPositionTrainingHours ?? 0}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Horas categoría: Personal
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {trainingHoursReport?.totalPersonalTrainingHours ?? 0}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Horas programa: Ser
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {trainingHoursReport?.totalSerTrainingHours ?? 0}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Horas programa: Hacer
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {trainingHoursReport?.totalHacerTrainingHours ?? 0}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Horas totales de capacitación a personal interno
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {trainingHoursReport?.totalInternalTrainingHours ?? 0}
                </Typography>
              </CardContent>
            </Card>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Horas totales de capacitación a personal externo
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {trainingHoursReport?.totalExternalTrainingHours ?? 0}
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
                      Horas totales inducción personal nuevo
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {newStaffInductionReport?.totalNewStaffInductionHours ?? 0}
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
                      Horas totales en inducción a personal administrativo
                    </Typography>
                    <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                      {administrativeInductionReport?.totalAdministrativeInductionHours ?? 0}
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
              General
            </Typography>
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr", lg: "1fr 1fr 1fr 1fr", }, gap: 2, }}>
            <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
              <CardContent>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Centro de soluciones que más capacitó
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 24, fontWeight: 800 }}>
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
                    Horas totales capacitación personal interno
                  </Typography>
                  <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                    {averageTrainingTimeReport?.totalInternalTrainingHours ?? 0}
                  </Typography>
                </CardContent>
              </Card>
              <Card elevation={0} sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8", }}>
                <CardContent>
                  <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                    Promedio horas por colaborador
                  </Typography>
                  <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                    {(averageTrainingTimeReport?.averageTrainingHoursPerWorker ?? 0).toFixed(4)}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
            <AverageGauge
              value={averageTrainingTimeReport?.averageTrainingHoursPerWorker ?? 0}
            />
          </Paper>
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