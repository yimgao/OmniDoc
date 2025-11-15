# OmniDoc Documentation Index

Welcome to the OmniDoc documentation! This index helps you find the information you need.

## 📚 Documentation Structure

All documentation is now in the project root for easy access:

### Getting Started
- **[README.md](README.md)** - Main documentation with quick start guide
  - What is OmniDoc?
  - Installation and setup
  - Basic usage examples
  - Project structure

### Backend Documentation
- **[BACKEND.md](BACKEND.md)** - Complete backend documentation
  - Quick start guide
  - Architecture overview
  - API reference
  - Core components
  - Database schema
  - Task queue configuration
  - Troubleshooting
  - Development guide

### Production Deployment
- **[README_PRODUCTION.md](README_PRODUCTION.md)** - Production deployment guide
  - Production features overview
  - Architecture diagram
  - Docker deployment
  - Security checklist

- **[PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)** - Detailed production setup
  - Step-by-step setup instructions
  - System dependencies
  - Configuration guide
  - Monitoring and troubleshooting

- **[ORACLE_CLOUD_DEPLOYMENT.md](ORACLE_CLOUD_DEPLOYMENT.md)** - Oracle Cloud Free Tier deployment
  - Complete step-by-step guide for OCI
  - Nginx configuration
  - SSL/HTTPS setup
  - Systemd service configuration
  - Oracle Cloud specific notes

- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist
  - Pre-deployment verification
  - Security checklist
  - Post-deployment verification
  - Quick reference commands

### Frontend Documentation
- **[FRONTEND.md](FRONTEND.md)** - Complete frontend guide
  - Next.js architecture
  - Component documentation
  - Internationalization (i18n)
  - API integration
  - Development and troubleshooting

### Security Documentation
- **[SECURITY.md](SECURITY.md)** - Security guide
  - Authentication & authorization
  - Database security
  - Redis security
  - CORS configuration
  - Input validation
  - Security checklist
  - Incident response

### Maintenance Documentation
- **[MAINTENANCE.md](MAINTENANCE.md)** - Maintenance guide
  - Regular maintenance tasks
  - Backup & recovery
  - Monitoring & health checks
  - Performance optimization
  - Troubleshooting
  - Updates & upgrades

### Code Improvements
- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - Code improvement recommendations
  - Critical issues and fixes
  - Medium priority improvements
  - Code quality enhancements
  - Performance optimizations
  - Security improvements

### Quality Assurance
- **[docs/QUALITY_SCORING.md](docs/QUALITY_SCORING.md)** - Quality scoring system
  - How quality scores are calculated
  - Automated metrics (word count, sections, readability)
  - LLM-as-Judge evaluation
  - Quality rules configuration (`quality_rules.json`)
  - Auto-fail rules and improvement workflow

## 🗂️ Quick Reference

### For New Users
1. Start with [README.md](README.md)
2. Follow the Quick Start guide
3. Check [BACKEND.md](BACKEND.md) for API details

### For Developers
1. [README.md](README.md) - Project structure and development setup
2. [BACKEND.md](BACKEND.md) - API and architecture
3. [FRONTEND.md](FRONTEND.md) - Frontend development
4. Code examples in the main README

### For DevOps/Deployment
1. [README_PRODUCTION.md](README_PRODUCTION.md) - Overview and architecture
2. [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md) - Detailed setup steps
3. [ORACLE_CLOUD_DEPLOYMENT.md](ORACLE_CLOUD_DEPLOYMENT.md) - Oracle Cloud deployment
4. [SECURITY.md](SECURITY.md) - Security configuration
5. [MAINTENANCE.md](MAINTENANCE.md) - Maintenance procedures

## 🔍 Finding Information

### I want to...
- **Install OmniDoc**: See [README.md - Quick Start](README.md#-quick-start)
- **Configure the backend**: See [BACKEND.md](BACKEND.md)
- **Understand the frontend**: See [FRONTEND.md](FRONTEND.md)
- **Deploy to production**: See [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md) or [ORACLE_CLOUD_DEPLOYMENT.md](ORACLE_CLOUD_DEPLOYMENT.md)
- **Configure security**: See [SECURITY.md](SECURITY.md)
- **Maintain the system**: See [MAINTENANCE.md](MAINTENANCE.md)
- **Understand the architecture**: See [README.md - Architecture](README.md#-architecture)
- **Troubleshoot issues**: See [BACKEND.md - Troubleshooting](BACKEND.md#-troubleshooting) or [MAINTENANCE.md - Troubleshooting](MAINTENANCE.md#-troubleshooting)
- **Use the API**: See [BACKEND.md - API Endpoints](BACKEND.md#-api-endpoints)
- **Understand quality scoring**: See [docs/QUALITY_SCORING.md](docs/QUALITY_SCORING.md)
- **Customize quality rules**: See [docs/QUALITY_SCORING.md - Configuration](docs/QUALITY_SCORING.md#configuration) and `src/config/quality_rules.json`

## 📝 Document Status

All documentation has been updated and cleaned:
- ✅ Removed outdated migration plans
- ✅ Removed duplicate example documents
- ✅ Consolidated information into clear guides
- ✅ Updated with latest production features
- ✅ All documentation moved to project root

## 💡 Tips

- **API Documentation**: When the backend is running, visit `http://localhost:8000/docs` for interactive API documentation
- **Environment Variables**: All configuration is done via `.env` file
- **Setup Script**: Use `./scripts/setup.sh` for automatic setup

---

**Need Help?** Check the troubleshooting sections in each document or open an issue on GitHub.

