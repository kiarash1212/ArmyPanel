from django.core.management import BaseCommand

from models.configure.models import Server, Node
from utils.api.node import fetch_all_nodes
from utils.api.token import check_token_status


class Command(BaseCommand):
    def handle(self, *args, **options):
        servers = Server.objects.filter(is_active=True)

        for item in servers:
            # Check token
            item.get_token()

            # Fetch nodes list from server
            node_list = fetch_all_nodes(item)
            for node in node_list['data']['nodes']:
                item_model, is_create = Node.objects.get_or_create(provider_id=node['id'], name=node['name'])
                item_model.domain = node['domain']
                item_model.port = node['port']
                item_model.type = node['nodeTypeId']

                if node['status'] == 1:
                    item_model.is_active = True
                else:
                    item_model.is_active = False
                item_model.server = item
                item_model.save()
        self.stdout.write(
            self.style.SUCCESS('Successfully update contract list')
        )
