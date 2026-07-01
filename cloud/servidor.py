"""
Servidor HTTP sem cache para o Painel AgroCloud.
Serve os arquivos da pasta 'painel/' na porta 8765.
Desabilita cache do navegador para garantir que alteracoes sejam carregadas.
"""
import http.server
import socketserver
import os

PASTA  = r"c:\Users\gugue\OneDrive\Documentos\ArquiteturaClaude\painel"
PORTA  = 8765

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PASTA, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma",        "no-cache")
        self.send_header("Expires",       "0")
        super().end_headers()

    def log_message(self, format, *args):
        print(f"  [{args[1]}] {args[0]}")

os.chdir(PASTA)
print(f"Servidor rodando em http://localhost:{PORTA}/")
print(f"Pasta: {PASTA}")
print("Cache desabilitado - Ctrl+C para parar.\n")

with socketserver.TCPServer(("", PORTA), NoCacheHandler) as httpd:
    httpd.serve_forever()
