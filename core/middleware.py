from django.utils.cache import add_never_cache_headers

class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Prevent caching for all authenticated pages
        if request.user.is_authenticated:
            add_never_cache_headers(response)
        return response
