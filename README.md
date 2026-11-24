# 🔍 FindIt – Smart Lost and Found Management Platform

> A centralized digital platform for college campuses to report, search, and claim lost & found items — replacing scattered WhatsApp groups and notice boards.

---

## 📋 Project Information

| Field | Details |
|---|---|
| **Student Name** | Druva Kumar B |
| **USN** | ENG25AD0110 |
| **Branch** | Artificial Intelligence & Data Science (AI&DS) |
| **Section** | B |
| **Roll Number** | 39 |
| **Institution** | Dayananda Sagar University, Bangalore |
| **Course** | Skill Enhancement Course – Full Stack Development |
| **Academic Year** | 2025–2026 |

---

## 🚀 Quick Start

Sign up with any valid email address and a password, then use those credentials to
sign in. Email verification and Firebase configuration are not required. Item
reports and claims require a contact phone number, but SMS verification is not
required. The phone number is protected on public item listings until a claim is
approved.

### Option 1 — Double-click to Launch (Easiest)

1. Double-click **`start-all.bat`** in the project root.
2. Two terminal windows will open — one for the backend, one for the frontend.
3. Open your browser and go to: **[http://localhost:5173](http://localhost:5173)**

### Option 2 — Run Servers Individually

**Terminal 1 — Backend (Flask API):**
```bat
start-backend.bat
```

**Terminal 2 — Frontend (React/Vite):**
```bat
start-frontend.bat
```

> ⚠️ Always start the **backend first**, then the frontend.

### Option 3 — Manual Commands (PowerShell)

**Backend:**
```powershell
Set-Location backend
& "..\.venv\Scripts\python.exe" run.py
```

**Frontend:**
```powershell
Set-Location frontend
npm run dev
```

---

## 🌐 Netlify Deployment

Netlify hosts the React/Vite frontend. The Flask API must be deployed separately
(for example, on Render, Railway, or Vercel) and connected using its public API URL.
The root `netlify.toml` configures the frontend build and React Router fallback.

1. Import this repository in Netlify. It will use the included build settings:
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `dist`
2. Deploy the Flask backend separately and configure it with a persistent database
   using `DATABASE_URL`. Do not use the backend's SQLite fallback for production.
3. In **Site configuration → Environment variables**, set
   `VITE_API_BASE_URL` to the backend API root, including `/api`, for example:
   ```text
   https://your-backend.example.com/api
   ```
4. Configure `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and
   `CLOUDINARY_API_SECRET` on the backend to keep uploaded images available
   between deployments. Then trigger a new Netlify deploy so Vite includes the
   API URL in the frontend build.

If `VITE_API_BASE_URL` is not set, the frontend uses `/api`, which is suitable
for local Vite development with the configured proxy but does not provide an API
on Netlify by itself. Backend-uploaded `/uploads/...` image paths are resolved
against the configured backend host.

---

## 🌐 Vercel Deployment Guide

FindIt is pre-configured for full-stack deployment on Vercel with zero hassle.

### Method 1 — 1-Click Deployment Script (Recommended)
1. Double-click **`deploy-vercel.bat`** in the project root.
2. Vercel CLI will launch automatically.
3. If not already logged in, it will prompt you to authorize your Vercel account in your browser.
4. Accept the default configuration prompts (hit Enter / Y).
5. Vercel will build both the frontend and backend serverless functions, then output your live production URL:
   ```
   https://findit-lost-and-found.vercel.app
   ```

### Method 2 — GitHub + Vercel Dashboard (Continuous Deployment)
1. Push this repository to GitHub:
   ```bash
   git remote add origin https://github.com/<your-username>/findit-platform.git
   git branch -M main
   git push -u origin main
   ```
2. Go to **[vercel.com/new](https://vercel.com/new)** and import your GitHub repository.
3. The included `vercel.json` and root `package.json` will automatically configure:
   - **Framework Preset:** Other / Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `frontend/dist`
   - **Serverless API:** `/api/index.py` (WSGI Python function)
4. In **Project Settings -> Environment Variables**, set:
   - `DATABASE_URL` (Supabase / Neon PostgreSQL or PlanetScale MySQL connection string)
   - `SECRET_KEY` and `JWT_SECRET_KEY` (independent, randomly generated secret values)
   - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` (for permanent user photo uploads)
5. Click **Deploy**. Vercel will deploy your live full-stack app!

---

Register with an email and password to create an account. For production
deployments, provision administrator accounts securely through the database rather
than using demo credentials.

---

## 🏗️ Technology Stack

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React.js | 19.x | UI framework |
| Vite | 5.x | Build tool & dev server |
| Bootstrap 5 | 5.3.x | Responsive CSS framework |
| Axios | 1.x | HTTP client for API calls |
| React Router | v7 | Client-side routing |
| Lucide React | latest | Icon library |
| Chart.js / react-chartjs-2 | 4.x | Admin analytics charts |

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.x | Runtime |
| Flask | 3.x | Web framework |
| Flask-SQLAlchemy | 3.x | ORM & database models |
| PyJWT | 2.x | JSON Web Token authentication |
| Flask-CORS | 4.x | Cross-origin request handling |
| Werkzeug | 3.x | Password hashing, file uploads |
| Pillow | 10.x | Image processing & thumbnails |
| python-dotenv | 1.x | Environment variable management |

### Database
| Environment | Database | Notes |
|---|---|---|
| Development | SQLite (`findit.db`) | Auto-created, zero config |
| Production | MySQL 8+ | Set env vars (see `.env.example`) |

---

## 📁 Project Structure

```
fsd_project/
├── backend/                    # Flask REST API
│   ├── app.py                  # App factory, CORS, blueprints
│   ├── config.py               # MySQL/SQLite auto-detection
│   ├── models.py               # Database models (8 tables)
│   ├── database.py             # Seed data (DSU demo data)
│   ├── run.py                  # Server entry point
│   ├── routes/
│   │   ├── auth.py             # Register, Login, /me, Profile
│   │   ├── items.py            # CRUD items, search, smart match
│   │   ├── claims.py           # Submit & review claims
│   │   ├── admin.py            # Admin dashboard, user/item mgmt
│   │   ├── notifications.py    # Get & mark notifications
│   │   └── contact.py          # Contact form submission
│   └── utils/
│       ├── auth_middleware.py  # JWT decorators
│       ├── matcher.py          # Smart AI similarity matching
│       └── file_upload.py      # Image upload & thumbnails
│
├── frontend/                   # React/Vite SPA
│   ├── src/
│   │   ├── pages/              # 20 pages (see below)
│   │   ├── components/         # Reusable UI components
│   │   ├── context/            # AuthContext (JWT state)
│   │   ├── services/           # API service wrappers
│   │   └── App.css             # Global styles & utilities
│   └── vite.config.js          # Proxy config (/api → :5000)
│
├── .tools/
│   ├── venv/                   # Python virtual environment
│   └── nodejs/                 # Node.js runtime
│
├── start-backend.bat           # 🟢 Start Flask API
├── start-frontend.bat          # 🔵 Start React dev server
├── start-all.bat               # 🚀 Start everything at once
└── README.md                   # This file
```

---

## 📄 Pages & Features

| Page | Route | Access | Description |
|---|---|---|---|
| Home | `/` | Public | Hero, stats, categories, recent items |
| Browse Items | `/browse` | Public | Paginated item grid with filters |
| Search | `/search` | Public | Full-text search with tag filters |
| Item Detail | `/items/:id` | Public | Full item view + Smart Match sidebar |
| Login | `/login` | Public | Email/password + demo quick-fill |
| Register | `/register` | Public | Account creation with role selection |
| Dashboard | `/dashboard` | 🔒 Auth | Personal overview & recent activity |
| Report Lost | `/report-lost` | 🔒 Auth | Form to report a lost item |
| Report Found | `/report-found` | 🔒 Auth | Form to report a found item |
| Claim Request | `/claim/:itemId` | 🔒 Auth | Submit ownership proof & claim |
| My Reports | `/my-reports` | 🔒 Auth | Manage your own reported items |
| My Claims | `/my-claims` | 🔒 Auth | Track claim status & history |
| Notifications | `/notifications` | 🔒 Auth | Smart match alerts, claim updates |
| Profile | `/profile` | 🔒 Auth | Edit personal info & change password |
| Contact | `/contact` | Public | Contact form + DSU office details |
| About | `/about` | Public | Project info + developer details |
| Admin Dashboard | `/admin` | 🛡️ Admin | Charts, stats, activity logs |
| Admin Items | `/admin/items` | 🛡️ Admin | View, filter, delete all items |
| Admin Users | `/admin/users` | 🛡️ Admin | Manage user accounts & roles |
| Admin Claims | `/admin/claims` | 🛡️ Admin | Review and approve/reject claims |

---

## 🧠 Smart Matching Algorithm

FindIt uses an AI-inspired similarity algorithm to automatically suggest potential matches between lost and found reports.

**Scoring weights:**
- 🏷️ **Category match** — 40% (exact category = full score)
- 📍 **Location similarity** — 25% (token overlap of location strings)
- 📝 **Description similarity** — 35% (Jaccard tokenized text similarity)
- 📅 **Date proximity bonus** — up to 5% extra (items reported close in time)

A score ≥ 0.4 (40%) is flagged as a potential match and shown in notifications and the Item Detail sidebar.

---

## 🔒 Authentication & Security

- Passwords hashed with **Werkzeug PBKDF2-SHA256** (not stored plain-text)
- **JWT tokens** (PyJWT) stored in `localStorage` with 24-hour expiry
- Protected routes use `token_required` / `admin_required` decorators
- File uploads sanitized — only JPEG/PNG/WEBP, max 10MB, UUID-renamed
- Contact info (phone/email) masked on found items for non-owners/non-admins

---

## 🗄️ Database Models

| Model | Fields | Notes |
|---|---|---|
| `User` | name, email, phone, role, status, avatar | Roles: user, finder, admin |
| `Category` | name, slug, icon, description | 8 pre-seeded categories |
| `Item` | type, name, category, description, location, date, contact, image, reward, status, user | 8 demo items seeded |
| `ItemImage` | item_id, path, is_primary | Multiple images per item |
| `ClaimRequest` | item_id, claimant, proof, status, admin_notes | Workflow: pending→approved/rejected |
| `Notification` | user_id, title, message, type, link, is_read | Smart match & claim alerts |
| `ActivityLog` | user_id, action, details, ip | Audit trail for admin |
| `ContactMessage` | name, email, subject, message, status | Contact form submissions |

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` in the project root and set your local database and
security-key values as needed. Firebase configuration is not required.

```env
# Flask
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
PORT=5000

# MySQL (optional — falls back to SQLite if not set)
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=3306
DB_NAME=findit_db

# Or use a full URL
DATABASE_URL=mysql+pymysql://root:password@localhost/findit_db
```

---

## 🌐 API Endpoints Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | ❌ | Register with email and password |
| POST | `/api/auth/login` | ❌ | Sign in with email and password |
| GET | `/api/auth/me` | 🔒 | Get current user |
| PUT | `/api/auth/profile` | 🔒 | Update profile |
| GET | `/api/items` | ❌ | List items (paginated, filtered) |
| POST | `/api/items` | 🔒 | Create new item report |
| GET | `/api/items/:id` | ❌ | Get single item |
| PUT | `/api/items/:id` | 🔒 | Update item |
| DELETE | `/api/items/:id` | 🔒 | Delete item |
| GET | `/api/items/:id/matches` | ❌ | Get smart matches |
| GET | `/api/items/my` | 🔒 | My reported items |
| POST | `/api/claims` | 🔒 | Submit claim |
| GET | `/api/claims/my` | 🔒 | My submitted claims |
| GET | `/api/claims/item/:id` | 🔒 | Claims on my item |
| PUT | `/api/claims/:id/review` | 🔒 | Approve/reject claim |
| GET | `/api/notifications` | 🔒 | Get notifications |
| PUT | `/api/notifications/:id/read` | 🔒 | Mark as read |
| GET | `/api/admin/stats` | 🛡️ | Dashboard stats & charts |
| GET | `/api/admin/users` | 🛡️ | All users |
| GET | `/api/admin/items` | 🛡️ | All items |
| GET | `/api/admin/claims` | 🛡️ | All claims |
| POST | `/api/contact` | ❌ | Submit contact message |

---

## 🛠️ Troubleshooting

**Backend won't start:**
- Make sure you're using the venv Python: `.tools\venv\Scripts\python.exe`
- Check `backend/findit.db` exists after first run (auto-created)

**Frontend shows blank page:**
- Backend must be running on port 5000 before opening the frontend
- Check browser console for CORS errors

**"Module not found" errors:**
- All packages are pre-installed in `.tools/venv` — do NOT use system Python

**Port already in use:**
```powershell
# Kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Fresh database reset:**
```powershell
Remove-Item backend\findit.db -Force
# Then restart the backend — it re-seeds automatically
```

---

## 📸 Sample Data (DSU Context)

The database is seeded with realistic DSU campus scenario data:
- **8 demo items** across Electronics, ID Cards, Bags, Keys, Books, Accessories
- **DSU locations**: Central Library, North Canteen, Science Quad, Main Auditorium, Parking Zone B, Gymnasium
- **Smart match demo**: Lost Dell XPS 13 ↔ Found Dell Laptop with DSU sticker (auto-detected!)
- **1 approved claim**: Sony WH-1000XM4 Headphones (claimed by Ravi via Security)

---

## 📞 Contact & Support

**Institution:** Dayananda Sagar University  
**Campus:** Kudlu Gate, Hosur Road, Bangalore – 560114  
**Phone:** +91 80 6782 1000  
**Platform Email:** support@findit.dsu.edu.in  

---

*FindIt v1.0 · AY 2025–2026 · SEC Full Stack Development · Dayananda Sagar University · Druva Kumar B (ENG25AD0110)*
