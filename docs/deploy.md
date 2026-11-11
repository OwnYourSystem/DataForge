# Test deployment on Render

`render.yaml` describes a free deployment for a test on a phone.

| Part | Render type | Plan | Notes |
|---|---|---|---|
| `dataforge` | Web service | Free | Web app, API, and worker in one container. The only public address. |
| `dataforge-db` | Postgres | Free | Render deletes a free database after 30 days. |

Sign-in is real (Supabase Auth). The development sign-in is off.

**This layout is for learners you trust.** dbt and learner SQL run in the
same container as the API, which holds the database address. The SQL guard,
the DuckDB file lock, and the minimal dbt environment stay. Before other
people sign in, change to the split layout (see the end of this page).

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
        ├── /api/v1/... forwarded to the API on localhost, same container
        ├── worker: runs dbt and grades, same container
        └── dataforge-db (Postgres, private network)
```

CI builds this image, runs the lesson 2 times through the public port with
a memory limit of 512 MB, and checks that the image has no reference
solutions.

## Limits of this deployment

- **Slow first request.** A free web service stops after 15 minutes with no
  traffic. The next request takes approximately 1 minute.
- **Memory.** A free service has 512 MB. One run uses most of it. Two runs
  at the same time are not possible.
- **One worker.** Runs go one at a time.
- **Email volume.** The built-in Supabase email service sends only a small
  number of emails each hour.
- **Sign-up is open.** Turn off new sign-ups in Supabase for an invite-only
  test.
- **Free database.** It ends after 30 days. Change the plan in `render.yaml`
  before that if you want to keep the data.

## Split layout (paid)

`deploy/render/blueprint-split.yaml` puts the worker in its own service
with no public address. The public container then has no dbt. It needs a
payment method in Render (Starter plan for the worker, approximately 7 USD
each month). To use it, copy that file to `render.yaml` in the repository
root and push.

