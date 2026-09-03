-- Quién de la plantilla recibió el encargo del cliente.
-- Aplicar en Supabase (SQL Editor) y también queda en docker/init-test-db.sql para local.

ALTER TABLE public.encargos_clientes
ADD COLUMN IF NOT EXISTS recibido_por text;
