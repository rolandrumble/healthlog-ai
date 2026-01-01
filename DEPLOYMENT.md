# HealthLog AI - Deployment Guide

## Quick Start Deployment (Railway)

This guide will help you deploy HealthLog AI to Railway with all bug fixes applied.

---

## Prerequisites

- GitHub account with the healthlog-ai repository
- Railway.app account (sign up at https://railway.app)
- Groq API key (get free at https://console.groq.com)
- Supabase account (optional, for cloud database)

---

## Step 1: Prepare Your Repository

All fixes have been applied to the repository. Verify these files are updated:

- ✅ `/static/js/app.js` - Fixed API URL configuration
- ✅ `/static/js/dashboard.js` - Fixed API URL configuration
- ✅ `.env.example` - Environment variables template
- ✅ `/server/main.py` - Backend with proper database support

---

## Step 2: Set Up Supabase (Recommended for Production)

### Option A: Use Provided Supabase Project

If using the provided Supabase credentials:

```
Project URL: https://your-project.supabase.co
Anon Key: your_anon_key_here
Service Role Key: your_service_role_key_here
```

### Option B: Create Your Own Supabase Project

1. Go to https://supabase.com
2. Click "New Project"
3. Fill in project details
4. Wait for project to initialize
5. Go to Settings → API Keys
6. Copy `anon public` and `service_role` keys

---

## Step 3: Deploy to Railway

### Method 1: Using Railway Dashboard (Easiest)

1. **Go to Railway.app**
   - Sign in to your Railway account
   - Go to https://railway.app/dashboard

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub
   - Select `rolandrumble/healthlog-ai` repository

3. **Configure Environment Variables**
   - Railway will auto-detect the repository
   - Go to the project settings
   - Click "Variables" tab
   - Add the following environment variables:

```
DATABASE_TYPE=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your-secret-key-change-this-in-production
```

4. **Deploy**
   - Railway will automatically deploy after variables are set
   - Wait 2-3 minutes for deployment to complete
   - You'll see a green checkmark when ready

5. **Get Your URL**
   - Go to "Deployments" tab
   - Copy the deployment URL (e.g., `https://web-production-xxxx.up.railway.app`)

---

### Method 2: Using Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init

# Add environment variables
railway variables set DATABASE_TYPE=supabase
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set SUPABASE_KEY=your_anon_key_here
railway variables set SUPABASE_SERVICE_KEY=your_service_role_key_here
railway variables set GROQ_API_KEY=your_groq_api_key_here
railway variables set SECRET_KEY=your-secret-key

# Deploy
railway up
```

---

## Step 4: Verify Deployment

After deployment completes:

1. **Open your app URL**
   - Go to `https://your-railway-url.up.railway.app`

2. **Test Signup**
   - Click "Get Started"
   - Create a test account
   - Should see success message

3. **Test Login**
   - Click "Sign In"
   - Login with your test account
   - Should see dashboard

4. **Test Meal Upload**
   - Click "+ Quick Log"
   - Click "Log Meal"
   - Upload a meal photo
   - Should see nutrition analysis

5. **Check Logs**
   - Go to Railway dashboard
   - Click your project
   - Go to "Logs" tab
   - Look for any errors

---

## Step 5: Update DNS (Optional)

If you want a custom domain:

1. Go to Railway project settings
2. Click "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions

---

## Troubleshooting

### Issue: "Cannot POST /api/auth/signup"

**Solution:**
- Verify `DATABASE_TYPE=supabase` is set in Railway variables
- Check that Supabase URL and keys are correct
- Restart the deployment

### Issue: "Meal upload shows 'Analyzing...' but never completes"

**Solution:**
- Verify `GROQ_API_KEY` is set in Railway variables
- Check Railway logs for errors
- Try uploading a different image

### Issue: "Data not saving"

**Solution:**
- Verify Supabase credentials are correct
- Check that database tables exist in Supabase
- Check Railway logs for database errors

### Issue: "502 Bad Gateway"

**Solution:**
- Wait 2-3 minutes for deployment to complete
- Check Railway logs for startup errors
- Verify all environment variables are set

### Issue: "Application crashes on startup"

**Solution:**
1. Check Railway logs for error messages
2. Verify all required environment variables are set
3. Verify Python dependencies are installed
4. Check that Procfile is correct

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_TYPE` | Yes | Set to `supabase` for production |
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon public key |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service role key |
| `GROQ_API_KEY` | Yes | Groq API key for AI analysis |
| `SECRET_KEY` | No | Secret key for sessions (auto-generated if not set) |
| `TELEGRAM_BOT_TOKEN` | No | Only if using Telegram bot |
| `API_BASE_URL` | No | Only if using Telegram bot |

---

## Monitoring & Maintenance

### View Logs
1. Go to Railway dashboard
2. Click your project
3. Click "Logs" tab
4. View real-time logs

### Restart Application
1. Go to Railway dashboard
2. Click your project
3. Click "Settings"
4. Click "Restart"

### Update Application
1. Push changes to GitHub
2. Railway automatically redeploys
3. Wait 2-3 minutes for new deployment

### Scale Application
1. Go to Railway dashboard
2. Click your project
3. Click "Settings"
4. Adjust CPU and Memory as needed

---

## Security Best Practices

1. **Change SECRET_KEY**
   - Generate a new secret key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Update in Railway variables

2. **Rotate API Keys Regularly**
   - Groq API key
   - Supabase keys

3. **Monitor Logs**
   - Check for suspicious activity
   - Monitor error rates

4. **Enable HTTPS**
   - Railway provides free HTTPS
   - Always use HTTPS in production

5. **Restrict CORS**
   - Update `allow_origins` in `server/main.py`
   - Only allow your domain

---

## Performance Optimization

### Database
- Supabase handles scaling automatically
- Monitor query performance in Supabase dashboard

### API Caching
- Consider adding Redis for caching
- Cache meal analysis results

### Image Optimization
- Compress images before upload
- Limit file size to 10MB

### CDN
- Use Railway's built-in CDN
- Or configure Cloudflare

---

## Backup & Recovery

### Backup Database
1. Go to Supabase dashboard
2. Click your project
3. Go to "Backups"
4. Click "Create backup"

### Restore Database
1. Go to Supabase dashboard
2. Click your project
3. Go to "Backups"
4. Click "Restore" on desired backup

---

## Support & Resources

- **Railway Docs:** https://docs.railway.app
- **Supabase Docs:** https://supabase.com/docs
- **Groq API Docs:** https://console.groq.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com

---

## Deployment Checklist

- [ ] All fixes applied to repository
- [ ] `.env.example` created with all variables
- [ ] Supabase project set up (or using provided credentials)
- [ ] Groq API key obtained
- [ ] Railway project created
- [ ] All environment variables set in Railway
- [ ] Application deployed successfully
- [ ] Signup tested and working
- [ ] Login tested and working
- [ ] Meal upload tested and working
- [ ] Data persists after refresh
- [ ] Logs checked for errors
- [ ] Custom domain configured (optional)
- [ ] Monitoring set up

---

## Next Steps

1. **Monitor Performance**
   - Check Railway metrics
   - Monitor Supabase usage

2. **Gather User Feedback**
   - Test with real users
   - Collect feedback

3. **Plan Improvements**
   - Add new features
   - Optimize performance

4. **Scale as Needed**
   - Increase resources on Railway
   - Upgrade Supabase plan

---

**Deployment completed! Your HealthLog AI app is now live! 🚀**
