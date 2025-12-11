import sqlite3
import time
from datetime import datetime

def monitor_yogurt():
    """Monitorear cambios en el stock del Yogurt 11111"""
    conn = sqlite3.connect('pos_cremeria.db')
    cursor = conn.cursor()
    
    print("="*60)
    print("MONITOREANDO YOGURT 11111 - Presiona Ctrl+C para detener")
    print("="*60)
    
    # Obtener estado inicial
    cursor.execute("SELECT stock, stock_kg FROM productos WHERE codigo = '11111'")
    resultado = cursor.fetchone()
    stock_anterior = resultado[0] if resultado else None
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stock inicial: {stock_anterior} unidades")
    
    try:
        while True:
            time.sleep(2)  # Verificar cada 2 segundos
            
            cursor.execute("SELECT stock, stock_kg FROM productos WHERE codigo = '11111'")
            resultado = cursor.fetchone()
            
            if resultado:
                stock_actual = resultado[0]
                
                if stock_actual != stock_anterior:
                    print(f"\n🔔 [{datetime.now().strftime('%H:%M:%S')}] ¡CAMBIO DETECTADO!")
                    print(f"   Stock anterior: {stock_anterior} unidades")
                    print(f"   Stock actual: {stock_actual} unidades")
                    print(f"   Diferencia: {stock_actual - stock_anterior}")
                    
                    # Verificar última venta
                    cursor.execute("""
                        SELECT fecha, cantidad, total 
                        FROM ventas 
                        WHERE codigo = '11111' 
                        ORDER BY fecha DESC 
                        LIMIT 1
                    """)
                    ultima_venta = cursor.fetchone()
                    if ultima_venta:
                        print(f"   Última venta: {ultima_venta[0]} - {ultima_venta[1]} unidades")
                    
                    stock_anterior = stock_actual
    
    except KeyboardInterrupt:
        print("\n\n✅ Monitoreo detenido")
    finally:
        conn.close()

if __name__ == "__main__":
    monitor_yogurt()
