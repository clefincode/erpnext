// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Education Selling Target"] = {
	"filters": [
		{
			fieldtype: "Date",
			fieldname: "start_date",
			label: "Start Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1
		},
		{
			fieldtype: "Date",
			fieldname: "end_date",
			label: "End Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldtype: "Link",
			fieldname: "program",
			label: "Program",
			options: "Program"
		}
	]
};
