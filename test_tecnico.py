import streamlit as st
from postgrest import SyncPostgrestClient
import json

st.set_page_config(page_title="Test Técnico", page_icon="🧪")
st.title("🧪 Panel de Pruebas Técnicas (Animalarium)")

# 1. TEST DE CONEXIÓN Y SECRETOS
def test_supabase_connection():
    print("--- 🔍 Test 1: Conexión a Supabase ---")
    st.subheader("🔍 Test 1: Conexión a Supabase")
    try:
        url = st.secrets["url"]
        key = st.secrets["key"]
        client = SyncPostgrestClient(f"{url}/rest/v1", headers={
            "apikey": key, "Authorization": f"Bearer {key}"
        })
        # Intentamos una lectura simple
        res = client.table("productos").select("count", count="exact").limit(1).execute()
        print("✅ Conexión establecida con éxito.")
        st.success("✅ Conexión establecida con éxito.")
        return client
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        st.error(f"❌ Error de conexión: {e}")
        return None

# 2. TEST DE ESQUEMA (VERIFICACIÓN DE COLUMNAS NUEVAS)
def test_database_schema(client):
    print("\n--- 🔍 Test 2: Verificación de Columnas Críticas ---")
    st.subheader("🔍 Test 2: Verificación de Columnas Críticas")
    tablas_a_revisar = {
        "facturas": ["descuento_global", "total_final", "productos"odu
        "ventas_historial": ["pago_efectivo", "p
    
    for tabla, columnas in tablas_a_revisar.items():
        try:
            # Pedimos una fila para ver las columnas
            res = client.table(tabla).select("*").limit(1).execute()
            columnas_reales = res.data[0].keys() if res.data else []
            if not res.data:
                print(f"⚠️ La tabla '{tabla}' está vacía, no se puede verificar el esquema visualmente.")
                st.warning(f"⚠️ La tabla '{tabla}' está vacía, asumiendo que el esquema es correcto pero no se puede verificar dinámicamente sin filas.")
                continue
                
            for col in columnas:
                if col in columnas_reales:
                    print(f"✅ Columna '{col}' detectada en '{tabla}'.")
                    st.write(f"✅ Columna `{col}` detectada en `{tabla}`.")
                else:
                    print(f"❌ ERROR: Falta la columna '{col}' en la tabla '{tabla}'.")
                    st.error(f"❌ ERROR: Falta la columna '{col}' en la tabla '{tabla}'.")
        except Exception as e:
            print(f"❌ Error al acceder a la tabla '{tabla}': {e}")
            st.error(f"❌ Error al acceder a la tabla '{tabla}': {e}")

# 3. TEST DE LÓGICA DE STOCK (SIMULACIÓN)
def test_stock_logic(client):
    print("\n--- 🔍 Test 3: Simulación de Lógica de Inventario ---")
    st.subheader("🔍 Test 3: Simulación de Lógica de Inventario")
    # Este test verifica que el código puede leer y escribir stock sin romper tipos de datos
    try:
        res = client.table("productos").select("id, nombre, stock_actual").limit(1).execute()
        if res.data:
            item = res.data[0]
            stock_original = item['stock_actual'] or 0
            id_prod = item['id']
            
            print(f"📦 Producto de prueba: {item['nombre']} (Stock actual: {stock_original})")
            st.write(f"📦 Producto de prueba: **{item['nombre']}** (Stock actual: {stock_original})")
            
            # Simulamos suma de stock (como en una compra)
            nuevo_stock = stock_original + 1
            client.table("productos").update({"stock_actual": nuevo_stock}).eq("id", id_prod).execute()
            
            # Verificamos
            res_v = client.table("productos").select("stock_actual").eq("id", id_prod).execute()
            if res_v.data[0]['stock_actual'] == nuevo_stock:
                print("✅ Lógica de actualización de stock: FUNCIONA.")
                st.success("✅ Lógica de actualización de stock: FUNCIONA (Se sumó correctamente).")
                # Restauramos
                client.table("productos").update({"stock_actual": stock_original}).eq("id", id_prod).execute()
                st.info("🔄 Stock restaurado a su valor original tras la prueba.")
            else:
                print("❌ ERROR: El stock no se actualizó correctamente.")
                st.error("❌ ERROR: El stock no se actualizó correctamente.")
        else:
            print("⚠️ No hay productos para testear stock.")
            st.warning("⚠️ No hay productos para testear stock.")
    except Exception as e:
        print(f"❌ Error en test de stock: {e}")
        st.error(f"❌ Error en test de stock: {e}")

# EJECUCIÓN
if st.button("🚀 EJECUTAR TESTS AHORA", type="primary"):
    c = test_supabase_connection()
    if c:
        test_database_schema(c)
        test_stock_logic(c)