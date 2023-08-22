# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():
	return[
		{
			"fieldtype": "Link",
			"fieldname": "student_group",
			"label": "Student Group",
			"options": "Student Group"
		},
		{
			"fieldtype": "Currency",
			"fieldname": "minimum_limit",
			"label": "Minimum Limit",
		},
		{
			"fieldtype": "Currency",
			"fieldname": "achieved",
			"label": "Achieved"
		}
	]

def get_data(filters=None):
	sg_filters = {
		"start_date": ["between", [filters.start_date, filters.end_date]],
		"status": ["!=", "Pending"]
	}
	if filters.get("program"):
		sg_filters.update({"program": filters.get("program")})

	data = frappe.get_list("Student Group", filters=sg_filters, fields=["name as student_group", "program"])
	for d in data:
		minimum_limit = frappe.db.get_value("Fee Structure", {
			"program": d.program,
			"description": "Enrollment Fee",
			"status": "Active"}, "minimum_limit")
		if minimum_limit: 
			d.update({"minimum_limit": minimum_limit})
	return data

