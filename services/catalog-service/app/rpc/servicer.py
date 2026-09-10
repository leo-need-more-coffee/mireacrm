import grpc
from mirea.catalog.v1 import catalog_pb2, catalog_pb2_grpc
from mireacrm_common.lifespan import AppContext
from mireacrm_common.rpc import Registration, parse_uuid

from app import domain
from app.rpc import mapping


class CatalogServicer(catalog_pb2_grpc.CatalogServiceServicer):
    def __init__(self, context: AppContext) -> None:
        self._context = context

    async def GetService(self, request, _context):
        branch_id = parse_uuid(request.branch_id, "branch_id") if request.branch_id else None

        async with self._context.session() as session:
            service = await domain.get_service(
                session, parse_uuid(request.service_id, "service_id"), branch_id
            )
        return catalog_pb2.GetServiceResponse(service=mapping.service(service))

    async def GetConsumptionNorms(self, request, _context):
        async with self._context.session() as session:
            norms = await domain.consumption_norms(
                session, parse_uuid(request.service_id, "service_id")
            )
        return catalog_pb2.GetConsumptionNormsResponse(
            norms=[mapping.norm(norm) for norm in norms]
        )


def registration(context: AppContext) -> Registration:
    def register(server: grpc.aio.Server) -> None:
        catalog_pb2_grpc.add_CatalogServiceServicer_to_server(CatalogServicer(context), server)

    return Registration(
        register=register,
        full_name=catalog_pb2.DESCRIPTOR.services_by_name["CatalogService"].full_name,
    )
