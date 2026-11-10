# Sign-in

The API has 2 identity modes. `DF_AUTH_MODE` selects one.

| Mode | How the API identifies a learner | Use |
|---|---|---|
| `jwt` | A signed token in `Authorization: Bearer <token>` | Pilot and production |
| `dev` | The `X-Dev-User` header, not verified | Local work and CI only |

**Status (10 November 2026):** the API is proven against the real Supabase
project `dataforge` (eu-north-1). A real ES256 token got HTTP 200, and a
changed token, the project's HS256 key, and the development header got
HTTP 401. The email link itself (email delivery and the redirect to the web
app) is not yet tested by a person.

## How `jwt` mode works

1. The learner types an email address in the web app.
2. Supabase Auth sends an email with a sign-in link. There is no password.
3. The link opens the web app, and Supabase gives the browser a signed token.
4. The web app sends the token with each API request.
5. The API checks the signature with the public keys of the project (JWKS),
   and checks the issuer, the audience, and the expiry.

The API accepts only asymmetric signatures (ES256, RS256, EdDSA). It refuses
shared-secret tokens (HS256), because a shared secret that leaks lets a
person make tokens for all learners.

The API stores `<issuer>|<subject>` in `users.identity_subject`. It keeps no
email address and no password. To change the provider later, change the 3
`DF_AUTH_*` values and the sign-in screen.

## Setup with Supabase

1. Make a Supabase project for DataForge. Do not share a project with a
   different app, because the two apps would share one list of users.
2. In **Authentication, Signing keys**, make sure the project signs tokens
   with an asymmetric key (ECC P-256). New projects do this by default.
3. In **Authentication, URL configuration**, set the site URL to the address
   of the web app (`http://localhost:3000` for the local stack) and add it to
   the redirect URLs.
4. Set these values. For the local stack, `.env.example` has the values of
   the `dataforge` project: copy it to `.env`.

| Variable | Value |
|---|---|
| `DF_AUTH_MODE` | `jwt` |
| `DF_AUTH_ISSUER` | `https://<project-ref>.supabase.co/auth/v1` |
| `DF_AUTH_AUDIENCE` | `authenticated` |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://<project-ref>.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | The publishable key (`sb_publishable_...`) |

The publishable key is public by design. Do not put a secret key
(`sb_secret_...`) in the web app or in this repository.

`DF_AUTH_JWKS_URL` is optional. The default is
`<issuer>/.well-known/jwks.json`.

5. Start the stack:

```bash
docker compose up --build
```

The web values are read at build time, so `--build` is necessary after a
change.

## Limits

- **Email volume.** The built-in Supabase email service sends only a small
  number of emails each hour. For a pilot, connect an SMTP service in the
  Supabase project.
- **Same device.** The learner must open the link in the browser that asked
  for it.
- **Sign-up is open.** Each person with an email address can sign in. To
  limit the pilot to invited learners, turn off new sign-ups in Supabase and
  invite the learners from the dashboard.
- **No roles.** All users are learners. There is no administrator role yet.
