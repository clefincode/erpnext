from __future__ import unicode_literals
from frappe import _
from frappe.utils import getdate, cstr
import json	
import frappe
from datetime import date
import datetime
from dateutil.relativedelta import relativedelta
from frappe.utils import getdate, cstr, fmt_money
def execute(filters=None):
	if not filters:
		filters = {}
	conditions = get_conditions(filters)
	conditions_date = get_conditions_date(filters)
	data = []
	columns = get_columns(conditions ,  filters)
	data  = get_data_normal(conditions = conditions , conditions_date = conditions_date )
	return columns , data
def get_conditions(filters):
	conditions = ""
	# if filters.get("from_date"):
	# 	conditions += " and s.attendance_date >= '{}' ".format(filters.get("from_date"))
	# if filters.get("to_date"):
	# 	conditions += " and s.attendance_date <=  '{}' ".format(filters.get("to_date"))
	if filters.get("item_code"):
		conditions += " and i.item_code =  '{}' ".format(filters.get("item_code"))
	if filters.get("warehouse"):
		conditions += " and b.warehouse =  '{}' ".format(filters.get("warehouse"))
	# if filters.get("status") == "Disabled":
	# 	conditions += " and i.disabled = 0  "
	# if filters.get("status") == "Enabled":
	# 	conditions += " and i.disabled = 1  "
	return conditions
def get_conditions_date(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += " and s.posting_date >= '{}' ".format(filters.get("from_date"))
	if filters.get("to_date"):
		conditions += " and s.posting_date <=  '{}' ".format(filters.get("to_date"))
	return conditions
def get_data_normal(conditions   = "", conditions_date = "", filters = {}):
	data =  frappe.db.sql(""" 
		SELECT
			b.item_code AS item_code,
			i .name AS item_code_name,
			i.item_name AS item_name,
			b.warehouse AS warehouse,
			SUM(b.actual_qty) AS available_quantity
		FROM
			`tabItem` i
		left JOIN
			`tabBin` b ON i.item_code = b.item_code
		WHERE 
			1=1  and i.disabled = 0
			AND 
			i.item_code NOT IN (
				SELECT si.item_code
				FROM `tabSales Invoice Item` si
				INNER JOIN `tabSales Invoice` s ON si.parent = s.name
				WHERE s.docstatus = 1
				{}
			)
			
			{}
		GROUP BY
			i.item_code,
			b.warehouse
		ORDER BY
			i.item_code ASC;
			""".format(conditions_date , conditions ), as_dict=1 , debug = True)
	return data
# def get_data_normal(conditions   = "", filters = {}):
# 	data =  frappe.db.sql(""" 
# 		SELECT
# 			i.item_code AS item_code,
# 			i.item_name AS item_name,
# 			b.warehouse AS warehouse,
# 			SUM(b.actual_qty) AS available_quantity
# 		FROM
# 			`tabItem` i
# 		LEFT JOIN
# 			`tabBin` b ON i.name = b.item_code
# 		WHERE 
# 			1=1 {}
# 			AND 
# 			i.item_code NOT IN (
# 				SELECT si.item_code
# 				FROM `tabSales Invoice Item` si
# 				INNER JOIN `tabSales Invoice` s ON si.parent = s.name
# 				WHERE s.docstatus = 1
# 			)
# 		GROUP BY
# 			i.item_code,
# 			b.warehouse
# 		ORDER BY
# 			i.item_code ASC;
# 			""".format(conditions ), as_dict=1 , debug = True)
# 	return data
# def get_data_normal(conditions   = "", filters = {}):
# 	data =  frappe.db.sql(""" 
# 		SELECT 
# 			i.item_code AS item_code,
# 			b.warehouse AS warehouse,
# 			SUM(b.actual_qty) AS available_quantity
# 		FROM
# 			`tabItem` i
# 		LEFT JOIN
# 			`tabBin` b ON i.name = b.item_code
# 		WHERE 
# 			1=1 {}
# 			AND 
# 			i.item_code NOT IN (
# 				SELECT si.item_code
# 				FROM `tabSales Invoice Item` si
# 				INNER JOIN `tabSales Invoice` s ON si.parent = s.name
# 				WHERE s.docstatus = 1
# 			)
# 		GROUP BY
# 			i.item_code,
# 			b.warehouse
# 		ORDER BY
# 			i.item_code ASC;
# 			""".format(conditions ), as_dict=1 , debug = True)
# 	return data
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
		"fieldname": "warehouse",
		"label": "Warehouse",
		"fieldtype": "Data",
		"width": 250
		},
		{
		"fieldname": "available_quantity",
		"label": _("Quantity"),
		"fieldtype": "Data",
		"width": 100
		}
	]
	return columns