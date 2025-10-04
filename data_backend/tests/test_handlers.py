from data_backend.handlers import ResponseHandler
from data_backend.models import APIResponse, APIRequest
import pytest


def test_add():

    def sample_parser(body):
        return {"parsed": True}
    
    def sample_generator(body):
        return [{"url": "http://example.com/new"}]
    
    handler = ResponseHandler()\
        .add_parser("sample_type", sample_parser)\
        .add_request_generator("sample_type", sample_generator)

    
    assert "sample_type" in handler.parsers
    assert handler.parsers["sample_type"] == sample_parser
    assert "sample_type" in handler.generators
    assert sample_generator in handler.generators["sample_type"]


def test_handle_and_collect():
    def sample_parser(body):
        return {"parsed": True}
    
    def sample_generator(body):
        return [APIRequest(url="http://example.com/new", type="sample_type2")]
    
    handler = ResponseHandler()\
        .add_parser("sample_type", sample_parser)\
        .add_request_generator("sample_type", sample_generator)
    
    response = handler.handle(
        APIResponse(
            body="{'data': 'value'}",
            request=APIRequest(type="sample_type", url="http://example.com")
        )
    )

    assert response == {"parsed": True}
    new_requests = list(handler.collect_new_requests())
    assert len(new_requests) == 1
    assert new_requests[0].url == "http://example.com/new"
    assert new_requests[0].type == "sample_type2"


def test_handle_no_parser():    
    handler = ResponseHandler()
    
    with pytest.raises(ValueError):
        handler.handle(
            APIResponse(
                body="{'data': 'value'}",
                request=APIRequest(type="sample_type", url="http://example.com")
            )
        )
