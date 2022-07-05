// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Training Plan Tool', {
	plan_income_expected: function (frm) {
		frm.set_value("difference", frm.doc.plan_income_expected - frm.doc.required_income);
	},
	required_income: function (frm) { frm.trigger("plan_income_expected"); },
	from_date: function (frm) {
		frm.call({
			method: "get_courses_count_in_period",
			doc: frm.doc,
			callback: function (d) {
				frm.refresh_field("courses_count_in_period");
			}
		});
	},
	till_date: function (frm) { frm.trigger("from_date");}
	
});

frappe.ui.form.on('Training Plan Tool Program', {
	repetition: function (frm, cdt, cdn) {
		calc_estimated_income(frm, cdt, cdn);
	},
	stu_count: function (frm, cdt, cdn) {
		calc_estimated_income(frm, cdt, cdn);
	},
	enrollment_fee: function (frm, cdt, cdn) {
		calc_estimated_income(frm, cdt, cdn);
	},
	programs_remove: function (frm, cdt, cdn) {
		frappe.call({
			method: "calc_totals",
			doc: frm.doc,
			callback: function (d) {
				frm.refresh_field('plan_income_expected');
				frm.refresh_field('difference');
			},
			freeze: 1,
			async: 0
		});
	}
});

function calc_estimated_income(frm, cdt, cdn) {
	var row = locals[cdt][cdn];
	row.estimated_income = row.repetition * row.stu_count * row.enrollment_fee;
	frm.refresh_field("programs");
	frappe.call({
		method: "calc_totals",
		doc: frm.doc,
		callback: function (d) {
			frm.refresh_field('plan_income_expected');
			frm.refresh_field('difference');

		}
	});
}