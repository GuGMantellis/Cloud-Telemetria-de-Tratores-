"""Popula o DynamoDB com 5 ciclos de 3 tratores (15 registros no total) e encerra."""
import boto3, random, uuid, time
from decimal import Decimal
from datetime import datetime, timezone

AWS_REGION      = "us-east-2"
TABELA_DYNAMODB = "TelemetriaTratores"
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
tabela = dynamodb.Table(TABELA_DYNAMODB)
TRATORES = ["TRATOR-001", "TRATOR-002", "TRATOR-003"]

total = 0
for ciclo in range(1, 6):
    print(f"\n--- Ciclo #{ciclo:02d} ---")
    for trator in TRATORES:
        dados = {
            "id_trator": trator,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "motor": {
                "temperatura_celsius":   Decimal(str(round(random.uniform(80, 110), 2))),
                "rpm":                   random.randint(1200, 2600),
                "pressao_oleo_bar":      Decimal(str(round(random.uniform(2.5, 5.0), 2))),
                "nivel_combustivel_pct": Decimal(str(round(random.uniform(20, 100), 1))),
            },
            "gps": {
                "latitude":         Decimal(str(round(random.uniform(-21.0, -20.9), 6))),
                "longitude":        Decimal(str(round(random.uniform(-48.6, -48.5), 6))),
                "altitude_metros":  Decimal(str(round(random.uniform(480, 520), 1))),
                "velocidade_kmh":   Decimal(str(round(random.uniform(0, 20), 1))),
            },
            "ambiente": {
                "temperatura_externa_celsius": Decimal(str(round(random.uniform(18, 38), 1))),
                "umidade_relativa_pct":        Decimal(str(round(random.uniform(40, 90), 1))),
            },
            "status_operacional": random.choice(["trabalhando", "em_transito", "parado"]),
            "id_registro":        str(uuid.uuid4()),
        }
        tabela.put_item(Item=dados)
        m = dados["motor"]
        print(f"  [OK] {trator} | Temp: {m['temperatura_celsius']}C | RPM: {m['rpm']} | "
              f"Fuel: {m['nivel_combustivel_pct']}% | Status: {dados['status_operacional']}")
        total += 1
        time.sleep(0.3)  # pequena pausa entre registros

print(f"\n[CONCLUIDO] {total} registros enviados ao DynamoDB us-east-2!")
print("Agora abra http://localhost:8765 e aperte F5 para ver os dados ao vivo.")
