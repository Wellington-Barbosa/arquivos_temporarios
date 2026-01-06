// src/pages/Login/index.jsx
// ============================================================================
// Tela de Login
// ----------------------------------------------------------------------------
// • Fundo com foto do hospital da Unimed + overlay em degradê verde suave.
// • Card central branco levemente translúcido (efeito "vidro").
// • Mantém toda a lógica atual (login, lembrar usuário, snackbar, etc.).
// • IMPORTANTE: ajuste o nome do arquivo de fundo se for diferente.
// ============================================================================

import React, { useState, useEffect } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Link as MuiLink,
  Snackbar,
  Alert,
  InputAdornment,
  IconButton,
  Divider,
  CircularProgress,
  Tooltip,
  FormControlLabel,
  Checkbox,
} from "@mui/material";
import { useNavigate, Link as RouterLink } from "react-router-dom";
import api from "../../services/api";
import logoUnimed from "../../assets/images/logo_unimed.png";
import bgHospital from "../../assets/images/bg_hospital_unimed.jpg"; // <- AJUSTE O NOME SE PRECISAR
import { jwtDecode } from "jwt-decode";
import { useAuth } from "@/context/AuthContext";

import PersonOutline from "@mui/icons-material/PersonOutline";
import LockOutlined from "@mui/icons-material/LockOutlined";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import InfoOutlined from "@mui/icons-material/InfoOutlined";

const MASTER_USERNAME = (import.meta.env.VITE_MASTER_USERNAME || "adm.wellington").toLowerCase();

// Extrai as claims do token (identity pode vir em `sub` como objeto)
function getClaimsFromToken(token) {
  const decoded = jwtDecode(token);
  return decoded?.sub && typeof decoded.sub === "object" ? decoded.sub : decoded;
}

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const isHomolog = import.meta.env.VITE_APP_ENV === 'homolog';

  const [form, setForm] = useState({ username: "", senha: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [capsOn, setCapsOn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [rememberUser, setRememberUser] = useState(false);

  // Snackbar de feedback rápido
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "error",
  });

  // ---------------------- Lembrar usuário (localStorage) ---------------------
  useEffect(() => {
    const savedUser = localStorage.getItem("rememberedUsername");
    if (savedUser) {
      setForm((prev) => ({ ...prev, username: savedUser }));
      setRememberUser(true);
    }
  }, []);

  useEffect(() => {
    if (rememberUser && form.username.trim()) {
      localStorage.setItem("rememberedUsername", form.username.trim());
    } else {
      localStorage.removeItem("rememberedUsername");
    }
  }, [rememberUser, form.username]);

  // ---------------------- Handlers básicos -----------------------------------
  const handleChange = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleKeyUp = (e) =>
    e.getModifierState && setCapsOn(e.getModifierState("CapsLock"));

  const submitDisabled =
    loading || !form.username.trim() || !form.senha.trim();

  // ---------------------- Submit (login) -------------------------------------
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (submitDisabled) return;

    try {
      setLoading(true);
      const res = await api.post("/auth/login", form);
      const { access_token, message, senha_temporaria } = res.data;

      // guarda token no contexto (AuthContext já configura Axios e F5)
      login(access_token);

      setSnackbar({
        open: true,
        message: message || "Login realizado com sucesso!",
        severity: "success",
      });

      setTimeout(() => {
        if (senha_temporaria) {
          navigate("/alterar-senha");
          return;
        }

        const claims = getClaimsFromToken(access_token);
        const username =
          (claims.username ??
            claims.user ??
            jwtDecode(access_token)?.sub ??
            ""
          )
            .toString()
            .toLowerCase();
        const role = (claims.tipo_login ?? "").toString().toLowerCase();

        // Master vai para seletor de perfil
        if (username === MASTER_USERNAME) {
          navigate("/selecao-perfil");
        } else if (role === "admin") {
          navigate("/dashboard/administrador");
        } else {
          navigate("/dashboard/usuario");
        }
      }, 500);
    } catch (err) {
      setSnackbar({
        open: true,
        message:
          err?.response?.data?.error ||
          "Credenciais inválidas. Verifique e tente novamente.",
        severity: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  // ---------------------- Render ---------------------------------------------
  return (
    <Box
      sx={{
        minHeight: "100vh",
        width: "100vw",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        // Fundo com imagem do hospital + overlay em degradê
        backgroundImage: `linear-gradient(
          135deg,
          rgba(3, 80, 40, 0.72),
          rgba(3, 99, 56, 0.60),
          rgba(3, 99, 56, 0.72)
        ), url(${bgHospital})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        // leve escurecida nas bordas para o card destacar
        p: 2,
      }}
    >
      {/* Card central com efeito "vidro" */}
      <Paper
        elevation={0}
        sx={{
          width: "100%",
          maxWidth: 460,
          borderRadius: 4,
          p: 4,
          backdropFilter: "blur(10px)",
          backgroundColor: "rgba(255, 255, 255, 0.94)",
          border: "1px solid rgba(255,255,255,0.7)",
          boxShadow: "0 18px 45px rgba(0,0,0,0.28)",
        }}
      >
        {/* Cabeçalho */}
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          gap={1}
        >
          <img
            src={logoUnimed}
            alt="Unimed Rio Verde"
            style={{ width: 150, height: "auto" }}
          />
          <Typography
            variant="h6"
            sx={{ color: "#2E7D32", fontWeight: 700, mt: 1 }}
          >
            Portal Declaração de Saúde
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: "text.secondary",
              mb: 2,
              textAlign: "center",
              maxWidth: 320,
            }}
          >
            Entre com seu usuário e senha corporativos para acessar a
            plataforma.
          </Typography>
        </Box>

        {/* Formulário */}
        <form onSubmit={handleSubmit} noValidate>
          <TextField
            label="Usuário"
            name="username"
            value={form.username}
            onChange={handleChange}
            fullWidth
            autoFocus
            required
            margin="normal"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <PersonOutline sx={{ color: "action.active" }} />
                </InputAdornment>
              ),
            }}
          />

          <TextField
            label="Senha"
            name="senha"
            type={showPassword ? "text" : "password"}
            value={form.senha}
            onChange={handleChange}
            onKeyUp={handleKeyUp}
            fullWidth
            required
            margin="normal"
            helperText={
              capsOn ? (
                <span style={{ color: "#b45309" }}>Caps Lock ativado</span>
              ) : (
                " "
              )
            }
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LockOutlined sx={{ color: "action.active" }} />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <Tooltip
                    title={showPassword ? "Ocultar senha" : "Mostrar senha"}
                  >
                    <IconButton
                      onClick={() => setShowPassword((v) => !v)}
                      edge="end"
                      aria-label="mostrar/ocultar senha"
                      size="small"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </Tooltip>
                </InputAdornment>
              ),
            }}
          />

          {/* Lembrar usuário */}
          <FormControlLabel
            control={
              <Checkbox
                checked={rememberUser}
                onChange={(e) => setRememberUser(e.target.checked)}
                color="success"
              />
            }
            label={
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                Lembrar meu usuário
              </Typography>
            }
            sx={{ mt: 1 }}
          />

          <Button
            type="submit"
            variant="contained"
            disableElevation
            fullWidth
            sx={{
              mt: 2,
              py: 1.2,
              fontWeight: 700,
              backgroundColor: "#2E7D32",
              "&:hover": { backgroundColor: "#256628" },
            }}
            disabled={submitDisabled}
          >
            {loading ? (
              <CircularProgress size={22} sx={{ color: "#fff" }} />
            ) : (
              "ENTRAR"
            )}
          </Button>
        </form>

        <Divider sx={{ my: 2 }} />

        {/* Rodapé: link para solicitação de acesso */}
        <Box sx={{ textAlign: "center" }}>
          <MuiLink
            component={RouterLink}
            to="/solicitar-acesso"
            underline="hover"
            sx={{ fontSize: 14, color: "#2E7D32", fontWeight: 500 }}
          >
            Solicite seu acesso
          </MuiLink>
          <Tooltip
            title="Em caso de dificuldade, contate o suporte de TI."
            placement="right"
            arrow
          >
            <IconButton size="small" sx={{ ml: 1 }}>
              <InfoOutlined fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      {/* Snackbar de feedback */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() =>
          setSnackbar((prev) => ({
            ...prev,
            open: false,
          }))
        }
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
        sx={{ mt: 1, mr: 1 }}
      >
        <Alert
          onClose={() =>
            setSnackbar((prev) => ({
              ...prev,
              open: false,
            }))
          }
          severity={snackbar.severity}
          variant="filled"
          elevation={3}
          sx={{ minWidth: 280 }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {isHomolog && (
      <div className="fixed bottom-0 w-full bg-red-600 text-white text-center p-2 font-bold z-50">
        ⚠️ AMBIENTE DE TREINAMENTO - DADOS FICTÍCIOS ⚠️
      </div>
    )}
    </Box>
  );
}
