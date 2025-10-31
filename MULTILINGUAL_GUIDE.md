# Guia do Sistema Multilíngue - L.A.A.R.I

## Visão Geral

Este documento explica como funciona o sistema de tradução multilíngue da aplicação L.A.A.R.I, implementado com JavaScript puro e localStorage.

## Idiomas Suportados

O sistema suporta quatro idiomas:

- **Português Brasileiro (pt-BR)** - Idioma padrão
- **Inglês (en)** - English
- **Espanhol (es)** - Español
- **Francês (fr)** - Français

## Arquitetura do Sistema

### 1. Arquivos JavaScript

#### `static/js/translations.js`
Contém todas as traduções em formato de objeto JavaScript. Estrutura:

```javascript
const translations = {
    "pt-BR": { "chave": "Texto em português", ... },
    "en": { "chave": "Text in English", ... },
    "es": { "chave": "Texto en español", ... },
    "fr": { "chave": "Texte en français", ... }
};
```

#### `static/js/i18n.js`
Implementa o sistema de internacionalização (i18n):

- **Detecção automática de idioma**: Detecta o idioma preferido do navegador
- **Persistência com localStorage**: Salva a escolha do usuário
- **Tradução dinâmica**: Atualiza todos os textos da página sem recarregar
- **Seletor de idioma**: Gerencia a mudança de idioma via cliques

### 2. Funcionamento

#### Inicialização

Quando a página carrega, o sistema:

1. Verifica se existe um idioma salvo no localStorage
2. Se não existir, detecta o idioma do navegador
3. Aplica as traduções correspondentes
4. Configura os eventos de mudança de idioma

#### Atributos HTML

Os elementos HTML usam atributos especiais para tradução:

- **`data-i18n="chave"`**: Traduz o conteúdo de texto do elemento
- **`data-i18n-html="chave"`**: Traduz permitindo HTML no conteúdo
- **`data-i18n-aria="chave"`**: Traduz o atributo aria-label
- **`data-language="codigo"`**: Identifica links do seletor de idioma

#### Exemplo de Uso

```html
<!-- Texto simples -->
<h1 data-i18n="app_name">L.A.A.R.I</h1>

<!-- Parágrafo com descrição -->
<p data-i18n="app_description">Sistema completo de gestão...</p>

<!-- Link do seletor de idioma -->
<a href="#" data-language="en">
    <span data-i18n="language_en">English</span>
</a>

<!-- Atributo aria-label -->
<button data-i18n-aria="theme_toggle">
    <span id="themeIcon">🌙</span>
</button>
```

### 3. Seletor de Idioma

O seletor de idioma está disponível em duas localizações:

1. **Navbar** (para usuários autenticados): Menu dropdown no topo direito
2. **Página inicial** (para visitantes): Botão dropdown no canto superior direito

Cada link do seletor possui:
- Atributo `data-language` com o código do idioma
- Atributo `data-i18n` para traduzir o nome do idioma
- Bandeira emoji do país

### 4. Persistência com localStorage

O sistema salva a escolha do idioma usando:

```javascript
// Salvar idioma escolhido
localStorage.setItem('laari_language', 'en');

// Recuperar idioma salvo
const savedLanguage = localStorage.getItem('laari_language');
```

O idioma permanece salvo entre sessões do navegador.

## Como Adicionar Novas Traduções

### Passo 1: Adicionar chave em translations.js

```javascript
const translations = {
    "pt-BR": {
        "nova_chave": "Novo texto em português"
    },
    "en": {
        "nova_chave": "New text in English"
    },
    "es": {
        "nova_chave": "Nuevo texto en español"
    },
    "fr": {
        "nova_chave": "Nouveau texte en français"
    }
};
```

### Passo 2: Usar no HTML

```html
<p data-i18n="nova_chave">Novo texto em português</p>
```

O texto padrão em português serve como fallback caso o JavaScript não carregue.

## API JavaScript

### I18n.translate(key, fallback)

Traduz uma chave programaticamente:

```javascript
const texto = I18n.translate('app_name', 'L.A.A.R.I');
console.log(texto); // Retorna a tradução no idioma atual
```

### I18n.setLanguage(language, showNotification)

Muda o idioma da aplicação:

```javascript
I18n.setLanguage('en', true); // Muda para inglês e mostra notificação
```

### I18n.formatNumber(number)

Formata números de acordo com o idioma:

```javascript
const formatted = I18n.formatNumber(1234.56);
// pt-BR: "1.234,56"
// en: "1,234.56"
```

### I18n.formatDate(date, options)

Formata datas de acordo com o idioma:

```javascript
const formatted = I18n.formatDate(new Date(), {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
});
// pt-BR: "31 de outubro de 2025"
// en: "October 31, 2025"
```

## Detecção Automática de Idioma

O sistema detecta automaticamente o idioma do navegador na primeira visita:

```javascript
const browserLang = navigator.language; // ex: "en-US"
// Sistema converte para: "en"
```

Prioridade de detecção:

1. Idioma salvo no localStorage (preferência do usuário)
2. Idioma do navegador detectado
3. Idioma padrão (pt-BR)

## Compatibilidade

- ✅ Todos os navegadores modernos (Chrome, Firefox, Safari, Edge)
- ✅ Dispositivos móveis (iOS e Android)
- ✅ Funciona sem JavaScript (exibe texto padrão em português)
- ✅ Acessível (suporta leitores de tela via aria-label)

## Manutenção

### Adicionar novo idioma

Para adicionar um quinto idioma (ex: Alemão):

1. Adicionar traduções em `translations.js`:
```javascript
const translations = {
    // ... idiomas existentes ...
    "de": {
        "app_name": "L.A.A.R.I",
        // ... todas as outras chaves ...
    }
};
```

2. Adicionar opção no seletor de idioma:
```html
<li><a class="dropdown-item" href="#" data-language="de">
    <span class="me-2">🇩🇪</span><span data-i18n="language_de">Deutsch</span>
</a></li>
```

3. Adicionar entrada no objeto de traduções para o nome do idioma:
```javascript
"language_de": "Deutsch"
```

## Boas Práticas

1. **Sempre use chaves descritivas**: `login_title` em vez de `text1`
2. **Mantenha consistência**: Use o mesmo padrão de nomenclatura
3. **Teste todos os idiomas**: Verifique se nenhuma tradução está faltando
4. **Texto padrão**: Sempre coloque o texto em português no HTML como fallback
5. **Contexto**: Inclua contexto nas chaves quando necessário (ex: `nav_dashboard` vs `page_dashboard`)

## Solução de Problemas

### Tradução não aparece

- Verifique se a chave existe em todos os idiomas em `translations.js`
- Confirme que o atributo `data-i18n` está correto no HTML
- Abra o console do navegador para ver erros

### Idioma não muda

- Verifique se o link possui o atributo `data-language`
- Confirme que o evento de clique está sendo capturado
- Verifique se não há erros JavaScript no console

### localStorage não funciona

- Alguns navegadores bloqueiam localStorage em modo privado
- Verifique as configurações de privacidade do navegador
- O sistema usa fallback para idioma do navegador neste caso

## Integração com Backend

Este sistema é puramente frontend. Se precisar sincronizar com o backend:

```javascript
// Após mudança de idioma, enviar ao servidor
I18n.setLanguage('en');
fetch('/api/set-language', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language: 'en' })
});
```

---

**Desenvolvido para o projeto L.A.A.R.I**  
**Sistema de Gestão Arqueológica**
