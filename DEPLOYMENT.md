# Deployment Guide

## Frontend - GitHub Pages

### Setup Steps:
1. **Repository Settings:**
   - Go to: https://github.com/Sunny-Soni00/Nyaya_AI_Agent/settings/pages
   - Under "Build and deployment"
   - Source: Deploy from a branch
   - Branch: `gh-pages` / `/ (root)`
   - Click Save

2. **Your site will be live at:**
   ```
   https://sunny-soni00.github.io/Nyaya_AI_Agent/
   ```

3. **Access pages:**
   - Login: https://sunny-soni00.github.io/Nyaya_AI_Agent/frontend/index.html
   - Meeting: https://sunny-soni00.github.io/Nyaya_AI_Agent/frontend/meeting.html

## Backend - Render

### Setup Steps:
1. **Create New Web Service:**
   - Go to: https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `Sunny-Soni00/Nyaya_AI_Agent`

2. **Configure Service:**
   - **Name:** nyaya-sahayak-backend (or your choice)
   - **Region:** Choose closest to your users
   - **Branch:** main
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables:**
   Add these in Render dashboard:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   ```

4. **Copy Backend URL:**
   After deployment, Render will give you a URL like:
   ```
   https://nyaya-sahayak-backend.onrender.com
   ```

5. **Update Frontend Config:**
   - Edit `frontend/config.js`
   - Replace `'https://your-render-app.onrender.com'` with your actual Render URL
   - Commit and push to `gh-pages` branch:
   ```bash
   git add frontend/config.js
   git commit -m "Update production API URL"
   git push origin gh-pages
   ```

## Post-Deployment

### Update CORS (Recommended):
Edit `backend/main.py` line 21:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sunny-soni00.github.io"],  # Your GitHub Pages URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Test Deployment:
1. Open: https://sunny-soni00.github.io/Nyaya_AI_Agent/frontend/index.html
2. Create a meeting
3. Test features: Video, Transcript, Evidence, Criminal Records, AI Chat
4. (As Judge) Test Report Generation

## Troubleshooting

### Frontend not loading:
- Check GitHub Pages is enabled in settings
- Verify gh-pages branch exists
- Wait 2-3 minutes for deployment
- Clear browser cache

### Backend connection errors:
- Verify Render service is running (not sleeping)
- Check environment variables are set
- Check backend logs in Render dashboard
- Verify CORS allows your frontend URL

### WebRTC/Video issues:
- Ensure HTTPS is used (GitHub Pages provides this)
- Check browser permissions for camera/microphone
- Test in Chrome/Edge (best WebRTC support)

## Free Tier Limits

### Render Free Tier:
- ⚠️ Service sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake
- 750 hours/month free
- Consider upgrading for production use

### GitHub Pages:
- ✅ Unlimited for public repositories
- 100 GB bandwidth/month
- Perfect for static frontend

## Cost-Free Alternative

For completely free hosting:
- Keep current setup (GitHub Pages + Render Free)
- Or use Vercel/Netlify for frontend (also free)
- Accept cold start delay on Render free tier
