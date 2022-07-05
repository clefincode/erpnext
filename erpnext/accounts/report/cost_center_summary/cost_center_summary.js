// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Cost Center Summary"] = {
	"filters": [
		{
			label: "Company",
			fieldname: "company",
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			label: "Academic Year",
			fieldname: "academic_year",
			fieldtype: "MultiSelectList",
			options: "Academic Year",
			get_data: function(txt){
				return frappe.db.get_link_options("Academic Year", txt);
			}
		}

	]
};
