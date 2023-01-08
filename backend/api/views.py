from rest_framework.response import Response
from rest_framework.decorators import api_view
import xml.etree.ElementTree as ET
from .models import Payment, Batch
from .helper import qs_to_csv_response, succint_view, get_batches, newParse
import json
from django.http import HttpResponse
import csv

# todo: error handling, try/catches

@api_view(["GET", "POST"])
def getCsv(request):
    response = Response()
    if request.method == "POST":
        csv_type, batch_id = request.data['type'], request.data['batch_id']
        if csv_type == "payments":
            return qs_to_csv_response(Payment.objects.filter(batch_id=batch_id), csv_type) 
        elif csv_type == "sources" or csv_type=="branches":
            query = Batch.objects.get(batch_id=batch_id)
            batch_dict = json.loads(query.data)['data'][csv_type]
            response = HttpResponse(
                content_type='text/csv',
                headers={'Content-Disposition': 'attachment; filename={}.csv'.format(csv_type)},
            )
            dict_writer = csv.DictWriter(response, batch_dict[0].keys())
            dict_writer.writeheader()
            dict_writer.writerows(batch_dict)
            return response
    if request.method == "GET":
        return get_batches()

@api_view(["POST"])
def getData(request):
    response = Response()
    if request.method == "POST":
        t = request.FILES['upload_file']
        response.data = succint_view(t.file)
    return response



@api_view(["POST"])
def processData(request):
    response = Response()
    if request.method == "POST":
        t = request.FILES['upload_file']
        response.data = newParse(t.file, approved=True)
    return response    

# todo: Payments/account queue
# todo: web hooks