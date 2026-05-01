#!/usr/bin/env python3
"""
Native Claude Client - Main Entry Point
Testing CLI for network-local Ollama architecture
"""

import argparse
import sys
import json
import socket
from typing import List, Dict, Optional
from pathlib import Path

try:
    import ollama
    from ollama import Client
except ImportError:
    print("⚠ ollama package not found. Install with: pip install ollama")
    sys.exit(1)


class NetworkOllamaDiscovery:
    """Discover Ollama instances on the local network"""
    
    DEFAULT_PORT = 11434
    TIMEOUT = 2  # seconds
    
    @staticmethod
    def scan_subnet(subnet: str = "192.168.12.0/24") -> List[Dict[str, str]]:
        """
        Scan subnet for Ollama instances
        
        Args:
            subnet: CIDR notation (e.g., "192.168.12.0/24")
        
        Returns:
            List of dicts with 'host', 'port', 'models'
        """
        import ipaddress
        
        network = ipaddress.ip_network(subnet, strict=False)
        found_instances = []
        
        print(f"🔍 Scanning {subnet} for Ollama instances (port {NetworkOllamaDiscovery.DEFAULT_PORT})...")
        
        for ip in network.hosts():
            host_str = str(ip)
            if NetworkOllamaDiscovery._test_ollama_host(host_str):
                found_instances.append({
                    'host': host_str,
                    'port': NetworkOllamaDiscovery.DEFAULT_PORT,
                    'url': f"http://{host_str}:{NetworkOllamaDiscovery.DEFAULT_PORT}"
                })
                print(f"  ✓ Found Ollama at {host_str}")
        
        return found_instances
    
    @staticmethod
    def _test_ollama_host(host: str, port: int = DEFAULT_PORT) -> bool:
        """Test if a host is running Ollama"""
        try:
            # Try socket connection first (faster)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(NetworkOllamaDiscovery.TIMEOUT)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                # Verify it's actually Ollama by trying to list models
                try:
                    client = Client(host=f"http://{host}:{port}")
                    client.list()
                    return True
                except Exception:
                    return False
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_models(host: str, port: int = DEFAULT_PORT) -> List[str]:
        """Get list of models available on an Ollama instance"""
        try:
            client = Client(host=f"http://{host}:{port}")
            models = client.list()
            return [m['name'] for m in models.get('models', [])]
        except Exception as e:
            print(f"⚠ Could not fetch models from {host}: {e}")
            return []


class NetworkOllamaRouter:
    """Route requests to network Ollama instances"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".config" / "erebos" / "config.json"
        self.nodules = []
        self.load_config()
    
    def load_config(self):
        """Load nodule configuration"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.nodules = config.get('nodules', [])
                    print(f"✓ Loaded {len(self.nodules)} nodules from {self.config_path}")
            except Exception as e:
                print(f"⚠ Error loading config: {e}")
        else:
            print(f"ℹ No config found at {self.config_path}")
            print(f"  Run 'erebos discover' to find Ollama instances")
    
    def save_config(self):
        """Save nodule configuration"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump({'nodules': self.nodules}, f, indent=2)
        print(f"✓ Config saved to {self.config_path}")
    
    def add_nodule(self, host: str, port: int = 11434, label: str = None, priority: int = 1):
        """Add a nodule to the configuration"""
        nodule = {
            'host': host,
            'port': port,
            'url': f"http://{host}:{port}",
            'label': label or f"Ollama @ {host}",
            'priority': priority,
            'type': 'ollama',
            'location': 'network'
        }
        self.nodules.append(nodule)
        print(f"✓ Added nodule: {nodule['label']}")
    
    def list_nodules(self):
        """List configured nodules with status"""
        if not self.nodules:
            print("No nodules configured.")
            return
        
        print("\n📡 Configured Nodules:")
        print("-" * 80)
        
        for i, nodule in enumerate(self.nodules, 1):
            status = "🟢" if self._test_nodule(nodule) else "🔴"
            models = NetworkOllamaDiscovery.get_models(nodule['host'], nodule['port'])
            model_count = len(models)
            
            print(f"{i}. {status} {nodule['label']}")
            print(f"   URL: {nodule['url']}")
            print(f"   Priority: {nodule['priority']} | Location: {nodule['location']}")
            print(f"   Models: {model_count} available")
            if models:
                print(f"   → {', '.join(models[:3])}" + (f" (+{model_count-3} more)" if model_count > 3 else ""))
            print()
    
    def _test_nodule(self, nodule: Dict) -> bool:
        """Test if a nodule is reachable"""
        return NetworkOllamaDiscovery._test_ollama_host(nodule['host'], nodule['port'])
    
    def run_request(self, prompt: str, model: str = "llama3.2", nodule_index: int = None):
        """
        Run a request through the network routing system
        
        Args:
            prompt: User prompt
            model: Model name
            nodule_index: Optional specific nodule to use (1-based index)
        """
        if not self.nodules:
            print("❌ No nodules configured. Run 'discover' first.")
            return
        
        # Select nodule
        if nodule_index is not None:
            if nodule_index < 1 or nodule_index > len(self.nodules):
                print(f"❌ Invalid nodule index: {nodule_index}")
                return
            nodule = self.nodules[nodule_index - 1]
        else:
            # Auto-select by priority (lowest number = highest priority)
            available = [n for n in self.nodules if self._test_nodule(n)]
            if not available:
                print("❌ No nodules are currently reachable")
                return
            nodule = min(available, key=lambda n: n['priority'])
        
        print(f"🚀 Routing to: {nodule['label']} ({nodule['url']})")
        print(f"📝 Prompt: {prompt}")
        print(f"🤖 Model: {model}")
        print("-" * 80)
        
        try:
            client = Client(host=nodule['url'])
            
            # Stream response
            stream = client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            )
            
            print("\n💬 Response:")
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    print(chunk['message']['content'], end='', flush=True)
            
            print("\n" + "-" * 80)
            print(f"✓ Request completed via {nodule['label']}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")


def cmd_discover(args):
    """Discover Ollama instances on the network"""
    subnet = args.subnet or "192.168.12.0/24"
    
    instances = NetworkOllamaDiscovery.scan_subnet(subnet)
    
    if not instances:
        print(f"\n❌ No Ollama instances found on {subnet}")
        print("   Make sure Ollama is running on your Desktop/P71 and accessible on the network")
        return
    
    print(f"\n✓ Found {len(instances)} Ollama instance(s)")
    print("\nDiscovered instances:")
    print("-" * 80)
    
    for i, instance in enumerate(instances, 1):
        models = NetworkOllamaDiscovery.get_models(instance['host'])
        print(f"{i}. {instance['url']}")
        print(f"   Models: {len(models)} available")
        if models:
            print(f"   → {', '.join(models)}")
        print()
    
    # Offer to add to config
    if args.save:
        router = NetworkOllamaRouter()
        for i, instance in enumerate(instances, 1):
            label = f"Ollama-{instance['host'].split('.')[-1]}"
            router.add_nodule(
                host=instance['host'],
                port=instance['port'],
                label=label,
                priority=i
            )
        router.save_config()


def cmd_add(args):
    """Manually add a nodule"""
    router = NetworkOllamaRouter()
    router.add_nodule(
        host=args.host,
        port=args.port,
        label=args.label,
        priority=args.priority
    )
    router.save_config()


def cmd_list(args):
    """List configured nodules"""
    router = NetworkOllamaRouter()
    router.list_nodules()


def cmd_run(args):
    """Run a test request"""
    router = NetworkOllamaRouter()
    router.run_request(
        prompt=args.prompt,
        model=args.model,
        nodule_index=args.nodule
    )


def cmd_config(args):
    """Show or edit configuration"""
    router = NetworkOllamaRouter()
    
    if args.show:
        print(f"\n📄 Config file: {router.config_path}")
        if router.config_path.exists():
            with open(router.config_path, 'r') as f:
                print(f.read())
        else:
            print("(No config file exists yet)")
    
    if args.reset:
        if router.config_path.exists():
            router.config_path.unlink()
            print(f"✓ Removed config file: {router.config_path}")
        else:
            print("No config file to remove")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Erebos - Network Ollama Testing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover Ollama instances on default network (192.168.12.0/24)
  erebos discover --save
  
  # Discover on custom subnet
  erebos discover --subnet 192.168.1.0/24 --save
  
  # List configured nodules
  erebos list
  
  # Run a test request (auto-routes to best available nodule)
  erebos run "What is 2+2?"
  
  # Run with specific model
  erebos run "Explain Python" --model llama3.2:70b
  
  # Run on specific nodule
  erebos run "Hello" --nodule 1
  
  # Manually add a nodule
  erebos add 192.168.12.50 --label "Desktop" --priority 1
  
  # Show configuration
  erebos config --show
  
  # Reset configuration
  erebos config --reset
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # discover command
    discover_parser = subparsers.add_parser('discover', help='Discover Ollama instances on network')
    discover_parser.add_argument('--subnet', help='Subnet to scan (CIDR notation, e.g., 192.168.12.0/24)')
    discover_parser.add_argument('--save', action='store_true', help='Save discovered instances to config')
    discover_parser.set_defaults(func=cmd_discover)
    
    # add command
    add_parser = subparsers.add_parser('add', help='Manually add a nodule')
    add_parser.add_argument('host', help='Hostname or IP address')
    add_parser.add_argument('--port', type=int, default=11434, help='Port (default: 11434)')
    add_parser.add_argument('--label', help='Human-readable label')
    add_parser.add_argument('--priority', type=int, default=1, help='Priority (lower = higher priority)')
    add_parser.set_defaults(func=cmd_add)
    
    # list command
    list_parser = subparsers.add_parser('list', help='List configured nodules')
    list_parser.set_defaults(func=cmd_list)
    
    # run command
    run_parser = subparsers.add_parser('run', help='Run a test request')
    run_parser.add_argument('prompt', help='Prompt to send')
    run_parser.add_argument('--model', default='llama3.2', help='Model to use (default: llama3.2)')
    run_parser.add_argument('--nodule', type=int, help='Specific nodule index to use (1-based)')
    run_parser.set_defaults(func=cmd_run)
    
    # config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    config_parser.add_argument('--reset', action='store_true', help='Reset configuration')
    config_parser.set_defaults(func=cmd_config)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command specified
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Execute command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()