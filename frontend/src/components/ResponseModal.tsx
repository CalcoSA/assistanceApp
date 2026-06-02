import { Box, Button, Dialog, DialogActions, DialogContent, Typography, } from "@mui/material";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import CloseOutlinedIcon from "@mui/icons-material/CloseOutlined";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import DoneOutlinedIcon from "@mui/icons-material/DoneOutlined";

export type ResponseModalSeverity = "success" | "error" | "warning" | "info";

interface ResponseModalProps {
  open: boolean;
  severity: ResponseModalSeverity;
  title: string;
  message: string;
  buttonText?: string;
  onClose: () => void;
}

const modalConfig = {
  success: {
    icon: <DoneOutlinedIcon />,
    color: "#2E7D32",
    bgColor: "#E8F5E9",
  },
  error: {
    icon: <CloseOutlinedIcon />,
    color: "#C62828",
    bgColor: "#FFEBEE",
  },
  warning: {
    icon: <WarningAmberOutlinedIcon />,
    color: "#ED6C02",
    bgColor: "#FFF4E5",
  },
  info: {
    icon: <InfoOutlinedIcon />,
    color: "#0288D1",
    bgColor: "#E5F6FD",
  },
};

export function ResponseModal({ open, severity, title, message, buttonText = "Aceptar", onClose, }: ResponseModalProps) {
  const config = modalConfig[severity];
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogContent sx={{ pt: 4, pb: 2, px: 4, textAlign: "center", }}>
        <Box sx={{ width: 72, height: 72, borderRadius: "50%", bgcolor: config.bgColor, color: config.color, display: "flex", alignItems: "center", justifyContent: "center", mx: "auto", mb: 2, "& svg": { fontSize: 44, },}}>
          {config.icon}
        </Box>
        <Typography sx={{ color: "#4B2E1F", fontSize: 22, fontWeight: 700, mb: 1, }}>
          {title}
        </Typography>
        <Typography sx={{ color: "#6B4A3A", fontSize: 15, lineHeight: 1.6, }}>
          {message}
        </Typography>
      </DialogContent>
      <DialogActions sx={{ px: 4, pb: 3, justifyContent: "center", }}>
        <Button
          variant="contained"
          onClick={onClose}
          sx={{ bgcolor: "#4B2E1F", color: "#FFFFFF", textTransform: "none", fontWeight: 600, minWidth: 130, "&:hover": { bgcolor: "#3A2318", },}}>
          {buttonText}
        </Button>
      </DialogActions>
    </Dialog>
  );
}