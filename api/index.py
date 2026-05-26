"""
Entry point para Vercel.
Vercel busca este archivo como punto de entrada.
"""
from app.main import app

# Vercel usa esta variable "app" para servir requests
handler = app
