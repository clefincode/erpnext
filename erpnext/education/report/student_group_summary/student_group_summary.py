# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt

def execute(filters=None):
	columns, data = get_columns() , get_data(filters)
	return columns, data

def get_data(filters):
	data = []
	sg_filters = {
		"start_date": ["between", [filters.from_date, filters.till_date]]
	}
	if filters.status: sg_filters.update({"status": filters.status})
	if filters.program: sg_filters.update({"program": filters.program})
	student_groups = frappe.get_list("Student Group", filters = sg_filters, fields = ["name", "status", "student_count", "total_hours"])
	for sg in student_groups:
		row = {"student_group": sg.name, "status": sg.status, "student_count": sg.student_count, "standard_hours": sg.total_hours}
		fee_structures = frappe.get_list("Fees", filters = {"student_group": sg.name}, pluck = "fee_structure")
		fee_structures = frappe.get_list("Fee Structure", filters = {"name": ["in", fee_structures], "description": "Enrollment Fee"}, pluck = "name")
		row.update({"fee_structure_avg": frappe.get_list("Fee Structure", fields = ["avg(total_amount) total_amount"], filters = {"name": ["in",fee_structures]})[0].total_amount or 0})
		fees = frappe.get_list("Fees", filters = {"fee_structure": ["in",fee_structures], "student_group": sg.name, "docstatus": 1}, pluck = "name")
		row.update({"fees_sum": frappe.get_list("Fees", fields = ["sum(grand_total) grand_total"], filters = {"name": ["in", fees]})[0].grand_total or 0})
		row.update({"discount_sum": frappe.get_list("Discount Voucher", fields = ["sum(discount_amount) amount"], filters = {"apply_for_fee": ["in", fees], "docstatus": 1})[0].amount or 0})
		row.update({"net_income": flt(row["fees_sum"]) - flt(row["discount_sum"])})
		instructor_invoice_sums = frappe.get_list("Instructor Invoice", filters = {"student_group": sg.name, "docstatus": 1}, fields = ["sum(grand_total) grand_total", "sum(total_count_hour) total_count_hour"])
		row.update({"instructors_cost": instructor_invoice_sums[0].grand_total or 0 , "actual_hours": instructor_invoice_sums[0].total_count_hour})
		data.append(row)
	return data




def get_columns():
	return[
		{
			"label": "Student Group",
			"fieldtype": "Link",
			"fieldname": "student_group",
			"options": "Student Group",
			"width": "400"
		},
		{
			"label": "Status",
			"fieldtype": "Data",
			"fieldname": "status",
			"width": "80"
		},
		{
			"label": "Standard Hours",
			"fieldtype": "Data",
			"fieldname": "standard_hours",
			"width": "80"
		},
		{
			"label": "Actual Hours",
			"fieldtype": "Data",
			"fieldname": "actual_hours",
			"width": "80"
		},
		{
			"label": "Student Count",
			"fieldtype": "Data",
			"fieldname": "student_count",
			"width": "80"
		},
		{
			"label": "Selling Price",
			"fieldtype": "Currency",
			"fieldname": "fee_structure_avg",
			"width": "120"
		},
		{
			"label": "Total Invoice",
			"fieldtype": "Currency",
			"fieldname": "fees_sum",
			"width": "140"
		},
		{
			"label": "Total Discount",
			"fieldtype": "Currency",
			"fieldname": "discount_sum",
			"width": "140"
		},
		{
			"label": "Net Income",
			"fieldtype": "Currency",
			"fieldname": "net_income",
			"width": "140"
		},
		{
			"label": "Instructors Exp",
			"fieldtype": "Currency",
			"fieldname": "instructors_cost",
			"width": "140"
		}

		
	]
