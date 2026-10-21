import schemathesis

schema = schemathesis.openapi.from_path(
    "../docs/api/drift/openapi.yaml"
)

schema.config.base_url = "http://localhost:8000"



import schemathesis
from hypothesis import settings

schema = schemathesis.openapi.from_path(
    "../docs/api/drift/openapi.yaml"
)

schema.config.base_url = "http://localhost:8000"


@schema.parametrize()
@settings(max_examples=10, deadline=None)
def test_api_contract(case):
    case.call_and_validate()
