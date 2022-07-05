frappe.listview_settings['Student Group'] = {
	hide_name_column: true,
	colwidths: {"days_str": 3},
	get_indicator: function(doc) {
			return [__(doc.status), {
				"Pending":  "grey",
				"Available":"orange",
				"Active":  "blue",
				"Finished":"green"
			}[doc.status], "status,=," + doc.status];
	}
}
