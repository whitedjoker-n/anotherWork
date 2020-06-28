from django.http import JsonResponse
from django.shortcuts import render

from appGame.models import KLine


def klineview(request):
    return render(request, 'newtest.html')


def runoob(request):
    context = KLine.objects.values().filter(code='HK.00001')[0:20]
    print(context)
    list(context)
    # return render(request, 'kline.html')
    return JsonResponse({"status": 1, "data": list(context)}, safe=False)
