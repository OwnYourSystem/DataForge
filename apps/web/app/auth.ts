import { createClient, type SupabaseClient } from "@supabase/supabase-js";

type PublicConfig = { supabaseUrl: string; supabasePublishableKey: string };

declare global {
  interface Window {
    __DATAFORGE__?: PublicConfig;
  }
}

let client: SupabaseClient | null | undefined;

/** The Supabase client, or null when real sign-in is not configured. Browser only. */
export function getSupabase(): SupabaseClient | null {
  if (client === undefined) {
    const config = window.__DATAFORGE__;
    client =
      config?.supabaseUrl && config.supabasePublishableKey
        ? createClient(config.supabaseUrl, config.supabasePublishableKey)
        : null;
  }
  return client;
}

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
