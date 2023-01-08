import datetime
import uuid
from django.db import connection
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
import collections
import xml.etree.ElementTree as ET
from .models import Employee, Source, Payment, Batch
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
import json

# todo: error handling, try catches

def get_batches():
    query = Batch.objects.all().values()
    d = []
    for each in query:
        cur_data = {
            "batch_id": each["batch_id"],
            "date_approved": json.loads(each['data'])["date_approved"]
        }
        cur = json.loads(each['data'])['data']
        if "total_cost" in cur:
            cur_data['status'] = "IN PROGRESS"
            total = sum(x['initial_owed_count'] for x in cur['sources'])
            paid = sum(x['paid_so_far_count'] for x in cur['sources'])
            cur_data['payments_remaining'] = total-paid
        else:
            cur_data['status'] = 'INITIALIZING'
            cur_data['payments_remaining'] = "..."
        d.append(cur_data)
    return JsonResponse({'batch_list': list(d)})


def newParse(file, approved=False):
    # if batch_id already in batch, return 'already approved'
    # assumes employee/source table is generated already
    branch_amt = collections.defaultdict(float)
    branch_cnt = collections.defaultdict(int)
    source_amt = collections.defaultdict(float)
    source_cnt = collections.defaultdict(int)
    total = 0

    # todo: batch_id should be passed in as a param
    batch_id = "BAT_"+ uuid.uuid4().hex[:10]
    now = datetime.datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    if approved:
        b = Batch()
        b.batch_id = batch_id
        b.data = json.dumps({"date_approved":now, "data":{}}, cls=DjangoJSONEncoder)
        b.save()

    curEmp = Employee()
    curSource = Source()
    curPayment = Payment()
    sourceMap = {}
    pays = []

    context = ET.iterparse(file, events=("start", "end"))

    for index, (event, elem) in enumerate(context):
        # Get the root element.
        if index == 0:
            root = elem 
        # Using array index assumes XML will preserve format order.
        # If we cannot make this assumption, check each elem.tag individually.
        if event == "end" and elem.tag == "Employee":
            curEmp = Employee.objects.get(pk=elem[0].text)
            #arr = [elem[x].text for x in range(len(elem))]
            #d_id, d_branch, f_name, l_name, dob, phone = arr
            #curEmp.d_id, curEmp.d_branch, = d_id, d_branch
            root.clear()
            elem.clear()
        if event == "end" and elem.tag == "Payor":
            # arr = [elem[x].text for x in range(len(elem)-1)]
            # d_id, aba_routing, acc_num, name, dba, ein = arr
            #curSource.d_id = d_id
            d_id = elem[0].text
            if d_id in sourceMap:
                curSource = sourceMap[d_id]
            else:
                curSource = Source.objects.get(pk=d_id)
                sourceMap[d_id] = curSource
            root.clear()
            elem.clear()
        # if event == "end" and elem.tag == "Payee":
        #     plaid, loan_acc = elem[0].text, elem[1].text
        #     root.clear()
        if event == "end" and elem.tag == "Amount":
            if approved:
                curPayment.amount = elem.text
                curPayment.pay_to = curEmp
                curPayment.pay_from = curSource
                curPayment.batch_id = batch_id
                curPayment.last_updated = now
                #curPayment.save()
                # batch approval, much faster and prevents partial
                pays.append(curPayment)
                curPayment = Payment()
            amt = float(elem.text[1:])
            total += amt
            branch_amt[curEmp.d_branch] += amt
            branch_cnt[curEmp.d_branch] += 1
            source_amt[curSource.d_id] += amt
            source_cnt[curSource.d_id] += 1
            root.clear()
            elem.clear()

    Payment.objects.bulk_create(pays)

    branches = [
        {
            "branch_id": k, 
            "initial_owed": "$" + str(round(v,2)),
            "initial_owed_count": branch_cnt[k],
            "paid_so_far": "$0", 
            "paid_so_far_count":0,
            "last_updated": now
        } for k,v in branch_amt.items()
    ]
    sources = [
        {
            "dunkin_id": k, 
            "initial_owed": "$" + str(round(v,2)),
            "initial_owed_count": source_cnt[k],
            "paid_so_far": "$0", 
            "paid_so_far_count":0,
            "last_updated": now
        } for k,v in source_amt.items()
    ]
    data = {
        "total_cost": str(round(total,2)),
        "total_payments":sum(source_cnt.values()),
        "branches": branches,
        "sources": sources,
    }
    if approved:
        b = Batch.objects.get(batch_id=batch_id)
        b.data = json.dumps({"date_approved":now, "data":data}, cls=DjangoJSONEncoder)
        b.save()
    return data

def succint_view(file):
    branch_amt = collections.defaultdict(float)
    branch_cnt = collections.defaultdict(int)
    source_amt = collections.defaultdict(float)
    source_cnt = collections.defaultdict(int)
    total = 0

    context = ET.iterparse(file, events=("start", "end"))
        
    cur = ["", ""]
    for index, (event, elem) in enumerate(context):
        if index == 0:
            root = elem
        if event == "end" and elem.tag == "DunkinBranch":
            cur[0] = elem.text
            root.clear()
        if event == "end" and elem.tag == "Payor":
            cur[1] = elem[0].text
            root.clear()
        if event == "end" and elem.tag == "Amount":
            amt = float(elem.text[1:])
            total += amt
            branch_amt[cur[0]] += amt
            branch_cnt[cur[0]] += 1
            source_amt[cur[1]] += amt
            source_cnt[cur[1]] += 1
            root.clear()

    branches = [(k,"$" + str(round(v,2)), branch_cnt[k]) for k,v in branch_amt.items()]
    sources = [(k,"$" + str(round(v,2)), source_cnt[k]) for k,v in source_amt.items()]
    data = {
        "total_cost": str(round(total,2)),
        "total_payments":sum([s[2] for s in sources]),
        "branches": branches,
        "sources": sources,
        # todo: generate and return batch_id here
    }
    return data

def qs_to_csv_response(qs, filename):
    sql, params = qs.query.sql_with_params()
    sql = f"COPY ({sql}) TO STDOUT WITH (FORMAT CSV, HEADER, DELIMITER E'\t')"
    filename = f'{filename}-{timezone.now():%Y-%m-%d_%H-%M-%S}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    with connection.cursor() as cur:
        sql = cur.mogrify(sql, params)
        cur.copy_expert(sql, response)
    return response

def create_employees_also(file):
    context = ET.iterparse(file, events=("start", "end"))
    batch_id = 'xd'
    cur = ["", ""]
    newEmp = Employee()
    newSource = Source()
    curPayment = Payment()
    empSeen = set()
    sourceSeen = set()
    cur_employee_id = ""
    cur_source_id = ""
    swap = 1
    for index, (event, elem) in enumerate(context):
        if index == 0:
            root = elem 
        if event == "end" and elem.tag == "DunkinId":
            # employee_id
            if swap > 0:
                cur_employee_id = elem.text
                newEmp.d_id = cur_employee_id
                if cur_employee_id in empSeen:
                    curPayment.pay_to = Employee.objects.get(d_id=cur_employee_id)
            else:
                cur_source_id = elem.text
                newSource.d_id = cur_source_id
                if cur_source_id in sourceSeen:
                    curPayment.pay_from = Source.objects.get(d_id=cur_source_id)
            root.clear()
            swap *= -1
        elif event == "end" and elem.tag == "DunkinBranch":
            cur_employee_branch = elem.text
            cur[0] = cur_employee_branch
            newEmp.d_branch = cur_employee_branch
            root.clear()
        elif event == "end" and elem.tag == "FirstName":
            cur_employee_fname = elem.text
            newEmp.first_name = cur_employee_fname
            root.clear()
        elif event == "end" and elem.tag == "LastName":
            newEmp.last_name = elem.text
            root.clear()
        elif event == "end" and elem.tag == "PhoneNumber":
            newEmp.phone = elem.text
            root.clear()
        elif event == "end" and elem.tag == "ABARouting":
            newSource.aba_routing = elem.tag
            root.clear()
        elif event == "end" and elem.tag == "AccountNumber":
            cur_source_acc = elem.text
            newSource.account_number = cur_source_acc
            root.clear()
        elif event == "end" and elem.tag == "Name":
            newSource.name = elem.text
            root.clear()
        elif event == "end" and elem.tag == "DBA":
            newSource.dba = elem.text
        elif event == "end" and elem.tag == "EIN":
            newSource.ein = elem.text
            root.clear()
        elif event == "end" and elem.tag == "PlaidId":
            newEmp.plaid_id = elem.text
            root.clear()
        elif event == "end" and elem.tag == "LoanAccountNumber":
            newEmp.loan_acc = elem.text
            root.clear()
        elif event == "end" and elem.tag == "Amount":
            amt = float(elem.text[1:])
            curPayment.amount = amt
            curPayment.batch_id = batch_id
            if cur_employee_id not in empSeen:
                newEmp.save()
                empSeen.add(cur_employee_id)
                curPayment.pay_to = newEmp
            if cur_source_id not in sourceSeen:
                newSource.save()
                sourceSeen.add(cur_source_id)
                curPayment.pay_from = newSource
            curPayment.save()
            newEmp = Employee()
            newSource = Source()
            curPayment = Payment()
            #
            cur = ["", ""]
            root.clear()
