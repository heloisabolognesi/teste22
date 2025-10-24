# 🚀 Deploy L.A.A.R.I na Railway - Pronto!

## Passos para Deploy

### 1. Preparar o Repositório
- Faça upload dos arquivos do projeto para um repositório GitHub
- Certifique-se de que todos os arquivos estão incluídos

### 2. Criar Conta na Railway
- Acesse https://railway.app
- Faça login com sua conta GitHub

### 3. Criar Novo Projeto
- Clique em "New Project"
- Selecione "Deploy from GitHub repo"
- Escolha seu repositório do L.A.A.R.I

### 4. Configurar Banco de Dados
- No dashboard do projeto, clique em "+ New"
- Selecione "Database" → "PostgreSQL"
- Railway criará automaticamente o banco e a variável DATABASE_URL

### 5. Configurar Variáveis de Ambiente
No painel do seu projeto, vá em "Variables" e adicione:

```
SESSION_SECRET=seu-token-secreto-aqui-muito-seguro
FLASK_ENV=production
ADMIN_EMAIL=admin@email.com
ADMIN_PASSWORD=senha-segura-admin
ADMIN_USERNAME=Admin
```

### 6. Deploy Automático
- Railway detectará automaticamente que é uma aplicação Flask
- O deploy começará automaticamente
- Aguarde alguns minutos para conclusão

### 7. Acessar Aplicação
- Após o deploy, clique em "View Logs" para verificar se tudo está funcionando
- Clique no domínio gerado para acessar sua aplicação

## Funcionalidades Incluídas
✓ Sistema de autenticação completo
✓ Catálogo de artefatos arqueológicos
✓ Galeria de fotos
✓ Sistema de upload de arquivos
✓ Diretório de profissionais
✓ Dashboard administrativo
✓ Suporte multi-idioma (PT/EN/ES)

## Custos
- Railway oferece um plano gratuito com recursos limitados
- Para uso profissional, considere o plano pago
- Banco PostgreSQL incluído no plano

## Problemas Comuns

### Build Failing?
- Verifique se todas as dependências estão no pyproject.toml
- Confirme que o arquivo railway.json está na raiz do projeto

### App não inicia?
- Verifique as variáveis de ambiente
- Veja os logs do deploy para identificar erros
- Certifique-se de que DATABASE_URL está configurado

### Upload de arquivos não funciona?
- Railway tem limitações de armazenamento
- Para produção, considere usar serviços como AWS S3

## Suporte
- Documentação Railway: https://docs.railway.app
- Para problemas específicos do L.A.A.R.I, consulte os logs da aplicação