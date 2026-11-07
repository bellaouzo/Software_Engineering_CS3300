# Maintenance Ticketing System

UCCS CS 3300 (Intro to Software Engineering), Fall 2026 semester team project.

A web app for reporting and tracking maintenance problems. A **Requester** submits
a ticket (title, description, location, category) and follows it as it moves
along. **Staff** see every ticket, move it through the status workflow, and
reply. Both roles can comment on a ticket.

Statuses, in order: `Submitted` → `Acknowledged` → `In Progress` → `Resolved` → `Closed`.

## Team

| Name | GitHub |
| --- | --- |
| Joel Brisk | [bellaouzo](https://github.com/bellaouzo) |
| Joseph Smith | [josephmsmith012-maker](https://github.com/josephmsmith012-maker) |
| Zachary Yarnell | [ZachYarnell](https://github.com/ZachYarnell) |
| Max Santomauro | [maxsantomauro](https://github.com/maxsantomauro) |
| Edison Otuonye | [Edison-Otuonye](https://github.com/Edison-Otuonye) |

## Features

- Username and password accounts through Supabase Auth (Req 1.1.1 to 1.2.2, 4.2)
- Submit a ticket and see your own tickets; staff see all tickets (2.1.1 to 2.2.2)
- Staff-only status updates, enforced in the database by Row-Level Security (2.3.1, 2.3.2, 4.1)
- Comments on a ticket, shown oldest first, with staff replies tagged (3.1.1, 3.2.1)
- Separate Requester and Staff dashboards with ticket counts by status
- Inline form validation (6.1) and layouts that work on a phone

## Built with

- **Python 3.14** and **Flask** (routes and back end), **Jinja2** (HTML templates)
- **Supabase** (hosted Postgres database and login)
- **Render** (hosting; deploys automatically from `main`)
- Plain HTML, CSS and JavaScript in the browser. No front end framework.

## Running it

You need **Python 3.14** and **Git**. For a private local database you also need
**Docker Desktop**, plus either the Supabase CLI or Node.js (for `npx supabase`).

```
git clone https://github.com/bellaouzo/Software_Engineering_CS3330.git
cd Software_Engineering_CS3330
python dev.py        # macOS/Linux: python3 dev.py
```

`dev.py` asks which database to use, sets up a virtual environment, installs
`requirements.txt`, starts the app and opens it at <http://127.0.0.1:5000>.

- **Local** runs Supabase in Docker with every migration applied. Nothing else
  needs to be set up.
- **Live** uses the team's shared Supabase project. Copy `.env.example` to `.env`
  and fill in `FLASK_SECRET_KEY`, `SUPABASE_URL` and `SUPABASE_KEY`. Ask the team
  for these values. They are not in the repo.

### Demo accounts

To fill the local database with demo accounts, tickets and comments, start it
with `python dev.py --db local --keep-db`. Then, in a second terminal, run:

```
python seed_demo_data.py --db local
```

Log in with any of these. The password is `demo-password` for all of them.

| Username | Role |
| --- | --- |
| `demo_requester` to `demo_requester5` | Requester |
| `demo_staff`, `demo_staff2` | Staff |

`python seed_demo_data.py --db local --remove` deletes the demo data again.

The Render site has its own accounts. To try it, register a new account (it
starts as a Requester) or ask the team for a staff login.

## Where things are

```
app.py              Flask app setup
routes/             Back end: login/register, tickets, dashboard
templates/          Front end: HTML pages and shared partials
static/             CSS and JavaScript
supabase/           Database migrations (the schema) and local config
dev.py              One-command launcher
seed_demo_data.py   Demo data script
docs/               Team documents and developer guides
```

[`AGENTS.md`](AGENTS.md) is the developer overview: coding rules, file size
limits and the branch and pull request workflow, with full guides in
[`docs/guides/`](docs/guides/).

## Open-source software used

The project uses these open-source packages and assets. Each one keeps its own
license.

| Component | Used for | License |
| --- | --- | --- |
| [Flask](https://github.com/pallets/flask) | Web framework | BSD-3-Clause |
| [Jinja2](https://github.com/pallets/jinja), [Werkzeug](https://github.com/pallets/werkzeug) (installed with Flask) | Templates, request handling | BSD-3-Clause |
| [supabase-py](https://github.com/supabase/supabase-py) | Supabase client for Python | MIT |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Loads `.env` settings | BSD-3-Clause |
| [Gunicorn](https://github.com/benoitc/gunicorn) | Production web server on Render | MIT |
| [Supabase CLI](https://github.com/supabase/cli) | Local database in Docker (development only) | MIT |
| [Barlow](https://github.com/jpt/barlow) font, via Google Fonts | Page font | SIL Open Font License 1.1 |

Supabase (database and auth) and Render (hosting) are hosted services we use on
their free tiers. They are not copied into this repo.

## License

Released under the MIT License. See [`LICENSE`](LICENSE).
