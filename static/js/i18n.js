/**
 * L.A.A.R.I - Sistema de Internacionalização (i18n)
 * Implementa tradução dinâmica com suporte a localStorage
 * Idiomas suportados: PT-BR, EN, ES, FR
 */

const I18n = {
    defaultLanguage: 'pt-BR',
    currentLanguage: null,
    
    /**
     * Inicializa o sistema de internacionalização
     * Carrega o idioma salvo no localStorage ou usa o padrão
     */
    init: function() {
        const savedLanguage = this.getSavedLanguage();
        const browserLanguage = this.getBrowserLanguage();
        
        const language = savedLanguage || browserLanguage || this.defaultLanguage;
        this.setLanguage(language, false);
        
        this.setupLanguageSelector();
        
        console.log('I18n initialized with language:', this.currentLanguage);
    },
    
    /**
     * Obtém o idioma salvo no localStorage
     */
    getSavedLanguage: function() {
        try {
            return localStorage.getItem('laari_language');
        } catch (e) {
            console.error('Erro ao ler idioma do localStorage:', e);
            return null;
        }
    },
    
    /**
     * Detecta o idioma preferido do navegador
     */
    getBrowserLanguage: function() {
        const browserLang = navigator.language || navigator.userLanguage;
        
        if (browserLang.startsWith('pt')) return 'pt-BR';
        if (browserLang.startsWith('en')) return 'en';
        if (browserLang.startsWith('es')) return 'es';
        if (browserLang.startsWith('fr')) return 'fr';
        
        return this.defaultLanguage;
    },
    
    /**
     * Define o idioma atual e atualiza toda a interface
     * @param {string} language - Código do idioma (pt-BR, en, es, fr)
     * @param {boolean} showNotification - Se deve exibir notificação de mudança
     */
    setLanguage: function(language, showNotification = true) {
        if (!translations[language]) {
            console.error('Idioma não suportado:', language);
            language = this.defaultLanguage;
        }
        
        this.currentLanguage = language;
        
        try {
            localStorage.setItem('laari_language', language);
        } catch (e) {
            console.error('Erro ao salvar idioma no localStorage:', e);
        }
        
        document.documentElement.setAttribute('lang', language);
        
        this.updatePageContent();
        this.updateLanguageSelector();
        
        if (showNotification && window.LAARI) {
            const message = this.translate('notification_language_changed');
            window.LAARI.showNotification(message, 'success', 3000);
        }
    },
    
    /**
     * Traduz uma chave para o idioma atual
     * @param {string} key - Chave da tradução
     * @param {string} fallback - Texto alternativo se a tradução não existir
     * @returns {string} - Texto traduzido
     */
    translate: function(key, fallback = '') {
        const lang = this.currentLanguage || this.defaultLanguage;
        
        if (translations[lang] && translations[lang][key]) {
            return translations[lang][key];
        }
        
        if (fallback) {
            return fallback;
        }
        
        if (translations[this.defaultLanguage] && translations[this.defaultLanguage][key]) {
            return translations[this.defaultLanguage][key];
        }
        
        console.warn('Tradução não encontrada para a chave:', key);
        return key;
    },
    
    /**
     * Atualiza todo o conteúdo da página com as traduções
     * Procura por elementos com atributo data-i18n
     */
    updatePageContent: function() {
        const elements = document.querySelectorAll('[data-i18n]');
        
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translatedText = this.translate(key);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                if (element.type === 'submit' || element.type === 'button') {
                    element.value = translatedText;
                } else {
                    element.placeholder = translatedText;
                }
            } else {
                const htmlContent = element.getAttribute('data-i18n-html');
                if (htmlContent) {
                    element.innerHTML = translatedText;
                } else {
                    element.textContent = translatedText;
                }
            }
        });
        
        const titleElement = document.querySelector('title[data-i18n]');
        if (titleElement) {
            const key = titleElement.getAttribute('data-i18n');
            titleElement.textContent = this.translate(key);
        }
        
        const ariaElements = document.querySelectorAll('[data-i18n-aria]');
        ariaElements.forEach(element => {
            const key = element.getAttribute('data-i18n-aria');
            const translatedText = this.translate(key);
            element.setAttribute('aria-label', translatedText);
        });
    },
    
    /**
     * Configura os seletores de idioma
     * Adiciona eventos de clique para mudança de idioma
     */
    setupLanguageSelector: function() {
        const languageLinks = document.querySelectorAll('[data-language]');
        
        languageLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const language = link.getAttribute('data-language');
                this.setLanguage(language, true);
            });
        });
    },
    
    /**
     * Atualiza o seletor de idioma para destacar o idioma atual
     */
    updateLanguageSelector: function() {
        const languageLinks = document.querySelectorAll('[data-language]');
        
        languageLinks.forEach(link => {
            const language = link.getAttribute('data-language');
            
            if (language === this.currentLanguage) {
                link.classList.add('active');
                link.style.fontWeight = 'bold';
            } else {
                link.classList.remove('active');
                link.style.fontWeight = 'normal';
            }
        });
    },
    
    /**
     * Formata números de acordo com o idioma atual
     * @param {number} number - Número a ser formatado
     * @returns {string} - Número formatado
     */
    formatNumber: function(number) {
        const locale = this.getLocale();
        return new Intl.NumberFormat(locale).format(number);
    },
    
    /**
     * Formata datas de acordo com o idioma atual
     * @param {Date|string} date - Data a ser formatada
     * @param {object} options - Opções de formatação
     * @returns {string} - Data formatada
     */
    formatDate: function(date, options = {}) {
        const locale = this.getLocale();
        const dateObj = date instanceof Date ? date : new Date(date);
        
        const defaultOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        return new Intl.DateTimeFormat(locale, finalOptions).format(dateObj);
    },
    
    /**
     * Obtém o código locale completo do idioma atual
     * @returns {string} - Código locale
     */
    getLocale: function() {
        const localeMap = {
            'pt-BR': 'pt-BR',
            'en': 'en-US',
            'es': 'es-ES',
            'fr': 'fr-FR'
        };
        
        return localeMap[this.currentLanguage] || 'pt-BR';
    }
};

document.addEventListener('DOMContentLoaded', function() {
    I18n.init();
});

window.I18n = I18n;

console.log('L.A.A.R.I i18n system loaded');
