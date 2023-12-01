from django.shortcuts import render
from . import data, forecaster
from django.http import JsonResponse

# Create your views here.
def getAQI(request):
    return render(request, 'index.html')


def demo(request):
    if request.method == 'POST':
        searchKey = request.POST.get("searchKey")
        #get the historical data of the city
        hist = data.getCityData(city_name=searchKey)
        #get the predictions 
        predictions = forecaster.getForecastData(data=hist)

        return JsonResponse(predictions)
    
