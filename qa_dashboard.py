import streamlit as st
import subprocess
import re

def render_pestana_qa(client=None):
    st.title("🧪 Dashboard Visual de QA (Pruebas Unitarias)")
    st.markdown("Ejecuta la suite de pruebas unitarias y comprueba la salud del código y la cobertura.")
    
    if st.button("🚀 Ejecutar Tests", use_container_width=True, type="primary"):
        with st.spinner("Ejecutando tests... (esto puede tardar unos segundos)"):
            try:
                # Se necesita usar el entorno virtual si existe, pero subprocess.run("pytest") 
                # funcionará si pytest está en el PATH de la consola de Streamlit.
                import os
                env = os.environ.copy()
                env["API_URL"] = "http://animalarium-api:3000"
                result = subprocess.run(
                    ["pytest", "tests/", "--cov=core_crm", "--cov=core_inventario", "--cov=core_tpv", "--cov=core_facturacion", "--cov=core_agenda", "--cov=core_historial", "--cov=core_ficha_clinica", "--cov=core_proveedores", "--cov=core_bancos", "--cov=core_contabilidad", "--cov=core_estadisticas", "--cov=core_marketing", "--cov=core_tareas", "--cov=core_proyectos", "--cov=core_configuracion", "--cov=personal", "--cov=caja", "--cov=caja_acciones", "--cov-report=term"],
                    capture_output=True,
                    text=True,
                    check=False,
                    env=env
                )
                
                output = result.stdout
                error_output = result.stderr
                
                if result.returncode == 0:
                    st.success("✅ **Todos los tests pasaron exitosamente.**")
                else:
                    st.error("❌ **Algunos tests fallaron.** Revisa el output completo para más detalles.")
                
                # Parsear cobertura buscando la línea TOTAL al final de pytest-cov
                coverage_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
                if coverage_match:
                    cov_percent = int(coverage_match.group(1))
                    
                    st.subheader(f"📊 Cobertura Global: {cov_percent}%")
                    st.progress(cov_percent / 100.0)
                    
                    if cov_percent >= 80:
                        st.info("🎉 ¡Objetivo de cobertura superado (>80%)!")
                    else:
                        st.warning("⚠️ La cobertura está por debajo del 80%. Se requieren más tests.")
                else:
                    st.info("No se encontró informe de cobertura. Asegúrate de tener instalado `pytest-cov`.")
                
                with st.expander("🔍 Ver registro completo de ejecución (Log)"):
                    st.code(output, language="text")
                    if error_output:
                        st.code(error_output, language="text")
                        
            except FileNotFoundError:
                st.error("No se encuentra el comando `pytest`. Asegúrate de estar ejecutando Streamlit en el entorno virtual correcto donde está instalado pytest.")
            except Exception as e:
                st.error(f"Error inesperado al ejecutar las pruebas: {str(e)}")

    st.divider()
    st.header("🌍 Simulador de Integración Web (WooCommerce)")
    st.write("Usa este botón para simular la llegada de un pedido web. El sistema buscará o creará al cliente 'Usuario Web Prueba', le calculará los puntos según la configuración y registrará la venta en Contabilidad e Historial.")
    
    if st.button("🛒 Simular Pedido Web Falso (50€)", type="secondary"):
        if client is None:
            st.error("Cliente de base de datos no inyectado.")
            return
            
        with st.spinner("Simulando webhook de WooCommerce..."):
            import json
            import uuid
            from datetime import datetime
            
            # 1. Configuración de Puntos
            cfg = client.table("configuracion_negocio").select("*").eq("id", 1).execute().data
            eur_punto = 10.0
            if cfg: eur_punto = float(cfg[0].get('euros_para_un_punto', 10.0))
            if eur_punto <= 0: eur_punto = 10.0
            
            # 2. Cliente
            telefono_web = "000000000"
            res_cli = client.table("clientes").select("*").eq("telefono", telefono_web).execute()
            if not res_cli.data:
                client.table("clientes").insert({
                    "nombre_dueno": "Usuario Web Prueba",
                    "telefono": telefono_web,
                    "email": "web@prueba.com",
                    "puntos": 0
                }).execute()
                res_cli = client.table("clientes").select("*").eq("telefono", telefono_web).execute()
            
            cli_data = res_cli.data[0]
            cli_id = cli_data['id']
            ptos_antiguos = int(cli_data.get('puntos', 0))
            
            # 3. Puntos
            puntos_ganados = int(50.0 // eur_punto)
            nuevo_saldo = ptos_antiguos + puntos_ganados
            client.table("clientes").update({"puntos": nuevo_saldo}).eq("id", cli_id).execute()
            
            # 4. Venta
            ticket_falso = [{
                "Producto": "Saco Pienso Perro Falso Web",
                "Precio": 50.0,
                "Cantidad": 1,
                "Descuento": 0.0,
                "Subtotal": 50.0,
                "ID": "WEB123"
            }]
            
            client.table("ventas_historial").insert({
                "created_at": datetime.now().isoformat(),
                "total": 50.0,
                "metodo_pago": "Web (WooCommerce)",
                "estado": "Completada",
                "productos": json.dumps(ticket_falso),
                "cliente_deuda": "Usuario Web Prueba",
                "cliente_id": cli_id,
                "descuento_global": 0.0,
                "hash_seguridad": "WEB_MOCK_HASH_" + str(uuid.uuid4())
            }).execute()
            
            st.success(f"✅ Pedido web registrado con éxito. El cliente ganó {puntos_ganados} puntos (Saldo actual: {nuevo_saldo}).")
            st.info("Ve al CRM para ver al cliente 'Usuario Web Prueba' y a Contabilidad/Historial para ver la venta.")
