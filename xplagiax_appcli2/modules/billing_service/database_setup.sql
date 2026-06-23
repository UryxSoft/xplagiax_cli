-- ============================================
-- CONFIGURACIÓN DE BASE DE DATOS PARA PAGOS
-- ============================================

-- PASO 1: Añadir columnas necesarias si no existen
-- ============================================

ALTER TABLE storage_plans ADD COLUMN IF NOT EXISTS stripe_price_monthly VARCHAR(255);
ALTER TABLE storage_plans ADD COLUMN IF NOT EXISTS stripe_price_annual VARCHAR(255);
ALTER TABLE storage_plans ADD COLUMN IF NOT EXISTS paypal_plan_monthly VARCHAR(255);
ALTER TABLE storage_plans ADD COLUMN IF NOT EXISTS paypal_plan_annual VARCHAR(255);

-- PASO 2: Verificar columnas en tabla Users
-- ============================================
-- Asegúrate de que tu tabla Users tenga estas columnas:

-- subscription_provider VARCHAR(50)      -- 'stripe' o 'paypal'
-- subscription_id VARCHAR(255)           -- ID de la suscripción
-- subscription_status VARCHAR(50)        -- 'active', 'canceled', 'past_due', etc.
-- subscription_type VARCHAR(50)          -- 'monthly' o 'annual'
-- subscription_starts_at DATETIME
-- subscription_ends_at DATETIME
-- subscription_renewal_notified BOOLEAN DEFAULT 0

-- PASO 3: Insertar o actualizar planes
-- ============================================

-- PLAN: Starter (Gratis)
INSERT INTO storage_plans (
    name,
    description,
    base_storage_mb,
    price_monthly_usd,
    price_annual_usd,
    trial_days,
    stripe_price_monthly,
    stripe_price_annual,
    paypal_plan_monthly,
    paypal_plan_annual,
    is_active,
    daily_analysis_limit
) VALUES (
    'Starter',
    'Perfect for getting started',
    100,
    0.00,
    0.00,
    0,
    NULL,
    NULL,
    NULL,
    NULL,
    1,
    3
)
ON DUPLICATE KEY UPDATE
    description = 'Perfect for getting started',
    is_active = 1;

-- PLAN: Scholar Suite
INSERT INTO storage_plans (
    name,
    description,
    base_storage_mb,
    price_monthly_usd,
    price_annual_usd,
    trial_days,
    stripe_price_monthly,
    stripe_price_annual,
    paypal_plan_monthly,
    paypal_plan_annual,
    is_active,
    daily_analysis_limit
) VALUES (
    'Scholar Suite',
    'Ideal for students and researchers',
    500,
    15.00,
    150.00,
    14,
    'price_1XXXXXXXXXXXXXXXX',  -- ⚠️ REEMPLAZAR con tu Stripe Price ID mensual
    'price_1YYYYYYYYYYYYYYYY',  -- ⚠️ REEMPLAZAR con tu Stripe Price ID anual
    'P-1XXXXXXXXXXXXXXXX',      -- ⚠️ REEMPLAZAR con tu PayPal Plan ID mensual
    'P-2YYYYYYYYYYYYYYYY',      -- ⚠️ REEMPLAZAR con tu PayPal Plan ID anual
    1,
    15
)
ON DUPLICATE KEY UPDATE
    stripe_price_monthly = 'price_1XXXXXXXXXXXXXXXX',
    stripe_price_annual = 'price_1YYYYYYYYYYYYYYYY',
    paypal_plan_monthly = 'P-1XXXXXXXXXXXXXXXX',
    paypal_plan_annual = 'P-2YYYYYYYYYYYYYYYY',
    is_active = 1;

-- PLAN: Individual
INSERT INTO storage_plans (
    name,
    description,
    base_storage_mb,
    price_monthly_usd,
    price_annual_usd,
    trial_days,
    stripe_price_monthly,
    stripe_price_annual,
    paypal_plan_monthly,
    paypal_plan_annual,
    is_active,
    daily_analysis_limit
) VALUES (
    'Individual',
    'Most popular for professionals',
    1024,
    25.00,
    250.00,
    14,
    'price_1AAAAAAAAAAAAAAAA',  -- ⚠️ REEMPLAZAR
    'price_1BBBBBBBBBBBBBBBB',  -- ⚠️ REEMPLAZAR
    'P-3AAAAAAAAAAAAAAAA',      -- ⚠️ REEMPLAZAR
    'P-4BBBBBBBBBBBBBBBB',      -- ⚠️ REEMPLAZAR
    1,
    30
)
ON DUPLICATE KEY UPDATE
    stripe_price_monthly = 'price_1AAAAAAAAAAAAAAAA',
    stripe_price_annual = 'price_1BBBBBBBBBBBBBBBB',
    paypal_plan_monthly = 'P-3AAAAAAAAAAAAAAAA',
    paypal_plan_annual = 'P-4BBBBBBBBBBBBBBBB',
    is_active = 1;

-- PLAN: Research Essentials
INSERT INTO storage_plans (
    name,
    description,
    base_storage_mb,
    price_monthly_usd,
    price_annual_usd,
    trial_days,
    stripe_price_monthly,
    stripe_price_annual,
    paypal_plan_monthly,
    paypal_plan_annual,
    is_active,
    daily_analysis_limit
) VALUES (
    'Research Essentials',
    'Advanced tools for researchers',
    2048,
    45.00,
    450.00,
    14,
    'price_1CCCCCCCCCCCCCCCC',  -- ⚠️ REEMPLAZAR
    'price_1DDDDDDDDDDDDDDDD',  -- ⚠️ REEMPLAZAR
    'P-5CCCCCCCCCCCCCCCC',      -- ⚠️ REEMPLAZAR
    'P-6DDDDDDDDDDDDDDDD',      -- ⚠️ REEMPLAZAR
    1,
    75
)
ON DUPLICATE KEY UPDATE
    stripe_price_monthly = 'price_1CCCCCCCCCCCCCCCC',
    stripe_price_annual = 'price_1DDDDDDDDDDDDDDDD',
    paypal_plan_monthly = 'P-5CCCCCCCCCCCCCCCC',
    paypal_plan_annual = 'P-6DDDDDDDDDDDDDDDD',
    is_active = 1;

-- PLAN: Institutes
INSERT INTO storage_plans (
    name,
    description,
    base_storage_mb,
    price_monthly_usd,
    price_annual_usd,
    trial_days,
    stripe_price_monthly,
    stripe_price_annual,
    paypal_plan_monthly,
    paypal_plan_annual,
    is_active,
    daily_analysis_limit
) VALUES (
    'Institutes',
    'Enterprise solution for institutions',
    10240,
    0.00,  -- Contact for pricing
    0.00,
    0,
    NULL,  -- Contact sales
    NULL,
    NULL,
    NULL,
    1,
    999999  -- Unlimited
)
ON DUPLICATE KEY UPDATE
    description = 'Enterprise solution for institutions',
    is_active = 1;

-- ============================================
-- PASO 4: Verificar datos insertados
-- ============================================

SELECT 
    id,
    name,
    price_monthly_usd,
    price_annual_usd,
    stripe_price_monthly,
    stripe_price_annual,
    paypal_plan_monthly,
    paypal_plan_annual,
    is_active
FROM storage_plans
WHERE is_active = 1
ORDER BY price_monthly_usd;

-- ============================================
-- QUERIES ÚTILES PARA ADMINISTRACIÓN
-- ============================================

-- Ver todos los usuarios con suscripción activa
SELECT 
    u.id,
    u.email,
    u.user_type,
    u.subscription_provider,
    u.subscription_status,
    u.subscription_type,
    u.subscription_starts_at,
    u.subscription_ends_at
FROM users u
WHERE u.subscription_status IN ('active', 'trialing')
ORDER BY u.subscription_starts_at DESC;

-- Ver suscripciones que vencen pronto (próximos 7 días)
SELECT 
    u.id,
    u.email,
    u.user_type,
    u.subscription_provider,
    u.subscription_ends_at,
    DATEDIFF(u.subscription_ends_at, NOW()) as days_remaining
FROM users u
WHERE u.subscription_status = 'active'
    AND u.subscription_ends_at IS NOT NULL
    AND DATEDIFF(u.subscription_ends_at, NOW()) BETWEEN 0 AND 7
ORDER BY days_remaining ASC;

-- Ver usuarios en trial
SELECT 
    u.id,
    u.email,
    u.user_type,
    u.trial_ends_at,
    DATEDIFF(u.trial_ends_at, NOW()) as trial_days_remaining
FROM users u
WHERE u.is_on_trial = 1
    AND u.trial_ends_at > NOW()
ORDER BY u.trial_ends_at ASC;

-- Estadísticas de suscripciones por plan
SELECT 
    sp.name as plan_name,
    COUNT(u.id) as total_subscribers,
    SUM(CASE WHEN u.subscription_provider = 'stripe' THEN 1 ELSE 0 END) as stripe_subs,
    SUM(CASE WHEN u.subscription_provider = 'paypal' THEN 1 ELSE 0 END) as paypal_subs,
    SUM(CASE WHEN u.subscription_type = 'monthly' THEN 1 ELSE 0 END) as monthly_subs,
    SUM(CASE WHEN u.subscription_type = 'annual' THEN 1 ELSE 0 END) as annual_subs
FROM storage_plans sp
LEFT JOIN users u ON sp.id = u.storage_plan_id 
    AND u.subscription_status IN ('active', 'trialing')
WHERE sp.is_active = 1
GROUP BY sp.id, sp.name
ORDER BY total_subscribers DESC;

-- Revenue estimado mensual
SELECT 
    SUM(
        CASE 
            WHEN u.subscription_type = 'monthly' THEN sp.price_monthly_usd
            WHEN u.subscription_type = 'annual' THEN sp.price_annual_usd / 12
            ELSE 0
        END
    ) as estimated_monthly_revenue
FROM users u
JOIN storage_plans sp ON u.storage_plan_id = sp.id
WHERE u.subscription_status IN ('active', 'trialing');

-- ============================================
-- SCRIPTS DE MANTENIMIENTO
-- ============================================

-- Cancelar suscripciones vencidas (ejecutar diariamente)
UPDATE users 
SET subscription_status = 'expired'
WHERE subscription_status = 'active'
    AND subscription_ends_at < NOW()
    AND subscription_type = 'annual';  -- Solo anuales, las mensuales se manejan por webhook

-- Limpiar trials vencidos
UPDATE users
SET is_on_trial = 0,
    trial_ends_at = NULL
WHERE is_on_trial = 1
    AND trial_ends_at < NOW();

-- ============================================
-- BACKUP Y RESTORE
-- ============================================

-- Backup de planes
-- mysqldump -u usuario -p database_name storage_plans > backup_plans.sql

-- Backup de suscripciones
-- mysqldump -u usuario -p database_name users --where="subscription_id IS NOT NULL" > backup_subscriptions.sql

-- ============================================
-- NOTAS IMPORTANTES
-- ============================================

/*
1. SIEMPRE hacer backup antes de modificar planes activos

2. Para actualizar precios de Stripe:
   - Crea un nuevo precio en Stripe Dashboard
   - Actualiza el price_id en la tabla storage_plans
   - Los usuarios existentes seguirán con el precio anterior
   
3. Para actualizar precios de PayPal:
   - Crea un nuevo plan en PayPal Dashboard
   - Actualiza el plan_id en la tabla storage_plans
   - Los usuarios existentes seguirán con el plan anterior

4. NUNCA eliminar planes que tengan suscripciones activas
   - En su lugar, marca is_active = 0
   - Esto los oculta de nuevos usuarios pero mantiene las suscripciones existentes

5. Para cambiar el precio de un plan existente:
   - No cambies el plan actual
   - Crea un nuevo plan con el nuevo precio
   - Migra usuarios gradualmente
   - Depreca el plan antiguo marcándolo como is_active = 0

6. Monitoreo recomendado:
   - Revisar suscripciones vencidas diariamente
   - Monitorear webhooks fallidos
   - Alertas para pagos fallidos
   - Reportes mensuales de revenue
*/
