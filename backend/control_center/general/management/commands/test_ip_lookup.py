from django.core.management.base import BaseCommand
from utils.ip_lookup_service import get_asn_from_ip, get_asn_from_ip_safe


class Command(BaseCommand):
    help = 'Test the IP-to-ASN lookup service'

    def handle(self, *args, **options):
        self.stdout.write("Testing IP-to-ASN Lookup Service")
        self.stdout.write("=" * 50)
        
        test_ips = [
            ("8.8.8.8", "Google DNS"),
            ("1.1.1.1", "Cloudflare DNS"),
            ("208.67.222.222", "OpenDNS"),
            ("192.168.1.1", "Private IP"),
            ("invalid-ip", "Invalid IP"),
        ]
        
        for ip, description in test_ips:
            try:
                result = get_asn_from_ip(ip)
                if result:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ {ip} ({description}) -> ASN: {result['asn']}, Org: {result['organization']}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"❌ {ip} ({description}) -> Not found")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ {ip} ({description}) -> Error: {e}")
                )
        
        self.stdout.write("\nTesting safe function:")
        self.stdout.write("=" * 30)
        
        # Test safe function
        result = get_asn_from_ip_safe("invalid-ip")
        self.stdout.write(f"invalid-ip (safe) -> {result}")
        
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("Test completed"))
