import { Alert, Box, Button, CircularProgress, InputAdornment, Paper, Stack, TextField, Typography, } from "@mui/material";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import LoginOutlinedIcon from "@mui/icons-material/LoginOutlined";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import { getErrorMessage } from "../services/errorService";
import CoffeeIcon from "@mui/icons-material/Coffee";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

export function LoginPage() {
  const [validationError, setValidationError] = useState("");
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const { login } = useAuth();

  const resetMessages = () => {
    setValidationError("");
  };

  const handleLogin = async () => {
    try {
      const cleanUsername = username.trim();

      if (!cleanUsername) {
        setValidationError("El usuario es obligatorio.");
        return;
      }

      if (!password) {
        setValidationError("La contraseña es obligatoria.");
        return;
      }

      setLoading(true);
      resetMessages();

      await login({
        username: cleanUsername,
        password,
      });

      navigate("/", { replace: true });
    } catch (err) {
      setValidationError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: "#FFFDF8",
        display: "grid",
        placeItems: "center",
        px: 2,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          width: "100%",
          maxWidth: 460,
          border: "1px solid #E0CDBB",
          borderRadius: 4,
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            bgcolor: "#4B2E1F",
            color: "#F7E8D8",
            px: 4,
            py: 4,
            textAlign: "center",
          }}
        >
          <Box
            component="img"
            src="/images/MonedaCrepes.png"
            alt="Crepes & Waffles"
            sx={{
              width: 110,
              height: 110,
              objectFit: "contain",
              mb: 2,
            }}
          />

          <Stack
            direction="row"
            spacing={1.2}
            sx={{
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <CoffeeIcon sx={{ fontSize: 32 }} />

            <Typography sx={{ fontSize: 21, fontWeight: 800 }}>
              Sistema registro de asistencia
            </Typography>
          </Stack>

          <Typography sx={{ mt: 1, fontSize: 14, color: "#EAD9C9" }}>
            Inicia sesión con tu usuario de intranet.
          </Typography>
        </Box>

        <Stack spacing={2.5} sx={{ px: 4, py: 4 }}>
          {validationError && <Alert severity="warning">{validationError}</Alert>}

          <TextField
            label="Usuario o correo"
            value={username}
            disabled={loading}
            fullWidth
            autoFocus
            onChange={(event) => setUsername(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                handleLogin();
              }
            }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <PersonOutlineOutlinedIcon sx={{ color: "#8B6A55" }} />
                  </InputAdornment>
                ),
              },
            }}
          />

          <TextField
            label="Contraseña"
            type="password"
            value={password}
            disabled={loading}
            fullWidth
            onChange={(event) => setPassword(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                handleLogin();
              }
            }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <LockOutlinedIcon sx={{ color: "#8B6A55" }} />
                  </InputAdornment>
                ),
              },
            }}
          />

          <Button
            variant="contained"
            startIcon={
              loading ? (
                <CircularProgress size={18} sx={{ color: "#FFFFFF" }} />
              ) : (
                <LoginOutlinedIcon />
              )
            }
            onClick={handleLogin}
            disabled={loading}
            sx={{
              bgcolor: "#4B2E1F",
              color: "#FFFFFF",
              height: 48,
              textTransform: "none",
              fontWeight: 700,
              "&:hover": {
                bgcolor: "#3A2318",
              },
            }}
          >
            {loading ? "Ingresando..." : "Iniciar sesión"}
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}