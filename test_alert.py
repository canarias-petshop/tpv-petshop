import sys
try:
    import streamlit as st
    from app import init_supabase
    client = init_supabase()
    from proveedores import fetch_proveedores, get_alertas_manuales
    res_provs = fetch_proveedores(client)
    if res_provs.data:
        alertas = get_alertas_manuales(res_provs.data)["urgentes"]
        print("Alertas:", alertas)
    else:
        print("No data")
except Exception as e:
    import traceback
    traceback.print_exc()
