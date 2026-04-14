#!/usr/bin/env python3
"""
Script simple para optimizar el endpoint /box creando índices de base de datos
Ejecutar desde el directorio raíz del proyecto: python optimize_box_endpoint.py
"""

import os
import sys
from sqlalchemy import text

# Agregar el directorio actual al path para importar la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def main():
    """Función principal para crear índices de optimización"""
    
    print("🔧 Optimizando endpoint /box - Creando índices de base de datos")
    print("=" * 70)
    
    # Crear la aplicación Flask
    app = create_app()
    
    with app.app_context():
        try:
            # Lista de índices críticos para el endpoint /box
            critical_indexes = [
                # Índices más críticos para el endpoint /box
                "CREATE INDEX IF NOT EXISTS idx_transaction_employee_date_type_status ON transaction(employee_id, creation_date, transaction_types, approval_status)",
                "CREATE INDEX IF NOT EXISTS idx_loan_employee_status ON loan(employee_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_loan_installment_loan_status ON loan_installment(loan_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_payment_installment_date ON payment(installment_id, payment_date)",
                "CREATE INDEX IF NOT EXISTS idx_salesman_manager_id ON salesman(manager_id)",
                "CREATE INDEX IF NOT EXISTS idx_manager_employee_id ON manager(employee_id)",
                "CREATE INDEX IF NOT EXISTS idx_employee_user_id ON employee(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_client_employee_status ON client(employee_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_loan_employee_date_renewal ON loan(employee_id, creation_date, is_renewal, status, approved)",
                "CREATE INDEX IF NOT EXISTS idx_payment_date ON payment(payment_date)"
            ]
            
            print(f"📊 Creando {len(critical_indexes)} índices críticos...")
            print()
            
            success_count = 0
            
            for i, index_sql in enumerate(critical_indexes, 1):
                try:
                    print(f"[{i:2d}] Ejecutando índice...")
                    db.session.execute(text(index_sql))
                    db.session.commit()
                    print(f"     ✅ Índice creado exitosamente")
                    success_count += 1
                    
                except Exception as e:
                    print(f"     ❌ Error: {str(e)}")
                    db.session.rollback()
                    continue
            
            print()
            print("=" * 70)
            print(f"📈 Resumen: {success_count}/{len(critical_indexes)} índices creados exitosamente")
            
            if success_count > 0:
                print()
                print("🎉 ¡Optimización completada!")
                print()
                print("💡 Próximos pasos recomendados:")
                print("   1. Probar el endpoint /box para verificar mejoras en rendimiento")
                print("   2. Monitorear el tiempo de respuesta")
                print("   3. Verificar que no hay errores en la aplicación")
                print()
                print("⚠️  Nota: Los índices pueden tardar unos minutos en ser efectivos")
                print("   dependiendo del tamaño de la base de datos.")
            else:
                print("❌ No se pudieron crear los índices. Revisar los errores anteriores.")
                
        except Exception as e:
            print(f"❌ Error general: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('app'):
        print("❌ Error: Ejecutar desde el directorio raíz del proyecto")
        print("   Directorio actual:", os.getcwd())
        print("   Debe contener la carpeta 'app'")
        sys.exit(1)
    
    success = main()
    
    if not success:
        sys.exit(1)
