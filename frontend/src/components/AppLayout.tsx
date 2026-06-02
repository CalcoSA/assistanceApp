import { Avatar, Box, Button, Collapse, Divider, IconButton, Tooltip, Typography, Dialog, DialogActions, DialogContent, DialogTitle, Paper, Stack, } from "@mui/material";
import AdminPanelSettingsOutlinedIcon from "@mui/icons-material/AdminPanelSettingsOutlined";
import DashboardCustomizeOutlinedIcon from "@mui/icons-material/DashboardCustomizeOutlined";
import DeliveryDiningOutlinedIcon from "@mui/icons-material/DeliveryDiningOutlined";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";
import AssessmentOutlinedIcon from "@mui/icons-material/AssessmentOutlined";
import PeopleAltOutlinedIcon from "@mui/icons-material/PeopleAltOutlined";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import EmailOutlinedIcon from "@mui/icons-material/EmailOutlined";
import EventOutlinedIcon from "@mui/icons-material/EventOutlined";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import TuneOutlinedIcon from "@mui/icons-material/TuneOutlined";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import InstagramIcon from "@mui/icons-material/Instagram";
import LanguageIcon from "@mui/icons-material/Language";
import FacebookIcon from "@mui/icons-material/Facebook";
import LogoutIcon from "@mui/icons-material/Logout";
import CoffeeIcon from "@mui/icons-material/Coffee";
import CloseIcon from "@mui/icons-material/Close";
import { type ReactNode, useState } from "react";
import { useAuth } from "../context/AuthContext";

interface MenuItem {
  label: string;
  path: string;
  icon: ReactNode;
}

interface SidebarProps {
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

const SIDEBAR_CLOSED_WIDTH = 82;
const SIDEBAR_OPEN_WIDTH = 260;

const masterItems: MenuItem[] = [
  {
    label: "Centro de soluciones",
    path: "/maestros/centro-soluciones",
    icon: <BusinessOutlinedIcon />,
  },
  {
    label: "Domiciliarios",
    path: "/maestros/domiciliarios",
    icon: <DeliveryDiningOutlinedIcon />,
  },
  {
    label: "Parámetros",
    path: "/maestros/parametros",
    icon: <TuneOutlinedIcon />,
  },
  {
    label: "Roles",
    path: "/maestros/roles",
    icon: <AdminPanelSettingsOutlinedIcon />,
  },
  {
    label: "Usuarios",
    path: "/maestros/usuarios",
    icon: <PeopleAltOutlinedIcon />,
  },
  {
    label: "Correos PDV",
    path: "/maestros/correos-pdv",
    icon: <EmailOutlinedIcon />,
  },
];

const mainItems: MenuItem[] = [
  {
    label: "Eventos",
    path: "/eventos",
    icon: <EventOutlinedIcon />,
  },
  {
    label: "Reportes",
    path: "/reportes",
    icon: <AssessmentOutlinedIcon />,
  },
];

type HelpPath = "/registro-domicilios" | "/reporte-domicilios";

interface HelpStep {
  title: string;
  description: string;
}

interface HelpContent {
  title: string;
  description: string;
  steps: HelpStep[];
  recommendations: string[];
}

const getHelpPathFromCurrentRoute = (pathname: string): HelpPath => {
  if (pathname === "/reporte-domicilios") {
    return "/reporte-domicilios";
  }

  return "/registro-domicilios";
};

const helpContentByPath: Record<HelpPath, HelpContent> = {
  "/registro-domicilios": {
    title: "Instructivo - Registro de domicilios",
    description:
      "Esta opción permite registrar los domicilios realizados por cada domiciliario, según la fecha y el punto de venta seleccionado. También permite registrar ausentismos cuando el domiciliario no realiza domicilios en la fecha seleccionada.",
    steps: [
      {
        title: "Selecciona la fecha",
        description:
          "Elige la fecha correspondiente al día que deseas registrar. Por defecto, el sistema puede cargar la fecha actual.",
      },
      {
        title: "Selecciona el punto de venta",
        description:
          "Escoge el punto de venta al que pertenecen los domiciliarios. Al seleccionarlo, el sistema cargará los domiciliarios activos asociados.",
      },
      {
        title: "Registra los domicilios",
        description:
          "Ingresa la cantidad de domicilios realizados por cada domiciliario. El campo solo permite valores numéricos.",
      },
      {
        title: "Selecciona un ausentismo si aplica",
        description:
          "Si un domiciliario no realizó domicilios ese día, selecciona el tipo de ausentismo correspondiente en la lista. Al seleccionar un ausentismo, la cantidad de domicilios queda en 0.",
      },
      {
        title: "Valida los registros",
        description:
          "Cada domiciliario debe tener una cantidad de domicilios mayor a 0 o un tipo de ausentismo seleccionado. No deben quedar filas pendientes antes de guardar.",
      },
      {
        title: "Guarda los registros",
        description:
          "Cuando todos los domiciliarios tengan una cantidad registrada o un ausentismo seleccionado, presiona el botón de guardar.",
      },
    ],
    recommendations: [
      "Verifica la fecha antes de guardar.",
      "Verifica que el punto de venta seleccionado sea el correcto.",
      "Todos los domiciliarios deben tener cantidad de domicilios o un ausentismo seleccionado.",
      "Si seleccionas un ausentismo, el sistema registrará la cantidad de domicilios en 0.",
      "Si seleccionaste mal el punto de venta, limpia el formulario y vuelve a iniciar.",
    ],
  },

  "/reporte-domicilios": {
    title: "Instructivo - Reporte de domicilios",
    description:
      "Esta opción permite consultar y exportar la información de domicilios registrados, usando filtros por fecha, periodo, punto de venta y domiciliario. El reporte también muestra los ausentismos registrados y sus cantidades.",
    steps: [
      {
        title: "Selecciona el rango de fechas",
        description:
          "Define la fecha inicial y la fecha final del reporte. La fecha final no debe ser menor que la fecha inicial.",
      },
      {
        title: "Selecciona el periodo",
        description:
          "Elige cómo deseas consultar la información: por día, semana o mes.",
      },
      {
        title: "Filtra por punto de venta",
        description:
          "Puedes consultar todos los puntos de venta o seleccionar uno específico para revisar información más detallada.",
      },
      {
        title: "Filtra por domiciliario si aplica",
        description:
          "Si seleccionas un punto de venta, también puedes consultar un domiciliario específico.",
      },
      {
        title: "Consulta la información",
        description:
          "Presiona el botón de consultar para cargar el reporte según los filtros seleccionados.",
      },
      {
        title: "Revisa domicilios y ausentismos",
        description:
          "El reporte muestra la cantidad de domicilios, el tipo de ausentismo registrado en el detalle y la cantidad total de ausentismos en los subtotales y totales.",
      },
      {
        title: "Exporta el reporte",
        description:
          "Cuando el reporte tenga información, puedes descargarlo en Excel usando el botón de exportar.",
      },
    ],
    recommendations: [
      "Primero consulta el reporte antes de exportarlo.",
      "Si no aparecen datos, valida que existan registros para el rango de fechas seleccionado.",
      "Usa los filtros para encontrar información más específica.",
      "En los subtotales y totales se muestra la cantidad de ausentismos, no el nombre de cada ausentismo.",
      "El nombre del ausentismo se muestra en el detalle del reporte cuando aplica.",
    ],
  },
};

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const toggleSidebar = () => {
    setSidebarOpen((prev) => !prev);
  };

  return (
    <Box
      sx={{
        height: "100vh",
        width: "100%",
        bgcolor: "#FFFDF8",
        display: "grid",
        gridTemplateColumns: `${
          sidebarOpen ? SIDEBAR_OPEN_WIDTH : SIDEBAR_CLOSED_WIDTH
        }px 1fr`,
        transition: "grid-template-columns 0.25s ease",
        overflow: "hidden",
      }}
    >
      <Sidebar sidebarOpen={sidebarOpen} onToggleSidebar={toggleSidebar} />

      <Box
        sx={{
          height: "100vh",
          display: "grid",
          gridTemplateRows: "86px minmax(0, 1fr) 95px",
          minWidth: 0,
          overflow: "hidden",
        }}
      >
        <Header />

        <Box
          component="main"
          sx={{
            bgcolor: "#FFFDF8",
            p: 4,
            overflowY: "auto",
            overflowX: "hidden",
            minHeight: 0,
          }}
        >
          <Outlet />
        </Box>

        <Footer />
      </Box>
    </Box>
  );
}

function Sidebar({ sidebarOpen, onToggleSidebar }: SidebarProps) {
  const { user, hasPermission } = useAuth();
  const location = useLocation();

  const isMastersActive = location.pathname.startsWith("/maestros");
  const [mastersOpen, setMastersOpen] = useState(isMastersActive);

  const allowedMasterItems = masterItems.filter((item) =>
    hasPermission(item.path)
  );

  const allowedMainItems = mainItems.filter((item) =>
    hasPermission(item.path)
  );

  const handleToggleMasters = () => {
    if (!sidebarOpen) {
      onToggleSidebar();
      setMastersOpen(true);
      return;
    }

    setMastersOpen((prev) => !prev);
  };

  const displayName = user?.wordpressDisplayName || "Usuario";
  const roleName = user?.roles?.[0]?.nameRole || "Sin rol";
  const avatarLetter = displayName.trim().charAt(0).toUpperCase() || "U";

  return (
    <Box
      sx={{
        height: "100vh",
        maxHeight: "100vh",
        bgcolor: "#4B2E1F",
        color: "#FFFFFF",
        display: "grid",
        gridTemplateRows: "155px minmax(0, 1fr) 95px",
        borderRight: "1px solid rgba(255,255,255,0.15)",
        position: "relative",
        transition: "all 0.25s ease",
        overflow: "hidden",
      }}
    >
      <IconButton
        onClick={onToggleSidebar}
        aria-label={sidebarOpen ? "Ocultar menú" : "Mostrar menú"}
        sx={{
          position: "absolute",
          top: 16,
          right: 10,
          zIndex: 10,
          color: "#F7E8D8",
          bgcolor: "transparent",
          border: "none",
          boxShadow: "none",
          p: 0.5,
          width: 30,
          height: 30,
          "&:hover": {
            bgcolor: "rgba(247, 232, 216, 0.08)",
            color: "#FFFFFF",
          },
        }}
      >
        {sidebarOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
      </IconButton>

      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          px: 1,
          overflow: "hidden",
        }}
      >
        <Box
          component={NavLink}
          to="/"
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            textDecoration: "none",
          }}
        >
          <Box
            component="img"
            src="/images/MonedaCrepes.png"
            alt="Crepes & Waffles"
            sx={{
              width: sidebarOpen ? 115 : 52,
              height: sidebarOpen ? 115 : 52,
              objectFit: "contain",
              transition: "all 0.25s ease",
              cursor: "pointer",
            }}
          />
        </Box>
      </Box>

      <Box
        sx={{
          minHeight: 0,
          height: "100%",
          overflow: "hidden",
        }}
      >
        <Box
          component="nav"
          sx={{
            height: "100%",
            minHeight: 0,
            px: sidebarOpen ? 2 : 1,
            pr: sidebarOpen ? 1 : 0.5,
            display: "flex",
            flexDirection: "column",
            gap: 1.2,
            transition: "all 0.25s ease",
            overflowY: "auto",
            overflowX: "hidden",
            pb: 2,

            "&::-webkit-scrollbar": {
              width: 6,
            },
            "&::-webkit-scrollbar-thumb": {
              bgcolor: "rgba(247, 232, 216, 0.35)",
              borderRadius: 10,
            },
            "&::-webkit-scrollbar-track": {
              bgcolor: "transparent",
            },
          }}
        >
          {allowedMasterItems.length > 0 && (
            <>
              <Tooltip
                title={!sidebarOpen ? "Maestros" : ""}
                placement="right"
                arrow
              >
                <Box
                  onClick={handleToggleMasters}
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: sidebarOpen ? "flex-start" : "center",
                    gap: sidebarOpen ? 1.5 : 0,
                    px: sidebarOpen ? 2 : 0,
                    py: 1.25,
                    minHeight: 48,
                    flexShrink: 0,
                    borderRadius: 2,
                    color: isMastersActive ? "#4B2E1F" : "#F8EBDD",
                    bgcolor: isMastersActive ? "#F7E8D8" : "transparent",
                    fontSize: 16,
                    fontWeight: 600,
                    textDecoration: "none",
                    cursor: "pointer",
                    transition: "all 0.25s ease",
                    "& svg": {
                      fontSize: 25,
                    },
                    "&:hover": {
                      bgcolor: isMastersActive
                        ? "#F7E8D8"
                        : "rgba(247, 232, 216, 0.18)",
                    },
                  }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      color: "inherit",
                    }}
                  >
                    <DashboardCustomizeOutlinedIcon />
                  </Box>

                  {sidebarOpen && (
                    <>
                      <Typography
                        sx={{
                          flex: 1,
                          fontSize: 16,
                          fontWeight: 600,
                          whiteSpace: "nowrap",
                        }}
                      >
                        Maestros
                      </Typography>

                      {mastersOpen ? (
                        <KeyboardArrowUpIcon sx={{ fontSize: 20 }} />
                      ) : (
                        <KeyboardArrowDownIcon sx={{ fontSize: 20 }} />
                      )}
                    </>
                  )}
                </Box>
              </Tooltip>

              <Collapse
                in={sidebarOpen && mastersOpen}
                timeout="auto"
                unmountOnExit
                sx={{
                  flexShrink: 0,
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 0.8,
                    mt: 0.5,
                    pl: 1.5,
                  }}
                >
                  {allowedMasterItems.map((item) => (
                    <Box
                      key={item.path}
                      component={NavLink}
                      to={item.path}
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1.2,
                        px: 1.5,
                        py: 1,
                        minHeight: 40,
                        flexShrink: 0,
                        borderRadius: 2,
                        color: "#F8EBDD",
                        fontWeight: 500,
                        textDecoration: "none",
                        transition: "all 0.25s ease",
                        "& svg": {
                          fontSize: 21,
                        },
                        "&.active": {
                          bgcolor: "rgba(247, 232, 216, 0.22)",
                          color: "#FFFFFF",
                        },
                        "&:hover": {
                          bgcolor: "rgba(247, 232, 216, 0.14)",
                        },
                      }}
                    >
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          color: "inherit",
                        }}
                      >
                        {item.icon}
                      </Box>

                      <Typography
                        sx={{
                          fontSize: 14,
                          fontWeight: 600,
                          whiteSpace: "nowrap",
                        }}
                      >
                        {item.label}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Collapse>
            </>
          )}

          {allowedMainItems.map((item) => (
            <Tooltip
              key={item.path}
              title={!sidebarOpen ? item.label : ""}
              placement="right"
              arrow
            >
              <Box
                component={NavLink}
                to={item.path}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: sidebarOpen ? "flex-start" : "center",
                  gap: sidebarOpen ? 1.5 : 0,
                  px: sidebarOpen ? 2 : 0,
                  py: 1.25,
                  minHeight: 48,
                  flexShrink: 0,
                  borderRadius: 2,
                  color: "#F8EBDD",
                  fontSize: 16,
                  fontWeight: 600,
                  textDecoration: "none",
                  transition: "all 0.25s ease",
                  "& svg": {
                    fontSize: 25,
                  },
                  "&.active": {
                    bgcolor: "#F7E8D8",
                    color: "#4B2E1F",
                  },
                  "&:hover": {
                    bgcolor: "rgba(247, 232, 216, 0.18)",
                  },
                  "&.active:hover": {
                    bgcolor: "#F7E8D8",
                  },
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    color: "inherit",
                  }}
                >
                  {item.icon}
                </Box>

                {sidebarOpen && (
                  <Typography
                    sx={{
                      fontSize: 16,
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {item.label}
                  </Typography>
                )}
              </Box>
            </Tooltip>
          ))}
        </Box>
      </Box>

      <Box
        sx={{
          minHeight: 95,
          overflow: "hidden",
        }}
      >
        <Divider sx={{ borderColor: "rgba(255,255,255,0.18)" }} />

        <Box
          sx={{
            px: sidebarOpen ? 2 : 1,
            py: 1.2,
            display: "flex",
            alignItems: "center",
            justifyContent: sidebarOpen ? "flex-start" : "center",
            gap: 1.2,
            transition: "all 0.25s ease",
          }}
        >
          <Avatar
            sx={{
              bgcolor: "#F7E8D8",
              color: "#4B2E1F",
              width: 42,
              height: 42,
              flexShrink: 0,
            }}
          >
            {avatarLetter}
          </Avatar>

          {sidebarOpen && (
            <>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  sx={{
                    fontSize: 11,
                    fontWeight: 700,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {displayName}
                </Typography>

                <Typography sx={{ fontSize: 12, color: "#EAD9C9" }}>
                  {roleName}
                </Typography>
              </Box>
            </>
          )}
        </Box>
      </Box>
    </Box>
  );
}

function Header() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <Box
      sx={{
        bgcolor: "#F7E8D8",
        borderBottom: "1px solid #C9A98E",
        px: 5,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        minHeight: 86,
        overflow: "hidden",
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 2,
          minWidth: 0,
        }}
      >
        <CoffeeIcon
          sx={{
            fontSize: 42,
            color: "#4B2E1F",
            flexShrink: 0,
          }}
        />

        <Box sx={{ minWidth: 0 }}>
          <Typography
            variant="h6"
            color="primary.main"
            sx={{
              fontWeight: 700,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            BIENVENIDO AL SISTEMA DE REGISTRO DE ASISTENCIA
          </Typography>
        </Box>
      </Box>

      <Button
        variant="outlined"
        startIcon={<LogoutIcon />}
        onClick={handleLogout}
        sx={{
          borderColor: "#8B6A55",
          color: "#4B2E1F",
          bgcolor: "rgba(255,255,255,0.35)",
          px: 2,
          py: 1,
          flexShrink: 0,
          "&:hover": {
            borderColor: "#4B2E1F",
            bgcolor: "rgba(255,255,255,0.55)",
          },
        }}
      >
        Cerrar Sesión
      </Button>
    </Box>
  );
}

function Footer() {
  const location = useLocation();
  const [helpOpen, setHelpOpen] = useState(false);
  const [termsOpen, setTermsOpen] = useState(false);
  const [privacyOpen, setPrivacyOpen] = useState(false);
  const [selectedHelpPath, setSelectedHelpPath] = useState<HelpPath>(() =>
    getHelpPathFromCurrentRoute(location.pathname)
  );

  const selectedHelpContent = helpContentByPath[selectedHelpPath];

  const handleOpenHelp = () => {
    setSelectedHelpPath(getHelpPathFromCurrentRoute(location.pathname));
    setHelpOpen(true);
  };

  const handleCloseHelp = () => {
    setHelpOpen(false);
  };

  const handleOpenPrivacy = () => {
    setPrivacyOpen(true);
  };

  const handleClosePrivacy = () => {
    setPrivacyOpen(false);
  };

  const handleOpenTerms = () => {
    setTermsOpen(true);
  };

  const handleCloseTerms = () => {
    setTermsOpen(false);
  };

  return (
    <>
      <Box
        sx={{
          bgcolor: "#4B2E1F",
          color: "#F7E8D8",
          px: 5,
          display: "grid",
          gridTemplateColumns: "1fr auto",
          alignItems: "center",
          columnGap: 4,
          minHeight: 95,
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 1.5,
            minWidth: 0,
          }}
        >
          <Typography
            sx={{
              fontSize: 15,
              mt: 1,
              textAlign: "center",
            }}
          >
            © Compañía de Alimentos Colombianos Calco S.A - Todos los derechos
            reservados
          </Typography>

          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 2.5,
            }}
          >
            <IconButton
              component="a"
              href="https://web.facebook.com/CrepesyWafflesOficial/"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Ir a FacebookIcon"
              sx={{ color: "#F7E8D8" }}
            >
              <FacebookIcon />
            </IconButton>

            <IconButton
              component="a"
              href="https://www.instagram.com/crepesywaffles/"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Ir a Instagram"
              sx={{ color: "#F7E8D8" }}
            >
              <InstagramIcon />
            </IconButton>

            <IconButton
              component="a"
              href="https://calcoweb.net/"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Ir a CalcoWeb"
              sx={{ color: "#F7E8D8" }}
            >
              <LanguageIcon />
            </IconButton>

            <Divider
              orientation="vertical"
              flexItem
              sx={{ borderColor: "rgba(247,232,216,0.35)" }}
            />

            <Typography
              onClick={handleOpenTerms}
              sx={{ fontSize: 14, whiteSpace: "nowrap", cursor: "pointer", }}>
              Términos y condiciones
            </Typography>

            <Divider
              orientation="vertical"
              flexItem
              sx={{ borderColor: "rgba(247,232,216,0.35)" }}
            />

            <Typography
              onClick={handleOpenPrivacy}
              sx={{ fontSize: 14, whiteSpace: "nowrap", cursor: "pointer", }} >
              Privacidad
            </Typography>

            <Divider
              orientation="vertical"
              flexItem
              sx={{ borderColor: "rgba(247,232,216,0.35)" }}
            />

            <Typography
              onClick={handleOpenHelp}
              sx={{
                fontSize: 14,
                whiteSpace: "nowrap",
                cursor: "pointer",
              }}
            >
              Ayuda
            </Typography>
          </Box>
        </Box>

        <Box
          component="img"
          src="/images/waffle-footer.png"
          alt="Waffle"
          sx={{
            width: 145,
            opacity: 0.45,
            display: { xs: "none", md: "block" },
          }}
        />
      </Box>

      <Dialog
        open={privacyOpen}
        onClose={handleClosePrivacy}
        fullWidth
        maxWidth="md"
        slotProps={{
          paper: {
            sx: {
              borderRadius: 3,
              overflow: "hidden",
              bgcolor: "#FFFDF8",
            },
          },
        }}
      >
        <DialogTitle
          sx={{
            bgcolor: "#4B2E1F",
            color: "#F7E8D8",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 2,
            py: 2,
            px: 3,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Typography sx={{ fontSize: 20, fontWeight: 700 }}>
              Política de privacidad y uso de la información
            </Typography>
          </Box>

          <IconButton
            onClick={handleClosePrivacy}
            sx={{
              color: "#F7E8D8",
              "&:hover": {
                bgcolor: "rgba(247,232,216,0.12)",
              },
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ p: 0 }}>
          <Box sx={{ p: 3 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              El Sistema de Registro de Domicilios es una aplicación de uso interno de
              la Compañía de Alimentos Colombianos Calco S.A. / Crepes & Waffles,
              destinada a apoyar la gestión operativa relacionada con puntos de venta,
              domiciliarios, registros de domicilios, ausentismos, liquidaciones,
              reportes, usuarios, roles y parámetros del sistema.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              La información registrada en esta aplicación será utilizada únicamente
              para fines operativos, administrativos, de seguimiento, auditoría, control
              interno y generación de reportes asociados al proceso de domicilios. No
              debe ser usada para fines personales, externos o diferentes a los
              autorizados por la Compañía.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              La aplicación puede tratar información como usuarios autenticados,
              correos autorizados de punto de venta, roles, permisos, puntos de venta,
              domiciliarios, documentos de identificación, fechas de registro,
              cantidades de domicilios, ausentismos, valores de liquidación,
              parámetros y trazabilidad de creación o actualización de registros.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              El acceso a la información se realiza de acuerdo con los perfiles y
              permisos asignados a cada usuario. Cada usuario es responsable del uso
              adecuado de sus credenciales, del manejo responsable de la información
              consultada y de no divulgar datos a personas no autorizadas.
            </Typography>

            <Paper
              elevation={0}
              sx={{
                mt: 2,
                mb: 2,
                border: "1px solid #E0CDBB",
                borderRadius: 2,
                p: 2,
                bgcolor: "#FFF8EF",
              }}
            >
              <Typography sx={{ color: "#4B2E1F", fontSize: 16, fontWeight: 700, mb: 1 }}>
                Fuente interna y marco normativo
              </Typography>

              <Typography sx={{ color: "#6A4A38", fontSize: 14, lineHeight: 1.7 }}>
                Esta política se fundamenta en el documento interno “Sistema de Gestión
                de Seguridad de la Información - TEC-I-CWN-01”, versión 4.2, de la
                Dirección de Tecnología de Crepes y Waffles S.A., y en la normativa
                colombiana aplicable sobre protección de datos personales,
                especialmente el artículo 15 de la Constitución Política de Colombia,
                la Ley 1581 de 2012 y sus decretos reglamentarios.
              </Typography>
            </Paper>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7 }}>
              El uso de esta aplicación implica la aceptación de estas condiciones y el
              compromiso de tratar la información de manera responsable, segura y
              exclusivamente para las finalidades autorizadas.
            </Typography>
          </Box>
        </DialogContent>

        <DialogActions
          sx={{
            px: 3,
            py: 2,
            borderTop: "1px solid #E0CDBB",
            bgcolor: "#FFF8EF",
          }}
        >
          <Button
            variant="contained"
            onClick={handleClosePrivacy}
            sx={{
              bgcolor: "#4B2E1F",
              color: "#FFFFFF",
              textTransform: "none",
              fontWeight: 600,
              px: 3,
              "&:hover": {
                bgcolor: "#3A2318",
              },
            }}
          >
            Entendido
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={termsOpen}
        onClose={handleCloseTerms}
        fullWidth
        maxWidth="md"
        slotProps={{
          paper: {
            sx: {
              borderRadius: 3,
              overflow: "hidden",
              bgcolor: "#FFFDF8",
            },
          },
        }}
      >
        <DialogTitle
          sx={{
            bgcolor: "#4B2E1F",
            color: "#F7E8D8",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 2,
            py: 2,
            px: 3,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Typography sx={{ fontSize: 20, fontWeight: 700 }}>
              Términos y condiciones de uso
            </Typography>
          </Box>

          <IconButton
            onClick={handleCloseTerms}
            sx={{
              color: "#F7E8D8",
              "&:hover": {
                bgcolor: "rgba(247,232,216,0.12)",
              },
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ p: 0 }}>
          <Box sx={{ p: 3 }}>
            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              El Sistema de Registro de Domicilios es un aplicativo de uso interno de la
              Compañía de Alimentos Colombianos Calco S.A. / Crepes & Waffles, dispuesto
              para apoyar la gestión operativa, administrativa y de seguimiento relacionada
              con el registro de domicilios, puntos de venta, domiciliarios, ausentismos,
              liquidaciones, reportes, usuarios, roles y parámetros del sistema.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              El acceso y uso de este aplicativo está permitido únicamente a usuarios
              autorizados por la Compañía, de acuerdo con los roles, permisos y perfiles
              asignados. Toda actividad realizada dentro del sistema podrá ser registrada
              para efectos de trazabilidad, auditoría, control interno, seguridad de la
              información y continuidad operativa.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              El usuario se compromete a utilizar el aplicativo exclusivamente para fines
              laborales, operativos y autorizados por la Compañía. Está prohibido usar la
              aplicación para fines personales, externos, fraudulentos, no autorizados o
              contrarios a las políticas internas de seguridad de la información.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              Las credenciales de acceso, códigos de verificación, usuarios, contraseñas y
              permisos asignados son personales, intransferibles y de uso exclusivo del
              usuario autorizado. El usuario es responsable de proteger sus accesos y de no
              compartirlos con terceros.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              La información consultada, registrada, modificada o exportada desde el
              aplicativo debe manejarse con confidencialidad y únicamente para las
              finalidades autorizadas. No está permitido divulgar, copiar, alterar, eliminar,
              extraer o distribuir información del sistema sin autorización previa de la
              Compañía.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              El software, código fuente, configuraciones, diseños, bases de datos,
              reportes, documentación técnica y demás componentes relacionados con este
              aplicativo son propiedad de la Compañía o se encuentran autorizados para su
              uso, según corresponda. No está permitida su reproducción, modificación,
              distribución, instalación o uso por fuera de los lineamientos definidos por la
              Dirección de Tecnología.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              El usuario no debe intentar vulnerar la seguridad del aplicativo, evadir
              controles de autenticación, acceder a módulos no autorizados, manipular datos
              sin permiso, afectar la disponibilidad del servicio o realizar cualquier acción
              que pueda comprometer la confidencialidad, integridad o disponibilidad de la
              información.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              La Compañía podrá realizar monitoreo, revisión, auditoría y seguimiento sobre
              el uso del aplicativo, con el fin de garantizar la seguridad de la información,
              el cumplimiento de políticas internas, la continuidad del servicio y la correcta
              operación del proceso.
            </Typography>

            <Paper
              elevation={0}
              sx={{
                mt: 2,
                mb: 2,
                border: "1px solid #E0CDBB",
                borderRadius: 2,
                p: 2,
                bgcolor: "#FFF8EF",
              }}
            >
              <Typography sx={{ color: "#4B2E1F", fontSize: 16, fontWeight: 700, mb: 1 }}>
                Fuente interna y marco normativo
              </Typography>

              <Typography sx={{ color: "#6A4A38", fontSize: 14, lineHeight: 1.7 }}>
                Estos términos se fundamentan en los lineamientos internos de seguridad de
                la información de la Compañía, especialmente en las políticas relacionadas
                con uso de aplicativos, uso de software, control de acceso, confidencialidad,
                respaldo, bases de datos, intranet, propiedad intelectual y manejo
                responsable de la información.
              </Typography>

              <Typography sx={{ color: "#6A4A38", fontSize: 14, lineHeight: 1.7, mt: 1.5 }}>
                También se apoyan en la normativa colombiana aplicable, incluyendo la Ley
                1581 de 2012 sobre protección de datos personales, la Ley 1273 de 2009
                sobre protección de la información y los datos, la Ley 23 de 1982 y el
                Decreto 1360 de 1989 sobre protección del software, y la Ley 527 de 1999
                sobre mensajes de datos y medios electrónicos.
              </Typography>
            </Paper>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7 }}>
              El uso de este aplicativo implica el conocimiento y aceptación de estos
              términos y condiciones, así como el compromiso de utilizar la información, los
              módulos y las funcionalidades del sistema de manera responsable, segura y
              exclusivamente para las finalidades autorizadas por la Compañía.
            </Typography>
          </Box>
        </DialogContent>

        <DialogActions
          sx={{
            px: 3,
            py: 2,
            borderTop: "1px solid #E0CDBB",
            bgcolor: "#FFF8EF",
          }}
        >
          <Button
            variant="contained"
            onClick={handleCloseTerms}
            sx={{
              bgcolor: "#4B2E1F",
              color: "#FFFFFF",
              textTransform: "none",
              fontWeight: 600,
              px: 3,
              "&:hover": {
                bgcolor: "#3A2318",
              },
            }}
          >
            Entendido
          </Button>
        </DialogActions>
      </Dialog>

        <Dialog
          open={helpOpen}
          onClose={handleCloseHelp}
          fullWidth
          maxWidth="md"
          slotProps={{
            paper: {
              sx: {
                borderRadius: 3,
                overflow: "hidden",
                bgcolor: "#FFFDF8",
              },
            },
          }}
        >
        <DialogTitle
          sx={{
            bgcolor: "#4B2E1F",
            color: "#F7E8D8",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 2,
            py: 2,
            px: 3,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Typography sx={{ fontSize: 20, fontWeight: 700 }}>
              Ayuda del sistema
            </Typography>
          </Box>

          <IconButton
            onClick={handleCloseHelp}
            sx={{
              color: "#F7E8D8",
              "&:hover": {
                bgcolor: "rgba(247,232,216,0.12)",
              },
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ p: 0 }}>
          <Box sx={{ p: 3 }}>
            <Typography
              sx={{
                color: "#6A4A38",
                fontSize: 14,
                lineHeight: 1.6,
                mb: 2,
              }}
            >
              Actualmente el sistema cuenta con instructivos para las opciones
              de Registro de domicilios y Reporte de domicilios.
            </Typography>

            <Stack
              sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
                gap: 1.5,
                mb: 3,
              }}
            >
              <Button
                variant={
                  selectedHelpPath === "/registro-domicilios"
                    ? "contained"
                    : "outlined"
                }
                startIcon={<AssignmentOutlinedIcon />}
                onClick={() => setSelectedHelpPath("/registro-domicilios")}
                sx={{
                  textTransform: "none",
                  justifyContent: "flex-start",
                  fontWeight: 600,
                  borderColor: "#8B6A55",
                  bgcolor:
                    selectedHelpPath === "/registro-domicilios"
                      ? "#4B2E1F"
                      : "transparent",
                  color:
                    selectedHelpPath === "/registro-domicilios"
                      ? "#FFFFFF"
                      : "#4B2E1F",
                  "&:hover": {
                    borderColor: "#4B2E1F",
                    bgcolor:
                      selectedHelpPath === "/registro-domicilios"
                        ? "#3A2318"
                        : "rgba(75, 46, 31, 0.05)",
                  },
                }}
              >
                Registro de domicilios
              </Button>

              <Button
                variant={
                  selectedHelpPath === "/reporte-domicilios"
                    ? "contained"
                    : "outlined"
                }
                startIcon={<AssessmentOutlinedIcon />}
                onClick={() => setSelectedHelpPath("/reporte-domicilios")}
                sx={{
                  textTransform: "none",
                  justifyContent: "flex-start",
                  fontWeight: 600,
                  borderColor: "#8B6A55",
                  bgcolor:
                    selectedHelpPath === "/reporte-domicilios"
                      ? "#4B2E1F"
                      : "transparent",
                  color:
                    selectedHelpPath === "/reporte-domicilios"
                      ? "#FFFFFF"
                      : "#4B2E1F",
                  "&:hover": {
                    borderColor: "#4B2E1F",
                    bgcolor:
                      selectedHelpPath === "/reporte-domicilios"
                        ? "#3A2318"
                        : "rgba(75, 46, 31, 0.05)",
                  },
                }}
              >
                Reporte de domicilios
              </Button>
            </Stack>

            <Typography
              sx={{
                color: "#4B2E1F",
                fontSize: 19,
                fontWeight: 700,
                mb: 1,
              }}
            >
              {selectedHelpContent.title}
            </Typography>

            <Typography
              sx={{
                color: "#4B2E1F",
                fontSize: 15,
                lineHeight: 1.7,
                mb: 3,
              }}
            >
              {selectedHelpContent.description}
            </Typography>

            <Typography
              sx={{
                color: "#4B2E1F",
                fontSize: 17,
                fontWeight: 700,
                mb: 1.5,
              }}
            >
              Paso a paso
            </Typography>

            <Stack spacing={1.5}>
              {selectedHelpContent.steps.map((step, index) => (
                <Paper
                  key={step.title}
                  elevation={0}
                  sx={{
                    border: "1px solid #E0CDBB",
                    borderRadius: 2,
                    p: 2,
                    display: "grid",
                    gridTemplateColumns: "42px 1fr",
                    gap: 2,
                    bgcolor: "#FFFFFF",
                  }}
                >
                  <Box
                    sx={{
                      width: 34,
                      height: 34,
                      borderRadius: "50%",
                      bgcolor: "#4B2E1F",
                      color: "#F7E8D8",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: 700,
                      fontSize: 15,
                    }}
                  >
                    {index + 1}
                  </Box>

                  <Box>
                    <Typography
                      sx={{
                        color: "#4B2E1F",
                        fontSize: 15,
                        fontWeight: 700,
                        mb: 0.5,
                      }}
                    >
                      {step.title}
                    </Typography>

                    <Typography
                      sx={{
                        color: "#6A4A38",
                        fontSize: 14,
                        lineHeight: 1.6,
                      }}
                    >
                      {step.description}
                    </Typography>
                  </Box>
                </Paper>
              ))}
            </Stack>

            <Paper
              elevation={0}
              sx={{
                mt: 3,
                border: "1px solid #E0CDBB",
                borderRadius: 2,
                p: 2,
                bgcolor: "#FFF8EF",
              }}
            >
              <Typography
                sx={{
                  color: "#4B2E1F",
                  fontSize: 15,
                  fontWeight: 700,
                  mb: 1,
                }}
              >
                Recomendaciones
              </Typography>

              <Stack spacing={0.8}>
                {selectedHelpContent.recommendations.map((item) => (
                  <Typography
                    key={item}
                    sx={{
                      color: "#6A4A38",
                      fontSize: 14,
                      lineHeight: 1.5,
                    }}
                  >
                    • {item}
                  </Typography>
                ))}
              </Stack>
            </Paper>
          </Box>
        </DialogContent>

        <DialogActions
          sx={{
            px: 3,
            py: 2,
            borderTop: "1px solid #E0CDBB",
            bgcolor: "#FFF8EF",
          }}
        >
          <Button
            variant="contained"
            onClick={handleCloseHelp}
            sx={{
              bgcolor: "#4B2E1F",
              color: "#FFFFFF",
              textTransform: "none",
              fontWeight: 600,
              px: 3,
              "&:hover": {
                bgcolor: "#3A2318",
              },
            }}
          >
            Entendido
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}