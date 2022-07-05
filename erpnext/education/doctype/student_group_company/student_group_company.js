// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student Group Company Student', {
	mark: function(frm, cdt, cdn){
		let row = locals[cdt][cdn];
		frappe.call({
			method: "erpnext.education.api.get_grade",
			args: {
				grading_scale: frm.doc.grading_scale,
				percentage: (parseFloat(row.mark)/ parseFloat(frm.doc.maximum_score)) * 100
			},
			callback: function(response){
				if(response.message){
					row.grade = response.message;
					frm.refresh_field("students");
				}
			}
		})
	}
	
});
