import os
import tempfile
import unittest

os.environ["DB_PATH"] = os.path.join(tempfile.gettempdir(), "teste_bot_agenda.db")

from app import app, criar_banco, responder

class TestBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        criar_banco()

    def test_menu(self):
        resposta = responder("oi", "whatsapp:+550000000000")
        self.assertIn("assistente virtual", resposta)

    def test_agendamento_invalido(self):
        resposta = responder("agendar", "whatsapp:+550000000000")
        self.assertIn("formato", resposta.lower())

if __name__ == "__main__":
    unittest.main()
