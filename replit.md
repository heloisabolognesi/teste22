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

**Files Modified**:
- `templates/dashboard.html` - Complete upload form validation and multilingual messaging

**Testing**:
- Created admin users for testing:
  - admin@laari.com / admin123
  - roboticos415f2@gmail.com / 24062025