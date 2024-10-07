// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Details Never Sold"] = {
	"filters": [

		{
			"fieldname":"item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"width": "150",
			"options": "Item",
        },

		{
			"fieldname":"warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"width": "150",
			"options": "Warehouse",
        },

		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": __("From Date"),
			"default" : frappe.datetime.month_start(),
			"reqd":  0  

		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": __("To Date"),
			"reqd":  0  , 
			"default": frappe.datetime.month_end()
		},


	]
};
