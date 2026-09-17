# Bot de Atendimento WhatsApp

Projeto em Python com Flask, Twilio e SQLite.

## Funções

- Recebe mensagens do WhatsApp.
- Responde dúvidas frequentes.
- Exibe um menu de atendimento.
- Agenda reuniões automaticamente.
- Impede dois agendamentos no mesmo horário.
- Salva as reuniões no banco `agenda.db`.

## 1. Instalação

No terminal:

```bash
python -m venv venv
```

Windows:

```bash
venv\\Scripts\\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## 2. Configuração

Copie `.env.example` para `.env` e altere:

```env
NOME_EMPRESA=Nome da sua empresa
HORARIO_INICIO=8
HORARIO_FIM=18
```

## 3. Executar

```bash
python app.py
```

O servidor ficará disponível em:

```text
http://localhost:5000
```

## 4. Conectar ao WhatsApp

Para receber mensagens reais, crie uma conta no Twilio e configure o WhatsApp Sandbox.

Depois, exponha sua aplicação local usando, por exemplo, ngrok:

```bash
ngrok http 5000
```

No painel do Twilio, configure o webhook de mensagens recebidas para:

```text
https://SEU-ENDERECO-NGROK.ngrok-free.app/whatsapp
```

Método: `POST`.

## 5. Formato para agendar

Envie pelo WhatsApp:

```text
agendar; Maria; 25/09/2026; 14:30; Reunião pedagógica
```

O bot validará:

- formato da data;
- horário de funcionamento;
- se a data é futura;
- se já existe outra reunião no mesmo horário.

## Observações

Este projeto é uma base funcional. Para uso em produção, adicione autenticação, painel administrativo, confirmação de cancelamento, integração com Google Calendar e proteção contra spam.
