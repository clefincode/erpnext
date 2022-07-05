frappe.listview_settings['Program Disenrollment'] = {
	add_fields: ["unpaid_balance"],
	get_indicator: function(doc) {
		if(flt(doc.unpaid_balance)==0 && doc.docstatus == 1) {
			return [__("Paid"), "green", "unpaid_balance,=,0"];
		} else if (flt(doc.unpaid_balance) > 0 && doc.docstatus == 1 ) {
			return [__("Unpaid"), "orange", "unpaid_balance,>,0"];
		}		},

	hide_name_column: true
}
