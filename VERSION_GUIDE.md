# Bloomberg Volatility Surface - Version Guide

## Overview
This repository contains multiple versions of the Bloomberg Volatility Surface application with different feature sets. This guide helps you understand which version to use.

## Repository Structure

### Our Repository: `Mich120232024/bloomberg-volatility-component`
- **Origin**: https://github.com/Mich120232024/bloomberg-volatility-component.git
- **Purpose**: Our development and production versions

### Branches & Versions

#### `main` Branch - Complete Version (7 Tabs) ✅ NEW STANDARD
- **Tabs**: Volatility Surface, Historical Analysis, Volatility Analysis, **Yield Curves**, **FX Forwards**, **Option Pricing**, **Portfolio**
- **Status**: Full-featured production version ✅ CURRENT RUNNING VERSION
- **Use Case**: Complete trading and analysis platform

#### `archive/original-5-tab-main` Branch - Original Basic Version (5 Tabs)
- **Tabs**: Volatility Surface, Historical Analysis, Volatility Analysis, Rate Curves, Options Pricing
- **Status**: Archived original version for reference
- **Use Case**: Reference for original simple implementation

#### `feature/bloomberg-data-fixes` Branch - Development
- **Status**: Development branch with ongoing fixes
- **Purpose**: Experimental features and bug fixes

## External References

### GZCIM Repository: `GZCIM/bloomberg-volatility-surface`
- **Remote**: `gzcim-prod` 
- **Purpose**: Original/reference version (not linked to our development)
- **Copy Location**: `/Users/mikaeleage/GZC Intel Workspace/projects/gzcim-apps/bloomberg-volatility-surface/`

## Current Status

### ✅ Running Version
- **Branch**: `main` (now contains complete 7-tab version)
- **URL**: http://localhost:3501
- **Features**: All 7 tabs including Yield Curves, FX Forwards, and Portfolio

### Key Features by Version

| Feature | Archive (5-tab) | Main (7-tab) |
|---------|-------------|-------------------|
| Volatility Surface | ✅ | ✅ |
| Historical Analysis | ✅ | ✅ |
| Volatility Analysis | ✅ | ✅ |
| Rate Curves | ✅ | ✅ |
| Options Pricing | ✅ | ✅ |
| **Yield Curves** | ❌ | ✅ |
| **FX Forwards** | ❌ | ✅ |
| **Portfolio** | ❌ | ✅ |

## Development Commands

```bash
# Run the complete version (main branch - default)
git checkout main
npm run dev

# Switch to archived basic version (if needed)
git checkout archive/original-5-tab-main
npm run dev

# Check current version
git branch --show-current
```

## Deployment Strategy

1. **Development**: Use `main` branch (complete 7-tab version)
2. **Testing**: All features available in main branch
3. **Production**: Main branch is production-ready
4. **No Git Linking**: GZCIM copy is standalone, no repository connection

## Bloomberg API Integration

All versions connect to:
- **Primary**: http://20.172.249.92:8080 (Bloomberg VM)
- **Local Gateway**: http://localhost:8000 (when running bloomberg-gateway-enhanced.py)

---

**Last Updated**: 2025-08-05  
**Current Running Version**: `main` (complete 7-tab version)