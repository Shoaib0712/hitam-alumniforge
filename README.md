# HITAM AlumniForge

**Connect. Learn. Mentor. Grow.**

HITAM AlumniForge is a full-stack career intelligence platform connecting HITAM students and alumni through explainable matching, Career DNA, mentorship, opportunities, and network insights.

## What is real today

- FastAPI + SQLite backend with JWT authentication and bcrypt password hashing
- React + Vite frontend with responsive command-center UI
- Student, alumni, and admin roles
- `@hitam.org` registration guard
- First-login password change for imported/demo accounts
- Database-backed Career DNA and alumni recommendations
- Explainable match scores with matching skills
- Mentorship requests, connection requests, notifications, and recommendation feedback
- Resume/job resonance and placement pulse tools
- Database-backed Opportunity Radar with profile fit scores, search, category filters, saved launch list, and external mission links
- 3D Career Constellation and Opportunity Galaxy views
- Career Time Machine for evidence-based skill exploration

The seeded records are demonstration data. They are not official college verification and must be replaced or supplemented with approved HITAM data before production use.

## Run locally

### 1. Requirements

- Python 3.11+
- Node.js 20+

### 2. Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python seed_data.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On startup the API creates the SQLite schema, imports the prepared CSV files, and ensures the opportunity catalog exists. The prepared account password is `12345`; the first login requires each account to choose a private password.

### 3. Frontend

Open a second terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:3000>.

If port 3000 is already in use, Vite will display an alternate port such as <http://127.0.0.1:3001>.

Demo accounts:

| Role | Email | Initial password |
|---|---|---|
| Student | rahul@hitam.org | 230101 |
| Alumni | vikram.alumni@hitam.org | ALUM2020 |
| Admin | admin@hitam.org | Admin@123 |

The student and alumni demo accounts must create a new password after first login.

### Panel demonstration flow

Use this sequence for a reliable 5–10 minute presentation:

1. Sign in as a student with a CSV account such as `karan.22com0001@hitam.org` and password `12345`.
2. Complete the one-time private password screen.
3. Open **My profile** to show the CSV-backed skills, interests, location, projects, academic details, and career goal.
4. Open **Opportunity radar**. Search by a company or skill, filter by Internship/Challenge/Fellowship, show the profile fit percentage, save an opportunity, and open its mission link.
5. Open **Opportunity galaxy** to show the same opportunity field as an interactive 3D mission map.
6. Open **Career constellation** to show the student’s skills, interests, gaps, and trajectory orbit.
7. Open **AI toolkit** and run Resume Resonance, Placement Pulse, and Career Time Machine.
8. To demonstrate networking, sign in in a second browser as an alumni account, accept the student connection in **Requests**, and exchange a message in **Messages**.
9. Sign in as `admin@hitam.org` / `Admin@123` to show the admin pulse and data-quality surfaces.

The 100 alumni accounts are in [data/alumni_clean.csv](data/alumni_clean.csv); the 100 student accounts are in [data/students_clean.csv](data/students_clean.csv). Every CSV account is imported as an active login and begins with password `12345`.

### Useful API checks

With the backend running, open <http://127.0.0.1:8000/docs> for interactive API documentation. The most useful panel-demo endpoints are:

| Endpoint | Purpose |
|---|---|
| `GET /users/me` | Full authenticated student or alumni profile |
| `GET /opportunities` | Profile-ranked opportunity catalog |
| `POST /opportunities/{id}/save` | Save an opportunity to the launch list |
| `DELETE /opportunities/{id}/save` | Remove a saved opportunity |
| `GET /career/readiness` | Personalized Placement Pulse |
| `POST /career/what-if` | Career Time Machine simulation |
| `GET /connections` | Student/alumni connection state |
| `GET /connections/{id}/messages` | Accepted-connection chat history |

## Deploy

### Render backend

1. Push the repository to GitHub.
2. Create a new Render Blueprint and select the repository.
3. Render can use [backend/render.yaml](backend/render.yaml).
4. Set `ALLOWED_ORIGINS` to the final Vercel URL.
5. Keep the persistent disk enabled; SQLite data is stored at `/var/data/app.db`.

### Vercel frontend

1. Import the repository into Vercel.
2. Set the project root to `frontend`.
3. Set `VITE_API_URL` to the Render API URL.
4. Deploy. [frontend/vercel.json](frontend/vercel.json) keeps SPA routes working on refresh.

## Data and privacy boundaries

- Email-domain checking is only an access rule; it does not prove institutional identity.
- “Platform Verified” means an admin verified the profile inside AlumniForge, not that HITAM officially verified it.
- Never upload real student data without permission and a privacy review.
- Roll numbers and passwords must never be exposed in public profile responses.

## Troubleshooting

| Problem | Fix |
|---|---|
| CORS error | Set `ALLOWED_ORIGINS` to the exact frontend origin and restart the API. |
| API connection refused | Start Uvicorn on port 8000 and confirm `VITE_API_URL`. |
| Login returns 401 | Use the exact demo email/password or seed a fresh database. |
| CSV account is rejected | Use the exact email from the CSV and password `12345`; complete the one-time password change after login. |
| Opportunity Radar is empty | Restart the API so startup seeding can ensure the opportunity catalog, then refresh the frontend. |
| Saved opportunity does not change | Confirm the API is running with the same browser token and refresh the Radar. |
| Demo account asks for a password | This is intentional first-login security behavior. |
| SQLite locked | Stop duplicate API processes and retry the request. |
| bcrypt error | Reinstall dependencies from `backend/requirements.txt`. |
| Excel import dependency missing | Install `openpyxl` in the backend virtual environment. |
| Vercel 404 on refresh | Confirm `frontend/vercel.json` is deployed from the frontend root. |
| Render database resets | Confirm the Render persistent disk is attached and `DATABASE_URL` is `/var/data/app.db`. |
| JWT loops back to login | Clear browser storage, log in again, and ensure frontend and backend clocks are current. |

## Final project boundaries

This release is a panel-ready demonstration build. The included dataset is synthetic and every opportunity link is a demonstration/external destination; verify live deadlines before real applications. For production deployment, replace SQLite with PostgreSQL, add approved HITAM data governance, configure a production JWT secret, add rate limiting, and complete the admin Dataset Import Center for approved CSV/XLSX uploads.
