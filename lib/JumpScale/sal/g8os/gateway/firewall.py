from JumpScale.sal.g8os.gateway import templates
import ipaddress


class Firewall:
    def __init__(self, container, publicip, privatenetwork, forwards):
        self.container = container
        self.publicip = publicip
        self.privatenetwork = ipaddress.IPv4Network(privatenetwork)
        self.forwards = forwards

    def apply_rules(self):
        # nftables
        nftables = templates.render('nftables.conf')
        self.container.upload_content('/etc/nftables.conf', nftables)
        snat = templates.render('snat.rules', subnet=str(self.privatenetwork.network_address),
                                subnetmask=self.privatenetwork.prefixlen, publicip=self.publicip)
        self.container.upload_content('/etc/snat_rules', snat)
        dnat = templates.render('dnat.rules', portforwards=self.forwards)
        self.container.upload_content('/etc/dnat_rules', dnat)
        self.container.system('nft -f /etc/nftables.conf').get()