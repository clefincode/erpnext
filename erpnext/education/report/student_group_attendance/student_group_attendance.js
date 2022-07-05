// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Student Group Attendance"] = {
	"filters": [
		{
		"fieldname": "student_group",
		"label": __("Student Group"),
		"fieldtype": "Link",
		"options": "Student Group",
		"reqd": 1
		},
		{
		"fieldname": "type",
		"label": __("Attendance Foe"),
		"fieldtype": "Select",
		"options": ["Students" ,"Instructors"],
		"reqd": 1
		}
	]
};
