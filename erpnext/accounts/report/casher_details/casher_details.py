# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import today


def execute(filters=None):
	columns =[
	{
		"fieldname": "type",
		"label": _("Type"),
		"fieldtype": "Data" ,
		"width": 100
	},
	#{	
	#	"fieldname": "account",
	#	"label": _("Account"),
	#	"fieldtype": "Link" ,
    #   "options": "Account" ,  
	#	"width": 100
	#},
	{
      "fieldname": "party_type",
	  "label": _("Party type"),
	  "fieldtype": "Data",
	  "width": 100
	},
	{

    	"fieldtype": "party",
		"label": _("Party"),
		"fieldtype": "Data",
		"width": 100 

	},
	{
		"fieldtype": "data",
		"label": "Party Name",
		"fieldname": "party_name",
		"width": 100
	},
	{
		"filedname": "amount",
		"label": _("Amount"),
		"fieldtype": "Currency",
		"width": 100
	},
	{
		"fieldtype": "balance",
		"label": _("Balance"),
		"fieldtype": "Currency",
		"width": 100
	},
	]
	modeofpayment= frappe.db.get_value("User Mode of Payment",{"parent":frappe.session.user, "is_default":True}, "mode_of_payment")
	if not modeofpayment:
		frappe.throw("this users dosnt have mode of payment")
	L=frappe.get_list("Payment Entry", filters={"posting_date":today(),"mode_of_payment":modeofpayment,"docstatus":1},fields=["payment_type","party","party_type","party_name","paid_from","paid_amount","paid_to",],order_by="creation")
	data=[]
	balance=0
	#account=""
	for k in L:
		if k.payment_type=="Receive":
		#	account=k.paid_from
			balance+=k.paid_amount
		else :
			balance-=k.paid_amount
		#	account=k.paid_to
		data.append({
		"type": k.payment_type,
		#"account":account,
		"party_type":k.party_type,
		"party_name": k.party_name,
		"party":k.party,
		"amount":k.paid_amount,
		"balance":balance,
		
		})
		
	



	return columns, data



