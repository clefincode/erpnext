// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Salesman Cash Report"] = {
	"filters": [
		{
			'fieldname': 'company',
			'fieldtype': 'Link',
			'label': 'Company',
			'options': 'Company',
			'default': frappe.defaults.get_user_default("Company"),
			'reqd': 1
		},
		{
			'fieldname': 'mode_of_payment',
			'fieldtype': 'MultiSelectList',
			'label': 'Mode Of Payment',
			'options': 'Mode of Payment',
			'reqd': 1,
			get_data: function(txt){
				return frappe.db.get_link_options("Mode of Payment", txt, {
					is_sales: 1
				});
			}
		},
		{
			'fieldname': 'start_date',
			'fieldtype': 'Date',
			'label': 'Start Date',
			'default': frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			'reqd': 1,
		},
		{
			'fieldname': 'end_date',
			'fieldtype': 'Date',
			'label': 'End Date',
			'default': frappe.datetime.get_today(),
			'reqd': 1
		},
		{
			'fieldname': 'student_group',
			'fieldtype': 'Link',
			'label': 'Student Group',
			'options': 'Student Group'
		}
	]
};
