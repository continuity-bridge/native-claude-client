"""
erebos/discovery.py

Network discovery for Ollama instances.

Two concurrent discovery methods:
    1. mDNS/Avahi  — browses for _ollama._tcp services (instant on
                     cooperative hosts, requires service advertisement)
    2. Threaded polling — scans subnet via parallel HTTP probes
                     (exhaustive, works everywhere, bounded by timeout)

Results from both paths are merged and deduplicated by normalized IP-based
URL before being handed to NoduleConfig for persistence.

Host-side mDNS advertisement (optional, enables fast discovery):
    Drop /etc/avahi/services/ollama.service on each Ollama host:

        <?xml version="1.0" standalone='no'?>
        <!DOCTYPE service-group SYSTEM "avahi-service.dtd">
        <service-group>
          <name>Ollama on %h</name>
          <service>
            <type>_ollama._tcp</type>
            <port>11434</port>
          </service>
        </service-group>

    Then: sudo systemctl restart avahi-daemon

Users without mDNS advertisement fall through to polling automatically.

Config is keyed on normalized IP-based URL.
On rediscovery of a known URL: update models + last_seen, preserve label.
On discovery of a new URL: generate label from hostname, add fresh entry.
"""

import ipaddress
import json
import logging
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .providers.ollama import OllamaClient
from .providers.base import ProviderConnectionError

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "erebos" / "config.json"
DEFAULT_SUBNET = "192.168.12.0/24"
DEFAULT_PORT = 11434
MDNS_SERVICE_TYPE = "_ollama._tcp.local."
MDNS_TIMEOUT = 5       # seconds to browse mDNS before declaring done
SCAN_TIMEOUT = 2       # socket probe timeout per host
MODEL_TIMEOUT = 3      # timeout for model list fetch
MAX_WORKERS = 16       # thread pool cap for polling


# ---------------------------------------------------------------------------
# Nodule Schema Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_to_ip(host: str) -> Optional[str]:
    """
    Resolve a hostname or mDNS name to an IPv4 address string.
    Returns None on failure.
    """
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


def _build_nodule(host_ip: str, port: int, hostname: Optional[str],
                  models: list[str], priority: int) -> dict:
    """
    Build a canonical nodule config dict.

    URL and host are always IP-based for stability.
    Hostname is stored separately for display/label generation.
    """
    url = f"http://{host_ip}:{port}"
    location = "local" if host_ip in ("127.0.0.1", "::1") else "network"
    label = f"Ollama-{hostname}" if hostname else f"Ollama-{host_ip.split('.')[-1]}"

    return {
        "url": url,
        "host": host_ip,
        "port": port,
        "hostname": hostname,
        "label": label,
        "provider": "ollama",
        "location": location,
        "priority": priority,
        "enabled": True,
        "models": models,
        "last_seen": _now_iso(),
    }


# ---------------------------------------------------------------------------
# Config Manager
# ---------------------------------------------------------------------------

class NoduleConfig:
    """
    Loads, manages, and persists nodule configuration.

    Nodules are keyed internally by normalized IP-based URL.
    All mutation goes through add_or_update() to enforce dedup logic.
    """

    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self._nodules: dict[str, dict] = {}  # url -> nodule dict
        self._load()

    # ---------------------------------------------------------------------------
    # Load / Save
    # ---------------------------------------------------------------------------

    def _load(self):
        """Load config from disk. Silent if file doesn't exist yet."""
        if not self.config_path.exists():
            logger.debug(f"No config at {self.config_path} — starting fresh")
            return

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)

            nodules = data.get("nodules", [])
            self._nodules = {n["url"]: n for n in nodules if "url" in n}
            logger.info(
                f"Loaded {len(self._nodules)} nodule(s) from {self.config_path}"
            )

        except json.JSONDecodeError as e:
            logger.error(f"Config file is malformed: {e} — starting fresh")
            self._nodules = {}
        except Exception as e:
            logger.error(f"Failed to load config: {e} — starting fresh")
            self._nodules = {}

    def save(self):
        """Persist current nodule config to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"nodules": list(self._nodules.values())}
        try:
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Config saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    # ---------------------------------------------------------------------------
    # Nodule Management
    # ---------------------------------------------------------------------------

    def add_or_update(self, nodule: dict) -> tuple[dict, bool]:
        """
        Add a new nodule or update an existing one by URL.

        If URL already exists:
            - Updates: models, last_seen, hostname (if newly resolved)
            - Preserves: label, priority, enabled, all user-set fields

        If URL is new:
            - Adds the nodule as provided

        Returns:
            Tuple of (nodule dict, was_new: bool)
        """
        url = nodule.get("url")
        if not url:
            raise ValueError("Nodule must have a 'url' field")

        if url in self._nodules:
            existing = self._nodules[url]
            existing["models"] = nodule.get("models", existing.get("models", []))
            existing["last_seen"] = _now_iso()
            # Only update hostname if we got a better answer than we had
            if nodule.get("hostname") and not existing.get("hostname"):
                existing["hostname"] = nodule["hostname"]
                # Update label too if it was IP-derived
                if existing["label"].split("-")[-1].isdigit():
                    existing["label"] = f"Ollama-{nodule['hostname']}"
            logger.debug(f"Updated existing nodule: {existing['label']} ({url})")
            return existing, False
        else:
            self._nodules[url] = nodule
            logger.debug(f"Added new nodule: {nodule['label']} ({url})")
            return nodule, True

    def remove(self, url: str) -> bool:
        """Remove a nodule by URL. Returns True if it existed."""
        if url in self._nodules:
            del self._nodules[url]
            return True
        return False

    def get(self, url: str) -> Optional[dict]:
        """Get a nodule by URL."""
        return self._nodules.get(url)

    def all(self, enabled_only: bool = False) -> list[dict]:
        """Return all nodules, optionally filtered to enabled only."""
        nodules = list(self._nodules.values())
        if enabled_only:
            nodules = [n for n in nodules if n.get("enabled", True)]
        return sorted(nodules, key=lambda n: n.get("priority", 99))

    def __len__(self) -> int:
        return len(self._nodules)


# ---------------------------------------------------------------------------
# mDNS Discovery
# ---------------------------------------------------------------------------

class MDNSDiscovery:
    """
    Browse for Ollama instances advertising via mDNS (_ollama._tcp).

    Requires zeroconf package. Fails gracefully if not installed or
    if no services are found within the timeout window.

    Host-side setup required — see module docstring.
    """

    @classmethod
    def discover(cls, timeout: float = MDNS_TIMEOUT,
                 port: int = DEFAULT_PORT) -> list[dict]:
        """
        Browse for _ollama._tcp mDNS services.

        Args:
            timeout: How long to browse before returning (seconds)
            port:    Expected Ollama port (used if service doesn't advertise one)

        Returns:
            List of nodule dicts for discovered instances.
            Empty list if zeroconf unavailable or nothing found.
        """
        try:
            from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
        except ImportError:
            logger.warning(
                "zeroconf not installed — mDNS discovery unavailable. "
                "Install with: pip install zeroconf"
            )
            return []

        found: dict[str, dict] = {}  # ip -> nodule, local dedup
        lock = threading.Lock()

        class OllamaListener(ServiceListener):
            def add_service(self, zc, type_, name):
                info = zc.get_service_info(type_, name)
                if not info:
                    return

                # Resolve IP from mDNS record
                addresses = info.parsed_addresses()
                if not addresses:
                    return

                host_ip = addresses[0]
                service_port = info.port or port
                hostname = info.server.rstrip(".").split(".")[0] if info.server else None

                # Normalize: resolve hostname to IP if we only got a name
                if not host_ip:
                    if not info.server:
                        logger.warning(f"Could not resolve mDNS host: no hostname")
                        return
                    resolved = _resolve_to_ip(info.server)
                    if not resolved:
                        logger.warning(f"Could not resolve mDNS host: {info.server}")
                        return
                    host_ip = resolved

                url = f"http://{host_ip}:{service_port}"

                # Fetch models — confirms it's live and gets model list
                try:
                    client = OllamaClient(
                        base_url=url,
                        timeout=MODEL_TIMEOUT
                    )
                    models = client.list_models()
                except Exception as e:
                    logger.warning(f"mDNS: found {url} but couldn't fetch models: {e}")
                    models = []

                nodule = _build_nodule(
                    host_ip=host_ip,
                    port=service_port,
                    hostname=hostname,
                    models=models,
                    priority=1
                )

                with lock:
                    if url not in found:
                        found[url] = nodule
                        logger.info(
                            f"mDNS: found Ollama at {url} "
                            f"({hostname or host_ip}) — {len(models)} model(s)"
                        )

            def remove_service(self, zc, type_, name):
                pass  # We don't remove nodules on mDNS goodbye packets

            def update_service(self, zc, type_, name):
                pass

        zeroconf = Zeroconf()
        browser = ServiceBrowser(zeroconf, MDNS_SERVICE_TYPE, OllamaListener())

        try:
            time.sleep(timeout)
        finally:
            zeroconf.close()

        return list(found.values())


# ---------------------------------------------------------------------------
# Polling Discovery
# ---------------------------------------------------------------------------

class PollingDiscovery:
    """
    Discover Ollama instances by parallel HTTP polling across a subnet.

    Uses ThreadPoolExecutor for concurrent probing. Worker count is
    capped at MAX_WORKERS (16) — sufficient for typical home/small
    office LANs, won't overwhelm the network.
    """

    @classmethod
    def scan_subnet(cls, subnet: str = DEFAULT_SUBNET,
                    port: int = DEFAULT_PORT) -> list[dict]:
        """
        Scan a subnet for reachable Ollama instances.

        Args:
            subnet: CIDR notation, e.g. "192.168.12.0/24"
            port:   Ollama port (default 11434)

        Returns:
            List of nodule dicts for discovered instances.
        """
        try:
            network = ipaddress.ip_network(subnet, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid subnet '{subnet}': {e}") from e

        hosts = [str(ip) for ip in network.hosts()]
        worker_count = min(len(hosts), MAX_WORKERS)

        logger.info(
            f"Polling {subnet} ({len(hosts)} hosts, {worker_count} workers) "
            f"for Ollama on port {port}..."
        )

        found = []

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(cls._probe_host, host, port): host
                for host in hosts
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    found.append(result)
                    logger.info(
                        f"Polling: found Ollama at {result['host']} "
                        f"({result['hostname'] or 'no hostname'}) "
                        f"— {len(result['models'])} model(s)"
                    )

        logger.info(f"Polling complete: {len(found)} instance(s) found")
        return found

    @classmethod
    def _probe_host(cls, host: str, port: int) -> Optional[dict]:
        """
        Probe a single host. Returns nodule dict if Ollama found, else None.

        Phase 1: socket connect (fast rejection of closed ports)
        Phase 2: API call (confirms Ollama, fetches models)
        Phase 3: hostname resolution (best-effort reverse DNS)
        """
        # Phase 1: socket probe
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(SCAN_TIMEOUT)
            result = sock.connect_ex((host, port))
            sock.close()
            if result != 0:
                return None
        except Exception:
            return None

        # Phase 2: verify it's Ollama and fetch models
        try:
            client = OllamaClient(
                base_url=f"http://{host}:{port}",
                timeout=MODEL_TIMEOUT
            )
            models = client.list_models()
        except Exception:
            return None

        # Phase 3: hostname resolution
        hostname = OllamaClient.resolve_hostname(host)

        return _build_nodule(
            host_ip=host,
            port=port,
            hostname=hostname,
            models=models,
            priority=1
        )


# ---------------------------------------------------------------------------
# Unified Discovery
# ---------------------------------------------------------------------------

class OllamaDiscovery:
    """
    Runs mDNS and polling concurrently, merges and deduplicates results.

    mDNS results arrive quickly for cooperative hosts.
    Polling catches everything else within one timeout window.
    Both run simultaneously — total discovery time is
    max(mDNS_timeout, polling_timeout) not their sum.

    Deduplication is by normalized IP-based URL, so the same host
    found by both paths appears only once in the result.
    """

    @classmethod
    def discover(cls, subnet: str = DEFAULT_SUBNET,
                 port: int = DEFAULT_PORT,
                 mdns_timeout: float = MDNS_TIMEOUT) -> list[dict]:
        """
        Run concurrent mDNS + polling discovery, return merged results.

        Args:
            subnet:       CIDR subnet for polling fallback
            port:         Ollama port
            mdns_timeout: How long to browse mDNS (seconds)

        Returns:
            Deduplicated list of nodule dicts, sorted by IP.
        """
        mdns_results: list[dict] = []
        polling_results: list[dict] = []
        mdns_error: Optional[Exception] = None
        polling_error: Optional[Exception] = None

        def run_mdns():
            nonlocal mdns_results, mdns_error
            try:
                mdns_results = MDNSDiscovery.discover(
                    timeout=mdns_timeout, port=port
                )
            except Exception as e:
                mdns_error = e
                logger.warning(f"mDNS discovery failed: {e}")

        def run_polling():
            nonlocal polling_results, polling_error
            try:
                polling_results = PollingDiscovery.scan_subnet(
                    subnet=subnet, port=port
                )
            except Exception as e:
                polling_error = e
                logger.warning(f"Polling discovery failed: {e}")

        mdns_thread = threading.Thread(target=run_mdns, daemon=True)
        polling_thread = threading.Thread(target=run_polling, daemon=True)

        mdns_thread.start()
        polling_thread.start()

        mdns_thread.join()
        polling_thread.join()

        # Merge and deduplicate by URL
        # mDNS results take precedence — they may have richer hostname info
        merged: dict[str, dict] = {}

        for nodule in mdns_results:
            merged[nodule["url"]] = nodule

        for nodule in polling_results:
            url = nodule["url"]
            if url not in merged:
                merged[url] = nodule
            else:
                # Already found via mDNS — enrich with polling data if needed
                existing = merged[url]
                if not existing.get("hostname") and nodule.get("hostname"):
                    existing["hostname"] = nodule["hostname"]
                    existing["label"] = f"Ollama-{nodule['hostname']}"

        results = sorted(merged.values(), key=lambda n: n["host"])
        logger.info(
            f"Discovery complete: {len(results)} unique instance(s) "
            f"({len(mdns_results)} mDNS, {len(polling_results)} polling)"
        )
        return results


# ---------------------------------------------------------------------------
# Convenience: discover and update config in one call
# ---------------------------------------------------------------------------

def discover_and_save(subnet: str = DEFAULT_SUBNET,
                      port: int = DEFAULT_PORT,
                      config_path: Path = DEFAULT_CONFIG_PATH,
                      mdns_timeout: float = MDNS_TIMEOUT
                      ) -> tuple[list[dict], list[dict]]:
    """
    Run discovery, update config with dedup logic, persist to disk.

    Args:
        subnet:       CIDR subnet for polling
        port:         Ollama port
        config_path:  Path to config file
        mdns_timeout: mDNS browse window in seconds

    Returns:
        Tuple of (new_nodules, updated_nodules) so the caller can
        report what changed without re-diffing the config.
    """
    config = NoduleConfig(config_path)
    existing_count = len(config)

    found = OllamaDiscovery.discover(
        subnet=subnet,
        port=port,
        mdns_timeout=mdns_timeout
    )

    new_nodules = []
    updated_nodules = []

    for nodule in found:
        result, was_new = config.add_or_update(nodule)
        if was_new:
            result["priority"] = existing_count + len(new_nodules) + 1
            new_nodules.append(result)
        else:
            updated_nodules.append(result)

    if new_nodules or updated_nodules:
        config.save()

    return new_nodules, updated_nodules