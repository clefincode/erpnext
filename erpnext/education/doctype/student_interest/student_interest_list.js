frappe.listview_settings['Student Interest'] = {
	get_indicator: function(doc) {
			return [__(doc.status), {
				"رغبة":"orange",
				"مهتم":"light blue",
				"مهتم لكن السعر": "light blue",
				"مهتم لكن التوقيت": "light blue",
				"سيرد خبر":"light blue",
				"سيسجل اكيد": "light blue",
				"غير ذلك": "light blue",
				"تم التسجيل": "green",
				"غير مهتم": "red"
			}[doc.status], "status,=," + doc.status];
		},
	hide_name_column: true
	}