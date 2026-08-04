# Supabase Urgent Setup

The mobile app sync is failing because `public.field_records` does not exist in Supabase yet.

## Run This Now

1. Open Supabase project:
   `https://supabase.com/dashboard/project/lagrhtwsomtwvwkhtchg/sql`
2. Open `supabase-postgis-setup.sql`.
3. Copy the full SQL into Supabase SQL Editor.
4. Press `Run`.
5. Return to the mobile app and press the sync button again.

## Expected Result

After the SQL runs, Supabase will have:

- `public.field_records` table
- PostGIS geometry column
- required Data API grants
- RLS policies for the prototype
- `asset-photos` storage bucket
- storage upload/read/update policies
- schema cache reload

Then mobile records can sync and the dashboard can load them.
