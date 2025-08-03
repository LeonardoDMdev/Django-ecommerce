# 🛒 E-commerce Django Project

Este é um projeto de e-commerce desenvolvido com Django, com integração à API do Mercado Pago para pagamentos.

---

## 🚀 Funcionalidades

- Catálogo de produtos  
- Carrinho de compras  
- Checkout com integração Mercado Pago  
- Painel administrativo  
- Django Templates customizados  
- Estrutura modular com apps separados  
- Envio de e-mails (confirmações, notificações, etc.)

---

## 🧰 Tecnologias Utilizadas

- Python 3.x  
- Django 5.2.3  
- Mercado Pago SDK (`mercadopago`)  
- SQLite3 (banco de dados local)  
- Pillow (para manipulação de imagens)  
- Ngrok (para testes locais com URLs públicas)

---

## 📦 Instalação

### 1. Clone o repositório:
```bash
git clone https://github.com/LeonardoDMdev/Django-ecommerce.git
cd Django-ecommerce

2. Crie e ative um ambiente virtual:
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

3. Instale as dependências:
pip install -r requirements.txt

4. Configure as variáveis de ambiente:
Crie um arquivo .env na raiz do projeto com o seguinte conteúdo:

# Chave secreta do Django - settings.py
SECRET_KEY=your_secret_key_here

# Configurações de e-mail - settings.py
EMAIL_HOST=smtp.seuservidor.com
EMAIL_PORT=587
EMAIL_HOST_USER=seuemail@dominio.com
EMAIL_HOST_PASSWORD=sua_senha_do_email
EMAIL_USE_TLS=True

# Mercado Pago
MERCADO_PAGO_ACCESS_TOKEN=your_access_token_here

# Hosts confiáveis - settings.py
ALLOWED_HOSTS=127.0.0.1,localhost,sualoja.com
CSRF_TRUSTED_ORIGINS=https://sualoja.com,https://*.ngrok.io

⚠️ Importante: Nunca compartilhe seu .env publicamente. Ele contém informações sensíveis.


5. Execute as migrações e o servidor:
python manage.py migrate
python manage.py runserver


🌐 Testando com Ngrok (opcional)
Caso queira testar com URLs públicas (ex: callbacks do Mercado Pago):
ngrok http 8000

Copie a URL gerada (ex: https://abc123.ngrok.io) e use como base nas configurações em:

CSRF_TRUSTED_ORIGINS=''

ALLOWED_HOSTS=''

No views.py linha 195 onde diz link=""



📁 Estrutura do Projeto
PROJETO_ECOMMERCE/
│
├── ecommerce/            # Configurações principais do Django
├── loja/                # App principal com lógica da loja
├── static/              # Arquivos estáticos
├── db.sqlite3           # Banco de dados local (ignorado no Git)
├── manage.py            # Script de gerenciamento
├── .env                 # Variáveis de ambiente (não versionado)
└── requirements.txt     # Dependências do projeto
