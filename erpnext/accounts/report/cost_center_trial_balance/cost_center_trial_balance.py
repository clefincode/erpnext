# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	data = []
	cost_centers = frappe.get_list("Student Group", filters={"academic_year": ["in", filters.academic_year], "status": ["in", filters.status], "company": filters.company}, pluck="cost_center", order_by = "cost_center")
	for cost_center in cost_centers:
		data += get_debit_credit_for_cost_center(cost_center, filters, 0, is_group=False)
		data += get_debit_credit_for_cost_center(cost_center, filters, 1)
	final_data = []
	for d in data:
		if d.account:
			final_data.append(d)
	return final_data

def get_debit_credit_for_cost_center(cost_center, filters, indent, is_group=True):
	conditions = ""
	if not filters.view_balance_sheet_accounts:
		conditions += "and a.report_type = 'Profit and Loss' "
	account = "cost_center as account"
	group_by = ""
	if is_group:
		account = "gl.account"
		group_by = "group by gl.account"

	res =  frappe.db.sql("""select {account} ,sum(gl.debit) as debit, sum(gl.credit) as credit,
		sum(gl.debit) - sum(gl.credit) as balance ,%(indent)s as indent, gl.cost_center from `tabGL Entry`gl 
		join `tabAccount` a on a.name = gl.account 
		where gl.cost_center = %(cost_center)s and gl.is_cancelled = 0 {conditions} {group_by} 
		""".format(account = account, conditions = conditions, group_by = group_by), values = {"cost_center": cost_center, "indent": indent}, as_dict = True, debug = 1)
	return res

def get_columns():
	return [{
		"label": "Account",
		"fieldname": "account",
		"fieldtype": "Link",
		"options": "Account",
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
	},
	{
		"label": "Cost Center",
		"fieldname": "cost_center",
		"fieldtype": "Link",
		"options": "Cost Center",
		"width": 200
	}
	]

	


