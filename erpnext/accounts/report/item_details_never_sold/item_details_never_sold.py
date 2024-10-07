from __future__ import unicode_literals
from frappe import _
from frappe.utils import getdate, cstr
import json	
import frappe
import ast
from datetime import date
import datetime
from dateutil.relativedelta import relativedelta
from frappe.utils import getdate, cstr, fmt_money
from datetime import *
from dateutil.relativedelta import *
import calendar
from datetime import date, timedelta
from frappe.utils import add_days, getdate, formatdate, nowdate ,  get_first_day, date_diff, add_years  , flt, cint, getdate, now


def execute(filters=None):
	if not filters:
		filters = {}

	conditions = get_conditions(filters)
	data = []
	columns = get_columns(conditions , filters)
	data  = get_data_normal(conditions = conditions )
	return columns , data


def get_conditions(filters):
	conditions = ""
	if filters.get("warehouse"):
		conditions += " and wh.name =  '{}' ".format(filters.get("warehouse"))
	if filters.get("item_code"):
		conditions += " and si.item_code =  '{}' ".format(filters.get("item_code"))


	if filters.get("from_date"):
		conditions += " and s.posting_date >= '{}' ".format(filters.get("from_date"))
	if filters.get("to_date"):
		conditions += " and s.posting_date <=  '{}' ".format(filters.get("to_date"))
	return conditions





def get_data_normal(conditions   = "", filters = {}):
	data =  frappe.db.sql(""" 
		SELECT i.item_code as item_code
		FROM `tabItem` i
		WHERE 1=1
		AND i.item_code NOT IN (
		SELECT si.item_code
		FROM `tabSales Invoice Item` si
		INNER JOIN `tabSales Invoice` s ON si.parent = s.name
		WHERE s.docstatus = 1 {}
		GROUP BY si.item_code
		)
		GROUP BY i.item_code, i.item_name;
	 """.format(conditions ), as_dict=1 , debug = True)
	print(data)

	return data








def get_columns(conditions  = "" ,  filters = {}):
	columns = [
		{
		"fieldname": "item_code",
		"label": "Item Code",
		"fieldtype": "Data",
		"width": 250
		},

		{
		"fieldname": "item_name",
		"label": "Item Name",
		"fieldtype": "Data",
		"width": 150
		},


		{
		"fieldname": "available_qty",
		"label": _("Quantity"),
		"fieldtype": "Data",
		"width": 80
		},

		{
		"fieldname": "warehouse",
		"label": _("Warehouse"),
		"fieldtype": "Data",
		"width": 200
		},


	]

	return columns








