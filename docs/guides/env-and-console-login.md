# Environment file and console login

## Where `.env` belongs

- **Location:** Project root of the prowlrbot repo — the same directory as `.env.example`, `pyproject.toml`, and `INSTALL.md`.
- **Name:** `.env` (copy from `.env.example` and edit).
- **Git:** `.env` is gitignored. Do not commit it.

Example layout:

```
prowlrbot/
├── .env          ← your local secrets (create from .env.example)
├── .env.example  ← template (committed)
├── pyproject.toml
├── INSTALL.md
└── ...
```

## When `.env` is loaded

These commands load `.env` from the **current working directory**:

| Command | Loads `.env` from |
|--------|--------------------|
| `prowlr app` | Current directory (run from project root) |
| `prowlr set-admin-password` | Current directory (run from project root) |

Run them from the project root so the file is found:

```bash
cd /path/to/prowlrbot   # project root
prowlr app
```

## Console admin login

The first user is created from:

- `PROWLRBOT_ADMIN_USERNAME` (default: `admin`)
- `PROWLRBOT_ADMIN_PASSWORD` (if unset, a random password is generated and printed on first run)

### Use a fixed password

1. In the project root, create or edit `.env`:

   ```bash
   PROWLRBOT_ADMIN_USERNAME=admin
   PROWLRBOT_ADMIN_PASSWORD=your-secure-password
   ```

2. If the admin user already exists, update the stored password so it matches `.env`:

   ```bash
   cd /path/to/prowlrbot
   prowlr set-admin-password
   ```

3. Start the app and log in to the console:

   ```bash
   prowlr app
   ```

   Then open the console in the browser and sign in with the username and password above.

### 401 Invalid credentials

If you get **401 Unauthorized — Invalid credentials** when logging in:

- The stored password does not match what you’re typing.
- Set `PROWLRBOT_ADMIN_PASSWORD` in `.env` (project root), then run from the project root:

  ```bash
  prowlr set-admin-password
  ```

  This updates the stored password for the admin user to match `.env`. Then log in again with that password.

### Override from the command line

```bash
prowlr set-admin-password --username admin --password "another-password"
```

Password must be at least 12 characters.

## Other `.env` variables

See `.env.example` in the project root for:

- War Room bridge (`PROWLR_HUB_URL`, `PROWLR_HUB_SECRET`, etc.)
- Working dir, API token, CORS, log level
- LLM API keys (or use `prowlr env set`)
