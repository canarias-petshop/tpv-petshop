import streamlit as st
import subprocess
import re

def render_pestana_qa():
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
                    ["pytest", "tests/", "--cov=core_crm", "--cov=core_inventario", "--cov=core_tpv", "--cov=core_facturacion", "--cov=core_agenda", "--cov=core_historial", "--cov=personal", "--cov=caja", "--cov=caja_acciones", "--cov-report=term"],
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
