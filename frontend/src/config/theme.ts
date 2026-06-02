import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#4B2E1F",
      dark: "#3A2318",
      light: "#F7E8D8",
    },
    secondary: {
      main: "#8B6A55",
    },
    background: {
      default: "#F8F3EC",
      paper: "#FFFDF8",
    },
    text: {
      primary: "#4B2E1F",
      secondary: "#7A6252",
    },
  },
  typography: {
    fontFamily: `"Segoe UI", "Roboto", "Arial", sans-serif`,
    h5: {
      fontWeight: 700,
    },
    h6: {
      fontWeight: 700,
    },
    button: {
      textTransform: "none",
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
});