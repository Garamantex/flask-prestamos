-- =====================================================
-- ÍNDICES DE OPTIMIZACIÓN PARA EL ENDPOINT /box
-- =====================================================
-- Este script contiene índices específicos para mejorar el rendimiento
-- del endpoint /box y otras consultas relacionadas.
-- 
-- IMPORTANTE: Ejecutar estos índices en un entorno de desarrollo primero
-- para verificar que no causen problemas de rendimiento en escritura.

-- =====================================================
-- 1. ÍNDICES PARA TABLA TRANSACTION
-- =====================================================
-- Optimiza consultas por employee_id, fecha y tipo de transacción
CREATE INDEX IF NOT EXISTS idx_transaction_employee_date_type_status 
ON transaction(employee_id, creation_date, transaction_types, approval_status);

-- Optimiza consultas por fecha y tipo de transacción (para agregaciones)
CREATE INDEX IF NOT EXISTS idx_transaction_date_type_status 
ON transaction(creation_date, transaction_types, approval_status);

-- Optimiza consultas por employee_id y fecha (muy frecuente)
CREATE INDEX IF NOT EXISTS idx_transaction_employee_date 
ON transaction(employee_id, creation_date);

-- Optimiza consultas por tipo de transacción y estado de aprobación
CREATE INDEX IF NOT EXISTS idx_transaction_type_status 
ON transaction(transaction_types, approval_status);

-- =====================================================
-- 2. ÍNDICES PARA TABLA LOAN
-- =====================================================
-- Optimiza consultas por employee_id y estado
CREATE INDEX IF NOT EXISTS idx_loan_employee_status 
ON loan(employee_id, status);

-- Optimiza consultas por client_id y estado
CREATE INDEX IF NOT EXISTS idx_loan_client_status 
ON loan(client_id, status);

-- Optimiza consultas por fecha de creación y estado
CREATE INDEX IF NOT EXISTS idx_loan_creation_date_status 
ON loan(creation_date, status);

-- Optimiza consultas por employee_id, fecha y tipo de préstamo
CREATE INDEX IF NOT EXISTS idx_loan_employee_date_renewal 
ON loan(employee_id, creation_date, is_renewal, status, approved);

-- =====================================================
-- 3. ÍNDICES PARA TABLA LOAN_INSTALLMENT
-- =====================================================
-- Optimiza consultas por loan_id y estado (muy frecuente)
CREATE INDEX IF NOT EXISTS idx_loan_installment_loan_status 
ON loan_installment(loan_id, status);

-- Optimiza consultas por fecha de vencimiento y estado
CREATE INDEX IF NOT EXISTS idx_loan_installment_due_date_status 
ON loan_installment(due_date, status);

-- Optimiza consultas por fecha de pago
CREATE INDEX IF NOT EXISTS idx_loan_installment_payment_date 
ON loan_installment(payment_date);

-- =====================================================
-- 4. ÍNDICES PARA TABLA PAYMENT
-- =====================================================
-- Optimiza consultas por installment_id y fecha de pago
CREATE INDEX IF NOT EXISTS idx_payment_installment_date 
ON payment(installment_id, payment_date);

-- Optimiza consultas por fecha de pago (para agregaciones diarias)
CREATE INDEX IF NOT EXISTS idx_payment_date 
ON payment(payment_date);

-- =====================================================
-- 5. ÍNDICES PARA TABLA CLIENT
-- =====================================================
-- Optimiza consultas por employee_id y estado
CREATE INDEX IF NOT EXISTS idx_client_employee_status 
ON client(employee_id, status);

-- Optimiza consultas por employee_id y fecha de creación
CREATE INDEX IF NOT EXISTS idx_client_employee_creation_date 
ON client(employee_id, creation_date);

-- Optimiza consultas por estado de deudor
CREATE INDEX IF NOT EXISTS idx_client_debtor 
ON client(debtor);

-- =====================================================
-- 6. ÍNDICES PARA TABLA EMPLOYEE
-- =====================================================
-- Optimiza consultas por user_id (muy frecuente)
CREATE INDEX IF NOT EXISTS idx_employee_user_id 
ON employee(user_id);

-- Optimiza consultas por estado
CREATE INDEX IF NOT EXISTS idx_employee_status 
ON employee(status);

-- =====================================================
-- 7. ÍNDICES PARA TABLA SALESMAN
-- =====================================================
-- Optimiza consultas por manager_id (muy frecuente en /box)
CREATE INDEX IF NOT EXISTS idx_salesman_manager_id 
ON salesman(manager_id);

-- Optimiza consultas por employee_id
CREATE INDEX IF NOT EXISTS idx_salesman_employee_id 
ON salesman(employee_id);

-- =====================================================
-- 8. ÍNDICES PARA TABLA MANAGER
-- =====================================================
-- Optimiza consultas por employee_id (muy frecuente)
CREATE INDEX IF NOT EXISTS idx_manager_employee_id 
ON manager(employee_id);

-- =====================================================
-- 9. ÍNDICES PARA TABLA EMPLOYEE_RECORD
-- =====================================================
-- Optimiza consultas por employee_id y fecha
CREATE INDEX IF NOT EXISTS idx_employee_record_employee_date 
ON employee_record(employee_id, creation_date);

-- Optimiza consultas por employee_id ordenadas por ID descendente
CREATE INDEX IF NOT EXISTS idx_employee_record_employee_id_desc 
ON employee_record(employee_id, id DESC);

-- =====================================================
-- 10. ÍNDICES PARA TABLA USER
-- =====================================================
-- Optimiza consultas por role (ya existe unique en username)
CREATE INDEX IF NOT EXISTS idx_user_role 
ON user(role);

-- =====================================================
-- ÍNDICES COMPUESTOS ESPECÍFICOS PARA /box
-- =====================================================

-- Índice específico para la consulta de transacciones diarias del coordinador
-- (líneas 1491-1499 y 1502-1510 del endpoint /box)
CREATE INDEX IF NOT EXISTS idx_transaction_daily_coordinator 
ON transaction(transaction_types, approval_status, creation_date, employee_id);

-- Índice específico para consultas de préstamos por vendedor y fecha
-- (líneas 1618-1624 y 1627-1635 del endpoint /box)
CREATE INDEX IF NOT EXISTS idx_loan_salesman_daily 
ON loan(employee_id, creation_date, is_renewal, status, approved);

-- Índice específico para consultas de pagos diarios
-- (líneas 1579-1588 del endpoint /box)
CREATE INDEX IF NOT EXISTS idx_payment_daily_collections 
ON payment(payment_date, installment_id);

-- =====================================================
-- VERIFICACIÓN DE ÍNDICES CREADOS
-- =====================================================
-- Ejecutar esta consulta para verificar que los índices se crearon correctamente:
-- 
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     indexdef
-- FROM pg_indexes 
-- WHERE tablename IN ('transaction', 'loan', 'loan_installment', 'payment', 'client', 'employee', 'salesman', 'manager', 'employee_record', 'user')
-- ORDER BY tablename, indexname;

-- =====================================================
-- NOTAS IMPORTANTES
-- =====================================================
-- 1. Estos índices están optimizados para el endpoint /box específicamente
-- 2. Pueden mejorar significativamente el rendimiento de consultas de lectura
-- 3. Pueden impactar ligeramente el rendimiento de escritura (INSERT/UPDATE/DELETE)
-- 4. Monitorear el rendimiento después de crear los índices
-- 5. Considerar eliminar índices que no se usen frecuentemente
-- 6. Los índices se crean con IF NOT EXISTS para evitar errores si ya existen
