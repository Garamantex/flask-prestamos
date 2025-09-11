-- =====================================================
-- RECOMENDACIONES DE OPTIMIZACIÓN DE BASE DE DATOS
-- Para el endpoint /box optimizado
-- =====================================================

-- 1. ÍNDICES PARA TRANSACCIONES (críticos para performance)
-- Estos índices son esenciales para las consultas de transacciones diarias

-- Índice compuesto para transacciones por empleado, fecha y tipo
CREATE INDEX IF NOT EXISTS idx_transactions_employee_date_type_status 
ON transactions (employee_id, creation_date, transaction_types, approval_status);

-- Índice para transacciones por fecha (usado en filtros de fecha)
CREATE INDEX IF NOT EXISTS idx_transactions_creation_date 
ON transactions (creation_date);

-- Índice para transacciones por empleado y fecha
CREATE INDEX IF NOT EXISTS idx_transactions_employee_date 
ON transactions (employee_id, creation_date);

-- 2. ÍNDICES PARA PAGOS (cobros diarios)
-- Optimiza las consultas de cobros por fecha

CREATE INDEX IF NOT EXISTS idx_payments_date 
ON payments (payment_date);

-- Índice compuesto para pagos con instalment
CREATE INDEX IF NOT EXISTS idx_payments_installment_date 
ON payments (installment_id, payment_date);

-- 3. ÍNDICES PARA PRÉSTAMOS
-- Optimiza consultas de préstamos por cliente y fechas

CREATE INDEX IF NOT EXISTS idx_loans_client_creation 
ON loans (client_id, creation_date);

CREATE INDEX IF NOT EXISTS idx_loans_creation_date 
ON loans (creation_date);

CREATE INDEX IF NOT EXISTS idx_loans_renewal_status 
ON loans (is_renewal, status, approved, creation_date);

-- 4. ÍNDICES PARA CLIENTES
-- Optimiza consultas de clientes por empleado

CREATE INDEX IF NOT EXISTS idx_clients_employee_creation 
ON clients (employee_id, creation_date);

-- 5. ÍNDICES PARA EMPLEADOS Y VENDEDORES
-- Optimiza las relaciones entre empleados y vendedores

CREATE INDEX IF NOT EXISTS idx_salesmen_manager 
ON salesmen (manager_id);

CREATE INDEX IF NOT EXISTS idx_managers_employee 
ON managers (employee_id);

-- 6. ÍNDICES PARA EMPLOYEE_RECORDS
-- Optimiza consultas de registros de empleados

CREATE INDEX IF NOT EXISTS idx_employee_records_employee_date 
ON employee_records (employee_id, creation_date);

CREATE INDEX IF NOT EXISTS idx_employee_records_employee_id_desc 
ON employee_records (employee_id, id DESC);

-- 7. ÍNDICES PARA CUOTAS DE PRÉSTAMOS
-- Optimiza consultas de cuotas pendientes

CREATE INDEX IF NOT EXISTS idx_loan_installments_loan_due_date 
ON loan_installments (loan_id, due_date);

CREATE INDEX IF NOT EXISTS idx_loan_installments_status 
ON loan_installments (status);

-- 8. ÍNDICES PARA USUARIOS
-- Optimiza consultas de usuarios por empleado

CREATE INDEX IF NOT EXISTS idx_employees_user_id 
ON employees (user_id);

-- 9. ANÁLISIS DE RENDIMIENTO
-- Consultas para monitorear el rendimiento

-- Verificar uso de índices
EXPLAIN ANALYZE 
SELECT t.employee_id, t.transaction_types, SUM(t.amount) as total_amount, COUNT(t.id) as count
FROM transactions t
WHERE t.employee_id IN (1, 2, 3, 4, 5)
  AND DATE(t.creation_date) = CURRENT_DATE
  AND t.approval_status = 'APROBADA'
GROUP BY t.employee_id, t.transaction_types;

-- 10. CONFIGURACIONES DE POSTGRESQL RECOMENDADAS
-- (Aplicar en postgresql.conf para producción)

-- shared_buffers = 256MB (25% de RAM)
-- effective_cache_size = 1GB (75% de RAM)
-- work_mem = 4MB
-- maintenance_work_mem = 64MB
-- random_page_cost = 1.1 (para SSD)
-- effective_io_concurrency = 200 (para SSD)

-- 11. ESTADÍSTICAS DE TABLAS
-- Actualizar estadísticas regularmente

ANALYZE transactions;
ANALYZE payments;
ANALYZE loans;
ANALYZE clients;
ANALYZE employees;
ANALYZE salesmen;
ANALYZE employee_records;

-- 12. MONITOREO DE RENDIMIENTO
-- Consultas para identificar cuellos de botella

-- Verificar consultas lentas
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
WHERE query LIKE '%transactions%' OR query LIKE '%payments%'
ORDER BY mean_time DESC
LIMIT 10;

-- Verificar uso de índices
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename IN ('transactions', 'payments', 'loans', 'clients')
ORDER BY idx_scan DESC;

-- 13. RECOMENDACIONES ADICIONALES

-- Particionado de tabla transactions por fecha (para grandes volúmenes)
-- CREATE TABLE transactions_y2024 PARTITION OF transactions
-- FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Limpieza periódica de datos antiguos
-- DELETE FROM transactions WHERE creation_date < NOW() - INTERVAL '2 years';

-- 14. CONFIGURACIÓN DE CONEXIONES
-- Para aplicaciones Flask con alta concurrencia

-- max_connections = 200
-- shared_preload_libraries = 'pg_stat_statements'
-- track_activity_query_size = 2048
-- log_min_duration_statement = 1000  -- Log queries > 1 second

-- 15. BACKUP Y MANTENIMIENTO
-- Scripts de mantenimiento recomendados

-- VACUUM ANALYZE transactions;
-- REINDEX TABLE transactions;
-- pg_dump --verbose --clean --no-acl --no-owner -h localhost database_name > backup.sql
