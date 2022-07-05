// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Commission', {
	get_data: function (frm) {
		frappe.call({
			method: "get_data",
			doc: frm.doc,
			callback: function(r){
				frm.refresh_fields();
				frm.dirty();
			},
			freeze: 1
		});
	},
	refresh_summaries: function (frm) {
		frappe.call({
			method: "refresh_summaries",
			doc: frm.doc,
			callback: function(r){
				frm.refresh_fields();
				frm.dirty();
			},
			freeze: 1
		});
	}
});
