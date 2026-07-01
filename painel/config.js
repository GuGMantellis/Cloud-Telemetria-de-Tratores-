/**
 * Configurações da AWS para o Frontend (Leitura do DynamoDB)
 * Projeto: Cloud para Telemetria de Tratores — Fatec Bebedouro
 *
 * ATENÇÃO: Para projetos acadêmicos/demonstração, as credenciais de LEITURA
 * podem ser expostas aqui. Em produção, utilize AWS Cognito Identity Pool.
 *
 * Esta chave tem permissão APENAS de:
 *   - dynamodb:Scan
 *   - dynamodb:Query
 *   - dynamodb:GetItem
 * (sem permissão para escrever ou deletar)
 */

window.AWS_CONFIG = {
    // Credenciais IAM com permissão estrita de LEITURA no DynamoDB
    accessKeyId: 'COLOQUE_SUA_ACCESS_KEY_AQUI',
    secretAccessKey: 'COLOQUE_SUA_SECRET_KEY_AQUI',
    region: 'us-east-2',

    // Recursos AWS utilizados pelo painel
    tableName: 'TelemetriaTratores',   // Tabela DynamoDB
    bucketName: 'projeto-trator-gugue-12345',  // Bucket S3

    // IDs dos tratores monitorados
    tratores: ['TRATOR-001', 'TRATOR-002', 'TRATOR-003'],

    // Intervalo de atualização automática (milissegundos)
    refreshInterval: 10000  // 10 segundos
};
