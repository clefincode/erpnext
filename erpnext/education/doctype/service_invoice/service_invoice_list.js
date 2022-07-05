frappe.listview_settings['Service Invoice'] = {
	add_fields: ["grand_total", "outstanding_amount"],
	get_indicator: function(doc) {
		if(flt(doc.outstanding_amount)==0) {
			return [__("Paid"), "green", "outstanding_amount,=,0"];
		} else if (flt(doc.outstanding_amount) > 0 ) {
			return [__("Unpaid"), "orange", "outstanding_amount,>,0|due_date,>,Today"];
		}
	},
	hide_name_column: true
};