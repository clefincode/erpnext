frappe.listview_settings['Student'] = {
	add_fields: [ "image"],
	get_indicator: function(doc) {
			return [__(doc.status), {
				"Prospective":  "blue",
				"Student":"green"
			}[doc.status], "status,=," + doc.status];
		}
	}
