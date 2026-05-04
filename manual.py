import streamlit as st

def render_pestana_manual():
    st.markdown("<h3 style='margin-bottom: 5px;'>📖 Manual de Ayuda y Procedimientos</h3>", unsafe_allow_html=True)
    st.write("Busca cualquier duda sobre el funcionamiento del sistema.")
    
    busqueda = st.text_input("🔍 Buscar en el manual (ej. 'caja', 'devolución', 'cita')...", placeholder="Escribe aquí para buscar...").strip().lower()
    
    st.markdown("---")
    
    def mostrar_manual(ruta_archivo, titulo):
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                contenido = f.read()
        except Exception:
            st.warning(f"No se encontró el archivo: {ruta_archivo}")
            return
            
        st.markdown(f"#### {titulo}")
        
        # Separamos el documento por encabezados de nivel 2 (## )
        secciones = contenido.split("\n## ")
        
        for i, sec in enumerate(secciones):
            if i > 0 or sec.startswith("## "):
                texto_seccion = "## " + sec if i > 0 else sec
            else:
                texto_seccion = sec
                
            if busqueda:
                if busqueda in texto_seccion.lower():
                    with st.expander(sec.split("\n")[0].replace("#", "").strip() or "Sección", expanded=True):
                        st.markdown(texto_seccion)
            else:
                if i == 0:
                    st.markdown(texto_seccion)
                else:
                    titulo_exp = sec.split("\n")[0].replace("#", "").strip()
                    with st.expander(titulo_exp, expanded=False):
                        st.markdown(texto_seccion)

    mostrar_manual("MANUAL_EMPLEADOS.md", "📘 Manual de Empleados")
    
    if st.session_state.get("rol") == "Admin":
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        mostrar_manual("MANUAL_ADMINISTRADORES.md", "👑 Manual de Administrador")