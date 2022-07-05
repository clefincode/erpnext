# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import today


def execute(filters=None):
	if not filters.mode_of_payment:
		return [], []
	columns =[
	{
		"fieldname": "type",
		"label": _("Type"),
		"fieldtype": "Data" ,
		"width": 100
	},
	{
      "fieldname": "party_type",
	  "label": _("Party Type"),
	  "fieldtype": "Data",
	  "width": 100
	},
	{

    	"fieldname": "party",
		"label": _("Party"),
		"fieldtype": "Data",
		"width": 170

	},
	{
		"fieldtype": "Data",
		"label": _("Party Name"),
		"fieldname": "party_name",
		"width": 170
	},
	{
		"fieldname": "amount",
		"label": _("Amount"),
		"fieldtype": "Currency",
		"width": 130
	},
	{
		"fieldname": "balance",
		"label": _("Balance"),
		"fieldtype": "Currency",
		"width": 130
	},
	{
		"fieldname": "student_group",
		"label": _("Student Group"),
		"fieldtype": "Link",
		"options": "Student Group",
		"width": 400
	},
	{
		"fieldname": "fees_category",
		"label": _("Fee Category"),
		"fieldtype": "Link",
		"options": "Fee Category",
		"width": 100
	}
	]
	l = frappe.db.sql("""
	select name, payment_type, party, party_type, party_name, paid_from, paid_amount, paid_to from `tabPayment Entry`
	where company = %s and mode_of_payment in (%s) and posting_date between %s and %s and docstatus = 1
	"""%('%s',', '.join(['%s']*len(filters.mode_of_payment)), '%s', '%s'), tuple([filters.company]+ filters.mode_of_payment + [filters.start_date, filters.end_date]), as_dict = 1, debug = 1)
	data=[]
	balance=0
	for k in l:
		student_group = ""
		fees_category = ""
		refs = frappe.get_list("Payment Entry Reference", filters = {"parent": k.name}, fields = ["reference_name", "reference_doctype"])
		for ref in refs :
			if ref.reference_doctype == "Fees":
				student_group , fees_category = frappe.db.get_value(ref.reference_doctype, ref.reference_name, ["student_group", "fees_category"])
				break
		if filters.student_group and filters.student_group != student_group:
			continue
		if k.payment_type=="Receive":
			balance+=k.paid_amount
		else :
			balance-=k.paid_amount
		data.append({
		"type": k.payment_type,
		"party_type":k.party_type,
		"party_name": k.party_name,
		"party":k.party,
		"amount":k.paid_amount,
		"balance":balance,
		"student_group": student_group,
		"fees_category": fees_category
		})
	return columns, data