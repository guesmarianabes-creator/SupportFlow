import os
import re
import sqlite3
from datetime import datetime

from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DB_PATH = os.getenv("DB_PATH", "agenda.db")
NOME_EMPRESA = os.getenv("NOME_EMPRESA", "Minha Empresa")
HORARIO_INICIO = int(os.getenv("HORARIO_INICIO", "8"))
HORARIO_FIM = int(os.getenv("HORARIO_FIM", "18"))


# ============================================================
# CONFIGURAÇÃO DAS RESPOSTAS DO BOT
# ============================================================

FAQ = {
    "horario": (
        f"Nosso horário de atendimento é de segunda a sexta, "
        f"das {HORARIO_INICIO}h às {HORARIO_FIM}h."
    ),

    "endereco": (
        "Nosso endereço é: informe aqui o endereço da empresa."
    ),

    "servicos": (
        "Oferecemos: atendimento, reuniões, suporte e orientações. "
        "Digite 'agendar' para marcar uma reunião."
    ),

    "contato": (
        "Você pode continuar falando comigo por este WhatsApp."
    ),
}


# ============================================================
# BANCO DE DADOS
# ============================================================

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def criar_banco():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reunioes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT NOT NULL,
                data TEXT NOT NULL,
                hora TEXT NOT NULL,
                assunto TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
        """)

        conn.commit()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar(texto):
    return " ".join(texto.lower().strip().split())


# ============================================================
# INTERPRETAÇÃO DE AGENDAMENTOS
# ============================================================

def extrair_agendamento(texto):
    """
    Aceita exemplos como:

    agendar; Maria; 25/09/2026; 14:30; Reunião pedagógica

    Também aceita:

    agendar Maria 25/09/2026 14:30 reunião pedagógica
    """

    padrao = re.search(
        r"agendar\s*;?\s*(.+?)\s*;?\s*"
        r"(\d{2}/\d{2}/\d{4})\s*;?\s*"
        r"(\d{1,2}:\d{2})\s*;?\s*(.+)",
        texto,
        re.IGNORECASE,
    )

    if not padrao:
        return None

    nome, data, hora, assunto = padrao.groups()

    try:
        data_obj = datetime.strptime(
            f"{data} {hora}",
            "%d/%m/%Y %H:%M"
        )

    except ValueError:
        return {
            "erro": "A data ou o horário está inválido."
        }

    # Não permite agendamento no passado
    if data_obj <= datetime.now():
        return {
            "erro": "Escolha uma data e horário futuros."
        }

    # Verifica horário de funcionamento
    if not HORARIO_INICIO <= data_obj.hour < HORARIO_FIM:
        return {
            "erro": (
                f"As reuniões acontecem entre "
                f"{HORARIO_INICIO}h e {HORARIO_FIM}h."
            )
        }

    return {
        "nome": nome.strip(),

        "data": data_obj.strftime("%Y-%m-%d"),

        "data_exibicao": data_obj.strftime("%d/%m/%Y"),

        "hora": data_obj.strftime("%H:%M"),

        "assunto": assunto.strip(),
    }


# ============================================================
# VERIFICAR DISPONIBILIDADE
# ============================================================

def horario_disponivel(data, hora):

    with conectar() as conn:

        registro = conn.execute(
            """
            SELECT id
            FROM reunioes
            WHERE data = ? AND hora = ?
            """,
            (data, hora),
        ).fetchone()

    return registro is None


# ============================================================
# SALVAR REUNIÃO
# ============================================================

def salvar_reuniao(dados, telefone):

    with conectar() as conn:

        conn.execute(
            """
            INSERT INTO reunioes
            (
                nome,
                telefone,
                data,
                hora,
                assunto,
                criado_em
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                dados["nome"],
                telefone,
                dados["data"],
                dados["hora"],
                dados["assunto"],
                datetime.now().isoformat(
                    timespec="seconds"
                ),
            ),
        )

        conn.commit()


# ============================================================
# CÉREBRO DO BOT
# ============================================================

def responder(mensagem, telefone):

    texto = normalizar(mensagem)

    # --------------------------------------------------------
    # SAUDAÇÃO
    # --------------------------------------------------------

    if texto in {
        "oi",
        "olá",
        "ola",
        "bom dia",
        "boa tarde",
        "boa noite"
    }:

        return (
            f"Olá! Eu sou o assistente virtual da "
            f"{NOME_EMPRESA}. 🤖\n\n"

            "Posso ajudar com:\n"

            "1 - Horário de atendimento\n"
            "2 - Serviços\n"
            "3 - Endereço\n"
            "4 - Agendar reunião\n\n"

            "Digite uma opção ou escreva sua dúvida."
        )

    # --------------------------------------------------------
    # HORÁRIO
    # --------------------------------------------------------

    if texto in {
        "1",
        "horario",
        "horário"
    }:

        return FAQ["horario"]

    # --------------------------------------------------------
    # SERVIÇOS
    # --------------------------------------------------------

    if texto in {
        "2",
        "servicos",
        "serviços"
    }:

        return FAQ["servicos"]

    # --------------------------------------------------------
    # ENDEREÇO
    # --------------------------------------------------------

    if texto in {
        "3",
        "endereco",
        "endereço"
    }:

        return FAQ["endereco"]

    # --------------------------------------------------------
    # AGENDAMENTO
    # --------------------------------------------------------

    if texto in {
        "4",
        "agendar",
        "reuniao",
        "reunião"
    }:

        return (
            "Para agendar, envie neste formato:\n\n"

            "agendar; Seu Nome; 25/09/2026; "
            "14:30; Assunto da reunião\n\n"

            "Exemplo:\n"

            "agendar; Maria; 25/09/2026; "
            "14:30; Reunião pedagógica"
        )

    # --------------------------------------------------------
    # PROCESSAR AGENDAMENTO
    # --------------------------------------------------------

    if texto.startswith("agendar"):

        dados = extrair_agendamento(mensagem)

        if not dados:

            return (
                "Não consegui entender o agendamento.\n\n"

                "Use este formato:\n"

                "agendar; Nome; DD/MM/AAAA; "
                "HH:MM; Assunto"
            )

        if "erro" in dados:

            return dados["erro"]

        # Verifica se horário já está ocupado
        if not horario_disponivel(
            dados["data"],
            dados["hora"]
        ):

            return (
                f"Já existe uma reunião em "
                f"{dados['data_exibicao']} às "
                f"{dados['hora']}.\n\n"

                "Escolha outro horário."
            )

        # Salva no banco
        salvar_reuniao(
            dados,
            telefone
        )

        return (
            "✅ Reunião agendada com sucesso!\n\n"

            f"Nome: {dados['nome']}\n"

            f"Data: {dados['data_exibicao']}\n"

            f"Horário: {dados['hora']}\n"

            f"Assunto: {dados['assunto']}\n\n"

            "Obrigado! Se precisar, "
            "digite 'menu'."
        )

    # --------------------------------------------------------
    # MENU
    # --------------------------------------------------------

    if texto in {
        "menu",
        "ajuda",
        "help"
    }:

        return (
            "Menu de atendimento:\n"

            "1 - Horário\n"
            "2 - Serviços\n"
            "3 - Endereço\n"
            "4 - Agendar reunião"
        )

    # --------------------------------------------------------
    # RESPOSTA PADRÃO
    # --------------------------------------------------------

    return (
        "Não encontrei uma resposta para essa dúvida. 🤔\n\n"

        "Digite 'menu' para ver as opções "
        "ou 'agendar' para marcar uma reunião."
    )


# ============================================================
# PÁGINA DO CHAT
# ============================================================

@app.route("/chat")
def chat():

    from flask import render_template

    return render_template("chat.html")

@app.route("/painel")
def painel():

    from flask import render_template

    return render_template("painel.html")


# ============================================================
# API DO CHAT
# ============================================================

@app.route("/api/mensagem", methods=["POST"])
def api_mensagem():

    dados = request.get_json(
        silent=True
    ) or {}

    mensagem = str(
        dados.get("mensagem", "")
    ).strip()

    if not mensagem:

        return {
            "resposta": (
                "Digite uma mensagem "
                "para começar o atendimento."
            )
        }, 400

    resposta = responder(
        mensagem,
        "web-chat"
    )

    return {
        "resposta": resposta
    }


# ============================================================
# API PARA LISTAR REUNIÕES
# ============================================================

@app.route("/api/reunioes", methods=["GET"])
def api_reunioes():

    with conectar() as conn:

        reunioes = conn.execute(
            """
            SELECT
                id,
                nome,
                telefone,
                data,
                hora,
                assunto
            FROM reunioes
            ORDER BY data ASC, hora ASC
            """
        ).fetchall()

    return {
        "reunioes": [
            dict(reuniao)
            for reuniao in reunioes
        ]
    }


# ============================================================
# API PARA CANCELAR REUNIÃO
# ============================================================

@app.route(
    "/api/reunioes/<int:reuniao_id>",
    methods=["DELETE"]
)
def cancelar_reuniao(reuniao_id):

    with conectar() as conn:

        reuniao = conn.execute(
            """
            SELECT id
            FROM reunioes
            WHERE id = ?
            """,
            (reuniao_id,),
        ).fetchone()

        if not reuniao:

            return {
                "erro": "Reunião não encontrada."
            }, 404

        conn.execute(
            """
            DELETE FROM reunioes
            WHERE id = ?
            """,
            (reuniao_id,),
        )

        conn.commit()

    return {
        "mensagem": (
            "Reunião cancelada "
            "com sucesso."
        )
    }


# ============================================================
# INICIAR SISTEMA
# ============================================================

if __name__ == "__main__":

    criar_banco()

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv("PORT", "5000")
        ),
        debug=True
    )