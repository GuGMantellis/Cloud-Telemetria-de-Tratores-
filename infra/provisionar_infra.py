"""
Script de Provisionamento — Cria a tabela DynamoDB e o bucket S3.
Projeto: Cloud para Telemetria de Tratores — Fatec Bebedouro

Execute UMA VEZ antes de rodar os scripts de telemetria e upload.
Requer credenciais IAM com permissão de administrador para criação de recursos.

Como usar:
  pip install boto3
  python provisionar_infra.py
"""

import boto3

# ─── Configuração AWS ─────────────────────────────────────────────────────────
AWS_REGION      = "us-east-1"
TABELA_DYNAMODB = "TelemetriaTratores"     # Nome exato da tabela
BUCKET_S3       = "projeto-trator-gugue-12345"  # Nome globalmente único do bucket



# ─── Criar tabela DynamoDB ────────────────────────────────────────────────────
def criar_tabela_dynamodb():
    """
    Cria a tabela DynamoDB com chave primária composta:
      - id_trator : Partition Key (String)
      - timestamp  : Sort Key (String)
    Modo de faturamento: PAY_PER_REQUEST (sem capacidade provisionada)
    """
    dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)

    try:
        dynamodb.create_table(
            TableName=TABELA_DYNAMODB,
            KeySchema=[
                {"AttributeName": "id_trator", "KeyType": "HASH"},   # Partition key
                {"AttributeName": "timestamp",  "KeyType": "RANGE"},  # Sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "id_trator", "AttributeType": "S"},
                {"AttributeName": "timestamp",  "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",   # Pague por uso — ideal para projetos
            Tags=[
                {"Key": "Projeto",     "Value": "TelemetriaTratores"},
                {"Key": "Instituicao", "Value": "FatecBebedouro"},
            ],
        )
        print(f"[OK DynamoDB] Tabela '{TABELA_DYNAMODB}' criada com sucesso.")
        print(f"              Chaves: id_trator (PK) + timestamp (SK)")
    except dynamodb.exceptions.ResourceInUseException:
        print(f"[INFO DynamoDB] Tabela '{TABELA_DYNAMODB}' ja existe. Nenhuma acao necessaria.")
    except Exception as e:
        print(f"[ERRO DynamoDB] Falha ao criar tabela: {e}")
        raise


# ─── Criar bucket S3 ──────────────────────────────────────────────────────────
def criar_bucket_s3():
    """
    Cria o bucket S3 privado para armazenar as imagens dos drones.
    Configura:
      - Bloqueio total de acesso público (Block Public Access)
      - Versionamento habilitado (protege as imagens de sobrescrita acidental)
    """
    s3 = boto3.client("s3", region_name=AWS_REGION)

    try:
        # us-east-1 não aceita LocationConstraint (regra da AWS)
        if AWS_REGION == "us-east-1":
            s3.create_bucket(Bucket=BUCKET_S3)
        else:
            s3.create_bucket(
                Bucket=BUCKET_S3,
                CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
            )

        # Bloquear todo acesso público ao bucket
        s3.put_public_access_block(
            Bucket=BUCKET_S3,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls":       True,
                "IgnorePublicAcls":      True,
                "BlockPublicPolicy":     True,
                "RestrictPublicBuckets": True,
            },
        )

        # Habilitar versionamento para proteger as imagens
        s3.put_bucket_versioning(
            Bucket=BUCKET_S3,
            VersioningConfiguration={"Status": "Enabled"},
        )

        print(f"[OK S3] Bucket '{BUCKET_S3}' criado e configurado.")
        print(f"        Acesso publico: BLOQUEADO | Versionamento: ATIVO")

    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"[INFO S3] Bucket '{BUCKET_S3}' ja existe e pertence a sua conta.")
    except Exception as e:
        print(f"[ERRO S3] Falha ao criar bucket: {e}")
        raise


# ─── Ponto de entrada ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Provisionamento de Infraestrutura - Fatec Bebedouro")
    print(f"  Região: {AWS_REGION}")
    print("=" * 60 + "\n")

    criar_tabela_dynamodb()
    criar_bucket_s3()

    print(f"\n{'=' * 60}")
    print("  [OK] Infraestrutura pronta para uso.")
    print(f"  Proximo passo: execute enviar_telemetria.py")
    print(f"{'=' * 60}")
