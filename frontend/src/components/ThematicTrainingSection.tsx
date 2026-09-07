import AccessTimeOutlinedIcon from "@mui/icons-material/AccessTimeOutlined";
import BadgeOutlinedIcon from "@mui/icons-material/BadgeOutlined";
import EngineeringOutlinedIcon from "@mui/icons-material/EngineeringOutlined";
import {
  Box,
  Card,
  CardContent,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import type { ThematicTrainingSection } from "../models/Report";

interface ThematicTrainingSectionProps {
  report: ThematicTrainingSection;
  formatDuration: (decimalHours?: number | null) => string;
}

const indicatorColors = ["#4B2E1F", "#8B6A55", "#D8A86A"];

export function ThematicTrainingSectionPanel({
  report,
  formatDuration,
}: ThematicTrainingSectionProps) {
  const { summary } = report;
  const indicators = [
    {
      label: `Colaboradores internos capacitados en ${report.name}`,
      value: summary.totalInternalTrainedPeople,
      formattedValue: String(summary.totalInternalTrainedPeople),
    },
    {
      label: `Tiempo total de capacitación ${report.name}`,
      value: summary.totalTrainingHours,
      formattedValue: formatDuration(summary.totalTrainingHours),
    },
    {
      label: `Tiempo por colaborador interno en ${report.name}`,
      value: summary.averageTrainingHoursPerInternalCollaborator,
      formattedValue: formatDuration(
        summary.averageTrainingHoursPerInternalCollaborator
      ),
    },
  ];
  const maximumIndicatorValue = Math.max(
    ...indicators.map((indicator) => indicator.value),
    1
  );
  const topicLabel = report.key === "PRODUCTO" ? "Línea de producto" : "Temario";

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 2 }}>
      <Box>
        <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 800 }}>
          Capacitaciones de {report.name}
        </Typography>
        <Typography sx={{ color: "#7A6252", fontSize: 13 }}>
          El tiempo total acumula la asistencia del personal interno y externo.
        </Typography>
      </Box>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", md: "1fr 1fr 1fr" },
          gap: 2,
        }}
      >
        <Card
          elevation={0}
          sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}
        >
          <CardContent>
            <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
              <Box
                sx={{
                  width: 50,
                  height: 50,
                  flex: "0 0 50px",
                  borderRadius: "50%",
                  bgcolor: "#F7E8D8",
                  color: "#4B2E1F",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <EngineeringOutlinedIcon />
              </Box>
              <Box sx={{ minWidth: 0 }}>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Colaboradores internos capacitados en {report.name}
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {summary.totalInternalTrainedPeople}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          elevation={0}
          sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}
        >
          <CardContent>
            <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
              <Box
                sx={{
                  width: 50,
                  height: 50,
                  flex: "0 0 50px",
                  borderRadius: "50%",
                  bgcolor: "#E8F5E9",
                  color: "#2E7D32",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <AccessTimeOutlinedIcon />
              </Box>
              <Box sx={{ minWidth: 0 }}>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Tiempo total de capacitación {report.name}
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {formatDuration(summary.totalTrainingHours)}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Card
          elevation={0}
          sx={{ border: "1px solid #E0CDBB", borderRadius: 3, bgcolor: "#FFFDF8" }}
        >
          <CardContent>
            <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
              <Box
                sx={{
                  width: 50,
                  height: 50,
                  flex: "0 0 50px",
                  borderRadius: "50%",
                  bgcolor: "#FFEBEE",
                  color: "#C62828",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <BadgeOutlinedIcon />
              </Box>
              <Box sx={{ minWidth: 0 }}>
                <Typography sx={{ color: "#7A6252", fontSize: 14 }}>
                  Tiempo {report.name} por colaborador interno
                </Typography>
                <Typography sx={{ color: "#4B2E1F", fontSize: 30, fontWeight: 800 }}>
                  {formatDuration(
                    summary.averageTrainingHoursPerInternalCollaborator
                  )}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" },
          gap: 2,
          alignItems: "stretch",
        }}
      >
        <Paper
          elevation={0}
          sx={{ border: "1px solid #E0CDBB", borderRadius: 3, p: 2, bgcolor: "#FFFDF8" }}
        >
          <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700, mb: 2 }}>
            Indicadores {report.name}
          </Typography>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {indicators.map((indicator, index) => {
              const width = Math.max(
                (indicator.value / maximumIndicatorValue) * 100,
                indicator.value > 0 ? 4 : 0
              );

              return (
                <Box key={indicator.label}>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 2,
                      mb: 0.8,
                    }}
                  >
                    <Typography sx={{ color: "#4B2E1F", fontSize: 14, fontWeight: 600 }}>
                      {indicator.label}
                    </Typography>
                    <Typography sx={{ color: "#7A6252", fontSize: 14, fontWeight: 700 }}>
                      {indicator.formattedValue}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      height: 14,
                      borderRadius: 10,
                      bgcolor: "#F7E8D8",
                      overflow: "hidden",
                    }}
                  >
                    <Box
                      sx={{
                        width: `${width}%`,
                        height: "100%",
                        borderRadius: 10,
                        bgcolor: indicatorColors[index],
                      }}
                    />
                  </Box>
                </Box>
              );
            })}
          </Box>
        </Paper>

        <Paper
          elevation={0}
          sx={{ border: "1px solid #E0CDBB", borderRadius: 3, overflow: "hidden", bgcolor: "#FFFDF8" }}
        >
          <Box sx={{ p: 2 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700 }}>
              Tiempo {report.name} por colaborador interno
            </Typography>
          </Box>
          <Box sx={{ maxHeight: 360, overflow: "auto" }}>
            <Table stickyHeader size="small" sx={{ minWidth: 700 }}>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: "#4B2E1F", fontWeight: 700, bgcolor: "#F7E8D8" }}>
                    Documento
                  </TableCell>
                  <TableCell sx={{ color: "#4B2E1F", fontWeight: 700, bgcolor: "#F7E8D8" }}>
                    Colaborador
                  </TableCell>
                  <TableCell sx={{ color: "#4B2E1F", fontWeight: 700, bgcolor: "#F7E8D8" }}>
                    Centro
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ color: "#4B2E1F", fontWeight: 700, bgcolor: "#F7E8D8" }}
                  >
                    Tiempo
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {report.byCollaborator.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} align="center" sx={{ color: "#7A6252", py: 3 }}>
                      No hay registros para mostrar.
                    </TableCell>
                  </TableRow>
                ) : (
                  report.byCollaborator.map((collaborator) => (
                    <TableRow key={collaborator.documentNumberAttendancePerson} hover>
                      <TableCell>{collaborator.documentNumberAttendancePerson}</TableCell>
                      <TableCell>{collaborator.fullNameAttendancePerson}</TableCell>
                      <TableCell>{collaborator.nameSolutionCenter}</TableCell>
                      <TableCell align="right">
                        {formatDuration(collaborator.totalTrainingHours)}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Box>
        </Paper>
      </Box>

      {["PRODUCTO", "SER"].includes(report.key) && (
        <Paper
          elevation={0}
          sx={{ border: "1px solid #E0CDBB", borderRadius: 3, overflow: "hidden", bgcolor: "#FFFDF8" }}
        >
          <Box sx={{ p: 2 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 18, fontWeight: 700 }}>
              {report.key === "PRODUCTO"
                ? "Capacitaciones por línea de producto"
                : `Temarios de ${report.name}`}
            </Typography>
          </Box>
          <Box sx={{ maxHeight: 360, overflow: "auto" }}>
            <Table stickyHeader size="small" sx={{ minWidth: 620 }}>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: "#4B2E1F", fontWeight: 700, bgcolor: "#F7E8D8" }}>
                    {topicLabel}
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ color: "#4B2E1F", fontWeight: 700, bgcolor: "#F7E8D8" }}
                  >
                    Capacitaciones
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ color: "#4B2E1F", fontWeight: 700, bgcolor: "#F7E8D8" }}
                  >
                    Personas capacitadas
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {report.byTopic.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} align="center" sx={{ color: "#7A6252", py: 3 }}>
                      No hay registros para mostrar.
                    </TableCell>
                  </TableRow>
                ) : (
                  report.byTopic.map((topic) => (
                    <TableRow key={topic.nameEventTopic} hover>
                      <TableCell sx={{ overflowWrap: "anywhere" }}>
                        {topic.nameEventTopic}
                      </TableCell>
                      <TableCell align="right">{topic.totalTrainings}</TableCell>
                      <TableCell align="right">{topic.totalTrainedPeople}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Box>
        </Paper>
      )}
    </Box>
  );
}
