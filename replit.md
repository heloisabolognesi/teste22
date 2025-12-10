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
-   **Account Verification System**: 
    - Professional accounts must upload CV for admin review before accessing cataloging features
    - University accounts require institutional information validation before full access
    - Student accounts have basic access without cataloging permissions
    - Status tracking: "Em análise" (Under review), "Aprovado" (Approved), "Rejeitado" (Rejected)
    - Automatic account deactivation on rejection
    - Multilingual notification messages (PT, EN, ES, FR)
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

### 2025-11-07: Comprehensive Authentication and User Verification System

**Implementation Overview**:
Implemented a complete authentication and user verification system with Portuguese status values, multilingual support, and role-based access control according to the specification provided in the attached requirements document.

**Changes Made**:

**1. Database Models (models.py)**:
- Updated default status values to Portuguese:
  - `cv_status` default: "Em análise" (previously "pending")
  - `institution_status` default: "Em análise" (previously "pending")
  - Status values: "Em análise", "Aprovado", "Rejeitado"
- Fixed `can_catalog_artifacts()` method:
  - Students now correctly return `False` (no cataloging access)
  - Professionals require CV status "Aprovado"
  - Universities require institution status "Aprovado"

**2. Registration Flow (routes.py)**:
- Professional accounts: CV upload mandatory, status set to "Em análise"
- University accounts: Institutional fields required, status set to "Em análise"
- Student accounts: No verification needed, basic access only

**3. Admin Validation Routes (routes.py)**:
- Updated `validate_cv` and `validate_institution` routes:
  - Use Portuguese status values ("Aprovado", "Rejeitado")
  - Automatic account deactivation (`is_active_user = False`) on rejection
  - Multilingual flash messages in PT, EN, ES, FR for approvals and rejections

**4. Access Control (routes.py)**:
- Added permission checks to `catalogacao` and `catalogar_novo` routes
- Prevents pending users from accessing cataloging features
- Multilingual error messages explaining access denial reasons:
  - Professional: "Seu currículo ainda está em análise" / CV status messages
  - University: "Seu cadastro institucional ainda está em análise" / Institution status messages
  - Student: "Contas de estudantes não têm permissão para catalogar artefatos"

**5. Admin Interface (templates/admin.html)**:
- Updated pending validation queries to filter by "Em análise" status
- Added comprehensive status badges in user table:
  - CV status indicators (Em Análise, Aprovado, Rejeitado)
  - Institution status indicators
  - Account type badges with icons (Profissional, Universitária, Estudante)
- Enhanced visual feedback for admins

**6. Data Migration**:
- Created `migrate_status_values.py` script to update legacy English status values to Portuguese
- Script maps: 'pending' → 'Em análise', 'approved' → 'Aprovado', 'rejected' → 'Rejeitado'

**Key Features**:
- ✅ Portuguese status values throughout the system
- ✅ Multilingual support (PT, EN, ES, FR) for all user-facing messages
- ✅ Automatic account deactivation on CV/institution rejection
- ✅ Access control preventing unauthorized cataloging
- ✅ Student accounts blocked from cataloging (as per requirements)
- ✅ Comprehensive admin interface for managing verifications
- ✅ Data migration support for existing databases

**Files Modified**:
- `models.py` - Status values and access control logic
- `routes.py` - Registration, validation, and access control routes
- `templates/admin.html` - Admin interface with status displays
- `migrate_status_values.py` - Migration script for legacy data

### 2025-11-07: Enhanced Team Photo Upload System with Validation

**Issues Fixed**:
1. Gallery would not reload after successful upload due to JavaScript scope issues
2. Submit button was always enabled, allowing invalid file submissions
3. No client-side validation for file type and size
4. No visual feedback for invalid files
5. Missing multilingual error/success messages

**Solutions Implemented**:

**Part 1 - Gallery Reload Fix:**
- Modified `templates/dashboard.html` to expose the `loadGalleryPhotos` function globally via `window.LAARI.reloadGallery()`
- Added a `forceReload` parameter to allow forcing a gallery refresh
- Updated the upload form submission handler to call the global reload function
- Gallery now automatically refreshes after uploading a new team photo without requiring a page reload

**Part 2 - File Validation & UX Improvements:**
- Submit button now starts disabled and only enables when a valid file is selected
- Implemented client-side validation:
  - Valid file types: JPG, JPEG, PNG, GIF
  - Maximum file size: 5 MB
- Added visual error messages for invalid files (type or size)
- Preview image only displays for valid files
- Multilingual validation messages (Portuguese, English, Spanish, French)
- Multilingual success messages after upload
- Fixed button state management: stays disabled after successful upload until new valid file is selected
- Error states re-enable button to allow retry

**Part 3 - Modal Scroll & Button Visibility Fix:**
- Moved upload form container into modal-body to make it part of the scrollable area
- Added bottom margin (mb-4) to upload form container to prevent footer from clipping buttons
- Implemented scroll sentinel element positioned after submit buttons
- Modified JavaScript to scroll to sentinel element using `scrollIntoView({block: 'end'})`
- Ensures "Enviar Foto" button is always visible on both mobile and desktop screens
- Smooth scroll animation with proper focus management
- Responsive behavior tested across different viewport sizes

**Files Modified**:
- `templates/dashboard.html` - Complete upload form validation, multilingual messaging, and scroll fix

### 2025-11-07: Production Deployment Configuration

**Issues Fixed**:
- Deployment failure due to missing database configuration
- Application attempting to connect to local development database ("helium") in production environment
- Database connection errors preventing successful deployment

**Solutions Implemented**:

**1. Database Setup**:
- Created PostgreSQL database using Replit's managed database service
- Configured DATABASE_URL environment variable for production
- Environment variables automatically provisioned: DATABASE_URL, PGPORT, PGUSER, PGPASSWORD, PGDATABASE, PGHOST

**2. Deployment Configuration**:
- Configured autoscale deployment target (suitable for stateless web applications)
- Set production run command: `gunicorn --bind=0.0.0.0:5000 --reuse-port main:app`
- Ensured secure, production-ready server configuration

**3. Database Migration**:
- Recreated database schema in production PostgreSQL database
- Recreated admin user account with same credentials
- Verified all tables created successfully

**Key Features**:
- ✅ PostgreSQL database configured for production deployment
- ✅ Autoscale deployment for efficient resource usage
- ✅ Gunicorn WSGI server for production stability
- ✅ Database environment variables properly configured
- ✅ Admin user recreated in production database

**Files Modified**:
- Deployment configuration via deploy_config_tool
- Database provisioned via create_postgresql_database_tool

**Admin Credentials** (Production):
- Email: roboticos415f2@gmail.com
- Password: 24062025
- Type: Administrator

### 2025-11-12: Favicon Integration

**Changes Made**:
- Added Tech Era team logo as site favicon
- Favicon file: `static/Logo TE Roxo e Verde.ico`
- Added favicon link tag to `templates/base.html` in the `<head>` section
- Favicon appears on all pages (all templates extend base.html)

**Files Modified**:
- `templates/base.html` - Added favicon link tag
- `static/Logo TE Roxo e Verde.ico` - Team logo favicon file

### 2025-12-10: Replit Object Storage Migration

**Issues Fixed**:
- User-uploaded files (artifacts, professionals, gallery photos) not persisting in production deployment
- Local filesystem storage is ephemeral in Replit's production environment
- Files uploaded in production were lost after deployment restarts

**Solutions Implemented**:

**1. Object Storage Integration**:
- Created `storage.py` utility module with functions:
  - `upload_file(file, folder)` - Uploads files to Object Storage with UUID-based naming
  - `download_file(file_path)` - Downloads file bytes from Object Storage
  - `file_exists(file_path)` - Checks if file exists in storage
  - `get_content_type(file_path)` - Returns MIME type based on file extension
  - `is_object_storage_available()` - Checks if Object Storage is initialized

**2. File Serving Route**:
- Created `/storage/<path:file_path>` route to serve files from Object Storage
- Implements local fallback for development with proper security
- Security hardening: Path traversal prevention with safe_join and explicit validation
- Proper MIME type detection and caching headers

**3. Template Updates**:
- Updated all templates to use `url_for('serve_storage_file', file_path=...)` instead of static file references
- Templates updated: catalogacao.html, acervo.html, profissionais.html, galeria.html, perfil_profissional.html, admin_galeria.html, inventario.html
- JavaScript updates in index.html and dashboard.html for dynamic gallery loading

**4. Security Measures**:
- Reject paths containing '..' or starting with '/'
- Use werkzeug.utils.safe_join for local fallback paths
- Abort with 403 on any path traversal attempts

**Key Features**:
- ✅ Persistent file storage using Replit Object Storage (99.999999999% durability)
- ✅ Automatic MIME type detection for images
- ✅ Secure file serving with path traversal prevention
- ✅ Local development fallback for testing
- ✅ One-year browser caching for performance

**Files Modified**:
- `storage.py` - New utility module for Object Storage operations
- `routes.py` - Updated save_uploaded_file and added serve_storage_file route
- Multiple templates updated for new storage route