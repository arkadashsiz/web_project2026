# Police Automation System (Django + React)

Full-stack project scaffold based on your specification.

## Stack
- Backend: Django + DRF
- Auth: Simple JWT (with local fallback if package is missing in offline env)
- Database: SQLite
- Frontend: React + Vite
- API docs: drf-spectacular Swagger

## Repository
- `/Users/reza/Documents/sag/backend`
- `/Users/reza/Documents/sag/frontend`
- `/Users/reza/Documents/sag/docker-compose.yml`

## Backend Run
```bash
cd /Users/reza/Documents/sag/backend
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py seed_roles
python3 manage.py runserver
```

## Frontend Run
```bash
cd /Users/reza/Documents/sag/frontend
npm install
npm run dev
```

## API Root
- `http://127.0.0.1:8000/api/`
- Swagger: `http://127.0.0.1:8000/api/docs/`

## Test
```bash
cd /Users/reza/Documents/sag/backend
python3 manage.py test accounts cases
```

## Docker
```bash
cd /Users/reza/Documents/sag
docker compose up --build
```
