import toml
import requests
import psycopg2
import json

def fetch_openapi_spec():
    s = toml.load('.streamlit/secrets.toml')
    r = requests.get(s['url'] + '/rest/v1/', headers={'apikey': s['key']})
    r.raise_for_status()
    return r.json()

def map_type(prop):
    fmt = prop.get('format', 'text')
    
    if fmt == 'character varying':
        max_len = prop.get('maxLength')
        if max_len:
            return f'VARCHAR({max_len})'
        return 'VARCHAR'
    if fmt == 'timestamp with time zone':
        return 'TIMESTAMPTZ'
    if fmt == 'timestamp without time zone':
        return 'TIMESTAMP'
    if fmt == 'numeric':
        return 'NUMERIC'
    if fmt == 'integer':
        return 'INTEGER'
    if fmt == 'bigint':
        return 'BIGINT'
    if fmt == 'boolean':
        return 'BOOLEAN'
    if fmt == 'uuid':
        return 'UUID'
    if fmt == 'jsonb':
        return 'JSONB'
    if fmt == 'date':
        return 'DATE'
    
    return 'TEXT'

def build_schema(spec):
    definitions = spec.get('definitions', {})
    sql_statements = []
    
    for table_name, table_def in definitions.items():
        if table_name.startswith('rpc-') or table_name == 'Int8Range':
            continue
            
        columns = []
        pks = []
        
        properties = table_def.get('properties', {})
        for col_name, prop in properties.items():
            pg_type = map_type(prop)
            
            # Check if it's PK
            desc = prop.get('description', '')
            if '<pk/>' in desc:
                pks.append(col_name)
                
            columns.append(f'"{col_name}" {pg_type}')
            
        if pks:
            columns.append(f'PRIMARY KEY ({", ".join(pks)})')
            
        columns_str = ',\n    '.join(columns)
        sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n    {columns_str}\n);'
        sql_statements.append(sql)
        
    return '\n\n'.join(sql_statements)

def sync_to_local(sql_statements):
    conn = psycopg2.connect(
        dbname="tpv_test_db",
        user="admin",
        password="admin_password",
        host="localhost",
        port="5432"
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("Ejecutando SQL...")
    for sql in sql_statements.split(';'):
        if sql.strip():
            print(f"Ejecutando: {sql.strip()[:50]}...")
            cursor.execute(sql)
            
    # Notify Postgrest to reload schema cache
    cursor.execute("NOTIFY pgrst, 'reload schema';")
    print("Schema sincronizado con éxito y PostgREST recargado.")

if __name__ == '__main__':
    spec = fetch_openapi_spec()
    sql = build_schema(spec)
    sync_to_local(sql)
