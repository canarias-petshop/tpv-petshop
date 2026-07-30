import pytest
import sys
import os
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_marketing import (
    calcular_progreso_objetivo,
    verificar_alertas_plan_marketing,
    clasificar_tipo_kpi,
    cita_esta_excluida,
    media_citas_por_semana,
    ticket_medio_de_ventas,
    suma_facturacion_ventas,
    media_ocupacion_talleres,
    calcular_packs_calma,
    calcular_valor_kpi,
    sincronizar_objetivos_desde_tpv,
)

KPI_H2 = [
    ("Citas peluquería confirmadas / semana", "citas_semana"),
    ("Altas nuevas en CRM", "altas_crm"),
    ("€ ticket medio TPV (productos)", "ticket_medio"),
    ("% plazas ocupadas (media talleres)", "ocupacion_talleres"),
    ("€ ventas atribuidas / € gastado (Ads + cartelería)", "roi_ads"),
    ("€ facturación productos campaña Nov-Dic", "facturacion_productos"),
    ("Talleres/consultas anti-estrés + packs calma vendidos", "packs_calma"),
]


def test_calcular_progreso_objetivo():
    assert calcular_progreso_objetivo(50, 100) == 0.5
    assert calcular_progreso_objetivo(150, 100) == 1.0  # Should cap at 1.0
    assert calcular_progreso_objetivo(50, 0) == 0.0  # Division by zero prevention
    assert calcular_progreso_objetivo(0, 100) == 0.0
    assert calcular_progreso_objetivo(-10, 100) == 0.0  # Negative progress prevention


def test_verificar_alertas_plan_marketing():
    hoy = date.today()

    # Error: less than 30 days
    fecha_error = (hoy + timedelta(days=20)).strftime('%Y-%m-%d')
    res_error = verificar_alertas_plan_marketing(fecha_error)
    assert res_error is not None
    assert res_error["nivel"] == "error"

    # Warning: 31-45 days
    fecha_warning = (hoy + timedelta(days=40)).strftime('%Y-%m-%d')
    res_warning = verificar_alertas_plan_marketing(fecha_warning)
    assert res_warning is not None
    assert res_warning["nivel"] == "warning"

    # None: > 45 days
    fecha_ok = (hoy + timedelta(days=60)).strftime('%Y-%m-%d')
    res_ok = verificar_alertas_plan_marketing(fecha_ok)
    assert res_ok is None

    # None: empty date
    assert verificar_alertas_plan_marketing("") is None
    assert verificar_alertas_plan_marketing(None) is None
    assert verificar_alertas_plan_marketing("fecha-invalida") is None
    # Caducado (días negativos) -> sin alerta
    fecha_pasada = (hoy - timedelta(days=5)).strftime("%Y-%m-%d")
    assert verificar_alertas_plan_marketing(fecha_pasada) is None


def test_calcular_progreso_objetivo_entradas_invalidas():
    assert calcular_progreso_objetivo("abc", 100) == 0.0
    assert calcular_progreso_objetivo(10, "x") == 0.0
    assert calcular_progreso_objetivo("25", "50") == 0.5


def test_clasificar_tipo_kpi_h2_y_desconocido():
    for texto, esperado in KPI_H2:
        assert clasificar_tipo_kpi(texto) == esperado, texto
    assert clasificar_tipo_kpi("Nº de likes en Instagram") == "desconocido"
    assert clasificar_tipo_kpi("") == "desconocido"
    assert clasificar_tipo_kpi(None) == "desconocido"


def test_cita_excluida_y_media_semanal():
    assert cita_esta_excluida("[ESTADO: Cancelada] Baño") is True
    assert cita_esta_excluida("[ESTADO: Anulada] X") is True
    assert cita_esta_excluida("[ESTADO: No presentado] Y") is True
    assert cita_esta_excluida("[ESTADO: Confirmada] Baño") is False
    assert cita_esta_excluida("Baño (Ana)") is False

    citas = [
        {"servicio": "Baño (Ana)"},
        {"servicio": "Corte (Juan)"},
        {"servicio": "[ESTADO: Cancelada] Baño"},
        {"servicio": "[ESTADO: Anulada] X"},
        {"servicio": "[ESTADO: No presentado] Y"},
        {"servicio": "[ESTADO: Confirmada] Spa"},
    ]
    # 14 días = 2 semanas; 3 citas válidas → 1.5
    media = media_citas_por_semana(citas, "2026-08-01", "2026-08-14")
    assert media == 1.5


def test_ticket_medio_y_facturacion_ignoran_devuelto():
    ventas = [
        {"total": 100.0, "estado": "Completado"},
        {"total": 50.0, "estado": "Completado"},
        {"total": 999.0, "estado": "DEVUELTO"},
    ]
    assert ticket_medio_de_ventas(ventas) == 75.0
    assert suma_facturacion_ventas(ventas) == 150.0
    assert ticket_medio_de_ventas([]) is None
    assert ticket_medio_de_ventas([{"total": 10, "estado": "DEVUELTO"}]) is None


def test_media_ocupacion_talleres():
    talleres = [
        {"id": 1, "plazas_totales": 10},
        {"id": 2, "plazas_totales": 8},
        {"id": 3, "plazas_totales": 0},  # ignorar
    ]
    asist = {1: 5, 2: 8}  # 50% y 100% → media 75
    assert media_ocupacion_talleres(talleres, asist) == 75.0
    assert media_ocupacion_talleres([], {}) is None


def test_packs_calma_omite_sin_match_y_cuenta_con_datos():
    assert calcular_packs_calma(
        [{"id": 1, "titulo": "Higiene básica"}],
        {1: 3},
        [{"estado": "Completado", "productos": [{"Producto": "Pienso", "Cantidad": 2}]}],
    ) is None

    talleres = [{"id": 10, "titulo": "Miedos, estrés y pirotecnia"}]
    ventas = [{
        "estado": "Completado",
        "productos": [{"Producto": "Pack calma nochevieja", "Cantidad": 2}],
    }]
    assert calcular_packs_calma(talleres, {10: 4}, ventas) == 6.0


def test_calcular_valor_kpi_roi_y_desconocido_none():
    client = MagicMock()
    assert calcular_valor_kpi(client, "roi_ads", "2026-08-01", "2026-12-31") is None
    assert calcular_valor_kpi(client, "desconocido", "2026-08-01", "2026-12-31") is None
    client.table.assert_not_called()


def test_sincronizar_objetivos_actualiza_omite_y_no_cambia_estado():
    client = MagicMock()

    objetivos = [
        {
            "id": 1,
            "titulo": "Altas",
            "kpi_medidor": "Altas nuevas en CRM",
            "estado": "En progreso",
            "valor_actual": 0,
            "fecha_inicio": "2026-08-01",
            "fecha_fin": "2026-08-31",
        },
        {
            "id": 2,
            "titulo": "ROI",
            "kpi_medidor": "€ ventas atribuidas / € gastado (Ads + cartelería)",
            "estado": "En progreso",
            "valor_actual": 0,
            "fecha_inicio": "2026-08-01",
            "fecha_fin": "2026-12-31",
        },
        {
            "id": 3,
            "titulo": "Hecho",
            "kpi_medidor": "Altas nuevas en CRM",
            "estado": "Completado",
            "valor_actual": 80,
            "fecha_inicio": "2026-08-01",
            "fecha_fin": "2026-12-31",
        },
        {
            "id": 4,
            "titulo": "Raro",
            "kpi_medidor": "Likes virales",
            "estado": "En progreso",
            "valor_actual": 5,
            "fecha_inicio": "2026-08-01",
            "fecha_fin": "2026-12-31",
        },
    ]

    with patch("core_marketing.calcular_valor_kpi") as mock_calc:
        def _side(client, tipo, fi, ff):
            if tipo == "altas_crm":
                return 12.0
            return None

        mock_calc.side_effect = _side
        resumen = sincronizar_objetivos_desde_tpv(client, objetivos)

    por_id = {r["id"]: r for r in resumen}
    assert 3 not in por_id  # Completado no se toca
    assert por_id[1]["accion"] == "actualizado"
    assert por_id[1]["valor_despues"] == 12.0
    assert por_id[2]["accion"] == "omitido"
    assert por_id[4]["accion"] == "omitido"

    # Solo un update y solo valor_actual
    assert client.table.call_count == 1
    client.table.assert_called_with("marketing_objetivos")
    update_call = client.table.return_value.update
    update_call.assert_called_once_with({"valor_actual": 12.0})
    update_call.return_value.eq.assert_called_once_with("id", 1)


def test_sincronizar_objetivos_error_en_calculo():
    client = MagicMock()
    objetivos = [{
        "id": 9,
        "titulo": "Citas",
        "kpi_medidor": "Citas peluquería confirmadas / semana",
        "estado": "En progreso",
        "valor_actual": 1,
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-31",
    }]
    with patch("core_marketing.calcular_valor_kpi", side_effect=RuntimeError("boom")):
        resumen = sincronizar_objetivos_desde_tpv(client, objetivos)
    assert resumen[0]["accion"] == "error"
    client.table.return_value.update.assert_not_called()


def test_sync_cron_script_resumir_y_main_desactivado():
    from scripts.sync_marketing_kpis_cron import resumir_sync, main, cron_habilitado

    resumen = [
        {"accion": "actualizado"},
        {"accion": "omitido"},
        {"accion": "error"},
    ]
    assert "1 actualizado" in resumir_sync(resumen)
    assert cron_habilitado() is True

    with patch.dict(os.environ, {"MKT_KPIS_CRON_ENABLED": "false"}):
        assert cron_habilitado() is False
        assert main([]) == 0


def test_sync_cron_script_run_sync_con_mock():
    from scripts.sync_marketing_kpis_cron import run_sync

    fake = [{"accion": "actualizado", "titulo": "Test"}]
    with patch("scripts.sync_marketing_kpis_cron.build_postgrest_client") as mock_cli:
        with patch("scripts.sync_marketing_kpis_cron.sincronizar_objetivos_desde_tpv", return_value=fake):
            out = run_sync()
    assert len(out) == 1
    mock_cli.assert_called_once()
