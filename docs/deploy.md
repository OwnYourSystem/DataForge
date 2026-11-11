# Test deployment on Render

`render.yaml` describes a small deployment for tests on a phone or with a
small number of invited learners.

| Part | Render type | Plan | Notes |
|---|---|---|---|
| `dataforge` | Web service | Free | Web app and API in one container. The only public address. |
| `dataforge-worker` | Background worker | Starter (about 7 USD each month) | Runs dbt. No public address. |
| `dataforge-db` | Postgres | Free | Render deletes a free database after 30 days. |

Sign-in is real (Supabase Auth). The development sign-in is off.

## Deploy

1. Open this link and sign in to Render with GitHub:
   `https://render.com/deploy?repo=https://github.com/OwnYourSystem/DataForge`
2. Give Render access to the repository, then select **Apply**. The first
   build takes approximately 5 to 10 minutes.
3. Copy the address of the `dataforge` service. It looks like
   `https://dataforge-xxxx.onrender.com`.
4. In the Supabase dashboard, project `dataforge`, open **Authentication,
   URL configuration**. Set **Site URL** to that address, and add the address
   to **Redirect URLs**. Without this step, the sign-in link opens
   `localhost` and not the app.
5. Open the address on your phone, type your email address, and open the
   link from the email on the same phone.

Render deploys again after each push to the branch that the blueprint was
made from.

## How it is put together

```text
Phone browser
  └── dataforge (public): web server
        └── /api/v1/... forwarded to the API on localhost, same container
              └── dataforge-db (Postgres, private network)
                    └── dataforge-worker: runs dbt, grades, no public address
```

The public container has no dbt and no reference solutions. CI builds both
images, runs the lesson through the public port, and checks these two
points.

## Limits of this deployment

- **Slow first request.** A free web service stops after 15 minutes with no
  traffic. The next request takes approximately 1 minute.
- **Worker isolation is weaker than in Docker Compose.** Render does not
  give a read-only file system or dropped capabilities for the worker. The
  SQL guard, the DuckDB file lock, and the minimal environment stay.
- **One worker.** Runs go one at a time.
- **Email volume.** The built-in Supabase email service sends only a small
  number of emails each hour.
- **Sign-up is open.** Turn off new sign-ups in Supabase for an invite-only
  test.
- **Free database.** It ends after 30 days. Change the plan in `render.yaml`
  before that if you want to keep the data.
