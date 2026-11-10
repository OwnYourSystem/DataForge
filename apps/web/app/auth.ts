import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "";

/** Real sign-in is on when the Supabase values are set at build time. */
export const supabase: SupabaseClient | null =
  SUPABASE_URL && SUPABASE_KEY ? createClient(SUPABASE_URL, SUPABASE_KEY) : null;

/** A signed-in learner. The API client asks it for request headers. */
export type Identity = {
  label: string;
  headers: () => Promise<Record<string, string>>;
  signOut: () => Promise<void>;
};

export function devIdentity(name: string, onSignOut: () => void): Identity {
  return {
    label: name,
    headers: async () => ({ "X-Dev-User": name }),
    signOut: async () => onSignOut(),
  };
}

export function supabaseIdentity(client: SupabaseClient, email: string): Identity {
  return {
    label: email,
    headers: async (): Promise<Record<string, string>> => {
      // getSession renews the token when it is near its expiry.
      const { data } = await client.auth.getSession();
      const token = data.session?.access_token;
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    signOut: async () => {
      await client.auth.signOut();
    },
  };
}
