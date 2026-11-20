# Residencial Sol Nascente 2 — Bloco 10

Endereço escolhido para o aplicativo no Streamlit: https://residencial-sol-nascente-2-bloco-10.streamlit.app/

Aplicativo Streamlit da síndica Daniela. Cadastro de condôminos, pagamentos, histórico, relatórios e recibos PDF/JPG. São 20 apartamentos, do térreo ao quarto andar.

## Publicação

Crie o repositório residencial-sol-nascente-2-bloco-10 no GitHub e envie os arquivos extraídos para a raiz da branch main. No Streamlit Community Cloud, crie um aplicativo a partir desse repositório e selecione app.py.

Crie um projeto Supabase exclusivo para o Sol Nascente e guarde a senha criada. Em Connect, selecione Session pooler e consulte o host, a porta, o banco e o usuário. Nas configurações do aplicativo Streamlit, copie o modelo abaixo em Secrets e preencha os valores do novo projeto.

```toml
DB_HOST = "HOST_DO_NOVO_PROJETO"
DB_PORT = "5432"
DB_DBNAME = "postgres"
DB_USER = "USUARIO_DO_NOVO_PROJETO"
DB_PASSWORD = "SENHA_DO_NOVO_BANCO"
APP_ACCESS_PASSWORD = "SENHA_EXCLUSIVA_DA_ADMINISTRACAO"
```

A página inicial pode ser pública. Daniela usa a senha da administração para acessar os cadastros e pagamentos. As tabelas são criadas durante o primeiro acesso administrativo. Guarde as senhas no gerenciador de senhas e nos Segredos do aplicativo.
