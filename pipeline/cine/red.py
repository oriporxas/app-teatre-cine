"""Lectura educada de webs para la cartelera de cine.

- Antes de pedir nada a una web, se lee su robots.txt y solo se pide lo que permite
  a cualquier programa («User-agent: *»). Si la web no deja leer su robots.txt
  (responde 401/403), se entiende que no quiere programas y no se le pide nada.
- Si la web bloquea a los programas de IA (GPTBot, ClaudeBot…), su contenido no se
  pasa por la IA: solo se lee con reglas fijas.
- Pausa entre peticiones a la misma web (la que pida su robots.txt, o 3 segundos).
- Nunca se intenta saltar un bloqueo (cambiar el «User-Agent», usar otra dirección…).
"""

from __future__ import annotations

import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

AGENTE = "CarteleraBarcelona/1.0"
PAUSA_POR_DEFECTO = 3.0
BOTS_IA = ("gptbot", "claudebot", "anthropic-ai", "claude-web", "ccbot", "google-extended", "perplexitybot")

_robots: dict[str, tuple[urllib.robotparser.RobotFileParser | None, bool, float]] = {}
_ultima: dict[str, float] = {}
_cerrojos: dict[str, threading.Lock] = {}
_CERROJO_GENERAL = threading.Lock()


def _reglas(url: str):
    """(parser o None si la web no quiere programas, bloquea IA, pausa en segundos)."""
    p = urllib.parse.urlsplit(url)
    host = p.netloc
    if host in _robots:
        return _robots[host]
    rp = urllib.robotparser.RobotFileParser()
    bloquea_ia, pausa = False, PAUSA_POR_DEFECTO
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"{p.scheme}://{host}/robots.txt",
                                                          headers={"User-Agent": AGENTE}), timeout=25)
        texto = r.read().decode("utf-8", "replace")
        rp.parse(texto.splitlines())
        agentes, bloqueados = [], set()
        for linea in texto.splitlines():
            l = linea.split("#")[0].strip().lower()
            if l.startswith("user-agent:"):
                agentes.append(l.split(":", 1)[1].strip())
            elif l.startswith("disallow:") and l.split(":", 1)[1].strip() == "/":
                bloqueados.update(agentes)
                agentes = []
            elif l and not l.startswith("user-agent"):
                agentes = []
        bloquea_ia = any(b in bloqueados for b in BOTS_IA)
        pausa = max(PAUSA_POR_DEFECTO, float(rp.crawl_delay(AGENTE) or 0))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            _robots[host] = (None, True, pausa)  # no quiere programas
            return _robots[host]
        rp.parse([])  # sin robots.txt (404): todo permitido
    except Exception:  # noqa: BLE001 - sin respuesta: mejor no insistir
        _robots[host] = (None, True, pausa)
        return _robots[host]
    _robots[host] = (rp, bloquea_ia, pausa)
    return _robots[host]


def permitido(url: str) -> bool:
    rp, _, _ = _reglas(url)
    return bool(rp and rp.can_fetch(AGENTE, url))


def permite_ia(url: str) -> bool:
    rp, bloquea_ia, _ = _reglas(url)
    return bool(rp) and not bloquea_ia


def _cerrojo(host: str) -> threading.Lock:
    with _CERROJO_GENERAL:
        return _cerrojos.setdefault(host, threading.Lock())


def pedir(url: str, timeout: int = 40, cabeceras: dict | None = None) -> bytes | None:
    """Devuelve el contenido, o None si robots.txt no lo permite o la web no responde.
    Una web nunca recibe dos peticiones a la vez ni más deprisa de lo que pide (aunque el cine, las
    noticias y la escena vayan en paralelo)."""
    host = urllib.parse.urlsplit(url).netloc
    with _cerrojo(host):
        if not permitido(url):
            return None
        _, _, pausa = _reglas(url)
        espera = _ultima.get(host, 0) + pausa - time.monotonic()
        if espera > 0:
            time.sleep(espera)
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENTE, **(cabeceras or {})}),
                                       timeout=timeout)
            return r.read()
        except Exception:  # noqa: BLE001
            return None
        finally:
            _ultima[host] = time.monotonic()
