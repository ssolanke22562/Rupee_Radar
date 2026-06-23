# RupeeRadar Deployment Guide

This guide explains how to deploy the RupeeRadar FastAPI backend on **Railway** and the React frontend on **Vercel**.

---

## 1. Backend Deployment (Railway)

The backend is built with FastAPI and runs in a Docker container using PostgreSQL as the persistent database.

### Step-by-Step Instructions:

1. **Log in to Railway**:
   - Go to [railway.app](https://railway.app/) and sign in.

2. **Create a New Project**:
   - Click **New Project** -> **Deploy from GitHub repo**.
   - Select your `Rupee_Radar` repository.

3. **Configure Build Settings**:
   - Railway will automatically detect the `railway.json` configuration file at the root.
   - It will build the backend using `Dockerfile.backend` and start the Uvicorn server on the correct port.

4. **Add PostgreSQL database**:
   - Inside your Railway project workspace, click **+ New** -> **Database** -> **Add PostgreSQL**.
   - Railway will automatically provision the database and inject the `DATABASE_URL` environment variable into your backend service.

5. **Set Environment Variables**:
   - Go to your backend service's **Variables** tab in Railway and add:
     * `GROQ_API_KEY`: Your Groq Cloud API Key (required for statement categorization and insights).
     * `GROQ_MODEL`: `llama-3.1-8b-instant` (or your preferred Llama model).
     * `CORS_ORIGINS`: Set this to your frontend Vercel URL (e.g. `https://rupee-radar.vercel.app`) or use `*` to allow all origins.
     * `SESSION_TTL_HOURS`: `24` (optional, determines how long data remains before auto-purging).

6. **Generate a Domain**:
   - Go to the backend service's **Settings** tab.
   - Under **Networking**, click **Generate Domain** (or set a custom one).
   - Copy this URL (e.g. `https://rupee-radar-production.up.railway.app`). You will need it for the frontend.

---

## 2. Frontend Deployment (Vercel)

The React client is built using Vite and deployed as a static site on Vercel. Thanks to our root-level workspaces configuration, it deploys automatically without needing manual folder routing on the Vercel dashboard.

### Step-by-Step Instructions:

1. **Log in to Vercel**:
   - Go to [vercel.com](https://vercel.com/) and sign in.

2. **Import Repository**:
   - Click **Add New** -> **Project**.
   - Select your `Rupee_Radar` repository.

3. **Configure Project Settings**:
   - Vercel will automatically detect the root `package.json` and select the configuration.
   - **Build Command**: `npm run build` (runs from the root to build the frontend workspace).
   - **Output Directory**: `frontend/dist` (automatically routed by `vercel.json`).
   - **Root Directory**: Leave it as the project root (default `./`).

4. **Configure Environment Variables**:
   - Expand the **Environment Variables** section.
   - Add the following variable:
     * **Key**: `VITE_API_BASE_URL`
     * **Value**: Your Railway backend API URL ending with `/api/v1` (e.g., `https://rupee-radar-production.up.railway.app/api/v1`).
   - *Note: Vite injects environment variables at build-time, so this environment variable must be set before deploying.*

5. **Deploy**:
   - Click **Deploy**. Vercel will install dependencies, build the frontend, and serve it.
