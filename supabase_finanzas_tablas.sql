-- =========================================
-- TABLAS DEL MÓDULO DE FINANZAS PARA SUPABASE
-- =========================================
-- Ejecutar este script en: Supabase Dashboard → SQL Editor
-- Fecha: 2025-12-12
-- =========================================

-- ===================================
-- 1. TABLA: egresos_adicionales
-- ===================================
CREATE TABLE IF NOT EXISTS public.egresos_adicionales (
    id BIGINT PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    monto NUMERIC(10, 2) NOT NULL,
    observaciones TEXT,
    usuario TEXT DEFAULT 'Sistema',
    fuente TEXT DEFAULT 'Banco',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Normaliza columnas requeridas si la tabla ya existía sin ellas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'egresos_adicionales' AND column_name = 'fecha'
    ) THEN
        ALTER TABLE public.egresos_adicionales ADD COLUMN fecha TIMESTAMPTZ DEFAULT NOW();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'egresos_adicionales' AND column_name = 'tipo'
    ) THEN
        ALTER TABLE public.egresos_adicionales ADD COLUMN tipo TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'egresos_adicionales' AND column_name = 'descripcion'
    ) THEN
        ALTER TABLE public.egresos_adicionales ADD COLUMN descripcion TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'egresos_adicionales' AND column_name = 'monto'
    ) THEN
        ALTER TABLE public.egresos_adicionales ADD COLUMN monto NUMERIC(10, 2);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'egresos_adicionales' AND column_name = 'observaciones'
    ) THEN
        ALTER TABLE public.egresos_adicionales ADD COLUMN observaciones TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'egresos_adicionales' AND column_name = 'usuario'
    ) THEN
        ALTER TABLE public.egresos_adicionales ADD COLUMN usuario TEXT DEFAULT 'Sistema';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'egresos_adicionales' AND column_name = 'fuente'
    ) THEN
        ALTER TABLE public.egresos_adicionales ADD COLUMN fuente TEXT DEFAULT 'Banco';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'egresos_adicionales' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE public.egresos_adicionales ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'egresos_adicionales' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE public.egresos_adicionales ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Índices para egresos_adicionales
CREATE INDEX IF NOT EXISTS idx_egresos_fecha ON public.egresos_adicionales(fecha);
CREATE INDEX IF NOT EXISTS idx_egresos_tipo ON public.egresos_adicionales(tipo);
CREATE INDEX IF NOT EXISTS idx_egresos_fuente ON public.egresos_adicionales(fuente);

-- Trigger para updated_at en egresos_adicionales
CREATE OR REPLACE FUNCTION update_egresos_adicionales_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_egresos_adicionales_updated_at ON public.egresos_adicionales;
CREATE TRIGGER set_egresos_adicionales_updated_at
    BEFORE UPDATE ON public.egresos_adicionales
    FOR EACH ROW
    EXECUTE FUNCTION update_egresos_adicionales_updated_at();

-- RLS para egresos_adicionales
ALTER TABLE public.egresos_adicionales ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Permitir lectura de egresos" ON public.egresos_adicionales;
CREATE POLICY "Permitir lectura de egresos"
    ON public.egresos_adicionales
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Permitir inserción de egresos autenticados" ON public.egresos_adicionales;
CREATE POLICY "Permitir inserción de egresos autenticados"
    ON public.egresos_adicionales
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated' OR true);

DROP POLICY IF EXISTS "Permitir actualización de egresos autenticados" ON public.egresos_adicionales;
CREATE POLICY "Permitir actualización de egresos autenticados"
    ON public.egresos_adicionales
    FOR UPDATE
    USING (auth.role() = 'authenticated' OR true);

-- Función RPC para upsert de egresos_adicionales
DROP FUNCTION IF EXISTS upsert_egreso_adicional(JSONB);
CREATE OR REPLACE FUNCTION upsert_egreso_adicional(_row JSONB)
RETURNS void AS $$
BEGIN
    INSERT INTO public.egresos_adicionales (
        id, fecha, tipo, descripcion, monto, observaciones, usuario, fuente
    )
    VALUES (
        (_row->>'id')::BIGINT,
        (_row->>'fecha')::TIMESTAMP WITH TIME ZONE,
        _row->>'tipo',
        _row->>'descripcion',
        (_row->>'monto')::NUMERIC,
        _row->>'observaciones',
        COALESCE(_row->>'usuario', 'Sistema'),
        COALESCE(_row->>'fuente', 'Banco')
    )
    ON CONFLICT (id) DO UPDATE SET
        fecha = EXCLUDED.fecha,
        tipo = EXCLUDED.tipo,
        descripcion = EXCLUDED.descripcion,
        monto = EXCLUDED.monto,
        observaciones = EXCLUDED.observaciones,
        usuario = EXCLUDED.usuario,
        fuente = EXCLUDED.fuente,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ===================================
-- 2. TABLA: ingresos_pasivos
-- ===================================
CREATE TABLE IF NOT EXISTS public.ingresos_pasivos (
    id BIGINT PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    descripcion TEXT NOT NULL,
    monto NUMERIC(10, 2) NOT NULL,
    observaciones TEXT,
    usuario TEXT DEFAULT 'Sistema',
    fuente TEXT DEFAULT 'Banco',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Normaliza columnas requeridas si la tabla ya existía sin ellas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ingresos_pasivos' AND column_name = 'fecha'
    ) THEN
        ALTER TABLE public.ingresos_pasivos ADD COLUMN fecha TIMESTAMPTZ DEFAULT NOW();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ingresos_pasivos' AND column_name = 'descripcion'
    ) THEN
        ALTER TABLE public.ingresos_pasivos ADD COLUMN descripcion TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ingresos_pasivos' AND column_name = 'monto'
    ) THEN
        ALTER TABLE public.ingresos_pasivos ADD COLUMN monto NUMERIC(10, 2);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ingresos_pasivos' AND column_name = 'observaciones'
    ) THEN
        ALTER TABLE public.ingresos_pasivos ADD COLUMN observaciones TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ingresos_pasivos' AND column_name = 'usuario'
    ) THEN
        ALTER TABLE public.ingresos_pasivos ADD COLUMN usuario TEXT DEFAULT 'Sistema';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ingresos_pasivos' AND column_name = 'fuente'
    ) THEN
        ALTER TABLE public.ingresos_pasivos ADD COLUMN fuente TEXT DEFAULT 'Banco';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ingresos_pasivos' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE public.ingresos_pasivos ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ingresos_pasivos' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE public.ingresos_pasivos ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Índices para ingresos_pasivos
CREATE INDEX IF NOT EXISTS idx_ingresos_fecha ON public.ingresos_pasivos(fecha);
CREATE INDEX IF NOT EXISTS idx_ingresos_fuente ON public.ingresos_pasivos(fuente);

-- Trigger para updated_at en ingresos_pasivos
CREATE OR REPLACE FUNCTION update_ingresos_pasivos_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_ingresos_pasivos_updated_at ON public.ingresos_pasivos;
CREATE TRIGGER set_ingresos_pasivos_updated_at
    BEFORE UPDATE ON public.ingresos_pasivos
    FOR EACH ROW
    EXECUTE FUNCTION update_ingresos_pasivos_updated_at();

-- RLS para ingresos_pasivos
ALTER TABLE public.ingresos_pasivos ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Permitir lectura de ingresos" ON public.ingresos_pasivos;
CREATE POLICY "Permitir lectura de ingresos"
    ON public.ingresos_pasivos
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Permitir inserción de ingresos autenticados" ON public.ingresos_pasivos;
CREATE POLICY "Permitir inserción de ingresos autenticados"
    ON public.ingresos_pasivos
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated' OR true);

DROP POLICY IF EXISTS "Permitir actualización de ingresos autenticados" ON public.ingresos_pasivos;
CREATE POLICY "Permitir actualización de ingresos autenticados"
    ON public.ingresos_pasivos
    FOR UPDATE
    USING (auth.role() = 'authenticated' OR true);

-- Función RPC para upsert de ingresos_pasivos
DROP FUNCTION IF EXISTS upsert_ingreso_pasivo(JSONB);
CREATE OR REPLACE FUNCTION upsert_ingreso_pasivo(_row JSONB)
RETURNS void AS $$
BEGIN
    INSERT INTO public.ingresos_pasivos (
        id, fecha, descripcion, monto, observaciones, usuario, fuente
    )
    VALUES (
        (_row->>'id')::BIGINT,
        (_row->>'fecha')::TIMESTAMP WITH TIME ZONE,
        _row->>'descripcion',
        (_row->>'monto')::NUMERIC,
        _row->>'observaciones',
        COALESCE(_row->>'usuario', 'Sistema'),
        COALESCE(_row->>'fuente', 'Banco')
    )
    ON CONFLICT (id) DO UPDATE SET
        fecha = EXCLUDED.fecha,
        descripcion = EXCLUDED.descripcion,
        monto = EXCLUDED.monto,
        observaciones = EXCLUDED.observaciones,
        usuario = EXCLUDED.usuario,
        fuente = EXCLUDED.fuente,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ===================================
-- 3. TABLA: caja_chica_movimientos
-- ===================================
CREATE TABLE IF NOT EXISTS public.caja_chica_movimientos (
    id BIGINT PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tipo TEXT NOT NULL CHECK (tipo IN ('INGRESO', 'EGRESO', 'AJUSTE')),
    monto NUMERIC(10, 2) NOT NULL,
    descripcion TEXT,
    usuario TEXT DEFAULT 'Sistema',
    referencia_tipo TEXT,
    referencia_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Normaliza columnas requeridas si la tabla ya existía sin ellas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'caja_chica_movimientos' AND column_name = 'fecha'
    ) THEN
        ALTER TABLE public.caja_chica_movimientos ADD COLUMN fecha TIMESTAMPTZ DEFAULT NOW();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'caja_chica_movimientos' AND column_name = 'tipo'
    ) THEN
        ALTER TABLE public.caja_chica_movimientos ADD COLUMN tipo TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'caja_chica_movimientos' AND column_name = 'monto'
    ) THEN
        ALTER TABLE public.caja_chica_movimientos ADD COLUMN monto NUMERIC(10, 2);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'caja_chica_movimientos' AND column_name = 'descripcion'
    ) THEN
        ALTER TABLE public.caja_chica_movimientos ADD COLUMN descripcion TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'caja_chica_movimientos' AND column_name = 'usuario'
    ) THEN
        ALTER TABLE public.caja_chica_movimientos ADD COLUMN usuario TEXT DEFAULT 'Sistema';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'caja_chica_movimientos' AND column_name = 'referencia_tipo'
    ) THEN
        ALTER TABLE public.caja_chica_movimientos ADD COLUMN referencia_tipo TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'caja_chica_movimientos' AND column_name = 'referencia_id'
    ) THEN
        ALTER TABLE public.caja_chica_movimientos ADD COLUMN referencia_id BIGINT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'caja_chica_movimientos' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE public.caja_chica_movimientos ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'caja_chica_movimientos' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE public.caja_chica_movimientos ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Índices para caja_chica_movimientos
CREATE INDEX IF NOT EXISTS idx_caja_chica_fecha ON public.caja_chica_movimientos(fecha);
CREATE INDEX IF NOT EXISTS idx_caja_chica_tipo ON public.caja_chica_movimientos(tipo);
CREATE INDEX IF NOT EXISTS idx_caja_chica_referencia ON public.caja_chica_movimientos(referencia_tipo, referencia_id);

-- Trigger para updated_at en caja_chica_movimientos
CREATE OR REPLACE FUNCTION update_caja_chica_movimientos_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_caja_chica_movimientos_updated_at ON public.caja_chica_movimientos;
CREATE TRIGGER set_caja_chica_movimientos_updated_at
    BEFORE UPDATE ON public.caja_chica_movimientos
    FOR EACH ROW
    EXECUTE FUNCTION update_caja_chica_movimientos_updated_at();

-- RLS para caja_chica_movimientos
ALTER TABLE public.caja_chica_movimientos ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Permitir lectura de caja chica" ON public.caja_chica_movimientos;
CREATE POLICY "Permitir lectura de caja chica"
    ON public.caja_chica_movimientos
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Permitir inserción de caja chica autenticados" ON public.caja_chica_movimientos;
CREATE POLICY "Permitir inserción de caja chica autenticados"
    ON public.caja_chica_movimientos
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated' OR true);

DROP POLICY IF EXISTS "Permitir actualización de caja chica autenticados" ON public.caja_chica_movimientos;
CREATE POLICY "Permitir actualización de caja chica autenticados"
    ON public.caja_chica_movimientos
    FOR UPDATE
    USING (auth.role() = 'authenticated' OR true);

-- Función RPC para upsert de caja_chica_movimientos (YA EXISTE en sync_manager)
DROP FUNCTION IF EXISTS upsert_caja_chica_movimiento(JSONB);
CREATE OR REPLACE FUNCTION upsert_caja_chica_movimiento(_row JSONB)
RETURNS void AS $$
BEGIN
    INSERT INTO public.caja_chica_movimientos (
        id, fecha, tipo, monto, descripcion, usuario, referencia_tipo, referencia_id
    )
    VALUES (
        (_row->>'id')::BIGINT,
        COALESCE((_row->>'fecha')::TIMESTAMP WITH TIME ZONE, NOW()),
        _row->>'tipo',
        (_row->>'monto')::NUMERIC,
        _row->>'descripcion',
        COALESCE(_row->>'usuario', 'Sistema'),
        _row->>'referencia_tipo',
        (_row->>'referencia_id')::BIGINT
    )
    ON CONFLICT (id) DO UPDATE SET
        fecha = EXCLUDED.fecha,
        tipo = EXCLUDED.tipo,
        monto = EXCLUDED.monto,
        descripcion = EXCLUDED.descripcion,
        usuario = EXCLUDED.usuario,
        referencia_tipo = EXCLUDED.referencia_tipo,
        referencia_id = EXCLUDED.referencia_id,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ===================================
-- 4. TABLA: ordenes_compra
-- ===================================
CREATE TABLE IF NOT EXISTS public.ordenes_compra (
    id BIGINT PRIMARY KEY,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_orden NUMERIC(10, 2) NOT NULL,
    estado TEXT DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'PAGADA', 'CANCELADA')),
    fecha_pago TIMESTAMP WITH TIME ZONE,
    notas TEXT,
    creado_por TEXT DEFAULT 'admin',
    pedido_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Normaliza columnas requeridas si la tabla ya existía sin ellas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ordenes_compra' AND column_name = 'fecha_creacion'
    ) THEN
        ALTER TABLE public.ordenes_compra ADD COLUMN fecha_creacion TIMESTAMPTZ DEFAULT NOW();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ordenes_compra' AND column_name = 'total_orden'
    ) THEN
        ALTER TABLE public.ordenes_compra ADD COLUMN total_orden NUMERIC(10, 2);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ordenes_compra' AND column_name = 'estado'
    ) THEN
        ALTER TABLE public.ordenes_compra ADD COLUMN estado TEXT DEFAULT 'PENDIENTE';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ordenes_compra' AND column_name = 'fecha_pago'
    ) THEN
        ALTER TABLE public.ordenes_compra ADD COLUMN fecha_pago TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ordenes_compra' AND column_name = 'notas'
    ) THEN
        ALTER TABLE public.ordenes_compra ADD COLUMN notas TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ordenes_compra' AND column_name = 'creado_por'
    ) THEN
        ALTER TABLE public.ordenes_compra ADD COLUMN creado_por TEXT DEFAULT 'admin';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ordenes_compra' AND column_name = 'pedido_id'
    ) THEN
        ALTER TABLE public.ordenes_compra ADD COLUMN pedido_id BIGINT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ordenes_compra' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE public.ordenes_compra ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'ordenes_compra' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE public.ordenes_compra ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Índices para ordenes_compra
CREATE INDEX IF NOT EXISTS idx_ordenes_fecha_creacion ON public.ordenes_compra(fecha_creacion);
CREATE INDEX IF NOT EXISTS idx_ordenes_estado ON public.ordenes_compra(estado);
CREATE INDEX IF NOT EXISTS idx_ordenes_pedido ON public.ordenes_compra(pedido_id);

-- Permite pedido_id NULL para evitar fallos de sincronización si pedidos aún no existen
ALTER TABLE public.ordenes_compra ALTER COLUMN pedido_id DROP NOT NULL;

-- Trigger para updated_at en ordenes_compra
CREATE OR REPLACE FUNCTION update_ordenes_compra_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_ordenes_compra_updated_at ON public.ordenes_compra;
CREATE TRIGGER set_ordenes_compra_updated_at
    BEFORE UPDATE ON public.ordenes_compra
    FOR EACH ROW
    EXECUTE FUNCTION update_ordenes_compra_updated_at();

-- RLS para ordenes_compra
ALTER TABLE public.ordenes_compra ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Permitir lectura de ordenes" ON public.ordenes_compra;
CREATE POLICY "Permitir lectura de ordenes"
    ON public.ordenes_compra
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Permitir inserción de ordenes autenticados" ON public.ordenes_compra;
CREATE POLICY "Permitir inserción de ordenes autenticados"
    ON public.ordenes_compra
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated' OR true);

DROP POLICY IF EXISTS "Permitir actualización de ordenes autenticados" ON public.ordenes_compra;
CREATE POLICY "Permitir actualización de ordenes autenticados"
    ON public.ordenes_compra
    FOR UPDATE
    USING (auth.role() = 'authenticated' OR true);

-- Función RPC para upsert de ordenes_compra (YA EXISTE en sync_manager)
DROP FUNCTION IF EXISTS upsert_orden_compra(JSONB);
CREATE OR REPLACE FUNCTION upsert_orden_compra(_row JSONB)
RETURNS void AS $$
BEGIN
    INSERT INTO public.ordenes_compra (
        id, fecha_creacion, total_orden, estado, fecha_pago, notas, creado_por, pedido_id
    )
    VALUES (
        (_row->>'id')::BIGINT,
        COALESCE((_row->>'fecha_creacion')::TIMESTAMP WITH TIME ZONE, NOW()),
        (_row->>'total_orden')::NUMERIC,
        COALESCE(_row->>'estado', 'PENDIENTE'),
        (_row->>'fecha_pago')::TIMESTAMP WITH TIME ZONE,
        _row->>'notas',
        COALESCE(_row->>'creado_por', 'admin'),
        (_row->>'pedido_id')::BIGINT
    )
    ON CONFLICT (id) DO UPDATE SET
        fecha_creacion = EXCLUDED.fecha_creacion,
        total_orden = EXCLUDED.total_orden,
        estado = EXCLUDED.estado,
        fecha_pago = EXCLUDED.fecha_pago,
        notas = EXCLUDED.notas,
        creado_por = EXCLUDED.creado_por,
        pedido_id = EXCLUDED.pedido_id,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =========================================
-- VERIFICACIÓN FINAL
-- =========================================
-- Después de ejecutar este script, verifica que:
-- 1. Las 4 tablas se crearon correctamente
-- 2. Los índices están activos
-- 3. Las políticas RLS están habilitadas
-- 4. Las funciones RPC están disponibles

-- Consultas de verificación:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('egresos_adicionales', 'ingresos_pasivos', 'caja_chica_movimientos', 'ordenes_compra');
-- SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public' AND routine_name LIKE 'upsert_%';
