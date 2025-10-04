from collections import defaultdict

from data_backend.models import APIResponse, APIRequest


class ResponseHandler:
    def __init__(self):
        self.parsers = {}
        self.generators = defaultdict(list)
        self._new_requests = []

    def add_parser(self, request_type: str, handler_func) -> "ResponseHandler":
        self.parsers[request_type] = handler_func
        return self
    
    def add_request_generator(self, request_type: str, handler_func) -> "ResponseHandler":
        self.generators[request_type].append(handler_func)
        return self
    
    def handle(self, response: APIResponse):
        for generator in self.generators.get(response.request.type, []):
            new_requests = generator(response.body)
            if new_requests:
                self._new_requests.extend(new_requests)
        parser = self.parsers.get(response.request.type)
        if not parser:
            raise ValueError(f"No parser registered for response type '{response.request.type}'")
        return parser(response.body)
        
    def collect_new_requests(self):
        while self._new_requests:
            yield self._new_requests.pop(0)
