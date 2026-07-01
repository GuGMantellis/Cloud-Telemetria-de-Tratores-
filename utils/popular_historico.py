"""
Script de populacao com historico — envia 20 ciclos de dados simulados
com timestamps espacados no passado, para preencher os graficos com historia.
Execute uma vez apos recriar a tabela com sort key 'timestamp'.
"""
import boto3, random, uuid, time
from decimal import Decimal
from datetime import datetime, timezone, timedelta

AWS_REGION      = "us-east-2"
TABELA_DYNAMODB = "TelemetriaTratores"
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
tabela   = dynamodb.Table(TABELA_DYNAMODB)
TRATORES = ["TRATOR-001", "TRATOR-002", "TRATOR-003"]

# Gera 20 ciclos com timestamps dos ultimos 40 minutos (a cada 2 minutos)
CICLOS      = 20
INTERVALO_S = 120  # 2 minutos entre leituras
total       = 0

agora = datetime.now(timezone.utc)

print("=" * 65)
print("  Populando historico - Tabela TelemetriaTratores")
print(f"  {CICLOS} ciclos x {len(TRATORES)} tratores = {CICLOS * len(TRATORES)} registros")
print("=" * 65 + "\n")

for ciclo in range(CICLOS, 0, -1):  # do mais antigo para o mais recente
    # Timestamp no passado (ciclo 20 = 40 min atras, ciclo 1 = 2 min atras)
    ts = (agora - timedelta(seconds=ciclo * INTERVALO_S)).isoformat()

    print(f"  Ciclo #{CICLOS - ciclo + 1:02d} | {ts[11:19]} UTC")
    for trator in TRATORES:
        dados = {
            "id_trator": trator,
            "timestamp": ts,
            "motor": {
                "temperatura_celsius":   Decimal(str(round(random.uniform(82, 108), 2))),
                "rpm":                   random.randint(1300, 2500),
                "pressao_oleo_bar":      Decimal(str(round(random.uniform(2.8, 4.9), 2))),
                "nivel_combustivel_pct": Decimal(str(round(random.uniform(22, 95), 1))),
            },
            "gps": {
                "latitude":         Decimal(str(round(random.uniform(-21.0, -20.9), 6))),
                "longitude":        Decimal(str(round(random.uniform(-48.6, -48.5), 6))),
                "altitude_metros":  Decimal(str(round(random.uniform(485, 515), 1))),
                "velocidade_kmh":   Decimal(str(round(random.uniform(0, 18), 1))),
            },
            "ambiente": {
                "temperatura_externa_celsius": Decimal(str(round(random.uniform(20, 36), 1))),
                "umidade_relativa_pct":        Decimal(str(round(random.uniform(42, 88), 1))),
            },
            "status_operacional": random.choice(["trabalhando", "trabalhando", "em_transito", "parado"]),
            "id_registro":        str(uuid.uuid4()),
        }
        tabela.put_item(Item=dados)
        total += 1

    time.sleep(0.1)  # pequena pausa para nao sobrecarregar

print(f"\n[CONCLUIDO] {total} registros enviados!")
print("Agora abra http://127.0.0.1:8765 e clique em Temperatura ou RPM para ver os graficos!")
