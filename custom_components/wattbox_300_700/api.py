from __future__ import annotations

import logging
from typing import List, Dict, Optional

import aiohttp
import async_timeout
import xml.etree.ElementTree as ET

_LOGGER = logging.getLogger(__name__)


class WattBoxHTTPClient:
    """HTTP client for WB-300 and WB-700"""

    def __init__(self, session: aiohttp.ClientSession, host: str, user: str, pw: str, verify_ssl: bool = True):
        self._session = session
        self._host = host.rstrip("/")
        self._auth = aiohttp.BasicAuth(user, pw)
        self._ssl = verify_ssl
        self._timeout = 8

    def _url(self, path: str) -> str:
        return f"http://{self._host}/{path.lstrip('/')}"

    async def _get_text(self, path: str) -> str:
        """Fetch a URL and return its body as text, even if server closes early."""
        url = self._url(path)
        headers = {"Connection": "keep-alive", "User-Agent": "HA"}
        async with async_timeout.timeout(self._timeout):
            async with self._session.get(url, auth=self._auth, ssl=self._ssl, headers=headers) as resp:
                chunks = []
                try:
                    async for c in resp.content.iter_any():
                        chunks.append(c)
                except Exception as e:
                    _LOGGER.debug("stream read error ignored: %s", e)
                try:
                    return b"".join(chunks).decode("utf-8", "ignore")
                except Exception:
                    return ""

    async def _fire_and_forget(self, path: str) -> None:
        """Send a command but ignore body (device often closes early)."""
        url = self._url(path)
        headers = {"Connection": "keep-alive", "User-Agent": "HA"}
        async with async_timeout.timeout(self._timeout):
            async with self._session.get(url, auth=self._auth, ssl=self._ssl, headers=headers) as resp:
                try:
                    await resp.content.readany()
                except Exception:
                    pass
                return

    # ---------- Public API ----------

    async def get_outlet_states(self) -> List[bool]:
        """Return list of outlet states as booleans, index 0 -> outlet 1"""
        xml_text = await self._get_text("wattbox_info.xml")
        try:
            root = ET.fromstring(xml_text)
        except Exception as e:
            _LOGGER.error("Failed to parse wattbox_info.xml: %s", e)
            raise

        node = root.find("outlet_status")
        if node is None or node.text is None:
            raise ValueError("outlet_status not found in XML")

        csv = node.text.replace("\r", "").replace("\n", "").strip()
        parts = [p.strip() for p in csv.split(",") if p.strip() != ""]
        return [p == "1" for p in parts]

    async def set_outlet(self, outlet: int, on: bool) -> None:
        """Turn one outlet on or off"""
        if outlet < 0:
            raise ValueError("outlet must be >= 0")
        cmd = 1 if on else 0
        await self._fire_and_forget(f"control.cgi?outlet={outlet}&command={cmd}")

    async def reset_outlet(self, outlet: int) -> None:
        # 0 means reset all
        if outlet < 0:
            raise ValueError("outlet must be >= 0")
        await self._fire_and_forget(f"control.cgi?outlet={outlet}&command=3")

    async def set_auto_reboot(self, enabled: bool) -> None:
        """Enable or disable auto reboot for all outlets"""
        cmd = 4 if enabled else 5
        await self._fire_and_forget(f"control.cgi?outlet=0&command={cmd}")
        
    async def get_outlet_names(self) -> list[str]:
        """Return list of outlet names from <outlet_name>."""
        xml_text = await self._get_text("wattbox_info.xml")
        root = ET.fromstring(xml_text)
        node = root.find("outlet_name")
        if node is None or node.text is None:
            return []
        csv = node.text.replace("\r", "").replace("\n", "").strip()
        return [p.strip() for p in csv.split(",") if p.strip() != ""]

    async def get_metrics(self) -> Dict[str, Optional[float]]:
        """Return voltage V, current A, power W if present"""
        xml_text = await self._get_text("wattbox_info.xml")
        try:
            root = ET.fromstring(xml_text)
        except Exception as e:
            _LOGGER.error("Failed to parse wattbox_info.xml: %s", e)
            raise

        def _read_int(tag: str) -> Optional[int]:
            node = root.find(tag)
            if node is None or node.text is None:
                return None
            try:
                return int(node.text.strip())
            except ValueError:
                return None

        v_raw = _read_int("voltage_value")   # 1115 -> 111.5 V
        a_raw = _read_int("current_value")   # 105 -> 10.5 A
        w_raw = _read_int("power_value")     # 600 -> 600 W

        return {
            "voltage": (v_raw / 10.0) if v_raw is not None else None,
            "current": (a_raw / 10.0) if a_raw is not None else None,
            "power": float(w_raw) if w_raw is not None else None,
        }