// Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.require("assets/erpnext/js/financial_statements.js", function() {
	frappe.query_reports["Direct Cash Flow"] = $.extend({},
		erpnext.financial_statements);
	frappe.query_reports["Direct Cash Flow"]["filters"].splice(8, 1);
	frappe.query_reports["Direct Cash Flow"]["filters"].splice(1, 1);
});