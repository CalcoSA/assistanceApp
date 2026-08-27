import { Avatar, Box, Button, Collapse, Divider, IconButton, Tooltip, Typography, Dialog, DialogActions, DialogContent, DialogTitle, Paper, Stack, } from "@mui/material";
import AdminPanelSettingsOutlinedIcon from "@mui/icons-material/AdminPanelSettingsOutlined";
import DashboardCustomizeOutlinedIcon from "@mui/icons-material/DashboardCustomizeOutlined";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import AssessmentOutlinedIcon from "@mui/icons-material/AssessmentOutlined";
import PeopleAltOutlinedIcon from "@mui/icons-material/PeopleAltOutlined";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import BusinessOutlinedIcon from "@mui/icons-material/BusinessOutlined";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
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
    label: "Parámetros",
    path: "/maestros/parametros",
    icon: <TuneOutlinedIcon />,
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

type HelpPath = "/eventos" | "/reportes" | "/maestros/parametros";

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
  if (pathname.startsWith("/reportes")) {
    return "/reportes";
  }

  if (pathname.startsWith("/maestros/parametros")) {
    return "/maestros/parametros";
  }

  return "/eventos";
};

const helpContentByPath: Record<HelpPath, HelpContent> = {
  "/eventos": {
    title: "Instructivo - Gestión de eventos",
    description:
      "Esta opción permite crear y administrar capacitaciones, consultar sus asistentes y compartir el acceso al registro mediante un código QR.",
    steps: [
      {
        title: "Crea el evento",
        description:
          "Presiona Crear evento y completa la información general, fecha, horario, centro de soluciones, motivo, programa, categoría y facilitadores.",
      },
      {
        title: "Agrega temas y competencias",
        description:
          "Registra al menos un tema tratado y selecciona las competencias relacionadas con la capacitación.",
      },
      {
        title: "Carga y revisa el PENSUM",
        description:
          "Adjunta el documento requerido y utiliza la opción de previsualización para confirmar que elegiste el archivo correcto.",
      },
      {
        title: "Valida la programación",
        description:
          "La hora de inicio debe ser posterior a la hora actual y menor que la hora final. El sistema permite programar eventos para el mismo día si aún no han comenzado.",
      },
      {
        title: "Guarda y notifica",
        description:
          "Al presionar Crear evento, el sistema guarda la información y envía la notificación al correo del usuario creador y a los destinatarios adicionales configurados en Parámetros.",
      },
      {
        title: "Consulta y comparte",
        description:
          "Desde las acciones del evento puedes ver el detalle, consultar asistentes, descargar el QR, actualizar la información o cancelar cuando corresponda.",
      },
    ],
    recommendations: [
      "Verifica la fecha, el horario y el número de personas programadas antes de crear.",
      "Confirma que el PENSUM previsualizado corresponda al evento.",
      "Si aparece una advertencia de correo, el evento sí quedó creado; revisa Parámetros o la configuración SMTP.",
      "Comparte el QR únicamente con las personas que deben registrar su asistencia.",
    ],
  },

  "/reportes": {
    title: "Instructivo - Reportes de capacitación",
    description:
      "Esta opción permite analizar la información registrada en los eventos y exportar los resultados de capacitación a Excel.",
    steps: [
      {
        title: "Selecciona el rango de fechas",
        description:
          "Define la fecha inicial y final de la consulta. La fecha inicial no puede ser posterior a la fecha final.",
      },
      {
        title: "Aplica los filtros",
        description:
          "Selecciona los criterios disponibles para enfocar el análisis en la información que necesitas.",
      },
      {
        title: "Consulta los resultados",
        description:
          "Ejecuta la consulta y revisa los indicadores, totales y detalles generados por el sistema.",
      },
      {
        title: "Exporta a Excel",
        description:
          "Cuando existan resultados, presiona Exportar Excel para descargar el reporte con los filtros seleccionados.",
      },
    ],
    recommendations: [
      "Primero consulta el reporte antes de exportarlo.",
      "Si no aparecen datos, valida que existan registros para el rango de fechas seleccionado.",
      "Usa los filtros para encontrar información más específica.",
      "Revisa el rango de fechas que aparece en el archivo exportado.",
    ],
  },

  "/maestros/parametros": {
    title: "Instructivo - Parámetros del sistema",
    description:
      "Esta opción administra claves de configuración utilizadas por procesos internos. En la creación de eventos, permite definir destinatarios adicionales al correo del usuario creador.",
    steps: [
      {
        title: "Ubica el parámetro de notificación",
        description:
          "Busca DESTINATARIOS_NOTIFICACION_EVENTO. Su nombre es una clave técnica fija y por eso no se puede renombrar ni eliminar.",
      },
      {
        title: "Actualiza los destinatarios",
        description:
          "Presiona editar e ingresa uno o varios correos adicionales separados por coma, punto y coma o salto de línea. Si el correo del creador también está en la lista, el sistema elimina el duplicado.",
      },
      {
        title: "Corrige los formatos inválidos",
        description:
          "El sistema valida cada dirección antes de guardar. Revisa cualquier correo señalado como inválido.",
      },
      {
        title: "Guarda y verifica",
        description:
          "Guarda el valor y crea un evento de prueba. El mensaje final indicará si la notificación se envió o si falta configuración SMTP.",
      },
    ],
    recommendations: [
      "Mantén únicamente destinatarios autorizados para recibir información de capacitaciones.",
      "No guardes contraseñas ni credenciales SMTP dentro de los parámetros.",
      "Las credenciales del servidor de correo se administran exclusivamente en el entorno del backend.",
      "Crear un parámetro nuevo solo almacena una clave y su valor; tendrá efecto cuando algún proceso de la aplicación use expresamente ese nombre.",
      "Evita eliminar parámetros desconocidos sin confirmar qué proceso los utiliza.",
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
              El Sistema de Registro de Asistencia es una aplicación de uso interno de
              la Compañía de Alimentos Colombianos Calco S.A. / Crepes & Waffles,
              destinada a gestionar capacitaciones, eventos, registro de asistentes y
              generación de reportes relacionados con estos procesos.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              Para cumplir esa finalidad, la aplicación puede tratar información de
              usuarios autorizados, roles y permisos; datos de los eventos y sus
              facilitadores; documentos PENSUM; y datos suministrados por los asistentes,
              como nombre, identificación, cargo, teléfono, centro de soluciones y firma.
              También puede registrar fecha, hora, dirección IP y datos técnicos básicos
              del navegador para fines de trazabilidad y seguridad.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              La información se utiliza exclusivamente para programar capacitaciones,
              acreditar y consultar asistencias, realizar seguimiento, generar reportes,
              enviar notificaciones operativas y atender necesidades de auditoría y
              control interno autorizadas por la Compañía.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              El acceso está limitado por autenticación, roles y opciones de menú. Los
              usuarios deben consultar, registrar, modificar, descargar o compartir datos
              únicamente cuando su función lo requiera, y deben evitar su divulgación a
              personas no autorizadas.
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
                Protección y actualización de la información
              </Typography>

              <Typography sx={{ color: "#6A4A38", fontSize: 14, lineHeight: 1.7 }}>
                La Compañía debe aplicar medidas razonables de seguridad y conservar la
                información durante el tiempo definido para el proceso. Las solicitudes
                de consulta, actualización, corrección o tratamiento de datos personales
                deben tramitarse mediante los canales corporativos y la política de
                protección de datos vigente.
              </Typography>
            </Paper>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7 }}>
              Este aviso resume el uso de información dentro de la aplicación y debe
              interpretarse junto con las políticas corporativas de privacidad, seguridad
              de la información y conservación documental que se encuentren vigentes.
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
              El Sistema de Registro de Asistencia es una aplicación de uso interno de la
              Compañía de Alimentos Colombianos Calco S.A. / Crepes & Waffles, dispuesta
              para programar capacitaciones, administrar eventos, registrar asistentes y
              consultar o exportar la información autorizada del proceso.
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
              Las credenciales, enlaces de acceso, códigos QR y permisos asignados deben
              protegerse y utilizarse únicamente para su finalidad. El usuario es
              responsable de no compartir accesos administrativos ni facilitar el registro
              de asistencia a personas ajenas al evento correspondiente.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              La información consultada, registrada, modificada o exportada debe manejarse
              con confidencialidad. El usuario debe verificar que los datos del evento, el
              PENSUM, los destinatarios de correo y la información de los asistentes sean
              correctos antes de guardarlos o compartirlos.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              No está permitido extraer, divulgar, modificar o eliminar información sin
              autorización; cargar archivos ajenos al proceso; configurar destinatarios no
              autorizados; ni utilizar los datos para fines personales, comerciales o
              diferentes a las funciones laborales aprobadas.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              El usuario no debe intentar vulnerar la seguridad del aplicativo, evadir
              controles de autenticación, acceder a módulos no autorizados, manipular datos
              sin permiso, afectar la disponibilidad del servicio o realizar cualquier acción
              que pueda comprometer la confidencialidad, integridad o disponibilidad de la
              información.
            </Typography>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7, mb: 2 }}>
              La actividad del sistema puede conservar trazabilidad para fines de soporte,
              auditoría, seguridad y control interno. La disponibilidad de determinadas
              funciones depende del rol, los permisos asignados y la configuración técnica
              de servicios como el envío de correo.
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
                Uso responsable
              </Typography>

              <Typography sx={{ color: "#6A4A38", fontSize: 14, lineHeight: 1.7 }}>
                Ante un dato incorrecto, un acceso no autorizado, un correo enviado a un
                destinatario equivocado o cualquier incidente de seguridad, el usuario debe
                detener la operación cuando sea posible y reportarla por los canales
                corporativos definidos para soporte y seguridad de la información.
              </Typography>
            </Paper>

            <Typography sx={{ color: "#4B2E1F", fontSize: 15, lineHeight: 1.7 }}>
              El uso de este aplicativo implica el conocimiento y aceptación de estos
              términos y condiciones y el compromiso de utilizar sus módulos e información
              de manera responsable, segura y exclusivamente para las finalidades
              autorizadas por la Compañía. Estos términos se complementan con las políticas
              corporativas vigentes.
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
              Consulta el paso a paso de las funciones principales del Sistema
              de Registro de Asistencia.
            </Typography>

            <Stack
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: "1fr",
                  md: "repeat(3, minmax(0, 1fr))",
                },
                gap: 1.5,
                mb: 3,
              }}
            >
              <Button
                variant={
                  selectedHelpPath === "/eventos"
                    ? "contained"
                    : "outlined"
                }
                startIcon={<EventOutlinedIcon />}
                onClick={() => setSelectedHelpPath("/eventos")}
                sx={{
                  textTransform: "none",
                  justifyContent: "flex-start",
                  fontWeight: 600,
                  borderColor: "#8B6A55",
                  bgcolor:
                    selectedHelpPath === "/eventos"
                      ? "#4B2E1F"
                      : "transparent",
                  color:
                    selectedHelpPath === "/eventos"
                      ? "#FFFFFF"
                      : "#4B2E1F",
                  "&:hover": {
                    borderColor: "#4B2E1F",
                    bgcolor:
                      selectedHelpPath === "/eventos"
                        ? "#3A2318"
                        : "rgba(75, 46, 31, 0.05)",
                  },
                }}
              >
                Eventos
              </Button>

              <Button
                variant={
                  selectedHelpPath === "/reportes"
                    ? "contained"
                    : "outlined"
                }
                startIcon={<AssessmentOutlinedIcon />}
                onClick={() => setSelectedHelpPath("/reportes")}
                sx={{
                  textTransform: "none",
                  justifyContent: "flex-start",
                  fontWeight: 600,
                  borderColor: "#8B6A55",
                  bgcolor:
                    selectedHelpPath === "/reportes"
                      ? "#4B2E1F"
                      : "transparent",
                  color:
                    selectedHelpPath === "/reportes"
                      ? "#FFFFFF"
                      : "#4B2E1F",
                  "&:hover": {
                    borderColor: "#4B2E1F",
                    bgcolor:
                      selectedHelpPath === "/reportes"
                        ? "#3A2318"
                        : "rgba(75, 46, 31, 0.05)",
                  },
                }}
              >
                Reportes
              </Button>

              <Button
                variant={
                  selectedHelpPath === "/maestros/parametros"
                    ? "contained"
                    : "outlined"
                }
                startIcon={<TuneOutlinedIcon />}
                onClick={() => setSelectedHelpPath("/maestros/parametros")}
                sx={{
                  textTransform: "none",
                  justifyContent: "flex-start",
                  fontWeight: 600,
                  borderColor: "#8B6A55",
                  bgcolor:
                    selectedHelpPath === "/maestros/parametros"
                      ? "#4B2E1F"
                      : "transparent",
                  color:
                    selectedHelpPath === "/maestros/parametros"
                      ? "#FFFFFF"
                      : "#4B2E1F",
                  "&:hover": {
                    borderColor: "#4B2E1F",
                    bgcolor:
                      selectedHelpPath === "/maestros/parametros"
                        ? "#3A2318"
                        : "rgba(75, 46, 31, 0.05)",
                  },
                }}
              >
                Parámetros
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
