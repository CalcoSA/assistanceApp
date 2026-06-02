import { Alert, Box, CircularProgress, Paper, Stack, Typography, } from "@mui/material";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getErrorMessage } from "../services/errorService";
import { useAuth } from "../context/AuthContext";
import CoffeeIcon from "@mui/icons-material/Coffee";
import { useEffect, useState } from "react";

export function IntranetAccessPage() {
  const [searchParams] = useSearchParams();
  const [error, setError] = useState("");
  const { intranetAccess } = useAuth();
  const navigate = useNavigate();
  
  useEffect(() => {
    const validateIntranetAccess = async () => {
      try {
        const userLogin = searchParams.get("userLogin");
        const ts = searchParams.get("ts");
        const sig = searchParams.get("sig");

        if (!userLogin || !ts || !sig) {
          setError("El enlace de acceso desde intranet no es válido.");
          return;
        }

        await intranetAccess({
          userLogin,
          ts,
          sig,
        });

        navigate("/", { replace: true });
      } catch (err) {
        setError(getErrorMessage(err));
      }
    };

    validateIntranetAccess();
  }, [searchParams, intranetAccess, navigate]);

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
              Registro de domicilios
            </Typography>
          </Stack>

          <Typography sx={{ mt: 1, fontSize: 14, color: "#EAD9C9" }}>
            Validando acceso desde la intranet.
          </Typography>
        </Box>

        <Stack spacing={2.5} sx={{ px: 4, py: 4, alignItems: "center" }}>
          {error ? (
            <Alert severity="warning" sx={{ width: "100%" }}>
              {error}
            </Alert>
          ) : (
            <>
              <CircularProgress sx={{ color: "#4B2E1F" }} />

              <Typography sx={{ color: "#6B4A3A", fontSize: 15 }}>
                Estamos validando tu sesión, por favor espera...
              </Typography>
            </>
          )}
        </Stack>
      </Paper>
    </Box>
  );
}