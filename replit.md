# L.A.A.R.I - Laboratório e Acervo Arqueológico Remoto Integrado

## Overview

L.A.A.R.I is a comprehensive archaeological management system built with Flask that centralizes documentation, cataloging, collection management, and inventory control. The application facilitates communication between field teams and laboratory staff by providing digital tools for artifact management, professional networking, transportation tracking, and 3D scanning integration. The system uses a web-based interface with Bootstrap styling and includes features for user authentication, artifact cataloging with photo/3D model uploads, professional directory management, and administrative controls.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Flask
- **UI Framework**: Bootstrap 5.3.0 for responsive design
- **Custom Styling**: Archaeological-themed CSS with custom color palette (#E6D2B7 beige, #5F3A1F brown)
- **Typography**: Kelly Slab font for archaeological aesthetic
- **Icons**: Font Awesome 6.4.0 for consistent iconography
- **JavaScript**: Vanilla JavaScript for interactive features (tooltips, modals, form validation, file uploads)

### Backend Architecture
- **Web Framework**: Flask with SQLAlchemy ORM
- **Database Layer**: SQLAlchemy with DeclarativeBase for model definitions
- **Authentication**: Flask-Login for session management
- **Form Handling**: FlaskWTF for form validation and CSRF protection
- **File Uploads**: Werkzeug secure filename handling with UUID generation
- **Middleware**: ProxyFix for deployment behind reverse proxies

### Database Design
- **User Model**: Authentication with role-based access (admin/regular users), account type selection (Professional/University/Student), and conditional academic information fields (university, course, entry year, institution type, location)
- **Artifact Model**: Core entity with metadata, photos, 3D models, and QR codes
- **Professional Model**: Directory of archaeological specialists
- **Transport Model**: Movement tracking for artifacts
- **Scanner3D Model**: 3D digitization records (referenced in forms but not in models.py)
- **Relationships**: User-to-Artifact cataloging relationship established

### Authentication & Authorization
- **Login System**: Email/password authentication with Flask-Login
- **User Registration**: New user account creation with three account types:
  - **Professional Account**: For professional archaeologists and researchers
  - **University Account**: For university students with mandatory academic information
  - **Student Account**: For students with mandatory academic information
- **Academic Information**: Conditional form fields displayed only for University and Student accounts including:
  - University selection from comprehensive list (Brazil, USA, UK, Canada, Spain, France, Mexico) with custom entry option
  - Course/Study area
  - Entry year
  - Institution type (Public/Private)
  - Location (City, State, Country)
- **Role Management**: Admin users with elevated privileges
- **Session Management**: Secure session handling with configurable secret keys
- **Access Control**: Login-required decorators for protected routes
- **Form Validation**: JavaScript-powered conditional field display and server-side validation ensuring all academic fields are mandatory for student/university accounts

### File Management System
- **Upload Handling**: Secure file uploads with extension validation
- **Storage Structure**: Organized upload directory with UUID-based filenames
- **File Types**: Support for images (jpg, jpeg, png, gif) and 3D models (obj, ply, stl, fbx)
- **Size Limits**: 16MB maximum file size configuration

## External Dependencies

### Core Dependencies
- **Flask**: Web application framework
- **SQLAlchemy**: Database ORM and connection management
- **Flask-Login**: User session and authentication management
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form validation and rendering
- **Werkzeug**: WSGI utilities and security functions

### Frontend Dependencies
- **Bootstrap 5.3.0**: CSS framework via CDN
- **Font Awesome 6.4.0**: Icon library via CDN
- **Google Fonts**: Kelly Slab typography via CDN

### Database Configuration
- **Database**: PostgreSQL (Replit-managed)
- **Configuration**: Via DATABASE_URL environment variable
- **Connection Pooling**: Configured with pool_recycle and pool_pre_ping options
- **Schema**: User table includes account_type, university, university_custom, course, entry_year, institution_type, city, state, and country columns

### Deployment Considerations
- **Environment Variables**: SESSION_SECRET and DATABASE_URL for configuration
- **Proxy Support**: ProxyFix middleware for reverse proxy deployments
- **Debug Mode**: Configurable debug settings for development
- **Host Binding**: 0.0.0.0 binding for container deployments

### Internationalization (i18n)
- **Supported Languages**: Portuguese (pt), English (en), Spanish (es), French (fr)
- **Language Selector**: Dropdown menu with flag emojis (🇧🇷 🇬🇧 🇪🇸 🇫🇷) in navigation
- **Translation System**: Simple dictionary-based translation function (_) injected into template context
- **Language Detection**: Automatic browser language detection with session-based persistence
- **Translation Coverage**: All interface elements including menus, buttons, forms, labels, messages, and content
- **Translation Examples**: 
  - "Pesquisar por Sítio Arqueológico" → "Search by Archaeological Site" (EN) / "Buscar por Sitio Arqueológico" (ES) / "Rechercher par Site Archéologique" (FR)
  - Dashboard, Cataloging, Collection, Scanner 3D, Professionals, Inventory, Transport modules fully translated

## Recent Changes

**Date:** October 24, 2025
- **Multilingual Support**: Implemented comprehensive multilingual system with 4 languages (Portuguese, English, Spanish, French)
- **Flag-Based Language Selector**: Added visual language selector with country flag emojis in navigation menu
- **Translation Dictionary**: Created extensive translation dictionary with 100+ terms covering all major system modules
- **Admin Account**: Created administrator account (roboticos415f2@gmail.com)
- **Form Improvements**: Added autocomplete attributes to login/register forms for better UX