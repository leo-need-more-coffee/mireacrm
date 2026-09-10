import grpc
from mirea.client.v1 import client_pb2, client_pb2_grpc
from mireacrm_common.lifespan import AppContext
from mireacrm_common.rpc import Registration, parse_uuid

from app import commands, domain
from app.rpc import mapping


class ClientServicer(client_pb2_grpc.ClientServiceServicer):
    def __init__(self, context: AppContext) -> None:
        self._context = context

    async def GetClientContacts(self, request, _context):
        async with self._context.session() as session:
            client = await domain.get_client(
                session, parse_uuid(request.client_id, "client_id")
            )
        return client_pb2.GetClientContactsResponse(contacts=mapping.contacts(client))

    async def AddLoyaltyPoints(self, request, _context):
        accrual = commands.LoyaltyAccrual(
            invoice_id=parse_uuid(request.invoice_id, "invoice_id"),
            paid_kopecks=request.paid.amount_kopecks,
        )

        async with self._context.session() as session:
            client, added = await domain.accrue_points(
                session, parse_uuid(request.client_id, "client_id"), accrual
            )

        return client_pb2.AddLoyaltyPointsResponse(
            points_added=added, points_balance=client.points_balance
        )


def registration(context: AppContext) -> Registration:
    def register(server: grpc.aio.Server) -> None:
        client_pb2_grpc.add_ClientServiceServicer_to_server(ClientServicer(context), server)

    return Registration(
        register=register,
        full_name=client_pb2.DESCRIPTOR.services_by_name["ClientService"].full_name,
    )
