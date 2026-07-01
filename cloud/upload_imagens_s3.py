"""
Script de Upload de Imagens — Envia fotos dos drones para o Amazon S3.
Projeto: Cloud para Telemetria de Tratores — Fatec Bebedouro

Como usar:
  1. Configure as credenciais IAM via variáveis de ambiente ou edite abaixo.
  2. Instale as dependências: pip install boto3
  3. Coloque imagens reais em ./imagens_drone/ (ou use imagens simuladas)
  4. Execute: python upload_imagens_s3.py
"""

import boto3
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuração AWS ─────────────────────────────────────────────────────────
AWS_REGION = "us-east-1"
BUCKET_S3  = "projeto-trator-gugue-12345"   # Nome real do bucket criado na AWS

# Cliente S3 (as credenciais devem estar configuradas no ambiente via aws configure ou IAM Role)
s3 = boto3.client("s3", region_name=AWS_REGION)


# ─── Verificar se bucket existe ───────────────────────────────────────────────
def verificar_bucket() -> None:
    """Confirma que o bucket S3 de destino existe e está acessível."""
    try:
        s3.head_bucket(Bucket=BUCKET_S3)
        print(f"[✅ S3] Bucket '{BUCKET_S3}' acessível.\n")
    except Exception as e:
        print(f"[❌ S3] Bucket '{BUCKET_S3}' inacessível: {e}")
        raise


# ─── Upload de uma imagem para S3 ─────────────────────────────────────────────
def fazer_upload_imagem(caminho_local: str, id_drone: str, id_trator: str) -> str:
    """
    Faz upload de uma imagem de drone para o S3 com metadados estruturados.

    Organização no bucket:
        imagens/<id_trator>/<YYYY-MM-DD>/<id_drone>/<uuid>.jpg

    Retorna a URI S3 do objeto criado.
    """
    if not os.path.isfile(caminho_local):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_local}")

    agora      = datetime.now(timezone.utc)
    data_str   = agora.strftime("%Y-%m-%d")
    nome_arq   = f"{uuid.uuid4()}.jpg"
    chave_s3   = f"imagens/{id_trator}/{data_str}/{id_drone}/{nome_arq}"

    # Metadados personalizados armazenados junto ao objeto no S3
    metadados = {
        "id-drone":     id_drone,
        "id-trator":    id_trator,
        "timestamp-utc": agora.isoformat(),
        "origem":        "sistema-telemetria-fatec-bebedouro",
    }

    try:
        with open(caminho_local, "rb") as arquivo:
            s3.put_object(
                Bucket=BUCKET_S3,
                Key=chave_s3,
                Body=arquivo,
                ContentType="image/jpeg",
                Metadata=metadados,
                # Sem ACL público — acesso via IAM com privilégio mínimo
            )

        uri_s3 = f"s3://{BUCKET_S3}/{chave_s3}"
        print(f"  [✅ S3] Upload OK | Drone: {id_drone} | Trator: {id_trator}")
        print(f"          URI: {uri_s3}")
        return uri_s3

    except Exception as e:
        print(f"  [❌ S3] Falha no upload de '{caminho_local}': {e}")
        raise


# ─── Processar pasta de imagens ───────────────────────────────────────────────
def processar_pasta(pasta: str, id_drone: str, id_trator: str) -> list[str]:
    """
    Varre uma pasta local e faz upload de todas as imagens .jpg/.jpeg/.png.
    Retorna lista com as URIs S3 de cada objeto criado.
    """
    extensoes = {".jpg", ".jpeg", ".png"}
    uris = []

    caminho = Path(pasta)
    if not caminho.exists():
        print(f"[⚠️  AVISO] Pasta '{pasta}' não encontrada. Criando pasta de exemplo...")
        caminho.mkdir(parents=True, exist_ok=True)
        # Cria uma imagem simulada para demonstração
        img_simulada = caminho / "drone_captura_exemplo.jpg"
        img_simulada.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # Header JPEG mínimo
        print(f"  [INFO] Imagem simulada criada: {img_simulada}")

    arquivos = [
        f for f in caminho.iterdir()
        if f.is_file() and f.suffix.lower() in extensoes
    ]

    if not arquivos:
        print(f"[⚠️  AVISO] Nenhuma imagem encontrada em '{pasta}'.")
        return uris

    print(f"\n[INFO] {len(arquivos)} imagem(ns) encontrada(s) em '{pasta}'.")
    for arquivo in sorted(arquivos):
        uri = fazer_upload_imagem(str(arquivo), id_drone, id_trator)
        uris.append(uri)

    return uris


# ─── Ponto de entrada ──────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  📷 Upload de Imagens de Drone — Fatec Bebedouro")
    print(f"  Bucket S3 : {BUCKET_S3}")
    print(f"  Região    : {AWS_REGION}")
    print("=" * 60)

    verificar_bucket()

    # Configuração dos drones e tratores associados
    # Na implantação real, estes parâmetros viriam de uma fila SQS
    missoes = [
        {"pasta": "./imagens_drone/drone_a1", "id_drone": "DRONE-A1", "id_trator": "TRATOR-001"},
        {"pasta": "./imagens_drone/drone_a2", "id_drone": "DRONE-A2", "id_trator": "TRATOR-002"},
        {"pasta": "./imagens_drone/drone_b1", "id_drone": "DRONE-B1", "id_trator": "TRATOR-003"},
    ]

    total_uploads = 0
    for missao in missoes:
        print(f"\n▶ Processando {missao['id_drone']} → {missao['id_trator']}")
        uris = processar_pasta(missao["pasta"], missao["id_drone"], missao["id_trator"])
        total_uploads += len(uris)

    print(f"\n{'=' * 60}")
    print(f"  [✅ CONCLUÍDO] {total_uploads} imagem(ns) enviada(s) ao S3.")
    print(f"  Bucket: s3://{BUCKET_S3}/imagens/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
