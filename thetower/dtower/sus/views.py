from django.http import HttpResponse
from django.views import View


class SusView(View):
    def post(self, request):
        return HttpResponse()
