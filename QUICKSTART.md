# 🚀 CLEAROID - QUICK START GUIDE

## ✅ System Status
All components tested and working:
- ✅ Database connection
- ✅ Backend routes (auth, titles, excel, admin)
- ✅ Services (embedding, title processing)
- ✅ Frontend files (all pages present)
- ✅ FastAPI application

## 🎯 Start Server

### Option 1: Using startup script
```bash
./start_server.sh
```

### Option 2: Manual start
```bash
source venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 🌐 Access URLs

| Page | URL |
|------|-----|
| Dashboard | http://localhost:8000/pages/dashboard.html |
| Sign In | http://localhost:8000/pages/signin.html |
| Upload | http://localhost:8000/pages/upload.html |
| Data Viewer | http://localhost:8000/pages/data.html |
| Export | http://localhost:8000/pages/export.html |
| API Docs | http://localhost:8000/docs |

## 🔑 Demo Account
- Email: `demo@clearoid.com`
- Password: `demo123`

## 📁 Project Structure
```
Testing-files--main/
├── backend/
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   ├── utils/           # Utilities
│   └── main.py          # FastAPI app
├── database/
│   ├── models/          # SQLAlchemy models
│   ├── connection.py    # DB setup
│   └── titles.db        # SQLite database
├── frontend/
│   ├── pages/           # HTML pages
│   └── assets/css/      # Stylesheets
├── start_server.sh      # Quick start script
└── test_server.py       # Test all components
```

## 🧪 Test Everything
```bash
source venv/bin/activate
python test_server.py
```

## 🔧 Troubleshooting

### Port already in use
```bash
lsof -ti:8000 | xargs kill -9
```

### Missing dependencies
```bash
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Database issues
```bash
rm database/titles.db
python -c "from database.connection import Base, engine; Base.metadata.create_all(bind=engine)"
```

## 📊 API Endpoints

### Authentication
- POST `/auth/signup` - Create account
- POST `/auth/signin` - Sign in

### Titles
- POST `/api/submit` - Submit title
- POST `/api/check-duplicate` - Check for duplicates
- GET `/api/history` - Get submission history
- GET `/api/stats` - Get statistics

### Excel Upload
- POST `/excel/bulk-upload` - Upload Excel/CSV file

### Admin
- GET `/admin/stats` - Get admin statistics

## 💡 Tips
- Use the demo account for quick testing
- Upload Excel files with a "title" column
- Check `/docs` for interactive API documentation
- All frontend files are in `frontend/pages/`
- Database is SQLite at `database/titles.db`
