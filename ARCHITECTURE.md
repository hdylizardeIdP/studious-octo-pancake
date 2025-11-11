# Architecture Documentation

Technical overview of the Grocery List application architecture, patterns, and design decisions.

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                        Client                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   React UI   │  │ Service      │  │  IndexedDB   │ │
│  │  (Zustand)   │←→│ Worker (PWA) │←→│  (Dexie.js)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ↕                                      ↕         │
└─────────┼──────────────────────────────────────┼─────────┘
          │                                      │
          ↓                                      ↓
┌─────────────────────┐              ┌──────────────────┐
│   FastAPI Backend   │              │    Supabase      │
│  ┌──────────────┐  │              │  ┌────────────┐  │
│  │ Document     │  │              │  │ PostgreSQL │  │
│  │ Parser       │  │              │  ├────────────┤  │
│  │ (OCR, NLP)   │  │              │  │ Real-time  │  │
│  └──────────────┘  │              │  ├────────────┤  │
└─────────────────────┘              │  │ Auth       │  │
                                     │  ├────────────┤  │
                                     │  │ Storage    │  │
                                     └──┴────────────┴──┘
```

## Frontend Architecture

### Technology Stack
- **React 18**: UI framework with concurrent features
- **TypeScript**: Type safety
- **Vite**: Build tool (fast HMR, optimized bundling)
- **TailwindCSS**: Utility-first styling
- **Zustand**: Lightweight state management
- **React Router**: Client-side routing
- **Supabase JS**: Database + auth client
- **Dexie.js**: IndexedDB wrapper for offline storage
- **Workbox**: Service worker management

### Directory Structure
```
frontend/src/
├── components/       # Reusable UI components
│   ├── ListItem.tsx
│   ├── Button.tsx
│   └── Modal.tsx
├── hooks/           # Custom React hooks
│   ├── useAuth.ts
│   ├── useOffline.ts
│   └── useVoice.ts
├── lib/             # Utilities and clients
│   ├── supabase.ts  # Supabase client config
│   └── db.ts        # Dexie IndexedDB config
├── pages/           # Route components
│   ├── HomePage.tsx
│   ├── ListPage.tsx
│   └── ShoppingMode.tsx
├── store/           # Zustand state stores
│   ├── listStore.ts
│   └── authStore.ts
├── styles/          # Global CSS
├── App.tsx          # Root component
└── main.tsx         # Entry point
```

### State Management Pattern

**Zustand stores** for global state:
```typescript
// store/listStore.ts
interface ListStore {
  lists: List[]
  selectedList: List | null
  fetchLists: () => Promise<void>
  addItem: (item: Item) => Promise<void>
  toggleItem: (id: string) => Promise<void>
}

export const useListStore = create<ListStore>((set) => ({
  lists: [],
  selectedList: null,
  fetchLists: async () => { /* ... */ },
  addItem: async (item) => { /* ... */ },
  toggleItem: async (id) => { /* ... */ }
}))
```

**React hooks** for component-specific logic:
```typescript
// hooks/useAuth.ts
export const useAuth = () => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Subscribe to auth changes
    supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })
  }, [])

  return { user, loading }
}
```

### Offline-First Pattern

1. **Read operations**: Check IndexedDB first, then Supabase
2. **Write operations**: Write to both IndexedDB and Supabase
3. **Sync**: Queue operations when offline, sync when online

```typescript
// Simplified offline pattern
const addItem = async (item: Item) => {
  // 1. Write to local DB immediately (fast UX)
  await localDB.items.add(item)

  try {
    // 2. Sync to Supabase
    const { data, error } = await supabase
      .from('items')
      .insert(item)

    if (error) {
      // 3. Queue for later sync if failed
      await syncQueue.add({ action: 'insert', table: 'items', data: item })
    }
  } catch (e) {
    // Offline - will sync later
    await syncQueue.add({ action: 'insert', table: 'items', data: item })
  }
}
```

### Real-time Updates Pattern

```typescript
// Subscribe to changes
useEffect(() => {
  if (!selectedList) return

  const subscription = supabase
    .channel(`list:${selectedList.id}`)
    .on('postgres_changes',
      { event: '*', schema: 'public', table: 'items', filter: `list_id=eq.${selectedList.id}` },
      (payload) => {
        handleRealtimeUpdate(payload)
      }
    )
    .subscribe()

  return () => {
    subscription.unsubscribe()
  }
}, [selectedList])
```

## Backend Architecture

### Technology Stack
- **FastAPI**: Modern async Python web framework
- **Uvicorn**: ASGI server
- **python-docx**: Word document parsing
- **pdfplumber/PyMuPDF**: PDF text extraction
- **Tesseract OCR**: Image text recognition
- **spaCy**: NLP for item extraction
- **Supabase Python SDK**: Database client

### Directory Structure
```
backend/
├── api/
│   ├── routers/
│   │   ├── documents.py   # Document upload/parsing endpoints
│   │   └── __init__.py
│   ├── main.py            # FastAPI app, CORS, middleware
│   └── __init__.py
├── services/
│   ├── document_parser.py  # Extract text from files
│   ├── item_extractor.py   # NLP to extract grocery items
│   └── __init__.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

### Document Processing Pipeline

```python
# 1. Upload document
@router.post("/parse")
async def parse_document(file: UploadFile):
    # 2. Extract raw text
    parser = DocumentParser()
    text = await parser.extract_text(file)

    # 3. Extract items using NLP
    extractor = ItemExtractor()
    items = extractor.extract_items(text)

    # 4. Return structured data
    return {"items": items}
```

**Document Parser** (services/document_parser.py):
```python
class DocumentParser:
    async def extract_text(self, file: UploadFile) -> str:
        if file.content_type == "text/plain":
            return await self._parse_text(file)
        elif file.content_type == "application/pdf":
            return await self._parse_pdf(file)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return await self._parse_docx(file)
        elif file.content_type.startswith("image/"):
            return await self._parse_image(file)
        else:
            raise ValueError("Unsupported file type")

    async def _parse_image(self, file: UploadFile) -> str:
        # Use Tesseract OCR
        image = Image.open(io.BytesIO(await file.read()))
        text = pytesseract.image_to_string(image)
        return text
```

**Item Extractor** (services/item_extractor.py):
```python
class ItemExtractor:
    def __init__(self):
        # Load spaCy model
        self.nlp = spacy.load("en_core_web_sm")

    def extract_items(self, text: str) -> List[Dict]:
        # Parse text
        doc = self.nlp(text)

        items = []
        for line in text.split('\n'):
            # Simple pattern: detect quantities and nouns
            # e.g., "2 apples", "milk", "1 lb butter"
            item = self._parse_line(line)
            if item:
                items.append(item)

        return items

    def _parse_line(self, line: str) -> Optional[Dict]:
        # Extract item name, quantity, unit
        # Implementation details...
        pass
```

### API Endpoints

**Documents Router** (api/routers/documents.py):
```python
router = APIRouter()

@router.post("/parse")
async def parse_document(file: UploadFile = File(...)):
    """Parse document and extract grocery items"""
    # Implementation

@router.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    """Extract raw text without parsing"""
    # Implementation
```

### CORS Configuration

```python
# api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Database Architecture

### Schema Design

**Entity Relationship Diagram:**
```
users (Supabase Auth)
  ↓
lists (one-to-many)
  ↓
items (one-to-many)

users ←→ list_members ←→ lists (many-to-many for sharing)
```

**Tables:**

```sql
-- Lists table
lists
├── id (uuid, PK)
├── user_id (uuid, FK → auth.users)
├── name (text)
├── created_at (timestamptz)
└── updated_at (timestamptz)

-- Items table
items
├── id (uuid, PK)
├── list_id (uuid, FK → lists)
├── name (text)
├── category (text, nullable)
├── checked (boolean)
├── position (integer)
├── checked_at (timestamptz, nullable)
└── created_at (timestamptz)

-- List members (for sharing)
list_members
├── list_id (uuid, FK → lists, PK)
├── user_id (uuid, FK → auth.users, PK)
├── role (text: 'owner' | 'editor' | 'viewer')
└── created_at (timestamptz)
```

### Row Level Security (RLS)

**Pattern:** Users can only access their own lists or shared lists.

```sql
-- Example policy
CREATE POLICY "Users can view their own lists or shared lists"
  ON lists FOR SELECT
  USING (
    auth.uid() = user_id
    OR
    EXISTS (
      SELECT 1 FROM list_members
      WHERE list_members.list_id = lists.id
      AND list_members.user_id = auth.uid()
    )
  );
```

### Real-time Replication

Enable for collaborative features:
```sql
-- Enable real-time for items table
ALTER PUBLICATION supabase_realtime ADD TABLE items;
```

## PWA Architecture

### Service Worker Strategy

**Caching Strategy:**
- **App shell**: Cache-first (HTML, CSS, JS)
- **API calls**: Network-first with cache fallback
- **Images**: Cache-first with stale-while-revalidate

```javascript
// vite.config.ts - Workbox configuration
VitePWA({
  strategies: 'injectManifest',
  srcDir: 'src',
  filename: 'sw.ts',
  registerType: 'autoUpdate',
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/.*\.supabase\.co\/.*/i,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'supabase-api-cache',
          expiration: {
            maxEntries: 100,
            maxAgeSeconds: 60 * 60 * 24 // 24 hours
          }
        }
      }
    ]
  }
})
```

### Offline Queue

Queue mutations when offline, sync when online:
```typescript
// Simplified queue
class SyncQueue {
  private queue: Operation[] = []

  async add(operation: Operation) {
    this.queue.push(operation)
    await this.saveToStorage()
  }

  async processQueue() {
    if (!navigator.onLine) return

    for (const op of this.queue) {
      try {
        await this.executeOperation(op)
        this.queue = this.queue.filter(o => o.id !== op.id)
      } catch (e) {
        // Keep in queue, retry later
      }
    }

    await this.saveToStorage()
  }
}
```

## Authentication Flow

```
1. User clicks "Sign in with Google"
   ↓
2. Supabase redirects to Google OAuth
   ↓
3. User authorizes
   ↓
4. Supabase handles callback
   ↓
5. Session stored in localStorage
   ↓
6. Frontend receives auth event
   ↓
7. UI updates (show user lists)
```

**Implementation:**
```typescript
// Login
const signInWithGoogle = async () => {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin
    }
  })
}

// Listen for auth changes
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN') {
    // Fetch user data, redirect to home
  } else if (event === 'SIGNED_OUT') {
    // Clear state, redirect to login
  }
})
```

## Security Considerations

### Frontend Security
1. **Use anon key** (not service key)
2. **RLS enforced** on database (server-side)
3. **No sensitive data** in localStorage
4. **HTTPS only** in production

### Backend Security
1. **Service key** stored in env vars (never exposed)
2. **File upload validation** (size, type, content)
3. **Rate limiting** (TODO: implement)
4. **Input sanitization** for NLP processing

### Database Security
1. **RLS policies** on all tables
2. **No direct SQL** from frontend
3. **Prepared statements** (handled by Supabase SDK)

## Performance Optimizations

### Frontend
1. **Code splitting**: Lazy load routes
2. **Image optimization**: Compress uploads
3. **Bundle size**: Tree shaking with Vite
4. **React.memo**: Memoize expensive components
5. **Virtual scrolling**: For large lists (TODO)

### Backend
1. **Async I/O**: FastAPI async endpoints
2. **Stream processing**: For large file uploads
3. **Model caching**: Load spaCy model once
4. **Connection pooling**: Supabase client reuse

### Database
1. **Indexes**: On frequently queried columns
2. **Pagination**: Limit result set size
3. **Select specific columns**: Not SELECT *

## Testing Strategy

### Frontend Tests (TODO)
- **Unit**: Component logic with Vitest
- **Integration**: User flows with Testing Library
- **E2E**: Critical paths with Playwright

### Backend Tests (TODO)
- **Unit**: Service functions with pytest
- **Integration**: API endpoints
- **Load**: Concurrent users with locust

## Deployment Architecture

### Docker Containers
```
┌─────────────────────────────────────────┐
│         Docker Host (Production)        │
│  ┌────────────────┐  ┌───────────────┐ │
│  │  Frontend      │  │  Backend      │ │
│  │  (nginx)       │  │  (uvicorn)    │ │
│  │  Port: 80      │  │  Port: 8000   │ │
│  └────────────────┘  └───────────────┘ │
│         │                     │          │
└─────────┼─────────────────────┼──────────┘
          │                     │
          └──────────┬──────────┘
                     ↓
          ┌──────────────────┐
          │    Supabase      │
          │  (External SaaS) │
          └──────────────────┘
```

### Environment-Specific Configs
- **Development**: Hot-reload, verbose logging
- **Staging**: Production builds, test data
- **Production**: Optimized builds, real data, monitoring

## Error Handling

### Frontend Pattern
```typescript
try {
  const data = await fetchData()
  setState(data)
} catch (error) {
  if (error.code === 'PGRST116') {
    // No data found - expected
    setState([])
  } else {
    // Unexpected error
    toast.error('Failed to load data')
    console.error(error)
  }
}
```

### Backend Pattern
```python
@router.post("/parse")
async def parse_document(file: UploadFile):
    try:
        text = await parser.extract_text(file)
        items = extractor.extract_items(text)
        return {"items": items}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log error
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Future Architecture Considerations

### Scalability
- **Backend**: Add load balancer, horizontal scaling
- **Database**: Read replicas for heavy queries
- **Storage**: CDN for user uploads
- **Cache**: Redis for frequently accessed data

### Features
- **WebSockets**: Real-time cursor presence
- **Queues**: Background jobs (email notifications)
- **Analytics**: Track usage patterns
- **ML Pipeline**: Train custom NER model for better item extraction

## Development Guidelines

### Code Style
- **Frontend**: Prettier + ESLint
- **Backend**: Black + Flake8
- **Commits**: Conventional Commits (feat, fix, docs, etc.)

### Git Workflow
1. Feature branch from main
2. Make changes
3. Test locally
4. Create PR
5. Review + merge

### Documentation
- **Code comments**: For complex logic
- **Docstrings**: All public functions
- **README**: Keep updated
- **Architecture docs**: Update on major changes

---

**Last Updated:** 2025-11-11
**Maintained By:** Development Team
**Questions?** See README.md or open an issue
