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
-   **File Uploads**: Secure handling with Werkzeug, UUID-based filenames, and support for images (jpg, jpeg, png, gif) and 3D models (obj, ply, stl, fbx) up to 16MB. File uploads are persistent using Replit Object Storage.
-   **Conditional Fields**: Dynamic display of academic information fields based on user account type (Professional, University, Student).
-   **Middleware**: ProxyFix for deployment behind reverse proxies.

### Feature Specifications
-   **User Management**: Registration with distinct account types (Professional, University, Student) and conditional academic information capture. Includes a comprehensive account verification system with status tracking ("Em análise", "Aprovado", "Rejeitado") and multilingual notifications. Rejected accounts are automatically deactivated.
-   **Artifact Management**: Cataloging with support for metadata, photo, and 3D model uploads, QR code generation, and full edit/delete functionality (creator or admin only).
-   **Professional Directory**: Management of archaeological specialists with contact information, including LinkedIn and Currículo Lattes profiles. Includes full edit/delete functionality (admin only).
-   **Transportation Tracking**: System for tracking the movement of artifacts.
-   **3D Digitization Records**: Integration for 3D scanner data, including manual upload of professional scans. Features Three.js-based interactive viewer with rotation, zoom, and pan controls.
-   **Excel Import**: Fully functional feature for importing artifact data from Excel spreadsheets (.xlsx, .xls) and CSV files. Implements a 5-step workflow: Upload, Validation, Preview, Confirmation, and Cataloging. Includes intentional limitations (100 artifacts per file, 12 standardized columns) and user guarantees (data preservation, reversibility, import history with batch IDs). Designed to facilitate gradual transition from traditional spreadsheet-based documentation.
-   **User Session Monitoring**: Real-time tracking of user sessions for administrators. Features include: active users count, login history with timestamps, session duration tracking, automatic session expiration (30 min timeout), and logout type classification (manual, expired, forced). Accessible via `/admin/monitoramento` with auto-refresh every 30 seconds.

### System Design Choices
-   **Database**: PostgreSQL, configured via `DATABASE_URL` environment variable, with connection pooling.
-   **Security**: CSRF protection, secure file handling, role-based access control, and path traversal prevention for file serving.
-   **Deployment**: Environment variable-driven configuration, with Gunicorn for production and Replit Object Storage for persistent file storage.

## External Dependencies

### Core Libraries
-   **Flask**: Web application framework.
-   **SQLAlchemy**: ORM for database interaction.
-   **Flask-Login**: User authentication and session management.
-   **Flask-WTF**: Form handling, validation, and CSRF protection.
-   **WTForms**: Form validation and rendering.
-   **Werkzeug**: WSGI utilities and security functions.
-   **Gunicorn**: WSGI HTTP Server for production deployment.

### Frontend Libraries (via CDN)
-   **Bootstrap 5.3.0**: CSS framework.
-   **Font Awesome 6.4.0**: Icon library.
-   **Google Fonts**: Kelly Slab typography.

### Database
-   **PostgreSQL**: Replit-managed database.

### Storage
-   **Cloudinary**: For persistent image and file storage (profile photos, artifact images, 3D models).
-   **Replit Object Storage**: Fallback for local development.

### 3D Visualization
-   **Three.js**: WebGL-based 3D model viewer for GLB/GLTF files with orbit controls.