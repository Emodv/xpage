import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

// Client-side Supabase client, authenticated as the signed-in owner.
// All queries go through Postgres RLS (see migrations/001_init.sql), so a
// signed-in user only ever sees rows for the tenant(s) they belong to.
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
