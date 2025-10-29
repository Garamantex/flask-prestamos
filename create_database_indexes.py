#!/usr/bin/env python3
"""
Script para crear índices de base de datos que optimicen el endpoint /box
Este script debe ejecutarse con cuidado y preferiblemente en un entorno de desarrollo primero.
"""

import os
import sys
from sqlalchemy import text
from app import create_app, db

def create_indexes():
    """Crea los índices de optimización para el endpoint /box"""
    
    # Lista de índices a crear con sus definiciones SQL
    indexes = [
        # 1. ÍNDICES PARA TABLA TRANSACTION
        {
            'name': 'idx_transaction_employee_date_type_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_transaction_employee_date_type_status ON transaction(employee_id, creation_date, transaction_types, approval_status)'
        },
        {
            'name': 'idx_transaction_date_type_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_transaction_date_type_status ON transaction(creation_date, transaction_types, approval_status)'
        },
        {
            'name': 'idx_transaction_employee_date',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_transaction_employee_date ON transaction(employee_id, creation_date)'
        },
        {
            'name': 'idx_transaction_type_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_transaction_type_status ON transaction(transaction_types, approval_status)'
        },
        
        # 2. ÍNDICES PARA TABLA LOAN
        {
            'name': 'idx_loan_employee_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_loan_employee_status ON loan(employee_id, status)'
        },
        {
            'name': 'idx_loan_client_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_loan_client_status ON loan(client_id, status)'
        },
        {
            'name': 'idx_loan_creation_date_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_loan_creation_date_status ON loan(creation_date, status)'
        },
        {
            'name': 'idx_loan_employee_date_renewal',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_loan_employee_date_renewal ON loan(employee_id, creation_date, is_renewal, status, approved)'
        },
        
        # 3. ÍNDICES PARA TABLA LOAN_INSTALLMENT
        {
            'name': 'idx_loan_installment_loan_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_loan_installment_loan_status ON loan_installment(loan_id, status)'
        },
        {
            'name': 'idx_loan_installment_due_date_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_loan_installment_due_date_status ON loan_installment(due_date, status)'
        },
        {
            'name': 'idx_loan_installment_payment_date',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_loan_installment_payment_date ON loan_installment(payment_date)'
        },
        
        # 4. ÍNDICES PARA TABLA PAYMENT
        {
            'name': 'idx_payment_installment_date',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_payment_installment_date ON payment(installment_id, payment_date)'
        },
        {
            'name': 'idx_payment_date',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_payment_date ON payment(payment_date)'
        },
        
        # 5. ÍNDICES PARA TABLA CLIENT
        {
            'name': 'idx_client_employee_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_client_employee_status ON client(employee_id, status)'
        },
        {
            'name': 'idx_client_employee_creation_date',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_client_employee_creation_date ON client(employee_id, creation_date)'
        },
        {
            'name': 'idx_client_debtor',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_client_debtor ON client(debtor)'
        },
        
        # 6. ÍNDICES PARA TABLA EMPLOYEE
        {
            'name': 'idx_employee_user_id',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_employee_user_id ON employee(user_id)'
        },
        {
            'name': 'idx_employee_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_employee_status ON employee(status)'
        },
        
        # 7. ÍNDICES PARA TABLA SALESMAN
        {
            'name': 'idx_salesman_manager_id',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_salesman_manager_id ON salesman(manager_id)'
        },
        {
            'name': 'idx_salesman_employee_id',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_salesman_employee_id ON salesman(employee_id)'
        },
        
        # 8. ÍNDICES PARA TABLA MANAGER
        {
            'name': 'idx_manager_employee_id',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_manager_employee_id ON manager(employee_id)'
        },
        
        # 9. ÍNDICES PARA TABLA EMPLOYEE_RECORD
        {
            'name': 'idx_employee_record_employee_date',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_employee_record_employee_date ON employee_record(employee_id, creation_date)'
        },
        {
            'name': 'idx_employee_record_employee_id_desc',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_employee_record_employee_id_desc ON employee_record(employee_id, id DESC)'
        },
        
        # 10. ÍNDICES PARA TABLA USER
        {
            'name': 'idx_user_role',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_user_role ON user(role)'
        },
        
        # ÍNDICES COMPUESTOS ESPECÍFICOS PARA /box
        {
            'name': 'idx_transaction_daily_coordinator',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_transaction_daily_coordinator ON transaction(transaction_types, approval_status, creation_date, employee_id)'
        },
        {
            'name': 'idx_loan_salesman_daily',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_loan_salesman_daily ON loan(employee_id, creation_date, is_renewal, status, approved)'
        },
        {
            'name': 'idx_payment_daily_collections',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_payment_daily_collections ON payment(payment_date, installment_id)'
        }
    ]
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 Iniciando creación de índices de optimización...")
            print(f"📊 Total de índices a crear: {len(indexes)}")
            print("-" * 60)
            
            created_count = 0
            skipped_count = 0
            
            for i, index_info in enumerate(indexes, 1):
                try:
                    print(f"[{i:2d}/{len(indexes)}] Creando índice: {index_info['name']}")
                    
                    # Ejecutar la creación del índice
                    db.session.execute(text(index_info['sql']))
                    db.session.commit()
                    
                    print(f"    ✅ Índice creado exitosamente")
                    created_count += 1
                    
                except Exception as e:
                    print(f"    ⚠️  Error creando índice: {str(e)}")
                    db.session.rollback()
                    skipped_count += 1
                    continue
            
            print("-" * 60)
            print(f"📈 Resumen de la operación:")
            print(f"   ✅ Índices creados: {created_count}")
            print(f"   ⚠️  Índices omitidos: {skipped_count}")
            print(f"   📊 Total procesados: {len(indexes)}")
            
            if created_count > 0:
                print("\n🎉 ¡Índices creados exitosamente!")
                print("💡 Recomendaciones:")
                print("   1. Monitorear el rendimiento de la aplicación")
                print("   2. Verificar que las consultas del endpoint /box sean más rápidas")
                print("   3. Considerar ejecutar ANALYZE en las tablas afectadas")
                print("   4. Monitorear el uso de espacio en disco")
            
        except Exception as e:
            print(f"❌ Error general durante la creación de índices: {str(e)}")
            db.session.rollback()
            return False
    
    return True

def verify_indexes():
    """Verifica que los índices se crearon correctamente"""
    app = create_app()
    
    with app.app_context():
        try:
            # Consulta para verificar índices existentes
            query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE tablename IN ('transaction', 'loan', 'loan_installment', 'payment', 'client', 'employee', 'salesman', 'manager', 'employee_record', 'user')
                AND indexname LIKE 'idx_%'
                ORDER BY tablename, indexname;
            """)
            
            result = db.session.execute(query)
            indexes = result.fetchall()
            
            print("\n🔍 Verificación de índices creados:")
            print("-" * 80)
            
            if indexes:
                for index in indexes:
                    print(f"📋 {index[2]} en tabla {index[1]}")
            else:
                print("⚠️  No se encontraron índices de optimización")
                
        except Exception as e:
            print(f"❌ Error verificando índices: {str(e)}")

def main():
    """Función principal"""
    print("=" * 60)
    print("🔧 CREADOR DE ÍNDICES DE OPTIMIZACIÓN - ENDPOINT /box")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('app'):
        print("❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Crear índices
    success = create_indexes()
    
    if success:
        # Verificar índices creados
        verify_indexes()
        
        print("\n" + "=" * 60)
        print("✅ Proceso completado exitosamente")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ El proceso falló. Revisar los errores anteriores.")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
