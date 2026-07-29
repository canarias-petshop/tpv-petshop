#!/usr/bin/env python3
"""
Semilla LOCAL (no producción): plan marketing H2 2026 Animalarium (Canarias).

Ritmo atractivo (no saturar):
- Instagram tienda: ~3 posts/semana (lun / mié / vie)
- Talleres intercalados con pocos anuncios (previsión + víspera + día/recap)
- Posts Instagram ~3/semana (lun/mié/vie) — ritmo atractivo
- Talleres fin de semana (sábado o domingo)
- 150 €/mes repartidos entre soportes con coste:
    Instagram/Facebook Ads ~70 · Google Ads ~45 · Cartelería ~35 · WhatsApp = 0 (manual)

Uso:
  python scripts/seed_marketing_h2_2026_local.py          # BD local Docker
  python scripts/seed_marketing_h2_2026_local.py --prod   # Supabase producción (secrets.toml)
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from typing import Any, Optional
from urllib.parse import quote

API = "http://localhost:3001"
AUTH_HEADERS: dict[str, str] = {}


def configure_target(prod: bool = False) -> str:
    """Local (default) o producción vía .streamlit/secrets.toml."""
    global API, AUTH_HEADERS
    if not prod:
        API = "http://localhost:3001"
        AUTH_HEADERS = {}
        return "local"
    import tomllib
    from pathlib import Path
    secrets_path = Path(__file__).resolve().parents[1] / ".streamlit" / "secrets.toml"
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
    raw = str(secrets.get("url", "")).strip().strip('"').strip("'").rstrip("/")
    key = str(secrets.get("key", "")).strip().strip('"').strip("'")
    if not raw or not key:
        raise SystemExit("Faltan url/key en .streamlit/secrets.toml para producción.")
    API = raw if raw.endswith("/rest/v1") else f"{raw}/rest/v1"
    AUTH_HEADERS = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }
    return "production"


def api(method: str, path: str, body: Optional[Any] = None, prefer: Optional[str] = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        **AUTH_HEADERS,
    }
    if prefer:
        headers["Prefer"] = prefer
    req = urllib.request.Request(f"{API}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code} {path}: {err}") from e


def http_delete(path: str) -> None:
    req = urllib.request.Request(
        f"{API}{path}",
        method="DELETE",
        headers={**AUTH_HEADERS, "Prefer": "return=minimal", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120):
        pass


CANAL_IG = "📱 Instagram / Facebook"
CANAL_ADS = "💰 Campaña Pagada (Ads)"
CANAL_WA = "💬 WhatsApp a Clientes"
CANAL_CART = "🏬 Cartelería / Diseño Físico"

CAT_DIG = "Digital (RRSS/Email)"
CAT_FIS = "Físico (Cartelería/Flyers)"

TIPO_ORD = "Acción Ordinaria (Día a Día)"
TIPO_EVT = "Campaña de Evento/Feria"
TIPO_INN = "Iniciativa Innovate"

EST = "Idea / Planificado"

HASHTAGS = "#Animalarium #MascotasTenerife #PeluqueriaCanina #Tenerife #Canarias"


OBJETIVOS = [
    {
        "titulo": "H2 · Agenda peluquería llena (Canarias)",
        "kpi_medidor": "Citas peluquería confirmadas / semana",
        "meta_cuantitativa": 45,
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-31",
        "estado": "En progreso",
        "valor_actual": 0,
        "notas": "IG ~3/sem + 150€/mes repartidos (IG Ads, Google, cartelería) + WA gratis.",
    },
    {
        "titulo": "H2 · Clientes nuevos captados",
        "kpi_medidor": "Altas nuevas en CRM",
        "meta_cuantitativa": 80,
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-31",
        "estado": "En progreso",
        "valor_actual": 0,
        "notas": "Contenido redes + Ads IG/Google + talleres.",
    },
    {
        "titulo": "H2 · Ticket medio tienda (otoño-navidad)",
        "kpi_medidor": "€ ticket medio TPV (productos)",
        "meta_cuantitativa": 32,
        "fecha_inicio": "2026-09-01",
        "fecha_fin": "2026-12-31",
        "estado": "En progreso",
        "valor_actual": 0,
        "notas": "Posts de producto + cartelería + BF/Navidad.",
    },
    {
        "titulo": "H2 · Ocupación talleres clientes",
        "kpi_medidor": "% plazas ocupadas (media talleres)",
        "meta_cuantitativa": 85,
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-31",
        "estado": "En progreso",
        "valor_actual": 0,
        "notas": "Anunciar cada taller ≥2–3 semanas antes (sáb o dom).",
    },
    {
        "titulo": "H2 · ROI inversión 150 €/mes (todos los soportes)",
        "kpi_medidor": "€ ventas atribuidas / € gastado (Ads + cartelería)",
        "meta_cuantitativa": 3,
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-31",
        "estado": "En progreso",
        "valor_actual": 0,
        "notas": "Reparto mensual: IG/FB Ads ~70€ · Google ~45€ · Cartelería ~35€ · WA 0€ (manual).",
    },
    {
        "titulo": "Q4 · Campaña Black Friday + Navidad",
        "kpi_medidor": "€ facturación productos campaña Nov-Dic",
        "meta_cuantitativa": 12000,
        "fecha_inicio": "2026-11-01",
        "fecha_fin": "2026-12-31",
        "estado": "En progreso",
        "valor_actual": 0,
        "notas": "",
    },
    {
        "titulo": "Dic · Bienestar fin de año (pirotecnia)",
        "kpi_medidor": "Talleres/consultas anti-estrés + packs calma vendidos",
        "meta_cuantitativa": 40,
        "fecha_inicio": "2026-11-15",
        "fecha_fin": "2026-12-31",
        "estado": "En progreso",
        "valor_actual": 0,
        "notas": "Crítico Nochevieja Canarias.",
    },
]
OBJETIVOS_TITULOS = [o["titulo"] for o in OBJETIVOS]

TALLERES = [
    {
        "titulo": "Higiene Básica en Casa: Oídos, Ojos y Uñas",
        "fecha": "2026-08-22",  # sábado
        "hora": "Sábado 10:30–12:00",
        "plazas_totales": 8,
        "precio": 15,
        "descripcion": "Taller de fin de semana (sábados o domingos). 15 € redimibles en productos Animalarium.",
        "corto": "higiene básica (oídos, ojos y uñas)",
        "anuncio_dias": [-14, -7, -1, 0, 2],
    },
    {
        "titulo": "Masterclass de Deslanado Casero",
        "fecha": "2026-09-20",  # domingo
        "hora": "Domingo 10:00–12:30",
        "plazas_totales": 8,
        "precio": 15,
        "descripcion": "Fin de semana (sáb/dom). Deslanado sin dañar el manto. Ideal post-verano Canarias.",
        "corto": "masterclass de deslanado casero",
        "anuncio_dias": [-14, -7, -1, 0, 2],
    },
    {
        "titulo": "Taller de Miedos, Estrés y Pirotecnia",
        "fecha": "2026-10-24",  # sábado
        "hora": "Sábado 11:00–12:30",
        "plazas_totales": 10,
        "precio": 15,
        "descripcion": "Fin de semana (sáb/dom). Preparación ante Halloween y Nochevieja en Canarias.",
        "corto": "miedos, estrés y pirotecnia",
        "anuncio_dias": [-21, -7, -1, 0, 2],
    },
    {
        "titulo": "Masajes Relajantes y SPA en Casa",
        "fecha": "2026-11-22",  # domingo
        "hora": "Domingo 11:00–12:30",
        "plazas_totales": 8,
        "precio": 15,
        "descripcion": "Fin de semana (sáb/dom). Bienestar y calma antes de Navidad.",
        "corto": "masajes relajantes y SPA en casa",
        "anuncio_dias": [-14, -7, -1, 0, 2],
    },
    {
        "titulo": "Fiesta Navideña y Cuidado Invernal",
        "fecha": "2026-12-12",  # sábado
        "hora": "Sábado 11:00–13:00",
        "plazas_totales": 12,
        "precio": 15,
        "descripcion": "Fin de semana (sáb/dom). Cierre de año con tip de cuidado y comunidad.",
        "corto": "fiesta navideña y cuidado invernal",
        "anuncio_dias": [-14, -7, -1, 0, 1],
    },
]

# Banco de textos LISTOS PARA COPIAR/PEGAR (tú solo añades foto o vídeo)
CONTENT_BANK = [
    (
        "Story · Buenos días Animalarium",
        """Buenos días desde Animalarium 🐾☀️

Empezamos el día con ganas de cuidaros a vosotros… y a quienes os hacen compañía.

Pasa a saludarnos cuando quieras. Estamos en horario continuo.

{h}""",
    ),
    (
        "Post · Pienso con criterio",
        """El mejor pienso no es “el de moda”.
Es el que encaja con TU perro 🐶

En Animalarium no empujamos marcas: miramos edad, tamaño, digestión y presupuesto. Trae la composición que usas ahora y te orientamos sin presión.

Te esperamos en tienda 💙

{h}""",
    ),
    (
        "Reel · Antes y después peluquería",
        """De “necesito pelu” a “mira qué guapo” ✨✂️

Resultado profesional, trato calmado y mucho cariño.

¿Reservamos cita? Escríbenos por WhatsApp o pásate por la tienda.

{h} #PeluqueriaCanina""",
    ),
    (
        "Story · Producto de la semana",
        """Producto de la semana en Animalarium 🛒

Pregúntanos y te decimos si encaja con tu mascota (tamaño, edad y necesidades).

Estamos para asesorarte, no solo para vender.

{h}""",
    ),
    (
        "Post · Recogida a domicilio",
        """¿Sin tiempo para traer al pelu? 🚗🐾

En Animalarium también ofrecemos recogida a domicilio: tú sigues con tu día y nosotros cuidamos el manto.

Pregunta disponibilidad por WhatsApp y te confirmamos hueco.

{h}""",
    ),
    (
        "Reel · Tip de cepillado",
        """Tip rápido de cepillado 🪥

Cepilla siempre a favor del pelo y con calma. Si hay nudos o el manto es denso, mejor no forzar en casa: te asesoramos en tienda o en peluquería.

¿Dudas con el cepillo? Pregúntanos 💬

{h}""",
    ),
    (
        "Post · Snacks con cabeza",
        """Chuches sí… pero con criterio 🦴

Mira ingredientes. En Animalarium te ayudamos a elegir snacks naturales según tamaño, alergias y objetivo (entrenamiento, premios, digestión).

Pásate por el rincón de naturales y te orientamos.

{h}""",
    ),
    (
        "Story · Gracias por confiar",
        """Gracias por confiar en Animalarium 💙🐾

Cada familia que pasa por aquí nos recuerda por qué hacemos esto.

Si te hemos ayudado, una reseña o un mensaje nos alegra el día.

{h}""",
    ),
    (
        "Post · Baño en casa vs peluquería",
        """Bañar en casa está bien… hasta que no lo está 🛁

Conviene peluquería profesional cuando hay nudos, oídos delicados, doble capa o ansiedad. Sin juicios: te decimos qué tiene sentido en tu caso.

Escríbenos y te damos cita.

{h}""",
    ),
    (
        "Reel · Tour por la tienda",
        """Así es un ratito en Animalarium 🏪🐾

Asesoramiento real, peluquería y productos pensados para Canarias.

Te esperamos en C. José Hernández Alfonso, 26 (Tenerife).

{h}""",
    ),
    (
        "Post · También somos de gatos",
        """Animalarium también es cosa de gatos 🐱✨

Arena, snacks, rascadores y consejo de verdad (urinario, bola de pelo, estrés…).

Pregúntanos en tienda: te escuchamos antes de recomendarte.

{h} #GatosTenerife""",
    ),
    (
        "Story · Huecos de peluquería",
        """Huecos de peluquería esta semana ✂️🐾

Si necesitas baño, arreglo o deslanado, escríbenos por WhatsApp y te reservamos.

¡Plazas limitadas!

{h}""",
    ),
    (
        "Post · Prevención en Canarias",
        """En Canarias la prevención cuenta todo el año 🏝️🦟

El clima suave mantiene activos a más parásitos durante más meses. Te orientamos en productos según si vais a playa, monte o ciudad.

Consulta en mostrador: sin presión, con criterio.

{h}""",
    ),
    (
        "Reel · Novedades en tienda",
        """¡Novedades en Animalarium! 📦✨

Ya disponible en tienda (y también puedes mirar en animalariumtenerife.es).

Pasa a verlo… o pregunta por WhatsApp.

{h}""",
    ),
    (
        "Post · Enriquecimiento y olfato",
        """Un perro que olfatea es un perro más calmado 🧠🐾

El enriquecimiento no es un lujo: ayuda a gastar cabeza y bajar estrés. En tienda tienes ideas de juguetes y snacks para olfato.

Ven y te montamos un plan sencillo para casa.

{h}""",
    ),
    (
        "Story · Tip Canarias (agua y sombra)",
        """Tip Canarias ☀️💧

Agua fresca siempre a mano, sombra en los paseos fuertes de calor, y si hay humedad: secar bien axilas y oídos al volver.

¿Necesitas bebedero de viaje o toalla? Te lo enseñamos en tienda.

{h}""",
    ),
    (
        "Post · No rapar (doble capa)",
        """En Canarias hace calor… pero rapar no siempre ayuda 🌡️✂️

En muchas razas de doble capa el manto aísla del sol. Rapar puede empeorar el golpe de calor y estropear el pelo meses.

Alternativas: baño bien hecho, deslanado profesional y paseos a primeras/últimas horas. Pregúntanos antes de decidir.

{h}""",
    ),
    (
        "Reel · Deslanado satisfying",
        """Esto salió en una sesión de deslanado ☁️✂️

Imagina ese pelo… en tu sofá.

Agenda tu deslanado profesional en Animalarium (también con recogida a domicilio si la necesitas).

{h} #Deslanado""",
    ),
    (
        "Post · Dónde estamos",
        """¿Primera vez en Animalarium? 📍

C. José Hernández Alfonso, 26 · Tenerife
Horario continuo · te asesoramos en tienda y peluquería

Guarda el contacto y escríbenos por WhatsApp cuando quieras.

{h}""",
    ),
    (
        "Story · Pack recomendado",
        """Pack recomendado de la semana 🎁🐾

Pregunta en mostrador: te armamos una combinación útil (sin vender por vender).

Si tienes duda de tamaño o edad, dínoslo y afinamos.

{h}""",
    ),
    (
        "Post · Web Animalarium",
        """También online 🌐🐾

animalariumtenerife.es

Encargos, consultas y lo que necesites… y si prefieres consejo cara a cara, la tienda física sigue siendo el corazón.

Enlace en la bio.

{h}""",
    ),
    (
        "Reel · El equipo",
        """Somos Animalarium 💙

Un equipo cercano, de Tenerife, para cuidaros con criterio y cariño.

Ven a conocernos. Tu mascota (y tú) sois bienvenidos.

{h}""",
    ),
    (
        "Post · Kit cachorro",
        """¿Cachorro en casa? Kit básico sin volverte loco Puppy✨

Pienso adecuado, snacks de entrenamiento, correa/arnés e higiene esencial. Te hacemos una lista personalizada según raza y edad.

Pásate por la tienda y lo montamos juntos.

{h}""",
    ),
    (
        "Story · Encuesta",
        """Encuesta rápida 🗳️🐾

¿Qué necesitáis más este mes?
✂️ Peluquería
🍖 Alimentación
🧸 Juguetes / enriquecimiento

Responde en la story y te preparamos contenido útil.

{h}""",
    ),
    (
        "Post · Viajar con mascota",
        """¿Viaje a la vista con tu mascota? ✈️⛴️🐶

Checklist rápido Animalarium:
• Bebedero de viaje
• Arnés seguro (mejor que solo collar)
• Documentos / cartilla al día
• Snacks y manta conocida para bajar estrés

En tienda te montamos el kit según si vais en barco, coche o avión. Pregúntanos y te lo dejamos claro sin líos.

{h}""",
    ),
    (
        "Reel · Oídos con cuidado",
        """Oídos: limpia solo por fuera y con calma 👂🐾

Si hay dolor, olor fuerte o mucho rascado, consulta al veterinario. En peluquería y en nuestros talleres te enseñamos hábitos seguros.

¿Quieres cita o plaza de taller? Escríbenos.

{h}""",
    ),
    (
        "Post · Senior y comodidad",
        """Mascotas senior: comodidad primero 🩶🐾

Camas adecuadas, apoyo articular y rutinas suaves. Te orientamos sin milagros ni presión.

Ven a tienda y te ayudamos a elegir lo que de verdad suma.

{h}""",
    ),
    (
        "Story · Ambiente peluquería",
        """En nuestra peluquería priorizamos calma ✂️💚

Sin prisas innecesarias. Tu compañero se merece un buen trato.

Agenda abierta: reserva por WhatsApp.

{h}""",
    ),
]


def month_flavor(d: date) -> tuple[str, str]:
    """Objetivo + frase estacional corta para cerrar el copy."""
    m, day = d.month, d.day
    if m == 8:
        return (
            "H2 · Agenda peluquería llena (Canarias)",
            "Agosto en Canarias: ojo con playa, arena y espigas. Si volvéis del baño, os esperamos para un buen arreglo.",
        )
    if m == 9:
        return (
            "H2 · Clientes nuevos captados",
            "Septiembre = vuelta a la rutina. Ideal para deslanar y resetear el manto tras el verano.",
        )
    if m == 10:
        if day == 12:
            return ("H2 · Clientes nuevos captados", "Si es puente, confirma nuestro horario por WhatsApp antes de venir.")
        if day >= 20:
            return ("Dic · Bienestar fin de año (pirotecnia)", "Halloween cerca: disfraz solo si está a gusto. Priorizamos bienestar.")
        return ("H2 · Ticket medio tienda (otoño-navidad)", "En el norte la humedad sube: seca bien oídos y axilas al volver del paseo.")
    if m == 11:
        if day >= 15:
            return ("Q4 · Campaña Black Friday + Navidad", "Temporada de ofertas y regalos: pregunta en tienda qué merece la pena de verdad.")
        return ("H2 · Ticket medio tienda (otoño-navidad)", "Noviembre suave en Canarias: buen momento para camas, snacks y preparación Navidad.")
    if day <= 15:
        return ("Q4 · Campaña Black Friday + Navidad", "Navidad a la vista: reserva peluquería pronto si quieres lucir en las fotos.")
    if day <= 27:
        return ("Dic · Bienestar fin de año (pirotecnia)", "Nochevieja en Canarias suena fuerte: preparad el plan anti-estrés con tiempo.")
    return ("H2 · Clientes nuevos captados", "Gracias por este año con nosotros. Os esperamos en 2027 con la misma ilusión.")


def row(fecha, canal, cat, tipo, tema, contenido, presupuesto=0.0, obj_key=None, obj_map=None):
    oid = obj_map.get(obj_key) if obj_key and obj_map else None
    text = contenido.strip()
    if "{h}" in text:
        text = text.format(h=HASHTAGS)
    return {
        "fecha_planificada": fecha if isinstance(fecha, str) else fecha.isoformat(),
        "canal": canal,
        "canal_categoria": cat,
        "tipo_campana": tipo,
        "tema": tema,
        "contenido_detallado": text,
        "presupuesto": float(presupuesto),
        "gasto_real": 0,
        "estado": EST,
        "objetivo_id": oid,
    }


def weekly_ig_post(d: date, obj_map: dict) -> dict:
    bank = CONTENT_BANK[(d.toordinal()) % len(CONTENT_BANK)]
    obj_key, season_line = month_flavor(d)
    tema = bank[0]
    cuerpo = bank[1]
    if "{h}" in cuerpo:
        cuerpo = cuerpo.format(h=HASHTAGS)
    # Texto final listo para pegar: copy + cierre estacional + nota mínima de media
    contenido = (
        f"{cuerpo.strip()}\n\n"
        f"{season_line}\n\n"
        f"—\n📷 Añade tú la foto o el vídeo y publica."
    )
    return row(d, CANAL_IG, CAT_DIG, TIPO_ORD, tema, contenido, obj_key=obj_key, obj_map=obj_map)


# Reparto fijo del presupuesto mensual 150 € entre soportes con coste
EUR_IG_ADS = 70.0      # Instagram / Facebook (Meta) — canal principal pagado
EUR_GOOGLE = 45.0      # Google Ads
EUR_CARTELERIA = 35.0  # Impresión / diseño físico
# WhatsApp a clientes: 0 € (envío manual 1 clic; API de pago aparcada)


def budget_month(
    year: int,
    month: int,
    obj_key: str,
    ig_tema: str,
    ig_anuncio: str,
    goo_tema: str,
    goo_titulares: str,
    goo_descripcion: str,
    cart_tema: str,
    cart_texto: str,
    obj_map: dict,
):
    """150 €/mes con textos de anuncio listos para pegar en las plataformas."""
    dia = date(year, month, 3 if month != 8 else 8)
    mes_txt = dia.strftime("%m/%Y")
    return [
        row(
            dia, CANAL_ADS, CAT_DIG, TIPO_ORD,
            f"Instagram/Facebook Ads {mes_txt} · {ig_tema}",
            f"""TEXTO DEL ANUNCIO (copiar en Meta Ads · prioridad Instagram):

{ig_anuncio}

—
Presupuesto este mes: {EUR_IG_ADS:.0f} € (del total 150 €: IG {EUR_IG_ADS:.0f} + Google {EUR_GOOGLE:.0f} + cartelería {EUR_CARTELERIA:.0f}).
📷 Usa una foto/vídeo real de tienda o pelu.""",
            presupuesto=EUR_IG_ADS, obj_key=obj_key, obj_map=obj_map,
        ),
        row(
            dia, CANAL_ADS, CAT_DIG, TIPO_ORD,
            f"Google Ads {mes_txt} · {goo_tema}",
            f"""TEXTO DEL ANUNCIO GOOGLE (copiar en anuncios de búsqueda):

Titulares:
{goo_titulares}

Descripción:
{goo_descripcion}

—
Presupuesto este mes: {EUR_GOOGLE:.0f} € (parte de los 150 €).""",
            presupuesto=EUR_GOOGLE, obj_key=obj_key, obj_map=obj_map,
        ),
        row(
            dia, CANAL_CART, CAT_FIS, TIPO_ORD,
            f"Cartelería mes {mes_txt} · {cart_tema}",
            f"""TEXTO PARA CARTEL / ESCAPARATE (copiar al diseño):

{cart_texto}

—
Sobre de impresión del mes: {EUR_CARTELERIA:.0f} € (parte de los 150 €).""",
            presupuesto=EUR_CARTELERIA, obj_key=obj_key, obj_map=obj_map,
        ),
    ]


def taller_extras(t: dict, obj_map: dict) -> list[dict]:
    """Anuncios de taller con texto listo para pegar (sáb o dom)."""
    base = date.fromisoformat(t["fecha"])
    dia_sem = "sábado" if base.weekday() == 5 else "domingo" if base.weekday() == 6 else base.strftime("%A")
    fecha_txt = base.strftime("%d/%m/%Y")
    out = []
    for delta in t["anuncio_dias"]:
        d = base + timedelta(days=delta)
        if d < date(2026, 8, 1) or d > date(2026, 12, 31):
            continue
        if delta < -1:
            out.append(row(
                d, CANAL_IG, CAT_DIG, TIPO_EVT,
                f"Taller · {t['corto']} ({dia_sem} {base.strftime('%d/%m')})",
                f"""¡Abrimos plazas! 🐾✨

Taller: {t['titulo']}
📅 {dia_sem.capitalize()} {fecha_txt}
🕒 {t['hora']}
👥 Solo {t['plazas_totales']} plazas
💶 {t['precio']} € (redimibles en productos de la tienda)

Los talleres de Animalarium son en sábado o domingo. Ideal para aprender con calma y llevarte trucos a casa.

¿Te apuntas? Responde a este post, escríbenos por WhatsApp o reserva en tienda.

{HASHTAGS} #TalleresAnimalarium

—
📷 Sube foto del cartel o del espacio del taller.""",
                obj_key="H2 · Ocupación talleres clientes", obj_map=obj_map,
            ))
            if delta == t["anuncio_dias"][0]:
                out.append(row(
                    d, CANAL_CART, CAT_FIS, TIPO_EVT,
                    f"Cartel · {t['corto']}",
                    f"""TEXTO DEL CARTEL (copiar al diseño):

{t['titulo'].upper()}

{dia_sem.capitalize()} {fecha_txt}
{t['hora']}

{t['plazas_totales']} plazas · {t['precio']} € redimibles en tienda
Talleres: sábados o domingos

Reserva en tienda o por WhatsApp
Animalarium Tenerife

—
💶 Impresión: sobre de cartelería del mes.""",
                    presupuesto=0.0,
                    obj_key="H2 · Ocupación talleres clientes", obj_map=obj_map,
                ))
        elif delta == -1:
            out.append(row(
                d, CANAL_WA, CAT_DIG, TIPO_EVT,
                f"WhatsApp · Taller {dia_sem} {t['corto']}",
                f"""¡Hola! 🐾 Te escribimos de Animalarium.

Mañana / en breve tenemos el taller «{t['titulo']}» el {dia_sem} {base.strftime('%d/%m')} ({t['hora']}).

Quedan plazas (máx. {t['plazas_totales']}) · {t['precio']} € redimibles en tienda. Los talleres son en sábado o domingo.

¿Te guardamos sitio? Responde a este mensaje y te confirmamos.""",
                presupuesto=0.0,
                obj_key="H2 · Ocupación talleres clientes", obj_map=obj_map,
            ))
            out.append(row(
                d, CANAL_IG, CAT_DIG, TIPO_EVT,
                f"Story · Últimas plazas {base.strftime('%d/%m')}",
                f"""Últimas plazas ⏳🐾

{t['titulo']}
{dia_sem.capitalize()} {base.strftime('%d/%m')} · {t['hora']}
{t['precio']} € redimibles

Responde a la story o escríbenos por WhatsApp para reservar.

{HASHTAGS}

—
📷 Story con el cartel o cuenta atrás.""",
                obj_key="H2 · Ocupación talleres clientes", obj_map=obj_map,
            ))
        elif delta == 0:
            out.append(row(
                d, CANAL_IG, CAT_DIG, TIPO_EVT,
                f"Cobertura · Hoy taller {t['corto']}",
                f"""¡Hoy toca taller en Animalarium! 🙌🐾

Estamos con «{t['titulo']}». Si no has podido venir, atento a la próxima fecha (siempre en sábado o domingo).

¿Quieres lista de espera? Escríbenos.

{HASHTAGS}

—
📷 Stories/Reel del taller (con permiso de quien salga).""",
                obj_key="H2 · Ocupación talleres clientes", obj_map=obj_map,
            ))
        else:
            out.append(row(
                d, CANAL_IG, CAT_DIG, TIPO_EVT,
                f"Recap · Taller {t['corto']}",
                f"""¡Gracias por venir al taller «{t['titulo']}»! 💙🐾

Aprendimos mucho y con muy buen rollo. Seguimos con talleres en sábado o domingo: la próxima fecha la publicamos aquí.

Si quieres plaza en el siguiente, escríbenos y te avisamos.

{HASHTAGS} #TalleresAnimalarium

—
📷 Foto grupal o detalle del taller (con permiso).""",
                obj_key="H2 · Ocupación talleres clientes", obj_map=obj_map,
            ))
    return out


def specials(obj_map: dict) -> list[dict]:
    P: list[dict] = []
    OK_ROI = "H2 · ROI inversión 150 €/mes (todos los soportes)"

    P += budget_month(
        2026, 8, OK_ROI,
        "Baño post-playa / peluquería",
        "¿Vuelves de la playa? 🌊🐶\nBaño + oídos + manto a punto en Animalarium (Tenerife).\nReserva por WhatsApp. También recogida a domicilio.",
        "Peluquería Tenerife",
        "Peluquería canina en Tenerife\nBaño post-playa y deslanado\nAnimalarium · Reserva fácil",
        "Agenda tu baño o arreglo en Animalarium. Horario continuo. WhatsApp y recogida a domicilio disponible.",
        "Kit anti-calor",
        "KIT ANTI-CALOR CANARIAS\nBebederos · snacks húmedos · toallas\nPregunta en Animalarium",
        obj_map,
    )
    P += budget_month(
        2026, 9, OK_ROI,
        "Deslanado otoño",
        "El pelo del verano… ¿sigue en tu sofá? ☁️✂️\nDeslanado profesional en Animalarium.\nReserva cita por WhatsApp.",
        "Deslanado / muda",
        "Deslanado profesional Tenerife\nMuda de pelo bajo control\nAnimalarium peluquería",
        "Deslanado profesional para dejar el manto sano y tu casa más limpia. Reserva en Animalarium.",
        "Cepillos y muda",
        "OTOÑO = MUDA\nElige el cepillo correcto\nPregúntanos en Animalarium",
        obj_map,
    )
    P += budget_month(
        2026, 10, OK_ROI,
        "Agenda pelu + otoño",
        "Humedad, paseos y oídos 👂🌧️\nIguala el manto y revisa higiene en Animalarium.\nHuecos de peluquería: escribe por WhatsApp.",
        "Tienda mascotas / peluquería",
        "Peluquería y tienda Animalarium\nMascotas Tenerife\nAsesoramiento real",
        "Peluquería canina y asesoramiento en tienda. Animalarium, Tenerife. Reserva por WhatsApp.",
        "Secar oídos",
        "PASEO MOJADO\n→ SECA OÍDOS Y AXILOS\nTe ayudamos en Animalarium",
        obj_map,
    )
    P += budget_month(
        2026, 11, "Q4 · Campaña Black Friday + Navidad",
        "Teaser + Black Friday",
        "Black Friday Animalarium 🖤🐾\nOfertas con criterio (no milagros).\nPasa por tienda o pregunta por WhatsApp.\nTambién: agenda peluquería de Navidad.",
        "Black Friday mascotas",
        "Black Friday mascotas Tenerife\nOfertas en tienda Animalarium\nCamas, snacks y más",
        "Aprovecha el Black Friday en Animalarium. Asesoramiento real en tienda. Consulta horarios y stock.",
        "Black Friday escaparate",
        "BLACK FRIDAY WEEK\nANIMALARIUM\nPregunta ofertas en tienda\n¡Te asesoramos!",
        obj_map,
    )
    P += budget_month(
        2026, 12, "Q4 · Campaña Black Friday + Navidad",
        "Regalos + agenda Navidad",
        "🎄 ¿Ya tienes la cita de peluquería para Nochebuena?\nLa agenda se llena. Reserva en Animalarium.\nTambién ideas de regalos para tu mascota 🎁",
        "Regalos mascotas Tenerife",
        "Regalos para mascotas Tenerife\nPeluquería Navidad\nAnimalarium",
        "Regalos y peluquería de Navidad en Animalarium. Reserva pronto tu hueco. WhatsApp disponible.",
        "Pelu Navidad",
        "ÚLTIMOS HUECOS\nPELUQUERÍA NAVIDAD\nReserva ya · Animalarium",
        obj_map,
    )

    for fecha, tema, txt, ok in [
        ("2026-08-28", "WhatsApp · Vuelta vacaciones / baño",
         "¡Hola! 🌊 Somos Animalarium.\n\nSi volvéis de playa o viaje, es buen momento para baño, oídos y revisión de manto. ¿Te buscamos hueco esta semana? También tenemos recogida a domicilio.\n\n¡Escríbenos y te confirmamos!",
         "H2 · Agenda peluquería llena (Canarias)"),
        ("2026-09-30", "WhatsApp · Rutina septiembre",
         "¡Hola! 🐾 Desde Animalarium.\n\nSeptiembre = vuelta a la rutina. ¿Necesitáis peluquería o deslanado este mes? Te damos el primer hueco libre.\n\n¿Te reservamos?",
         "H2 · Agenda peluquería llena (Canarias)"),
        ("2026-10-26", "WhatsApp · Igualar mantos",
         "¡Hola! 🍂 Animalarium por aquí.\n\nEstamos abriendo huecos para igualar mantos tras el verano. ¿Te reservamos día y hora?\n\nTambién recogida a domicilio si la necesitas.",
         "H2 · Agenda peluquería llena (Canarias)"),
        ("2026-11-18", "WhatsApp · VIP Black Friday",
         "¡Hola! 🖤 Acceso anticipado Black Friday Animalarium.\n\nOfertas destacadas:\n1) [completar]\n2) [completar]\n3) [completar]\n\nTambién puedes reservar ya la peluquería de Navidad. ¿Te guardamos algo o una cita?",
         "Q4 · Campaña Black Friday + Navidad"),
        ("2026-12-04", "WhatsApp · Agenda Navidad se cierra",
         "¡Hola! 🎄 Desde Animalarium.\n\nLa agenda de peluquería para Nochebuena/Navidad se está cerrando. Si quieres a tu compañero impecable para las fotos, responde y te damos el primer hueco libre.\n\n¡También recogida a domicilio!",
         "H2 · Agenda peluquería llena (Canarias)"),
        ("2026-12-28", "WhatsApp · Pirotecnia fin de año",
         "¡Hola! 🐾 Equipo Animalarium.\n\nRecordatorio de fin de año: los petardos en Canarias pueden ser muy duros para ellos. Si necesitas ideas de manejo o productos de apoyo, escríbenos. Estamos con vosotros.",
         "Dic · Bienestar fin de año (pirotecnia)"),
    ]:
        P.append(row(fecha, CANAL_WA, CAT_DIG, TIPO_ORD, tema, txt, presupuesto=0.0, obj_key=ok, obj_map=obj_map))

    for fecha, tema, txt, ok in [
        ("2026-08-07", "Cartel · Kit anti-calor",
         """KIT ANTI-CALOR CANARIAS ☀️💧

Bebederos de viaje
Snacks húmedos
Toallas refrescantes

Pregunta en mostrador — te armamos el pack
Animalarium · C. José Hernández Alfonso, 26""",
         "H2 · Ticket medio tienda (otoño-navidad)"),
        ("2026-09-10", "Cartel · Cepillos y muda",
         """OTOÑO = MUDA ☁️

Elige el cepillo correcto
(Furminator · carda · peine)

¿No sabes cuál? Pregúntanos
Animalarium Tenerife""",
         "H2 · Ticket medio tienda (otoño-navidad)"),
        ("2026-10-08", "Cartel · Secar oídos",
         """PASEO MOJADO
→ SECA OÍDOS Y AXILOS 👂

Evita otitis y malos olores
Te ayudamos en Animalarium""",
         "H2 · Ticket medio tienda (otoño-navidad)"),
        ("2026-10-31", "Cartel · Truco o trato",
         """🎃 TRUCO O TRATO PET-FRIENDLY 🎃

Pasa a saludar con tu mascota
Te esperamos con un snack / chuche de bienvenida

(Disfraz opcional — solo si está a gusto)
Animalarium Tenerife""",
         "H2 · Clientes nuevos captados"),
        ("2026-11-07", "Cartel · Black Friday",
         """🖤 BLACK FRIDAY WEEK 🖤
ANIMALARIUM

Ofertas con criterio
Pregunta en tienda — te asesoramos de verdad

¡Stock limitado!""",
         "Q4 · Campaña Black Friday + Navidad"),
        ("2026-11-27", "Cartel · Remate camas/rascadores",
         """BLACK FRIDAY · REMATE FINAL

Camas y rascadores
Precios especiales · stock limitado

Animalarium — pregunta en mostrador""",
         "Q4 · Campaña Black Friday + Navidad"),
        ("2026-12-05", "Cartel · Pelu Navidad",
         """🎄 ÚLTIMOS HUECOS 🎄
PELUQUERÍA NAVIDAD

Para lucir en las fotos de Nochebuena
Reserva ya · WhatsApp o tienda

Animalarium Tenerife""",
         "H2 · Agenda peluquería llena (Canarias)"),
        ("2026-12-23", "Cartel · Pack calma Nochevieja",
         """PACK CALMA NOCHEVIEJA 🎆🐾

Ideas y productos de apoyo
para ruidos y estrés

Pregunta en mostrador
Animalarium — estamos con ellos""",
         "Dic · Bienestar fin de año (pirotecnia)"),
    ]:
        P.append(row(fecha, CANAL_CART, CAT_FIS, TIPO_ORD, tema, txt, presupuesto=0.0, obj_key=ok, obj_map=obj_map))

    P.append(row(
        "2026-09-26", CANAL_IG, CAT_DIG, TIPO_INN,
        "Post · Marketing con números",
        f"""Marketing con números, no a ciegas 📊🐾

En Animalarium limitamos la inversión a 150 €/mes repartidos entre Instagram/Facebook Ads, Google Ads y cartelería. WhatsApp lo seguimos haciendo a mano.

Así cuidamos el presupuesto de una pyme canaria y medimos qué funciona de verdad.

{HASHTAGS} #InnovacionPyme

—
📷 Infografía simple o captura del plan (sin datos sensibles).""",
        obj_key=OK_ROI, obj_map=obj_map,
    ))
    P.append(row(
        "2026-11-14", CANAL_IG, CAT_DIG, TIPO_INN,
        "Post · Cómo medimos el Black Friday",
        f"""Black Friday con criterio 🖤

Este año medimos resultados: de dónde viene cada cliente, qué anuncio funciona y qué merece la pena repetir.

Porque en Animalarium preferimos vender bien… a vender por vender.

{HASHTAGS}

—
📷 Carrusel con 3 tips de compra consciente.""",
        obj_key=OK_ROI, obj_map=obj_map,
    ))

    for t in TALLERES:
        P.extend(taller_extras(t, obj_map))
    return P


def build_plan(obj_map: dict) -> list[dict]:
    """~3 posts IG/semana (lun/mié/vie) + talleres/Ads/WA/cartelería intercalados."""
    rows: list[dict] = []
    start, end = date(2026, 8, 1), date(2026, 12, 31)
    taller_dates = {date.fromisoformat(t["fecha"]) for t in TALLERES}
    d = start
    while d <= end:
        if d.weekday() in (0, 2, 4):
            if d not in taller_dates:
                rows.append(weekly_ig_post(d, obj_map))
        d += timedelta(days=1)
    rows.extend(specials(obj_map))
    rows.sort(key=lambda r: (r["fecha_planificada"], r["canal"], r["tema"]))
    return rows


def seed_talleres():
    """Upsert: borra por título H2 y vuelve a insertar (fechas sáb/dom actualizadas)."""
    for t in TALLERES:
        try:
            http_delete(f"/eventos_talleres?titulo=eq.{quote(t['titulo'])}")
        except Exception:
            pass
        payload = {k: t[k] for k in ("titulo", "fecha", "hora", "plazas_totales", "precio", "descripcion")}
        api("POST", "/eventos_talleres", payload, prefer="return=minimal")
    print(f"Talleres OK ({len(TALLERES)}) — sabados o domingos")


def seed_objetivos() -> dict:
    for tit in OBJETIVOS_TITULOS:
        try:
            http_delete(f"/marketing_objetivos?titulo=eq.{quote(tit)}")
        except Exception:
            pass
    mapping = {}
    for o in OBJETIVOS:
        created = api("POST", "/marketing_objetivos", o, prefer="return=representation")
        if isinstance(created, list) and created:
            mapping[o["titulo"]] = created[0]["id"]
        elif isinstance(created, dict):
            mapping[o["titulo"]] = created["id"]
    print(f"Objetivos OK: {len(mapping)}")
    return mapping


def seed_plan(obj_map: dict):
    rows = build_plan(obj_map)
    for i in range(0, len(rows), 25):
        api("POST", "/marketing_plan", rows[i : i + 25], prefer="return=minimal")
    paid = sum(r["presupuesto"] for r in rows)
    ig = sum(1 for r in rows if r["canal"] == CANAL_IG)
    print(f"Plan H2: {len(rows)} acciones | IG {ig} | presupuesto total {paid:.0f} EUR (150/mes x 5, IG+Google+carteleria)")


def main():
    prod = "--prod" in sys.argv or "--production" in sys.argv
    target = configure_target(prod=prod)
    print(f"Sembrando marketing H2 2026 ({target})...")
    # Smoke test (no imprime datos sensibles)
    probe = api("GET", "/marketing_plan?select=id&limit=1")
    print(f"Conexion OK (filas muestra plan: {0 if probe is None else len(probe)})")
    seed_talleres()
    # Solo borra H2 (ago+); no toca mayo-julio
    http_delete("/marketing_plan?fecha_planificada=gte.2026-08-01")
    obj_map = seed_objetivos()
    seed_plan(obj_map)
    print(f"OK en {target}. Marketing -> Plan Maestro / Objetivos / Talleres.")


if __name__ == "__main__":
    main()
