// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Item Details Never Sold"] = {
	"filters": [

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
		{
			"fieldname":"warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"width": "80",
			"options" : "Warehouse",
			"reqd":  0
        },
		{
			"fieldname":"item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"width": "80",
			"options" : "Item",
			"reqd":  0
        },
		{
			"fieldname":"status",
			"label": __("Status"),
			"fieldtype": "Select",
			"width": "80",
			"default" : "Enabled",
			"options" : ["Disabled","Enabled"],
			"reqd":  1
        }


	]
};
