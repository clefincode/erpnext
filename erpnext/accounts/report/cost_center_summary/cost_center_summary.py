# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data
	
def get_columns():
	return [{
		"label": "Cost Center",
		"fieldname": "cost_center",
		"fieldtype": "Link",
		"options": "Cost Center",
		"width": 500
	},
	{
		"label": "Debit",
		"fieldname": "debit",
		"fieldtype": "Currency",
		"width": 200
	},
	{
		"label": "Credit",
		"fieldname": "credit",
		"fieldtype": "Currency",
		"width": 200
	},
	{
		"label": "Balance",
		"fieldname": "balance",
		"fieldtype": "Currency",
		"width": 200
	}
	]

def get_data(filters):
	data = []
	sg_filters = {
		"company": filters.company
	}
	if filters.academic_year:
		sg_filters.update({"academic_year": ["in",filters.academic_year]})
	student_groups = frappe.get_list("Student Group", filters = sg_filters, fields = ["program", "cost_center", "name"], order_by = "program")
	if student_groups:
		parent_row = {
			"program": student_groups[0].program,
			"cost_center" : student_groups[0].program,
			"credit": 0,
			"debit": 0
		}
		index = 0
		for sg in student_groups:
			debit_credit = get_debit_credit_for_cost_center(sg.cost_center)
			if parent_row["program"] != sg.program:
				parent_row.update({"balance": parent_row["credit"] - parent_row["debit"]})
				data.insert(index, parent_row)
				parent_row = {
					"program": sg.program,
					"cost_center": sg.program,
					"credit": 0,
					"debit": 0
					}
				#new index
				index = len(data)
			data.append({
				"cost_center": sg.cost_center,
				"debit": debit_credit.debit,
				"credit": debit_credit.credit,
				"balance": debit_credit.credit - debit_credit.debit,
				"indent": 1,
			})
			parent_row["credit"] += debit_credit.credit
			parent_row["debit"] += debit_credit.debit
	return data

def get_debit_credit_for_cost_center(cost_center):
	res =  frappe.db.sql("""select sum(gl.debit) as debit, sum(gl.credit) as credit from `tabGL Entry`gl 
		join `tabAccount` a on a.name = gl.account 
		where a.report_type = 'Profit and Loss' and gl.cost_center = %(cost_center)s 
		""", values = {"cost_center": cost_center}, as_dict = True)[0]
	res.debit = 0 if not res.debit else res.debit
	res.credit = 0 if not res.credit else res.credit
	return res
