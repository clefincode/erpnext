// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Student Group Summary"] = {
	"filters": [
		{
			fieldtype: "Link",
			label: "Program",
			fieldname: "program",
			options: "Program"
		},
		{
			fieldtype: "Select",
			fieldname: "status",
			label: "Status",
			options: ["","Pending", "Available", "Active", "Finished"]
		},
		{
			fieldtype: "Date",
			fieldname: "from_date",
			label: "From Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
			reqd: 1
		},
		{
			fieldtype: "Date",
			fieldname: "till_date",
			label: "Till Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		}

	]
};
