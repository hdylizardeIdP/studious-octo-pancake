# Quick Start Guide

Get the Grocery List app running in 5 minutes.

## Prerequisites Check

```bash
# Check Docker installed
docker --version
docker-compose --version

# If not installed:
# - macOS: Install Docker Desktop
# - Ubuntu: sudo apt install docker.io docker-compose
# - Windows: Install Docker Desktop
```

## Setup Steps

### 1. Get Supabase Credentials (2 minutes)

1. **Create account**: https://supabase.com (free)
2. **Create project**: New Project → Wait ~2 minutes for setup
3. **Get credentials**:
   - Go to **Settings** (gear icon) → **API**
   - Copy these values:
     - **Project URL** (starts with `https://`)
     - **anon public** key (for frontend)
     - **service_role** key (for backend - keep secret!)

### 2. Setup Database Schema (1 minute)

1. In Supabase dashboard, go to **SQL Editor**
2. Paste this SQL:

```sql
-- Create lists table
CREATE TABLE lists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create items table
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

-- Create list members table (for sharing)
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

-- Lists policies
CREATE POLICY "Users can view their own lists"
  ON lists FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own lists"
  ON lists FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own lists"
  ON lists FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own lists"
  ON lists FOR DELETE
  USING (auth.uid() = user_id);

-- Items policies
CREATE POLICY "Users can view items in their lists"
  ON items FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM lists
      WHERE lists.id = items.list_id
      AND lists.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert items in their lists"
  ON items FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM lists
      WHERE lists.id = items.list_id
      AND lists.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update items in their lists"
  ON items FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM lists
      WHERE lists.id = items.list_id
      AND lists.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete items in their lists"
  ON items FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM lists
      WHERE lists.id = items.list_id
      AND lists.user_id = auth.uid()
    )
  );
```

3. Click **Run** (or press Cmd/Ctrl + Enter)

### 3. Enable Real-time (30 seconds)

1. In Supabase dashboard, go to **Database** → **Replication**
2. Find the `items` table
3. Toggle **Enable** for real-time replication

### 4. Setup Auth (Optional - 1 minute)

For Google OAuth:
1. Go to **Authentication** → **Providers**
2. Find **Google**
3. Toggle **Enable**
4. Add your Google OAuth credentials (or use Supabase's for testing)

Or skip for now - you can use email authentication by default.

### 5. Configure Environment (1 minute)

```bash
# In project root
cp .env.example .env

# Edit .env (use nano, vim, or any editor)
nano .env

# Add your Supabase credentials:
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGci...  # service_role key

VITE_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...  # anon public key
```

**Save and exit** (Ctrl+X, then Y, then Enter)

### 6. Start the App (1 minute)

```bash
# Build and start containers
docker-compose up -d

# Watch logs (optional)
docker-compose logs -f
```

Wait 30-60 seconds for services to start...

### 7. Open and Test

Open in browser:
- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs

Test backend health:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

## You're Done! 🎉

The app is now running. Try:
1. Sign up / Sign in
2. Create a list
3. Add items
4. Test real-time (open in two browsers)

## Common Issues

### Port already in use
```bash
# Check what's using the port
sudo lsof -i :3000
sudo lsof -i :8000

# Kill the process or change port in docker-compose.yaml
```

### Backend health check failing
```bash
# Check backend logs
docker-compose logs backend

# Common issues:
# - Missing Supabase credentials
# - Invalid service_role key
# - Tesseract not installed (should auto-install in Docker)
```

### Frontend shows blank page
```bash
# Check browser console (F12)
# Common issues:
# - Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY
# - CORS error (check backend ALLOWED_ORIGINS includes http://localhost:3000)
```

### Can't connect to Supabase
```bash
# Test connection from backend container
docker-compose exec backend python -c "
import os
from supabase import create_client
print('Testing connection...')
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('✓ Connected successfully')
"
```

## Next Steps

### Development Mode (Hot Reload)

Stop production containers and start dev mode:
```bash
docker-compose down
docker-compose -f docker-compose.dev.yaml up
```

Now code changes auto-reload!
- Frontend: http://localhost:5173
- Backend: http://localhost:8000

### Manual Setup (Without Docker)

If you prefer running without Docker:

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with Supabase credentials
npm run dev
```

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr

cp .env.example .env
# Edit .env with Supabase credentials
uvicorn api.main:app --reload --port 8000
```

## Learn More

- [README.md](./README.md) - Full documentation
- [DOCKER.md](./DOCKER.md) - Docker guide and troubleshooting
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical architecture
- [TODO.md](./TODO.md) - Development roadmap

## Test Features

### Upload Document
1. Create a test file:
```bash
echo "milk
eggs
bread
2 apples
cheese" > grocery-list.txt
```

2. Go to http://localhost:3000
3. Upload the file
4. Watch items get extracted!

### Test Real-time Collaboration
1. Open http://localhost:3000 in Chrome
2. Open http://localhost:3000 in Firefox (or incognito)
3. Sign in as same user in both
4. Add item in one browser
5. Watch it appear instantly in the other!

### Test Offline Mode
1. Open DevTools (F12)
2. Go to **Network** tab
3. Check **Offline**
4. Add items (they queue locally)
5. Uncheck **Offline**
6. Watch items sync to server!

---

**Need help?** See [README.md](./README.md#troubleshooting) troubleshooting section or open an issue.
