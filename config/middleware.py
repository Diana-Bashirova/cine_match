import time
import logging

logger = logging.getLogger('django.request')

class ResponseTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"{request.method} {request.path} | Status: {response.status_code} | Duration: {duration_ms:.2f}ms"
        )
        return response