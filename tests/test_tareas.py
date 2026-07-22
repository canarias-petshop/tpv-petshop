import pytest
import sys
import os
import pandas as pd
from datetime import date
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_tareas import generar_proyeccion_virtual

def test_generar_proyeccion_virtual():
    tareas_db = [
        {
            'titulo': 'Limpiar jaulas',
            'periodicidad': 'Diario',
            'fecha_programada': '2023-10-01',
            'notas': 'Usar desinfectante'
        },
        {
            'titulo': 'Reunión de equipo',
            'periodicidad': 'Semanal',
            'fecha_programada': '2023-10-02', # Lunes
            'notas': ''
        },
        {
            'titulo': 'Tarea puntual',
            'periodicidad': 'Puntual',
            'fecha_programada': '2023-10-15',
            'notas': ''
        }
    ]
    
    start_str = '2023-10-10'
    end_str = '2023-10-20'
    
    proyectadas = generar_proyeccion_virtual(tareas_db, start_str, end_str)
    
    # 1. Puntual in range (10-15 to 10-20) -> 2023-10-15 is in range. 1 tarea.
    # 2. Diario (11 days, 10th to 20th inclusive) -> 11 tareas.
    # 3. Semanal (started 2023-10-02). Next are 09, 16. In range: 16 -> 1 tarea.
    # Total: 11 + 1 + 1 = 13
    
    assert len(proyectadas) == 13
    
    titulos = [p['titulo'] for p in proyectadas]
    assert titulos.count('Tarea puntual') == 1
    assert titulos.count('Reunión de equipo') == 1
    assert titulos.count('Limpiar jaulas') == 11
    
    # Check that virtual is set correctly for projected tasks
    diarias = [p for p in proyectadas if p['titulo'] == 'Limpiar jaulas']
    assert all(p['es_virtual'] for p in diarias)
    
    puntuales = [p for p in proyectadas if p['titulo'] == 'Tarea puntual']
    assert not puntuales[0]['es_virtual']
