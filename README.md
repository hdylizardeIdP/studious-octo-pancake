# Grocery List Application

Smart grocery list manager with real-time collaboration, offline support, and intelligent document parsing.

## Features

- ✅ Create and manage multiple grocery lists
- ✅ Real-time collaboration (multiple users can edit simultaneously)
- ✅ Offline-first PWA (works without internet)
- ✅ Shopping mode (optimized for in-store use)
- 📄 Document upload (text, Word, PDF)
- 🖼️ Image parsing with OCR
- 🎤 Voice input (coming soon)
- 📱 Progressive Web App (installable on mobile)

## Tech Stack

### Frontend
- **React 18** + **TypeScript**
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Zustand** - State management
- **React Router** - Navigation
- **Supabase JS** - Real-time DB and auth
- **Dexie.js** - Offline storage (IndexedDB)
- **Workbox** - Service worker for PWA

### Backend
- **Python 3.10+**
- **FastAPI** - REST API framework
- **python-docx** - Word document parsing
- **pdfplumber/PyMuPDF** - PDF parsing
- **Tesseract OCR** - Image text extraction
- **spaCy** - NLP for item extraction

### Infrastructure
- **Supabase** - Postgres DB, Auth, Real-time, Storage
- **Vercel** - Frontend hosting
- **Vercel Serverless Functions** or **AWS Lambda** - Backend hosting

## Project Structure

```
grocery-list/
├── frontend/              # React PWA
│   ├── public/
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── lib/          # Utilities (Supabase client)
│   │   ├── pages/        # Page components
│   │   ├── store/        # Zustand state management
│   │   ├── styles/       # CSS files
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
│
├── backend/              # Python FastAPI
│   ├── api/
│   │   ├── routers/     # API endpoints
│   │   └── main.py      # FastAPI app
│   ├── services/        # Business logic
│   │   ├── document_parser.py
│   │   └── item_extractor.py
│   └── requirements.txt
│
└── README.md
```

## Database Schema

```sql
-- Users (handled by Supabase Auth)

-- Lists
CREATE TABLE lists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Items
CREATE TABLE items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  list_id UUID REFERENCES lists(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  category TEXT,
  checked BOOLEAN DEFAULT FALSE,
  position INTEGER DEFAULT 0,
  checked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- List Members (for sharing)
CREATE TABLE list_members (
  list_id UUID REFERENCES lists(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'editor',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (list_id, user_id)
);

-- Enable Row Level Security
ALTER TABLE lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
ALTER TABLE list_members ENABLE ROW LEVEL SECURITY;

-- RLS Policies (examples)
CREATE POLICY "Users can view their own lists"
  ON lists FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own lists"
  ON lists FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

## Setup Instructions

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.10+
- Supabase account (free tier available)
- Tesseract OCR (for image processing)

### 1. Clone and Setup Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with your Supabase credentials
npm run dev
```

Frontend runs at http://localhost:3000

### 2. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install Tesseract OCR
# Ubuntu: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract

# Download spaCy model
python -m spacy download en_core_web_sm

cp .env.example .env
# Edit .env with your credentials

# Run server
uvicorn api.main:app --reload --port 8000
```

Backend runs at http://localhost:8000

### 3. Setup Supabase

1. Create project at https://supabase.com
2. Run the SQL schema above in Supabase SQL Editor
3. Enable Google OAuth in Authentication settings
4. Copy project URL and anon key to .env files

### 4. Enable Real-time

In Supabase dashboard:
1. Go to Database → Replication
2. Enable replication for `items` table

## Development

### Frontend Commands
```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run preview      # Preview production build
npm run lint         # Lint code
```

### Backend Commands
```bash
uvicorn api.main:app --reload           # Dev server
pytest                                   # Run tests (TODO)
python -m services.item_extractor       # Test item extraction
```

## Deployment

### Frontend (Vercel)
```bash
cd frontend
npm run build
# Connect repo to Vercel, auto-deploys on push
```

### Backend (Vercel Serverless)
```bash
# Add vercel.json in backend/
# Deploy via Vercel CLI
vercel
```

Alternative: Deploy to AWS Lambda, Google Cloud Functions, or Railway.

## Roadmap

- [x] Basic list CRUD
- [x] Real-time collaboration
- [x] Shopping mode
- [x] Document parsing (txt, docx, pdf)
- [ ] Voice recognition
- [ ] Smart categorization with ML
- [ ] Recipe import
- [ ] Store layout optimization
- [ ] Price tracking
- [ ] Meal planning integration

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push and create PR

## License

MIT
