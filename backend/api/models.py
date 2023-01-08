from django.db import models

class Employee(models.Model):
    d_id = models.CharField(primary_key=True, max_length=50)
    mfi_created = models.BooleanField(default=False)
    d_branch = models.CharField(max_length=50, default="")
    first_name = models.CharField(max_length=50,default="")
    last_name = models.CharField(max_length=50,default="")
    phone = models.CharField(max_length=50,default="")
    plaid_id = models.CharField(max_length=50,default="")
    loan_acc = models.CharField(max_length=50,default="")

class Source(models.Model):
    d_id = models.CharField(primary_key=True, max_length=50)
    mfi_created = models.BooleanField(default=False)
    aba_routing = models.CharField(max_length=50,default="")
    account_number = models.CharField(max_length=50,default="")
    name = models.CharField(max_length=50,default="")
    dba = models.CharField(max_length=50,default="")
    ein = models.CharField(max_length=50,default="")

class Payment(models.Model):
    batch_id = models.CharField(max_length=50, default="")
    pay_to = models.ForeignKey(Employee, on_delete=models.CASCADE, default="")
    pay_from = models.ForeignKey(Source, on_delete=models.CASCADE, default="")
    amount = models.CharField(max_length=50, default="")    
    status = models.CharField(default="NOT EXECUTED", max_length=50)
    last_updated = models.DateTimeField(auto_now_add=True)
    # todo: add field for IDEMP key

class Batch(models.Model):
    batch_id = models.CharField(max_length=50, primary_key=True)
    data = models.JSONField(default=dict)