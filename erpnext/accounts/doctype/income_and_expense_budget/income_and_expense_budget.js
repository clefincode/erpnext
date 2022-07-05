// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Income and Expense Budget', {
});

frappe.ui.form.on('Income and Expense Budget Expense', {
	growth_rate: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		row.growth_balance = row.period_balance * (100 + parseFloat(row.growth_rate)) / 100;
		frm.refresh_field('expenses');
	}
});

frappe.ui.form.on('Income and Expense Budget Income', {
	growth_rate: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		row.growth_balance = row.period_balance * (100 + parseFloat(row.growth_rate)) / 100;
		frm.refresh_field('incomes');
	}
});
