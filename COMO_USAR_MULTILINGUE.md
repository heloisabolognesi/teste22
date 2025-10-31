# Como Usar o Sistema Multilíngue - Guia Rápido

## Para Usuários da Aplicação

### Mudando o Idioma

1. **Na página inicial (sem login)**:
   - Clique no botão "Language" (ou "Idioma") no canto superior direito
   - Selecione o idioma desejado:
     - 🇧🇷 Português
     - 🇬🇧 English
     - 🇪🇸 Español
     - 🇫🇷 Français

2. **Após fazer login (na navegação)**:
   - Clique no menu dropdown "Idioma" na barra superior
   - Selecione o idioma desejado

### Idioma Automático

- Na primeira visita, o sistema detecta automaticamente o idioma do seu navegador
- Sua escolha é salva e mantida em futuras visitas ao site

### O que é traduzido

✅ **Traduzido automaticamente:**
- Todos os menus de navegação
- Botões e links
- Títulos e descrições
- Mensagens do sistema
- Rodapé

## Para Desenvolvedores

### Como Adicionar Tradução em Nova Página

1. **Adicione os atributos data-i18n nos elementos HTML:**

```html
<h1 data-i18n="titulo_pagina">Título da Página</h1>
<p data-i18n="descricao">Descrição em português</p>
<button data-i18n="btn_salvar">Salvar</button>
```

2. **Adicione as traduções em `static/js/translations.js`:**

```javascript
const translations = {
    "pt-BR": {
        "titulo_pagina": "Título da Página",
        "descricao": "Descrição em português",
        "btn_salvar": "Salvar"
    },
    "en": {
        "titulo_pagina": "Page Title",
        "descricao": "Description in English",
        "btn_salvar": "Save"
    },
    "es": {
        "titulo_pagina": "Título de la Página",
        "descricao": "Descripción en español",
        "btn_salvar": "Guardar"
    },
    "fr": {
        "titulo_pagina": "Titre de la Page",
        "descricao": "Description en français",
        "btn_salvar": "Enregistrer"
    }
};
```

### Testando

Abra o console do navegador (F12) e digite:

```javascript
// Mudar para inglês
I18n.setLanguage('en');

// Mudar para espanhol
I18n.setLanguage('es');

// Mudar para francês
I18n.setLanguage('fr');

// Voltar para português
I18n.setLanguage('pt-BR');
```

### Traduzir via JavaScript

```javascript
// Obter tradução da chave atual
const texto = I18n.translate('app_name');

// Com fallback
const texto = I18n.translate('chave_inexistente', 'Texto padrão');
```

## Troubleshooting

**Problema**: Idioma não muda ao clicar  
**Solução**: Verifique se há erros no console (F12) e se o JavaScript está carregado

**Problema**: Texto não está traduzido  
**Solução**: Certifique-se que:
1. O elemento tem o atributo `data-i18n`
2. A chave existe em `translations.js` para todos os idiomas
3. A página foi recarregada após as mudanças

**Problema**: Idioma volta ao padrão após atualizar  
**Solução**: Verifique se o localStorage está habilitado no navegador (não funciona em modo anônimo de alguns navegadores)

## Documentação Completa

Para documentação técnica completa, veja: **MULTILINGUAL_GUIDE.md**

---

**Desenvolvido para L.A.A.R.I**  
Sistema de Gestão Arqueológica
