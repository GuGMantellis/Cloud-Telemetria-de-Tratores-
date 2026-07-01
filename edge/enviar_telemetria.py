"""
Script de Telemetria — Envia dados de temperatura, RPM e GPS para o DynamoDB.
Projeto: Cloud para Telemetria de Tratores — Fatec Bebedouro

Como usar:
  1. Configure as credenciais IAM via variáveis de ambiente (ou aws configure):
       $env:AWS_ACCESS_KEY_ID     = "SUA_ACCESS_KEY"
       $env:AWS_SECRET_ACCESS_KEY = "SUA_SECRET_KEY"
     (ou use `aws configure` com o perfil do trator)
  2. Regiao: us-east-2 (Ohio) — onde a tabela TelemetriaTratores foi criada
  3. Execute: python enviar_telemetria.py
"""

import boto3
import uuid
import time
import random
from datetime import datetime, timezone
from decimal import Decimal

# ─── Configuração AWS ────────────────────────────────────────────────────────
AWS_REGION     = "us-east-2"
TABELA_DYNAMODB = "TelemetriaTratores"   # Nome exato criado no DynamoDB

# Credenciais devem ser configuradas no ambiente ou via AWS IAM Roles.
import os
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

# Cliente DynamoDB usando credenciais do ambiente
if AWS_ACCESS_KEY and AWS_SECRET_KEY:
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )
else:
    # Se não encontrar as variáveis explicitamente, tenta o default do boto3 (aws configure)
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

tabela = dynamodb.Table(TABELA_DYNAMODB)


# ─── Frota de tratores da fazenda ────────────────────────────────────────────
TRATORES = ["TRATOR-001", "TRATOR-002", "TRATOR-003"]

# Coordenadas da região de Bebedouro/SP (base das simulações GPS)
LAT_BASE  = -20.95
LNG_BASE  = -48.56


# ─── Gerador de dados de telemetria ─────────────────────────────────────────
def gerar_telemetria(id_trator: str) -> dict:
    """
    Gera um registro de telemetria com dados aninhados e dinâmicos.
    Simula leituras reais de sensores de um trator autônomo.

    Estrutura JSON (aninhada):
        id_trator   : str  — Partition Key
        timestamp   : str  — Sort Key (ISO 8601 UTC)
        motor       : dict — temperatura, RPM, pressão óleo, combustível
        gps         : dict — latitude, longitude, altitude, velocidade
        ambiente    : dict — temperatura externa, umidade
        status_operacional : str
        id_registro : str  — UUID único do registro
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    return {
        # Chave primária composta (Partition Key + Sort Key)
        "id_trator": id_trator,
        "timestamp": timestamp,

        # Dados de motor (JSON aninhado)
        "motor": {
            "temperatura_celsius":  Decimal(str(round(random.uniform(80.0, 110.0), 2))),
            "rpm":                  random.randint(1200, 2600),
            "pressao_oleo_bar":     Decimal(str(round(random.uniform(2.5, 5.0),   2))),
            "nivel_combustivel_pct": Decimal(str(round(random.uniform(20.0, 100.0), 1))),
        },

        # Localização GPS (aninhada) — baseada em Bebedouro/SP
        "gps": {
            "latitude":         Decimal(str(round(random.uniform(LAT_BASE - 0.05, LAT_BASE + 0.05), 6))),
            "longitude":        Decimal(str(round(random.uniform(LNG_BASE - 0.05, LNG_BASE + 0.05), 6))),
            "altitude_metros":  Decimal(str(round(random.uniform(480.0, 520.0), 1))),
            "velocidade_kmh":   Decimal(str(round(random.uniform(0.0, 20.0),    1))),
        },

        # Sensores ambientais
        "ambiente": {
            "temperatura_externa_celsius": Decimal(str(round(random.uniform(18.0, 38.0), 1))),
            "umidade_relativa_pct":        Decimal(str(round(random.uniform(40.0, 90.0), 1))),
        },

        # Status operacional e identificação do registro
        "status_operacional": random.choice(["trabalhando", "em_transito", "parado"]),
        "id_registro":        str(uuid.uuid4()),
    }


# ─── Envio para DynamoDB ──────────────────────────────────────────────────────
def enviar_para_dynamodb(dados: dict) -> None:
    """Insere um item na tabela DynamoDB com privilégio mínimo (PutItem apenas)."""
    try:
        tabela.put_item(Item=dados)
        motor = dados["motor"]
        gps   = dados["gps"]
        print(
            f"  [OK DynamoDB] {dados['id_trator']:12s} | "
            f"Temp: {motor['temperatura_celsius']:6}C | "
            f"RPM: {motor['rpm']:4d} | "
            f"Combustivel: {motor['nivel_combustivel_pct']:5}% | "
            f"GPS: ({gps['latitude']}, {gps['longitude']}) | "
            f"Status: {dados['status_operacional']}"
        )
    except Exception as e:
        print(f"  [ERRO DynamoDB] Falha ao enviar dados de {dados['id_trator']}: {e}")
        raise


# ─── Loop principal ────────────────────────────────────────────────────────────
def main():
    intervalo_segundos = 10
    ciclos = 0

    print("=" * 70)
    print("  Sistema de Telemetria de Tratores - Fatec Bebedouro")
    print(f"  Tabela DynamoDB : {TABELA_DYNAMODB}")
    print(f"  Regiao AWS      : {AWS_REGION}")
    print(f"  Tratores        : {', '.join(TRATORES)}")
    print(f"  Intervalo       : {intervalo_segundos}s por ciclo")
    print("=" * 70)
    print("  Pressione Ctrl+C para encerrar.\n")

    while True:
        ciclos += 1
        agora = datetime.now().strftime("%H:%M:%S")
        print(f"\n--- Ciclo #{ciclos:03d} | {agora} -------------------------------------------")

        for id_trator in TRATORES:
            dados = gerar_telemetria(id_trator)
            enviar_para_dynamodb(dados)

        print(f"  [Aguardando {intervalo_segundos}s para o proximo ciclo...]")
        time.sleep(intervalo_segundos)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTelemetria encerrada pelo operador.")
