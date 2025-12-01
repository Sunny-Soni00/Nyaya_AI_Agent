// API Configuration
// Change this URL to your Render backend URL after deployment
const CONFIG = {
    API_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'  // Local development
        : 'https://your-render-app.onrender.com'  // Production (Update this after deploying to Render)
};
