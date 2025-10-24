# Sistema Multilíngue L.A.A.R.I

## 🌍 Idiomas Suportados

O sistema L.A.A.R.I agora possui suporte completo para 4 idiomas:

- 🇧🇷 **Português** (Idioma padrão)
- 🇬🇧 **Inglês** (English)
- 🇪🇸 **Espanhol** (Español)
- 🇫🇷 **Francês** (Français)

## 📋 Funcionalidades

### Seletor de Idiomas com Bandeiras

O sistema possui um seletor de idiomas visual disponível em duas localizações:

1. **Páginas Públicas** (antes do login): Botão fixo no canto superior direito das páginas inicial, login e cadastro
2. **Páginas Internas** (após login): Menu dropdown na barra de navegação superior

Ambos exibem as bandeiras dos países correspondentes:

```
🇧🇷 Português
🇬🇧 English
🇪🇸 Español
🇫🇷 Français
```

### Detecção Automática

O sistema detecta automaticamente o idioma preferido do navegador do usuário e carrega a interface nesse idioma (se disponível).

### Tradução Completa

Todos os elementos da interface são traduzidos, incluindo:

✅ Menus de navegação
✅ Botões e rótulos
✅ Mensagens do sistema
✅ Campos de formulário
✅ Títulos e descrições
✅ Estatísticas e indicadores

## 🔧 Exemplos de Tradução

### Pesquisa por Sítio Arqueológico

**Português:** "Pesquisar por Sítio Arqueológico"
**Inglês:** "Search by Archaeological Site"
**Espanhol:** "Buscar por Sitio Arqueológico"
**Francês:** "Rechercher par Site Archéologique"

### Dashboard e Módulos

**Português:** "Bem-vindo ao sistema de gestão arqueológica"
**Inglês:** "Welcome to the archaeological management system"
**Espanhol:** "Bienvenido al sistema de gestión arqueológica"
**Francês:** "Bienvenue au système de gestion archéologique"

### Catalogação

**Português:** "Catalogação de Artefatos"
**Inglês:** "Artifact Cataloging"
**Espanhol:** "Catalogación de Artefactos"
**Francês:** "Catalogage d'Artefacts"

### Estatísticas

**Português:** "Artefatos Catalogados"
**Inglês:** "Cataloged Artifacts"
**Espanhol:** "Artefactos Catalogados"
**Francês:** "Artefacts Catalogués"

## 💻 Implementação Técnica

### Função de Tradução

O sistema utiliza a função `_()` (underscore) nos templates para marcar textos traduzíveis:

```html
<h1>{{ _('Dashboard') }}</h1>
<p>{{ _('Bem-vindo ao sistema de gestão arqueológica') }}</p>
```

### Dicionário de Traduções

As traduções são armazenadas no arquivo `app.py` em um dicionário estruturado por idioma:

```python
translations = {
    'en': {
        'Pesquisar por Sítio Arqueológico': 'Search by Archaeological Site',
        # ... mais traduções
    },
    'es': {
        'Pesquisar por Sítio Arqueológico': 'Buscar por Sitio Arqueológico',
        # ... mais traduções
    },
    'fr': {
        'Pesquisar por Sítio Arqueológico': 'Rechercher par Site Archéologique',
        # ... mais traduções
    }
}
```

### Persistência de Idioma

O idioma selecionado pelo usuário é armazenado na sessão e persiste durante toda a navegação:

```python
session['language'] = language
```

## 🚀 Como Usar

### Para Usuários Não Autenticados (Páginas Públicas)

1. **Acesse qualquer página pública** (página inicial, login ou cadastro)
2. **Clique no botão "Idioma"** no canto superior direito da tela
3. **Selecione o idioma desejado** clicando na bandeira correspondente
4. **A interface será automaticamente traduzida** para o idioma selecionado

### Para Usuários Autenticados (Dentro do Sistema)

1. **Faça login no sistema L.A.A.R.I**
2. **Clique no menu "Idioma"** na barra de navegação superior
3. **Selecione o idioma desejado** clicando na bandeira correspondente
4. **A interface será automaticamente traduzida** para o idioma selecionado

## 📝 Notas Importantes

- O idioma padrão é **Português (pt)**
- A seleção de idioma é **persistente** durante a sessão
- O sistema detecta automaticamente o idioma do navegador
- Todos os módulos principais estão traduzidos:
  - Dashboard
  - Acervo
  - Catalogação
  - Scanner 3D
  - Profissionais
  - Inventário
  - Transporte
  - Galeria

## 🎯 Módulos Traduzidos

### Dashboard
- Estatísticas (Artefatos, Profissionais, Transportes)
- Módulos principais
- Painel administrativo

### Catalogação
- Títulos e descrições
- Formulários de cadastro
- Mensagens de sucesso/erro

### Acervo
- Listagens de artefatos
- Filtros e pesquisas
- Detalhes de itens

### Scanner 3D
- Interface de digitalização
- Formulários de registro

### Profissionais
- Diretório de arqueólogos
- Perfis profissionais

### Inventário
- Controle de estoque
- Rastreamento de itens

### Transporte
- Gestão de movimentação
- Status de transporte

### Galeria
- Categorias de fotos
- Filtros e navegação

---

**Desenvolvido por:** Heloisa Bolognesi  
**Sistema:** L.A.A.R.I - Laboratório e Acervo Arqueológico Remoto Integrado
