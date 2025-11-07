# L.A.A.R.I - Laboratório e Acervo Arqueológico Remoto Integrado

## Overview
L.A.A.R.I (Integrated Remote Archaeological Laboratory and Collection) is a Flask-based archaeological management system. Its primary purpose is to centralize and streamline documentation, cataloging, collection management, and inventory control for archaeological findings. The system aims to facilitate communication between field and laboratory teams through digital tools for artifact management, professional networking, transportation tracking, and 3D scanning integration. This web-based application provides a comprehensive solution for managing archaeological data, enhancing collaboration, and preserving cultural heritage digitally.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
-   **Template Engine**: Jinja2 with Flask
-   **UI Framework**: Bootstrap 5.3.0 for responsive design
-   **Custom Styling**: Archaeological-themed CSS with a custom color palette (#E6D2B7 beige, #5F3A1F brown)
-   **Typography**: Kelly Slab font for an archaeological aesthetic
-   **Icons**: Font Awesome 6.4.0 for consistent iconography
-   **Internationalization (i18n)**: Client-side JavaScript-based system supporting Portuguese (pt-BR), English (en), Spanish (es), and French (fr), with dynamic DOM updates and language persistence.

### Technical Implementations
-   **Web Framework**: Flask with SQLAlchemy ORM
-   **Database Layer**: SQLAlchemy with DeclarativeBase for model definitions
-   **Authentication**: Flask-Login for session management and role-based access (admin/regular users).
-   **Form Handling**: FlaskWTF for form validation and CSRF protection.
-   **File Uploads**: Secure handling with Werkzeug, UUID-based filenames, and support for images (jpg, jpeg, png, gif) and 3D models (obj, ply, stl, fbx) up to 16MB.
-   **Conditional Fields**: Dynamic display of academic information fields based on user account type (Professional, University, Student).
-   **Middleware**: ProxyFix for deployment behind reverse proxies.

### Feature Specifications
-   **User Management**: Registration with distinct account types (Professional, University, Student) and conditional academic information capture.
-   **Artifact Management**: Cataloging with support for metadata, photo, and 3D model uploads, and QR code generation.
-   **Professional Directory**: Management of archaeological specialists with contact information, including LinkedIn and Currículo Lattes profiles.
-   **Transportation Tracking**: System for tracking the movement of artifacts.
-   **3D Digitization Records**: Integration for 3D scanner data (referenced in forms).

### System Design Choices
-   **Database**: PostgreSQL, configured via `DATABASE_URL` environment variable, with connection pooling.
-   **Security**: CSRF protection, secure file handling, and role-based access control.
-   **Deployment**: Environment variable-driven configuration for session secrets and database, with proxy support.

## External Dependencies

### Core Libraries
-   **Flask**: Web application framework.
-   **SQLAlchemy**: ORM for database interaction.
-   **Flask-Login**: User authentication and session management.
-   **Flask-WTF**: Form handling, validation, and CSRF protection.
-   **WTForms**: Form validation and rendering.
-   **Werkzeug**: WSGI utilities and security functions.

### Frontend Libraries (via CDN)
-   **Bootstrap 5.3.0**: CSS framework.
-   **Font Awesome 6.4.0**: Icon library.
-   **Google Fonts**: Kelly Slab typography.

### Database
-   **PostgreSQL**: Replit-managed database.

## Recent Changes

### 2025-11-07: Fixed Team Photo Upload System
**Issue**: The team photo upload form in the dashboard would show a preview when an image was selected, but the gallery would not reload after a successful upload due to JavaScript scope issues.

**Solution**: 
- Modified `templates/dashboard.html` to expose the `loadGalleryPhotos` function globally via `window.LAARI.reloadGallery()`
- Added a `forceReload` parameter to allow forcing a gallery refresh
- Updated the upload form submission handler to call the global reload function instead of local scoped variables
- This ensures the gallery automatically refreshes after uploading a new team photo without requiring a page reload

**Files Modified**:
- `templates/dashboard.html` - Fixed JavaScript scope issues in the gallery and upload form handlers

**Testing**:
- Created admin user (admin@laari.com / admin123) for testing upload functionality