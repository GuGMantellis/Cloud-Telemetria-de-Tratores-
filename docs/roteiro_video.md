# Roteiro Sugerido para o Vídeo de Apresentação

Este é um roteiro estruturado para garantir que você e sua amiga tirem a nota máxima. Ele foca em mostrar o funcionamento, a estética premium e os conhecimentos técnicos exigidos pelas instruções do professor.

## Dicas Iniciais
- Usem um software de gravação de tela que mostre o rosto de vocês no canto (ex: OBS Studio, Loom, Zoom).
- Dividam as falas. Uma pessoa foca na Arquitetura e Python (Backend), e a outra foca no Docker, Interface Web e Segurança (Frontend/Ops).

---

## 🎬 Ato 1: Introdução e O Cenário (1 a 2 minutos)
**Pessoa 1:** "Olá, professor! Nós desenvolvemos uma arquitetura de telemetria completa para modernizar a frota de tratores autônomos de uma fazenda. O objetivo do projeto é capturar dados dos sensores em tempo real e disponibilizá-los em um painel seguro na nuvem para os agrônomos."

**Pessoa 2:** "Para isso, nós adotamos uma arquitetura totalmente baseada em serviços Cloud. Separamos a camada de ingestão de dados da camada de visualização."
*(Mostrem o Diagrama Mermaid que está no `relatorio_aws.md` na tela).*

## 🎬 Ato 2: O Emulador do Trator (Python + DynamoDB/S3) (2 minutos)
**Pessoa 1 (Apresentando o código):** "Aqui temos o nosso script Python `emulador_trator.py`. Ele atua como o 'cérebro' do trator. Nós geramos dados dinâmicos e aninhados usando a biblioteca `boto3`. 
Veja que criamos um JSON com `id_trator`, sensores (como `rpm` e `temperatura`), e o `gps`."

*(Rode o script Python no terminal ao vivo! Deixe os dados passando na tela)*
**Pessoa 1:** "Como o professor pode ver rodando no terminal, ele simula envios constantes para nossa tabela NoSQL do **DynamoDB** e também faria upload periódico de imagens de drone para um Bucket do **Amazon S3**."

## 🎬 Ato 3: Segurança e IAM (1 minuto)
**Pessoa 2:** "Um ponto crucial das instruções era a segurança. Nós não usamos um usuário AWS root no trator. Configuramos uma política estrita do **IAM** com privilégio mínimo! Como mostramos no relatório, o trator possui apenas as permissões `dynamodb:PutItem` e `s3:PutObject`. Ele não consegue deletar dados, garantindo a integridade da telemetria da fazenda em caso de invasão no trator."

## 🎬 Ato 4: Docker e Grupos de Segurança (1 minuto)
**Pessoa 2:** "Para hospedar o painel, nós conteinerizamos a aplicação usando este `Dockerfile`." *(Mostre o Dockerfile na tela)*.
"Usamos a imagem oficial do **Apache (httpd)**, super leve, e mapeamos apenas a porta 80. Na AWS, colocaríamos este container em uma instância EC2, protegida por um **Security Group** que bloqueia todas as portas externas, exceto o acesso HTTP na porta 80 para os agrônomos."

## 🎬 Ato 5: O Grande Final - Demonstração do Painel (2 minutos)
**Pessoa 1:** "E aqui está o resultado final, a visão que o agrônomo tem ao acessar a aplicação conteinerizada!"
*(Abra o arquivo `index.html` no navegador)*

**Pessoa 1 e 2 (Revezando):** 
- "Nós optamos por um design de alto padrão, usando o estilo 'Glassmorphism' (efeito vidro) e gráficos fluidos com *Chart.js*."
- "Como vocês podem ver, os dados de Rotação (RPM) e Temperatura variam em tempo real. Se a temperatura subir muito, a interface sinaliza visualmente em vermelho!"
- "E aqui ao lado temos a representação da imagem capturada pelo drone, armazenada no nosso S3 e puxada diretamente para a interface, garantindo que o agrônomo possa validar a operação."

**Pessoa 1:** "Esse projeto integra Python, Bancos de Dados NoSQL, Armazenamento de Objetos, Docker e Segurança em Nuvem em uma única solução prática."

**Pessoa 2:** "Obrigado por assistir, professor!"
