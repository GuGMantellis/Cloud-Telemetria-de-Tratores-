#!/usr/bin/env bash
# ==============================================================================
# Security Groups — Painel do Agrônomo
# Projeto: Cloud para Telemetria de Tratores — Fatec Bebedouro
# ==============================================================================
#
# Este script documenta a configuração dos Security Groups na AWS.
# Os comandos utilizam a AWS CLI e podem ser executados:
#   - Localmente (com credenciais de administrador)
#   - No AWS CloudShell (sem instalar nada)
#
# IMPORTANTE: Substitua <VPC_ID> pelo ID real da sua VPC antes de executar.
# ==============================================================================

set -euo pipefail

# ── Variáveis ──────────────────────────────────────────────────────────────────
VPC_ID="<VPC_ID>"          # Ex: vpc-0abc1234567890def  (substitua pelo real)
PROJETO="TelemetriaTratores"
INST="FatecBebedouro"

echo "=== Configurando Security Groups — $PROJETO ==="

# ── 1. Criar Security Group para o container Docker (Painel Web) ──────────────
SG_PAINEL=$(aws ec2 create-security-group \
  --group-name "sg-painel-agronomo" \
  --description "Permite HTTP (porta 80) apenas para o painel do agronomo" \
  --vpc-id "$VPC_ID" \
  --tag-specifications "ResourceType=security-group,Tags=[{Key=Projeto,Value=${PROJETO}},{Key=Instituicao,Value=${INST}}]" \
  --query 'GroupId' \
  --output text)

echo "[✅] Security Group criado: $SG_PAINEL"

# ── 2. Regra de ENTRADA — Permitir HTTP (porta 80) de qualquer IP ─────────────
# Permite que os agrônomos acessem o painel via navegador web.
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_PAINEL" \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

echo "[✅] Regra de entrada porta 80 (HTTP) configurada."

# (Opcional) Para restringir ao IP da fazenda apenas, substitua 0.0.0.0/0 por:
# --cidr 203.0.113.0/24

# ── 3. Regra de ENTRADA — Bloquear tudo o mais ───────────────────────────────
# Por padrão, a AWS nega todo tráfego de entrada não permitido explicitamente.
# NÃO adicione regras para portas 22 (SSH) ou outras que não sejam necessárias.
echo "[ℹ️ ] Todo tráfego de entrada não listado está BLOQUEADO (padrão AWS)."

# ── 4. Regra de SAÍDA — Permitir saída irrestrita (padrão AWS) ────────────────
# O container pode fazer requisições de saída normalmente (DNS, AWS APIs etc.).
echo "[ℹ️ ] Saída irrestrita (padrão AWS) — mantida para permitir chamadas AWS SDK."

# ── 5. Verificar as regras configuradas ──────────────────────────────────────
echo ""
echo "=== Regras configuradas para o Security Group $SG_PAINEL ==="
aws ec2 describe-security-groups \
  --group-ids "$SG_PAINEL" \
  --query 'SecurityGroups[*].{Nome:GroupName,Entrada:IpPermissions,Saida:IpPermissionsEgress}' \
  --output table

# ── 6. Associar o Security Group à instância EC2 que roda o container ─────────
# Substitua <INSTANCE_ID> pelo ID da instância EC2 (ex: i-0abc123456789def0)
# aws ec2 modify-instance-attribute \
#   --instance-id <INSTANCE_ID> \
#   --groups "$SG_PAINEL"

echo ""
echo "=== RESUMO DAS REGRAS DE REDE ==="
echo ""
echo " ┌─────────────┬───────────┬────────┬─────────────┬──────────────────────────┐"
echo " │ Direção     │ Protocolo │ Porta  │ Origem/Dest │ Propósito                │"
echo " ├─────────────┼───────────┼────────┼─────────────┼──────────────────────────┤"
echo " │ Entrada     │ TCP       │ 80     │ 0.0.0.0/0   │ Acesso HTTP ao painel    │"
echo " │ Saída       │ ALL       │ ALL    │ 0.0.0.0/0   │ Padrão AWS (liberado)    │"
echo " │ Entrada     │ (demais)  │ (todos)│ -           │ BLOQUEADO (sem regra)    │"
echo " └─────────────┴───────────┴────────┴─────────────┴──────────────────────────┘"
echo ""
echo "[✅] Configuração concluída. Security Group ID: $SG_PAINEL"
