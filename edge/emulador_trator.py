import json
import time
import random
import boto3
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÃO - SCRIPT DE TELEMETRIA DO TRATOR
# ==============================================================================
# Este script emula o envio de dados aninhados (JSON) de um Trator Autônomo 
# para o DynamoDB e o upload de uma imagem simulada de Drone para o S3.
#
# Para rodar isso de verdade na AWS:
# 1. Configure as credenciais no seu computador usando `aws configure` (com IAM de privilégio mínimo).
# 2. Instale o boto3: `pip install boto3`
# ==============================================================================

REGION_NAME = 'us-east-1'
DYNAMODB_TABLE_NAME = 'TelemetriaTratores'
S3_BUCKET_NAME = 'projeto-trator-gugue-12345' # Substitua pelo nome do seu bucket na AWS
TRATOR_ID = 'TRT-8000-ALPHA'

# Inicializando os clientes Boto3 (SDK da AWS para Python)
# Nota: Quando rodar local, certifique-se de ter credenciais IAM configuradas.
try:
    dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
    s3 = boto3.client('s3', region_name=REGION_NAME)
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
except Exception as e:
    print(f"⚠️ Aviso: Não foi possível conectar à AWS. Você configurou as credenciais IAM? Erro: {e}")

def gerar_dados_telemetria():
    """Gera um dicionário (JSON aninhado) com dados fictícios do trator."""
    timestamp = datetime.utcnow().isoformat()
    
    # Dados aninhados
    dados = {
        'id_trator': TRATOR_ID,          # Partition Key do DynamoDB
        'timestamp': timestamp,          # Sort Key do DynamoDB (se configurado)
        'status_operacao': 'Ativo',
        'sensores': {
            'temperatura_motor': round(random.uniform(85.0, 105.0), 2), # Celsius
            'rpm': random.randint(1800, 2500),
            'nivel_combustivel_pct': round(random.uniform(40.0, 95.0), 1)
        },
        'gps': {
            'latitude': round(random.uniform(-23.500, -23.600), 6),
            'longitude': round(random.uniform(-46.600, -46.700), 6)
        }
    }
    return dados

def enviar_para_dynamodb(dados):
    """Envia os dados aninhados em JSON para o DynamoDB."""
    try:
        # A API put_item converte automaticamente o dicionário Python para o formato esperado pelo Dynamo
        response = table.put_item(Item=dados)
        print(f"[DynamoDB] ✅ Dados enviados com sucesso! Temp: {dados['sensores']['temperatura_motor']}°C | RPM: {dados['sensores']['rpm']}")
    except Exception as e:
        print(f"[DynamoDB] ❌ Falha ao enviar dados: {e}")

def fazer_upload_imagem_s3():
    """Simula o upload de uma imagem do drone no S3."""
    nome_arquivo_local = 'drone_capture_simulada.jpg'
    nome_arquivo_s3 = f"capturas/{TRATOR_ID}/imagem_{int(time.time())}.jpg"
    
    # Cria um arquivo falso localmente apenas para o exemplo (ou você pode ler uma imagem real)
    with open(nome_arquivo_local, 'w') as f:
        f.write('Bytes ficticios de uma imagem jpeg')

    try:
        s3.upload_file(nome_arquivo_local, S3_BUCKET_NAME, nome_arquivo_s3)
        print(f"[S3] 📸 Imagem de drone '{nome_arquivo_s3}' enviada ao S3 com sucesso!")
    except Exception as e:
        print(f"[S3] ❌ Falha ao fazer upload da imagem: {e}")

if __name__ == "__main__":
    print("🚜 Iniciando Módulo de Telemetria do Trator Autônomo...")
    print("Pressione Ctrl+C para parar.")
    
    ciclos_upload_s3 = 0
    
    try:
        while True:
            # 1. Gerar e enviar dados JSON de telemetria a cada 2 segundos
            dados_atuais = gerar_dados_telemetria()
            # print(json.dumps(dados_atuais, indent=2)) # Descomente para ver o JSON localmente
            
            # ATENÇÃO: As linhas abaixo tentam acessar a AWS real. 
            # Se você não tem AWS configurada, elas vão gerar os logs de erro ou exceções.
            # enviar_para_dynamodb(dados_atuais)
            
            # Simula a impressão na tela (para o vídeo da apresentação, isso fica legal no terminal!)
            print(f"[{dados_atuais['timestamp']}] Trator: {TRATOR_ID} | Temp: {dados_atuais['sensores']['temperatura_motor']}°C | RPM: {dados_atuais['sensores']['rpm']} | GPS: {dados_atuais['gps']['latitude']}, {dados_atuais['gps']['longitude']}")
            
            # 2. A cada 10 segundos (5 ciclos), envia uma imagem para o S3
            ciclos_upload_s3 += 1
            if ciclos_upload_s3 >= 5:
                # fazer_upload_imagem_s3()
                print(f"[S3 Simulação] 📸 Upload de imagem de drone finalizado para a nuvem.")
                ciclos_upload_s3 = 0
                
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nDesligando trator...")
