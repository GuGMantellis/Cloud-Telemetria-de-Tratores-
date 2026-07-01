# ==============================================================================
# Dockerfile — Painel do Agrônomo
# Projeto: Cloud para Telemetria de Tratores — Fatec Bebedouro
#
# Constrói um container com Apache HTTP Server servindo o painel HTML/JS/CSS.
# Porta exposta: 80 (HTTP) — controlada pelo Security Group da AWS.
#
# Build:
#   docker build -t painel-agronomo .
#
# Run:
#   docker run -d -p 80:80 --name painel-agronomo painel-agronomo
#
# Acesse: http://localhost  (ou IP público da EC2)
# ==============================================================================

# Imagem base oficial do Apache (Debian Bookworm — menor superfície de ataque)
FROM httpd:2.4-bookworm

# ── Metadados da imagem ────────────────────────────────────────────────────────
LABEL maintainer="Fatec Bebedouro <cloud@fatec.edu.br>"
LABEL description="Painel do Agrônomo — Telemetria de Tratores"
LABEL version="2.0"

# ── Copiar o painel completo para o diretório raiz do Apache ──────────────────
# Inclui: index.html, style.css, app.js, config.js e pasta img/
COPY ./painel/ /usr/local/apache2/htdocs/

# ── Configuração de segurança do Apache ───────────────────────────────────────
# - Oculta a versão do Apache nos cabeçalhos de resposta (ServerTokens Prod)
# - Desativa a assinatura nas páginas de erro (ServerSignature Off)
# - Adiciona cabeçalhos de segurança HTTP (X-Content-Type-Options, etc.)
RUN sed -i \
    -e 's/^ServerTokens .*/ServerTokens Prod/' \
    -e 's/^ServerSignature .*/ServerSignature Off/' \
    /usr/local/apache2/conf/httpd.conf 2>/dev/null || true

# ── Porta exposta ──────────────────────────────────────────────────────────────
# O Security Group da AWS DEVE permitir entrada APENAS na porta 80.
# NUNCA abrir portas 22 (SSH), 443 ou outras desnecessárias neste SG.
EXPOSE 80

# ── Verificação de saúde (Health Check) ──────────────────────────────────────
# O Docker verifica a cada 30s se o Apache está respondendo corretamente.
# Se falhar 3 vezes consecutivas, o container é marcado como "unhealthy".
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

# ── Comando padrão ────────────────────────────────────────────────────────────
# "-D FOREGROUND" mantém o Apache em primeiro plano (obrigatório em containers)
CMD ["httpd-foreground"]
